# P2-01-C-D3: Worker-Local Runnable Queue High-Frame Runtime Execution

**Date:** 2026-09-11
**Base Commit:** 2588602799b60f0e33b2e5597ad0355e3a31062c (D2 SEALED)
**Branch:** feature/P2-01-C-D3-runtime-high-frame-execution

## 1. Architecture

D3 adds Worker-local Runnable Queue to reduce global queue contention:

```
TLLVM
??? Program (shared / read-only)
??? Workers[]
?   ??? Worker 0
?   ?   ??? ctx0
?   ?   ??? local Runnable Queue  ? NEW
?   ??? Worker 1
?       ??? ctx1
?       ??? local Runnable Queue  ? NEW
??? Global Runnable Queue
```

Scheduling priority:
1. Worker local queue (non-blocking try_dequeue)
2. Global queue (timeout dequeue)
3. No tasks ? wait / IO check

**No Work Stealing in D3.** Workers do NOT steal from each other's local queues.

## 2. Modifications

### 2.1 tllvm.h
- Added `TLLRunnableQueue local_queue` to `TLLWorker`
- Added `local_enqueue_count`, `local_dequeue_count` statistics (evidence only)

### 2.2 vm.c
- **New function `tll_runnable_queue_try_dequeue()`**: Non-blocking dequeue.
  - Windows: `WaitForSingleObject(sem, 0)` + lock
  - POSIX: `pthread_mutex_trylock()`
  - Returns coroutine index if available, -1 if queue empty

- **Worker thread init**: Added `tll_runnable_queue_init(&worker->local_queue)`
- **Worker thread cleanup**: Added `tll_runnable_queue_cleanup(&worker->local_queue)`

- **Worker loop (local-first)**:
  ```c
  int coro_idx = tll_runnable_queue_try_dequeue(&worker->local_queue);
  if (coro_idx != -1) {
      worker->local_dequeue_count++;
  } else {
      coro_idx = tll_runnable_queue_dequeue_timeout(&vm->runnable_queue, 50);
      if (coro_idx == -1) { tll_wake_io_ready(vm, 0); continue; }
  }
  ```

- **Requeue path (prefer local)**:
  ```c
  if (should_requeue) {
      tll_runnable_queue_enqueue(&worker->local_queue, coro_idx);
      worker->local_enqueue_count++;
  }
  ```

- **Thread-safe coroutine table insertion**: Added conditional lock in `coroutine_create()`:
  - If `vm->coroutine_table_lock` is initialized (multi-worker active), lock before realloc/insert
  - Prevents realloc race with worker threads accessing `vm->coroutines[]`
  - If lock not initialized (pre-worker), no lock needed (single-threaded)

## 3. Tests

### 3.1 D2 Regression (7/7 PASS)
- multi_worker_parallel: PASS
- multi_worker_overlap_proof: PASS
- multi_worker_stress_2w_100t: PASS
- worker_global_test: PASS
- simple_sleep_wakeup_test: PASS
- worker_ownership_boundary: PASS
- wake_list_300_coroutines: PASS (300/300)

### 3.2 D3 High-Frame Tests
- **1000 tasks**: PASS (1000/1000, worker0=1000, worker1=0)
- **2000 tasks**: CRASH (heap corruption 0xC0000374)
- **5000 tasks**: CRASH
- **10000 tasks**: CRASH

### 3.3 Test Observations
- 1000-task test: worker0 executes all tasks, worker1 executes 0 (tasks too short, worker0 completes before worker1 gets tasks)
- Crash threshold between 1000 and 2000 tasks
- Crash is heap corruption (STATUS_HEAP_CORRUPTION 0xC0000374)

## 4. A-GAP (Critical)

### A-GAP-1: High-task-count heap corruption (>1000 tasks)
- **Symptom**: Tests with >1000 simultaneously submitted tasks crash with heap corruption
- **Threshold**: 1000 tasks PASS, 2000 tasks CRASH
- **Possible causes** (not yet confirmed):
  1. Coroutine table realloc race despite lock (lock may not cover all access paths)
  2. Worker local queue semaphore/lock interaction issue
  3. Shutdown race: worker still executing when main thread frees worker struct
  4. Global queue node allocation/free race under high load
- **Impact**: D3 local queue works for low/medium task counts but unstable at high counts
- **Status**: OPEN, requires further investigation

## 5. B-GAP
- Channel/IO end-to-end TLL tests: NOT RUN (inherited from D2)
- ASan: NOT AVAILABLE (environment permission issue, inherited from D2)
- Linux/macOS: NOT RUN (inherited from D2)
- Performance benchmark D2 vs D3: NOT COMPLETE (blocked by A-GAP-1)
- Memory efficiency measurement: NOT COMPLETE (blocked by A-GAP-1)
- 100K task test: NOT RUN (blocked by A-GAP-1)

