# P2-01-C-D2 Reality Audit

**Baseline:** ee69925b3186a0332b0ce3db8aff64c06f97f400 (D-1)
**Branch:** feature/P2-01-C-D2-true-multi-worker
**Date:** 2026-09-11

---

## 1. Current State Classification

### 1.1 VM-Global State (shared across all workers)
| State | Location | Shared? | Thread Safe? |
|-------|----------|---------|--------------|
| `TLLProgram *program` | `TLLVM.program` | Yes (read-only) | Immutable |
| `TLLValue *globals` | `TLLVM.globals` | Yes (mutable) | **No explicit sync** |
| `int globalCount` | `TLLVM.globalCount` | Yes | **No explicit sync** |
| `TLLCoroutine **coroutines` | `TLLVM.coroutines` | Yes (shared) | **No explicit sync** |
| `int coroutineCount` | `TLLVM.coroutineCount` | Yes | **No explicit sync** |
| `int coroutineCapacity` | `TLLVM.coroutineCapacity` | Yes | **No explicit sync** |
| Heap objects (Array/Map/String) | runtime/ | Yes (shared) | **refCount is plain int, NOT atomic** |

### 1.2 Execution-Local State (D-1 extracted to TLLExecutionContext)
| State | Location | Shared? |
|-------|----------|---------|
| `TLLFrame **callStack` | `TLLExecutionContext.callStack` | **No (per-worker)** |
| `int callStackSize` | `TLLExecutionContext.callStackSize` | **No** |
| `int callStackCapacity` | `TLLExecutionContext.callStackCapacity` | **No** |
| `int currentCoroutine` | `TLLExecutionContext.currentCoroutine` | **No** |
| `int invokeTargetStackSize` | `TLLExecutionContext.invokeTargetStackSize` | **No** |

**Current problem:** `TLLVM` contains only ONE `ctx` field. All workers share the same `ctx`. Not truly per-worker.

### 1.3 Coroutine-Local State
| State | Location |
|-------|----------|
| `TLLFrame **callStack` | `TLLCoroutine.callStack` |
| `int callStackSize` | `TLLCoroutine.callStackSize` |
| `int callStackCapacity` | `TLLCoroutine.callStackCapacity` |
| `int state` | `TLLCoroutine.state` (0=alive/ready, 2=dead) |
| `TLLValue result` | `TLLCoroutine.result` |
| `int invokeTargetStackSize` | `TLLCoroutine.invokeTargetStackSize` |
| `long long wakeTime` | `TLLCoroutine.wakeTime` |
| `int waitingFd` | `TLLCoroutine.waitingFd` |
| `int waitingEvents` | `TLLCoroutine.waitingEvents` |
| `void *waitingChannel` | `TLLCoroutine.waitingChannel` |
| `long long waitDeadline` | `TLLCoroutine.waitDeadline` |
| `int waitResult` | `TLLCoroutine.waitResult` |

### 1.4 Frame State (coroutine-owned, via callStack)
| State | Location |
|-------|----------|
| `TLLFunction *function` | `TLLFrame.function` |
| `int pc` | `TLLFrame.pc` |
| `TLLValue *registers` | `TLLFrame.registers` (Dynamic Frame, D-1) |
| `int registerCount` | `TLLFrame.registerCount` |
| `TLLValue *locals` | `TLLFrame.locals` |
| `int localCount/localCapacity` | `TLLFrame` |
| `TLLValue *argStack` | `TLLFrame.argStack` |
| `int argStackSize/argStackCapacity` | `TLLFrame` |
| `int *tryStack` | `TLLFrame.tryStack` |
| `int tryStackSize/tryStackCapacity` | `TLLFrame` |
| `int returnReg` | `TLLFrame.returnReg` |
| `int exception_pending` | `TLLFrame.exception_pending` |
| `TLLValue pending_exception` | `TLLFrame.pending_exception` |
| `TLLClosureEnv *closureEnv` | `TLLFrame.closureEnv` |

---

## 2. g_vm_lock Current Coverage

### 2.1 Definition
- **Windows:** `static CRITICAL_SECTION g_vm_lock;` (builtin.c:126)
- **POSIX:** `static pthread_mutex_t g_vm_lock = PTHREAD_MUTEX_INITIALIZER;` (builtin.c:222)

### 2.2 Usage Sites
Only ONE usage site: `http_process_task()` (builtin.c:391-400)
```c
EnterCriticalSection(&g_vm_lock);  // or pthread_mutex_lock
TLLValue resp = tll_vm_invoke(vm, handlerFn, handlerArgs, 1);
LeaveCriticalSection(&g_vm_lock);  // or pthread_mutex_unlock
```

### 2.3 Coverage Analysis
- g_vm_lock **only** protects HTTP server handler invocation
- It does NOT protect:
  - Coroutine scheduler (vm.c, single-threaded)
  - Global variable access
  - Heap/refCount operations
  - Coroutine table modifications
- The entire VM execution path (`tll_vm_exec`, `tll_vm_invoke`) is assumed single-threaded

### 2.4 Current Worker Model (HTTP only)
```
HTTP accept loop
    ↓ enqueue_task(HttpTask{vm, handler_fn, client_fd})
    ↓
Global Task Queue (g_queue_lock + g_task_sem)
    ↓
8 Worker threads (WORKER_POOL_SIZE=8)
    ↓ each worker:
    ↓ WaitForSingleObject(g_task_sem)
    ↓ dequeue task
    ↓ g_vm_lock (GLOBAL SERIALIZATION)
    ↓ tll_vm_invoke(SHARED vm, handler_fn)
    ↓ g_vm_unlock
    ↓ HTTP response
```

