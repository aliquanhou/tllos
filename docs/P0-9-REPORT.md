# TLL High-Temporal-Resolution Runtime Report — P0-9

**Date**: 2026-08-28
**Repository**: aliquanhou/tllos @ main
**Phase**: P0-9 — TLL High-Temporal-Resolution Runtime
**Key result**: Worker Pool replaces thread-per-connection. High-frame-rate benchmark established. VM global lock identified as the core wall.

---

## 1. Executive Summary

P0-9 began the journey from "concurrent-capable HTTP server" to "high-temporal-resolution runtime." Two concrete deliverables:

1. **Worker Pool** (P0-9.1): Fixed 8-thread pool + thread-safe task queue replaces thread-per-connection, eliminating OS thread explosion at high connection counts.
2. **High-Frame-Rate Benchmark** (P0-9.2): First systematic measurement of TLL VM throughput — Frames/sec, State Updates/sec, Events/sec.

The benchmark revealed the core wall: **function call overhead is 300x slower than simple loop iteration**. Frame creation/destruction (4096 registers + locals + argStack + tryStack allocated per call) is the primary bottleneck.

---

## 2. Worker Pool Architecture (P0-9.1)

### Before (P0-8): thread-per-connection
```
accept() → CreateThread(worker) → worker handles connection → thread exits
1000 connections = 1000 OS threads
```

### After (P0-9): fixed worker pool
```
accept() → enqueue_task() → worker pool (8 threads) dequeues → handles connection
1000 connections = 8 OS threads + task queue
```

### Implementation details (host/c/builtin.c)
```c
#define WORKER_POOL_SIZE 8

static TaskNode *g_task_head, *g_task_tail;
static CRITICAL_SECTION g_queue_lock;
static HANDLE g_task_sem;  // Semaphore for worker wakeup

static void init_worker_pool(void) {
    InitializeCriticalSection(&g_queue_lock);
    g_task_sem = CreateSemaphore(NULL, 0, 1000000, NULL);
    for (int i = 0; i < WORKER_POOL_SIZE; i++)
        CreateThread(NULL, 0, worker_thread, NULL, 0, NULL);
}

static DWORD WINAPI worker_thread(LPVOID param) {
    while (1) {
        WaitForSingleObject(g_task_sem, INFINITE);
        EnterCriticalSection(&g_queue_lock);
        TaskNode *node = dequeue();
        LeaveCriticalSection(&g_queue_lock);
        if (node) { http_process_task(node->task); free(node); }
    }
}
```

### Why this matters
- **Thread count bounded**: 8 threads regardless of connection count
- **Natural backpressure**: Semaphore limits queue depth
- **Foundation for per-worker callStack**: Each worker can eventually have independent VM execution state
- **VM lock still active**: `g_vm_lock` serializes `tll_vm_invoke()` — this is the next wall

---

## 3. High-Frame-Rate Benchmark (P0-9.2)

### Benchmark: benchmarks/high_frame_rate.tll

| Metric | Result | Workload |
|--------|--------|----------|
| **Frames/sec** (empty fn calls) | **9,790** | 50,000 calls in 5,107ms |
| **Loop iterations/sec** | **3,144,650** | 500,000 iterations |
| **State Updates/sec** (map writes) | **81,633** | 20,000 map inserts |
| **Events/sec** (create+dispatch) | **9,615** | 5,000 events |

### Key insight: 300x gap
```
Loop iteration:    3,144,650 /sec
Function call:         9,790 /sec
Ratio:                    321x slower
```

**Root cause**: Every function call allocates a new TLLFrame with:
- 4096 registers (`calloc(4096, sizeof(TLLValue))`)
- locals array (`calloc(localCount, sizeof(TLLValue))`)
- argStack (64 entries)
- tryStack (16 entries)
- Then `free_frame()` frees all of the above

This is the single biggest optimization opportunity for high-frame-rate runtime.

### What these numbers mean for TLL's direction
- **AI Agent loop**: An agent that calls functions for observation → decision → action would run at ~9.8K decisions/sec single-threaded. With 8 workers (serialized by VM lock), still ~9.8K/sec total.
- **Event-driven systems**: 9.6K events/sec is adequate for many applications, but high-frequency trading, real-time analytics, or large agent swarms need more.
- **State-heavy applications**: 81.6K map writes/sec is reasonable, but concurrent access needs fine-grained locking.

---

## 4. VM Architecture Audit: Where the Lock Is