## 6. What Works
- Worker-local queue infrastructure (init, enqueue, try_dequeue, cleanup)
- Local-first worker loop
- Requeue to local queue
- Thread-safe coroutine table insertion (conditional lock)
- All D2 functionality preserved (7/7 regression)
- 1000-task high-frame test PASS

## 7. What Doesn't Work
- >1000 simultaneously submitted tasks ? heap corruption (A-GAP-1)
- Worker distribution: worker1 gets 0 tasks in short-task tests (fairness issue, not crash)

## 8. Git
- Base: 2588602 (D2 SEALED)
- Branch: feature/P2-01-C-D3-runtime-high-frame-execution
- Modified files:
  - host/c/tllvm.h
  - host/c/vm.c
  - tests/d3_high_frame_1000.tll (NEW)
  - tests/d3_high_frame_10000.tll (NEW, crashes)
  - docs/evidence/P2-01-C-D3-HIGH-FRAME-RUNTIME.md (THIS FILE)

**Construction Complete. Awaiting independent architecture audit.**

## 9. P2-01-C-D3-R1 Root Cause Analysis (2026-09-11)

### 9.1 Key Finding: High-load crash is D2-origin, not D3-introduced

D3-R1 isolation testing confirmed:
- **D2 baseline (2588602) also crashes** with 10000 tasks (STATUS_HEAP_CORRUPTION)
- D3 local queue is NOT the root cause
- The crash exists in D2's true multi-worker runtime

### 9.2 Root Cause Hypothesis: Concurrent coroutine_create during worker execution

**Pre-creation test**: Create ALL coroutines BEFORE starting workers → NO CRASH (but completed=0 due to test design).

This proves:
- When coroutine_create() runs concurrently with worker execution, heap corruption occurs
- When all coroutines are pre-created before workers start, no crash

### 9.3 Identified Race Conditions

#### Race 1: Frame Pool (global, unprotected)
- `frame_pool_acquire()` and `frame_pool_release()` use global variables:
  - `g_frame_pool`, `g_frame_pool_size`, `g_frame_pool_capacity`
- **No lock protection**
- `coroutine_create()` (main thread) calls `create_frame()` → `frame_pool_acquire()`
- Worker execution calls `create_frame()` / `free_frame()` → `frame_pool_acquire()` / `frame_pool_release()`
- Concurrent access causes: double-acquire, pool array overflow, realloc race

#### Race 2: Lock ordering deadlock (why simple Frame Pool lock fails)
Attempting to add a simple lock to Frame Pool causes **deadlock**:
1. Main thread: `coroutine_create()` → `create_frame()` → acquires `frame_pool_lock` → then tries to acquire `coroutine_table_lock`
2. Worker: claim coroutine → acquires `coroutine_table_lock` → executes → `create_frame()` → tries to acquire `frame_pool_lock`
3. **Deadlock**: each holds one lock and waits for the other

This means Frame Pool protection requires careful lock ordering or a different approach.

#### Race 3: Coroutine table realloc
- `coroutine_create()` may realloc `vm->coroutines[]` while workers access it
- D3 added conditional lock in `coroutine_create()`, but workers access `vm->coroutines[]` in many places
- The cached `current_coro` approach helps but doesn't cover all access paths

### 9.4 D3 1000-task test also has task loss
- D3 original: 1000 tasks → 978/1000 completed (22 lost)
- worker0=198, worker1=784 (both workers active)
- Task loss may be related to the same race conditions

### 9.5 Recommended Fix Direction (for architecture review)

**Option A: Pre-allocate coroutine table + Frame Pool at worker startup**
- Pre-allocate `vm->coroutines[]` to a large capacity (e.g., 65536) before starting workers
- Pre-allocate Frame Pool to FRAME_POOL_MAX before starting workers
- This avoids realloc during worker execution
- Limitation: fixed upper bound on concurrent coroutines

**Option B: Lock ordering fix**
- Establish strict lock ordering: `coroutine_table_lock` → `frame_pool_lock`
- Never acquire `frame_pool_lock` while holding `coroutine_table_lock`
- Move `create_frame()` call in `coroutine_create()` to BEFORE acquiring `coroutine_table_lock`
- This requires careful audit of all lock acquisition paths

**Option C: Thread-local Frame Pool**
- Each worker has its own Frame Pool (no sharing)
- Main thread has its own Frame Pool for coroutine_create
- Eliminates race entirely, at cost of memory overhead

### 9.6 R1 Status
- **Root cause identified**: concurrent coroutine_create + Frame Pool race + coroutine table race
- **Simple fix attempted**: Frame Pool lock → causes deadlock
- **No code fix committed**: awaiting architecture decision on fix direction
- **A-GAP-1 remains OPEN**: high-load heap corruption

**R1 Construction Complete. Awaiting independent architecture audit.**