**Key problem:** All 8 workers share the SAME `vm` pointer and the SAME `ctx`. The `g_vm_lock` serializes ALL VM execution. This is NOT true multi-worker parallel execution.

---

## 3. Scheduler Current Location & Model

### 3.1 Location
- Coroutine scheduler is in `vm.c`, inside `tll_vm_exec()`
- It is a **cooperative single-threaded scheduler**
- No separate scheduler thread
- No work stealing
- No global runnable queue (coroutines are in `vm->coroutines[]` array)

### 3.2 Scheduling Logic
```
tll_vm_exec(vm):
    while (!tll_should_exit):
        if callStackSize <= targetStack:
            if invokeMode: break
            else: mark current coroutine dead → yield
        execute one bytecode instruction
        on OP_YIELD: switch to next runnable coroutine
        on OP_SLEEP: set wakeTime, yield
        on OP_WAIT_READ/WRITE/CHANNEL: set waiting state, yield
```

### 3.3 Coroutine State Machine
- `state = 0`: alive/ready (runnable or running)
- `state = 2`: dead
- No explicit RUNNING/WAITING distinction in state field
- Waiting is implied by `waitingFd > 0` or `waitingChannel != NULL` or `wakeTime > 0`

### 3.4 Coroutine Switching
- `coroutine_yield_to()` saves current callStack to coroutine, loads next coroutine's callStack
- Round-robin: scan `vm->coroutines[]` for next alive coroutine
- No priority, no affinity, no migration control

---

## 4. Shared Object Cross-Worker Boundary

### 4.1 Can Be Shared (read-only)
- `TLLProgram` (bytecode, functions, constants) — immutable after load
- Function metadata — immutable
- Bytecode instructions — immutable

### 4.2 Can Be Shared (mutable, NEEDS SYNC)
- `TLLValue *globals` — mutable, no current sync
- Heap objects (Array, Map, String, ClosureEnv) — mutable, refCount is plain int
- `TLLCoroutine **coroutines` table — mutable, no current sync

### 4.3 CANNOT Be Shared (execution-local)
- `callStack` — must be per-worker
- `currentCoroutine` — must be per-worker
- `invokeTargetStackSize` — must be per-worker
- Frame registers/locals — per-coroutine, but accessed via callStack

### 4.4 refCount Thread Safety
- `runtime/tll_runtime.h`: `int refCount;` — PLAIN INT, NOT ATOMIC
- `tll_value_incref()` / `tll_value_free()` — no synchronization
- **This is a known gap for D-2.** Concurrent incref/free from multiple workers is NOT safe.
- D-2 strategy: minimize cross-worker shared heap mutation; document as PENDING for D-3 (Atomic Heap)

---

## 5. Key Gaps for D-2

| Gap | Severity | D-2 Strategy |
|-----|----------|--------------|
| Only one `ctx` in TLLVM | Critical | Create `TLLWorker` with own `ctx`; TLLVM holds `Workers[]` |
| g_vm_lock serializes all VM execution | Critical | Remove for new multi-worker path; keep for HTTP legacy if needed |
| No general-purpose runnable queue | Critical | Implement Global Runnable Queue (mutex+cond) |
| Coroutine table not thread-safe | High | Add mutex for coroutine table operations |
| refCount not atomic | High | Document as PENDING; D-2 tests avoid cross-worker heap mutation |
| globals not thread-safe | High | Document as PENDING; D-2 tests use worker-local data |
| No worker abstraction | Critical | Define `TLLWorker` struct with id, thread, ctx, local state |
| No parallel execution proof | Critical | New test: multi_worker_parallel.tll with barrier-based overlap proof |
| Coroutine ownership not defined | High | Implement RUNNABLE/RUNNING/WAITING/COMPLETED state with sync |

---

## 6. D-2 Architecture Direction

```
TLLRuntime (TLLVM)
├── Program (shared, read-only)
├── Globals (shared, mutable — sync PENDING)
├── Heap (shared, mutable — refCount atomic PENDING)
├── Coroutine Table (shared, mutex-protected)
├── Global Runnable Queue (shared, mutex+cond)
└── Workers[]
    ├── Worker 0
    │   ├── worker_id = 0
    │   ├── thread handle
    │   ├── ctx0 (TLLExecutionContext — INDEPENDENT)
    │   └── local scheduler state
    ├── Worker 1
    │   ├── worker_id = 1
    │   ├── thread handle
    │   ├── ctx1 (TLLExecutionContext — INDEPENDENT)
    │   └── local scheduler state
    └── ...
```

**Worker lifecycle:**
1. Worker thread starts
2. Loop: dequeue runnable coroutine from Global Queue
3. Load coroutine's callStack into worker's ctx
4. Execute until yield/complete/wait
5. Save callStack back to coroutine
6. If complete: mark COMPLETED
7. If waiting: don't requeue (IO/timer will requeue later)
8. If yielded: requeue to Global Queue
9. Repeat

**Key invariant:** A coroutine is executed by exactly ONE worker at a time. The Global Queue + RUNNING state ensures this.

---

## 7. Reality Audit Conclusion

- Current runtime is fundamentally single-threaded for VM execution
- HTTP worker pool exists but is serialized by g_vm_lock
- D-1 ExecutionContext extraction is correct but only one instance exists
- D-2 must: create per-worker ctx, implement global runnable queue, implement worker threads, prove parallel execution
- Shared mutable state (globals, heap refCount, coroutine table) needs explicit synchronization or documentation as PENDING
- No need to modify bytecode format, opcodes, native ABI, or consensus

**Ready for implementation.**