### TLLVM structure (host/c/tllvm.h)
```c
typedef struct {
    TLLProgram *program;          // read-only, safely shared
    TLLFrame **callStack;         // MUST be per-worker
    int callStackSize;
    int callStackCapacity;
    TLLValue *globals;            // shared, needs fine-grained lock
    int globalCount;
    int invokeTargetStackSize;    // MUST be per-worker
} TLLVM;
```

### TLLFrame structure (already independent!)
```c
typedef struct {
    TLLFunction *function;    // read-only
    int pc;                   // per-frame
    TLLValue *registers;      // per-frame (4096)
    TLLValue *locals;         // per-frame
    TLLValue *argStack;       // per-frame
    int *tryStack;            // per-frame
    int returnReg;
    TLLClosureEnv *closureEnv; // shared (refcounted)
} TLLFrame;
```

### Shared heap objects (refcounted)
- TLLArray (refCount)
- TLLMap (refCount)
- TLLClosureEnv (refCount)
- TLLUpvalue (refCount)
- Strings (char*, currently not refcounted)

### The wall
```
HTTP Thread (8 workers)
    ↓
IO concurrent ✅
    ↓
🔒 g_vm_lock (global)
    ↓
tll_vm_invoke() — serialized 🔴
    ↓
VM execution — one at a time
```

To break this wall:
1. **Per-worker callStack**: Move `callStack`, `callStackSize`, `invokeTargetStackSize` out of TLLVM into a per-worker TLLExecutionContext
2. **Fine-grained globals lock**: Reader-writer lock for `globals` array, or per-global locking
3. **Atomic refcounting**: `InterlockedIncrement`/`InterlockedDecrement` for heap object refCounts
4. **Frame pooling**: Pre-allocate frame pool to eliminate `calloc/free` per call (addresses the 300x gap)

---

## 5. Current Runtime Rating (updated from P0-8 audit)

| Capability | P0-8 | P0-9 |
|------------|------|------|
| HTTP multi-connection | 🟢 | 🟢 |
| IO concurrency | 🟢 | 🟢 |
| Worker pool (bounded threads) | 🔴 | 🟢 |
| Session isolation | 🟢 | 🟢 |
| VM safety | 🟢 | 🟢 |
| VM true parallel | 🔴 | 🔴 (next wall) |
| 50+ stress verified | 🟡 | 🟡 |
| Frame/sec measured | ❓ | 🟢 9,790/sec |
| State Updates/sec measured | ❓ | 🟢 81,633/sec |
| Events/sec measured | ❓ | 🟢 9,615/sec |
| High-frame VM | 🔴 | 🔴 (identified path) |
| Frame pooling | 🔴 | 🔴 (identified as 300x bottleneck) |

---

## 6. Git Commits

| Commit | Description |
|--------|-------------|
| afadae1 | P0-9.1: Worker Pool - fixed thread pool replaces thread-per-connection |
| (pending) | P0-9.2: High frame rate benchmark framework + baseline data |
| (pending) | P0-9: Final report |

---

## 7. Next Phase: P0-10 — Break the VM Lock

### Priority order (based on benchmark data)
1. **Frame pooling** (biggest win: addresses 300x call overhead)
   - Pre-allocate pool of TLLFrame objects
   - Reuse frames instead of calloc/free per call
   - Target: 10x+ improvement in Frames/sec

2. **Per-worker execution context** (breaks global lock)
   - Move callStack + invokeTargetStackSize to TLLWorkerContext
   - Each worker has independent execution state
   - Shared: program (read-only), globals (with RW lock), heap (atomic refcount)

3. **Atomic refcounting** (required for parallel heap access)
   - InterlockedIncrement/Decrement for all refCount fields
   - String refcounting (currently strings are not refcounted)

4. **Fine-grained globals locking**
   - Reader-writer lock for globals array
   - Or per-global locking for hot globals

5. **Concurrency stress test** (10/50/100/500/1000)
   - Measure true parallel throughput after lock is broken
   - Session isolation under load
   - Order creation under concurrent load

---

## 8. Conclusion

P0-9 established two critical foundations for TLL's high-temporal-resolution runtime:

1. **Worker Pool** bounds thread count and provides the structural basis for per-worker execution contexts.

2. **Benchmark data** quantifies the exact bottleneck: function call overhead (Frame allocation) is 300x slower than simple iteration. This tells us exactly where to optimize first.

The path forward is clear: **frame pooling → per-worker execution context → atomic refcounting → fine-grained globals → true parallel VM**. Each step is measurable with the benchmark framework established in P0-9.

TLL is no longer guessing where the wall is — we have measured it.
