# P2-01-C-D2: True Multi-Worker Runtime — Evidence

**Status:** Construction Complete, awaiting independent architecture audit
**Baseline:** ee69925b3186a0332b0ce3db8aff64c06f97f400 (D-1)
**Branch:** feature/P2-01-C-D2-true-multi-worker
**Date:** 2026-09-11

---

## 1. Architecture

### Worker Model
```
TLLVM
├── Program (shared, read-only)
├── Globals (shared)
├── Heap (shared)
├── Workers[]
│   ├── Worker 0 → TLLExecutionContext ctx0
│   ├── Worker 1 → TLLExecutionContext ctx1
│   └── Worker N → TLLExecutionContext ctxN
└── Global Runnable Queue (thread-safe)
```

### Key Structures
- `TLLWorker`: worker_id, independent ctx, vm back-pointer, running flag, tasks_completed
- `TLLExecutionContext`: callStack, callStackSize, callStackCapacity, currentCoroutine, invokeTargetStackSize
- `TLLRunnableQueue`: thread-safe FIFO queue with mutex + semaphore

### Thread-Local Context
- `g_tll_current_worker`: `__declspec(thread)` / `__thread` pointer to current worker
- `TLL_CTX(vm)` macro: returns `&worker->ctx` if on worker thread, else `&vm->ctx`

---

## 2. g_vm_lock Status

**Status:** Removed for new multi-worker path.

- New `runtime.startWorkers()` / `runtime.submitCoroutine()` / `runtime.shutdownWorkers()` API does NOT use `g_vm_lock`.
- Each worker thread executes `tll_vm_exec(vm)` with its own independent context.
- Legacy HTTP server path may still use `g_vm_lock` (not modified in D-2).

---

## 3. Global Runnable Queue

### Implementation
- `tll_runnable_queue_init()`: allocates CRITICAL_SECTION + Semaphore (Windows) / pthread_mutex + cond (POSIX)
- `tll_runnable_queue_enqueue()`: thread-safe enqueue with mutex, signals semaphore
- `tll_runnable_queue_dequeue()`: blocks on semaphore, then mutex-protected dequeue

### Opaque Pointer Types
- `TLL_MUTEX = void*`, `TLL_SEM = void*`, `TLL_THREAD = void*`
- Actual CRITICAL_SECTION/HANDLE allocated in vm.c, avoids windows.h include in tllvm.h

---

## 4. Coroutine Ownership

### State Machine
- `TLL_COROUTINE_RUNNABLE = 0`
- `TLL_COROUTINE_RUNNING = 1`
- `TLL_COROUTINE_WAITING = 2`
- `TLL_COROUTINE_COMPLETED = 3`

### Execution Flow
```
coroutine.spawn(fn) → creates coroutine, returns index
runtime.submitCoroutine(idx) → enqueues to global queue
Worker dequeues → loads coroutine callStack → tll_vm_exec()
  → if callStackSize == 0: COMPLETED
  → else: re-enqueue as RUNNABLE (yielded/waiting)
```

### Safety
- One coroutine executed by exactly one worker at a time
- Worker sets state to RUNNING before execution
- Completed coroutines skipped by workers

---

## 5. Parallel Execution Evidence

### Test: multi_worker_parallel.tll (2 Workers, 2 Tasks)
```
=== P2-01-C-D2 Multi-Worker Parallel Test ===
CPU count: 4
startWorkers(2) = 0
workerCount = 2
spawned coroutines: 1, 2
submitCoroutine: 0, 0
TASK_1 START worker=0
TASK_2 START worker=1
TASK_1 END worker=0 sum=4999950000
TASK_2 END worker=1 sum=4999950000
All tasks completed: worker0=1 worker1=1
Final tasks completed: worker0=1 worker1=1
Workers shutdown
TEST_RESULT: PASS (2 tasks completed by workers)
```

**Key observations:**
- TASK_1 executed on worker=0, TASK_2 executed on worker=1
- Both tasks completed successfully
- No task loss, no duplicate execution

### Test: multi_worker_stress_2w_100t.tll (2 Workers, 100 Tasks)
```
=== P2-01-C-D2 Concurrency Test: 2W/100T ===
Workers started: 2
Submitted 100 tasks
All tasks completed: worker0=51 worker1=49
Final: worker0=51 worker1=49 total=100
TEST_RESULT: PASS (100/100 tasks completed, no loss)
```

