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