**Key observations:**
- 100/100 tasks completed, no loss
- Load balanced: worker0=51, worker1=49
- No crash, no deadlock

---

## 6. Concurrency Correctness Tests

| Test | Workers | Tasks | Result |
|------|---------|-------|--------|
| multi_worker_parallel.tll | 2 | 2 | PASS |
| multi_worker_stress_2w_100t.tll | 2 | 100 | PASS |

**Verified:**
- No task loss
- No duplicate execution
- No crash
- No deadlock
- Load balancing across workers

---

## 7. Regression Tests

| Test | Result |
|------|--------|
| test_simple_coroutine.tll | PASS |
| coroutine_512_test.tll | PASS |
| coroutine_sleep_test.tll | PASS (Test 1 & 2) |
| test_spawn.tll | PASS |
| dynamic_frame_test.tll | PASS (ALL TESTS PASSED) |

**No regressions detected.**

---

## 8. New Builtin API (223-229)

| Index | Function | Description |
|-------|----------|-------------|
| 223 | runtime.startWorkers(count) | Start N worker threads, returns 0 on success |
| 224 | runtime.submitCoroutine(coro_idx) | Submit coroutine to global queue, returns 0 on success |
| 225 | runtime.shutdownWorkers() | Shutdown all workers, returns 0 |
| 226 | runtime.currentWorkerId() | Returns current worker ID, -1 if main thread |
| 227 | runtime.workerCount() | Returns number of active workers |
| 228 | runtime.workerTasksCompleted(worker_id) | Returns tasks completed by worker |
| 229 | runtime.cpuCount() | Returns CPU core count |

---

## 9. Files Modified

- `host/c/tllvm.h`: TLL_COROUTINE_* constants, TLLRunnableNode/TLLRunnableQueue/TLLWorker structures, TLLVM extension (workers[], runnable_queue, etc.), opaque pointer types (TLL_MUTEX/TLL_SEM/TLL_THREAD), g_tll_current_worker extern
- `host/c/vm.c`: g_tll_current_worker thread-local, TLL_CTX() macro, 132 field access migrations, queue init/enqueue/dequeue, worker thread function, start/submit/shutdown API, opaque pointer allocation
- `host/c/builtin.c`: builtin 223-229 implementation
- `compiler/codegen.tll`: runtime module builtin registration (223-229)
- `tools/TLLC/tllc.tllbc`: recompiled with codegen.tll changes

---

## 10. Known Limitations (B-GAP)

- **Atomic Heap / RefCount:** Not implemented in D-2. Heap objects still use plain int refCount. Workers should not concurrently modify shared heap objects without external synchronization.
- **Work Stealing:** Not implemented. Workers use a single global FIFO queue.
- **IO Reactor:** Not modified. Existing IO-aware scheduler remains.
- **Global State Fine-Grained Locking:** Not implemented. globals array remains shared.
- **Linux/macOS:** Code compiles conceptually (POSIX paths present), but not tested on Linux/macOS.
- **ASan:** Not run (environment permission issue, inherited from B12).
- **Full Native/Cross-target Regression:** Not run in D-2 (focus on runtime multi-worker).
- **coroutine_100K:** Not run in D-2.

---

## 11. Performance Observations (MEASURED, not formal benchmark)

- 2 Workers / 100 Tasks: completed successfully with load balancing (51/49)
- Worker context switch overhead: minimal (queue dequeue + callStack load)
- No formal performance comparison with baseline (different test methodology)

---

## 12. Build & Test Commands

```bash
# Build
cmd /c build_all.bat

# Compile test
tllvm.exe tools\TLLC\tllc.tllbc compile tests\multi_worker_parallel.tll -o tests\multi_worker_parallel.tllbc

# Run test
tllvm.exe tests\multi_worker_parallel.tllbc
```

---

## 13. Self-Audit Checklist

- [x] True Per-Worker ExecutionContext (ctx0 != ctx1)
- [x] Worker 0 can execute TLL, Worker 1 can execute TLL
- [x] No global VM execution lock serializes workers
- [x] Task A and Task B execution windows overlap (different workers)
- [x] 100-task stress: no loss, no duplicate, no crash, no deadlock
- [x] Existing coroutine functionality intact
- [x] Dynamic Frame (D-1) intact
- [x] No || true
- [x] No fake measurements
- [x] No deleted/weakened tests
- [x] Git clean (no .exe/.obj/temp files)

---

**Construction Complete. Awaiting independent architecture audit.**
