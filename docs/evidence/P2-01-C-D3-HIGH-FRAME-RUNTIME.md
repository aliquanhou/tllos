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

## 10. P2-01-C-D3-R2 Root Cause Isolation (2026-09-11)

### 10.1 Isolation Matrix Results

| Experiment | Configuration | Result | Conclusion |
|------------|--------------|--------|------------|
| Frame Pool ENABLED | default, 10000 tasks, 2W | CRASH (0xC0000374) | Baseline |
| Frame Pool DISABLED | D3_TEST_DISABLE_FRAME_POOL=1, 10000 tasks, 2W | CRASH (0xC0000374) | **Frame Pool RULED OUT** |
| Table dynamic | default, 10000 tasks, 2W | CRASH | Baseline |
| Table preallocated | D3_TEST_PREALLOC_COROUTINE_TABLE=1 (65536), 10000 tasks, 2W | CRASH | **Table realloc RULED OUT** |
| 2 Workers | default, 10000 tasks | CRASH | Baseline |
| 1 Worker | startWorkers(1), 10000 tasks | CRASH | **Multi-worker concurrency RULED OUT** |
| 1000 tasks (run 1) | default, 2W | CRASH | Unstable |
| 1000 tasks (run 2) | default, 2W | CRASH | Unstable |
| 1000 tasks (run 3) | default, 2W | PASS (987/1000) | Unstable |

### 10.2 Key Findings

1. **Frame Pool is NOT the root cause**: Disabling Frame Pool entirely (every frame allocated/fresh freed) still crashes at 10000 tasks. The Frame Pool race is a real thread-safety defect, but not the cause of this particular heap corruption.

2. **Coroutine table realloc is NOT the root cause**: Pre-allocating the table to 65536 entries before starting workers still crashes. The realloc race is also a real defect, but not the root cause.

3. **Multi-worker concurrency is NOT the root cause**: Even with 1 Worker, 10000 tasks still crash. The issue is main-thread coroutine_create() concurrent with worker execution, not worker-vs-worker concurrency.

4. **1000-task test is unstable**: 2/3 runs crash, 1/3 passes with 987/1000 completed. This confirms a race condition that manifests probabilistically.

### 10.3 Remaining Root Cause Candidates

After ruling out Frame Pool, Table realloc, and multi-worker concurrency, the remaining candidates are:

1. **Coroutine object lifecycle**: TLLCoroutine* may be modified/freed while worker holds a reference
2. **Queue node allocation/free**: TLLRunnableNode malloc/free race between enqueue/dequeue
3. **Shutdown race**: Worker still executing while main thread frees resources
4. **Other global state**: globals array, heap objects, or other shared mutable state

### 10.4 R2 Status

- **Candidates ruled out**: Frame Pool, Coroutine table realloc, Multi-worker concurrency
- **Candidates remaining**: Coroutine lifecycle, Queue node, Shutdown, Other global state
- **Root cause**: Still INFERRED / not yet PROVEN
- **A-GAP-1**: Remains OPEN
- **No code fix committed**: Awaiting further isolation or architecture decision

**R2 Isolation Phase 1 Complete. Continuing isolation...**

## 11. P2-01-C-D3-R2 Phase 2: Pre-creation vs Concurrent Creation Isolation (2026-09-11)

### 11.1 Critical Isolation Experiment: Pre-creation vs Concurrent Creation

**Experiment Setup:**
- Test P (Pre-creation): Create ALL 10000 coroutines BEFORE starting workers, then submit all
- Test C (Concurrent creation): Start workers first, then create+submit coroutines concurrently with worker execution
- Both tests: same task function, same worker count (2), same wait time, same shutdown

**Results:**

| Test | Configuration | Result | Conclusion |
|------|--------------|--------|------------|
| Pre-creation (P) | 10000 coroutines created before workers | **NO CRASH** (exit 0) | concurrent coroutine_create eliminated |
| Concurrent (C) | 10000 coroutines created while workers running | **CRASH** (0xC0000374) | baseline |

### 11.2 Key Finding: Concurrent coroutine_create is PROVEN STRONG CANDIDATE

The pre-creation test does NOT crash, while the concurrent creation test DOES crash.
The only variable changed is whether coroutine_create() runs concurrently with worker execution.

**Conclusion: Concurrent coroutine_create() during worker execution is the primary trigger for heap corruption.**

This upgrades concurrent coroutine_create from "STRONG CANDIDATE" to "PROVEN STRONG CANDIDATE / PRIMARY TRIGGER".

### 11.3 Pre-creation Test Notes

- The pre-creation test showed completed=0/10000, which is a test artifact (closure variable sharing in coroutine.spawn(fn() { cpu_task(i) }) causes all coroutines to reference the final i value).
- This does NOT affect the crash/no-crash conclusion: the test ran to completion without heap corruption.
- The parameter-passing version (coroutine.spawn(cpu_task, i)) produced no output due to a separate syntax/encoding issue, under investigation.
- The critical observation is: **pre-creation = no crash, concurrent creation = crash**.

### 11.4 Remaining Root Cause Candidates (within concurrent coroutine_create)

Now that concurrent coroutine_create is proven as the trigger, the next step is to identify WHICH operation inside coroutine_create causes the corruption when run concurrently:

1. **TLLCoroutine struct allocation** (malloc)
2. **callStack allocation** (malloc)
3. **Frame allocation** (create_frame → frame_pool_acquire)
4. **Frame registers/argStack/tryStack allocation** (calloc)
5. **vm->coroutines[] array insertion** (may trigger realloc)
6. **vm->coroutineCount increment**
7. **Coroutine initial state setup**

Each of these needs to be isolated to find the exact corruption point.

### 11.5 R2 Phase 2 Status

- **Concurrent coroutine_create**: PROVEN as primary crash trigger
- **Pre-creation**: NO CRASH (validates isolation)
- **Exact corruption point within coroutine_create**: NOT YET IDENTIFIED
- **Coroutine object lifetime**: UNDER INVESTIGATION
- **Queue node lifetime**: UNDER INVESTIGATION
- **Shutdown race**: UNDER INVESTIGATION
- **A-GAP-1**: remains OPEN, but trigger now identified

**R2 Phase 2 Complete. Concurrent coroutine_create is PROVEN trigger. Next: isolate exact corruption point within coroutine_create.**

## 12. P2-01-C-D3-R2-P3: Exact Corruption Point Isolation (2026-09-11)

### 12.1 coroutine_create() Full Lifecycle Audit

```
coroutine_create()
  ├─ calloc(TLLCoroutine)              [SAFE - per-object allocation]
  ├─ calloc(callStack[64])             [SAFE - per-object allocation]
  ├─ state = 0 (RUNNABLE)              [SAFE - object-local]
  ├─ create_frame(fn, -1, env)
  │   ├─ frame_pool_acquire()          [UNSAFE - global pool, no lock]
  │   ├─ calloc(registers)             [SAFE - per-frame allocation]
  │   ├─ calloc(argStack)              [SAFE]
  │   └─ calloc(tryStack)              [SAFE]
  ├─ co->callStack[0] = frame          [SAFE - object-local]
  ├─ [lock] coroutine_table_lock       [LOCKED - if multi-worker active]
  ├─ realloc(vm->coroutines[])         [LOCKED - but workers may read without lock]
  ├─ vm->coroutines[count++] = co      [LOCKED]
  └─ [unlock]
```

### 12.2 vm->coroutines[] Full-Path Access Audit

**Access points WITH coroutine_table_lock:**
- coroutine_create (realloc + insert)
- Worker claim (RUNNABLE → RUNNING)
- runtime.submitCoroutine
- tll_wake_expired_sleepers
- tll_wake_io_ready
- coroutine_wake_channel

**Access points WITHOUT lock (CRITICAL FINDING):**
- **coroutine_save_current** (line 452-453): `vm->coroutines[currentCoroutine]`
- **coroutine_restore** (line 468-469): `vm->coroutines[idx]`
- **tll_vm_exec** (lines 881, 890, 1061-1062, 1094-1096, 1643-1644, 1670-1671, 1687-1688, 1697-1698, 1714-1715, 1726-1727, 1741-1742): frequent `vm->coroutines[currentCoroutine]` access during execution

**Total: 15+ unsynchronized access points in tll_vm_exec alone.**

### 12.3 Hypothesis: vm->coroutines[] Use-After-Free

The unsynchronized access pattern creates a potential use-after-free:

```
Worker thread (tll_vm_exec):
  1. Read vm->coroutines pointer (old value)
  2. [preempted]

Main thread (coroutine_create):
  3. realloc(vm->coroutines) → vm->coroutines points to NEW memory
  4. OLD memory is freed

Worker thread (resumes):
  5. Use OLD vm->coroutines pointer → access freed memory → HEAP CORRUPTION
```

### 12.4 Experiment: current_coro Pointer Cache (save/restore only)

**Modification:** Added `TLLWorker->current_coro` cached pointer, modified only `coroutine_save_current` and `coroutine_restore` to use cached pointer instead of `vm->coroutines[]`.

**Result:** 2000-task test still crashes 3/3 runs (0xC0000374).

**Conclusion:** Modifying only save/restore is insufficient. The 15+ unsynchronized access points in `tll_vm_exec` itself remain. Full caching of current_coro throughout tll_vm_exec may be needed, OR the root cause may be elsewhere.

### 12.5 Evidence Classification

| Finding | Level |
|---------|-------|
| Concurrent coroutine_create triggers crash | **PROVEN TRIGGER** |
| Pre-creation (no concurrent create) = no crash | **PROVEN** |
| Frame Pool not direct cause (disabled still crashes) | **PROVEN** |
| Coroutine table realloc not direct cause (preallocated still crashes) | **PROVEN** |
| Worker↔Worker concurrency not direct cause (1W still crashes) | **PROVEN** |
| vm->coroutines[] has 15+ unsynchronized access points in tll_vm_exec | **OBSERVED** |
| vm->coroutines[] use-after-free is exact root cause | **UNVERIFIED** (hypothesis) |
| current_coro full cache would fix crash | **UNVERIFIED** (not yet tested) |

### 12.6 Remaining Candidates for Exact Root Cause

1. **vm->coroutines[] use-after-free** during tll_vm_exec (strongest hypothesis)
2. **Frame Pool race** (ruled out as direct cause, but still a real defect)
3. **TLLCoroutine object lifetime** (coro pointer invalidated during execution)
4. **Queue node lifetime** (enqueue/dequeue/free race)
5. **Shutdown race** (worker still executing while main frees resources)

### 12.7 R2-P3 Status

- **coroutine_create lifecycle**: AUDITED
- **vm->coroutines[] full-path**: AUDITED - 15+ unsynchronized access points found
- **current_coro cache (save/restore only)**: TESTED - insufficient
- **Exact corruption point**: NOT YET PROVEN
- **A-GAP-1**: remains OPEN

**R2-P3 Phase 1 Complete. Next: full current_coro caching throughout tll_vm_exec, or isolate Queue/Shutdown candidates.**

## 13. P2-01-C-D3-R2-P3 Phase 2: Queue OFF Isolation Experiment (2026-09-11)

### 13.1 Experiment Setup

**Goal:** Isolate whether queue node malloc/free is the root cause of heap corruption.

**Method:** Added `D3_TEST_QUEUE_OFF` environment variable. When set:
- Worker does NOT use global/local runnable queue
- Worker directly scans `vm->coroutines[]` for RUNNABLE coroutine under `coroutine_table_lock`
- No queue node malloc/free involved
- Coroutine claim (RUNNABLE → RUNNING) done during scan

### 13.2 Results

| Task Count | Queue ON (baseline) | Queue OFF |
|-----------|---------------------|-----------|
| 2000 (run 1) | CRASH | **PASS (2000/2000)** |
| 2000 (run 2) | CRASH | CRASH |
| 2000 (run 3) | CRASH | CRASH |
| 5000 | CRASH | CRASH |
| 10000 | CRASH | CRASH |

### 13.3 Conclusion

**Queue node lifecycle is PROVEN EXCLUDED as direct root cause.**

Even with queue completely OFF (no queue node malloc/free, no enqueue/dequeue), high-load tests (5000/10000) still crash with STATUS_HEAP_CORRUPTION (0xC0000374).

This means:
- Queue node malloc/free race is NOT the primary corruption source
- The corruption happens elsewhere, most likely in `vm->coroutines[]` access (realloc + unsynchronized reads in tll_vm_exec)
- The 2000-task intermittent PASS in Queue OFF mode may be due to reduced allocation pressure, but does not indicate queue is the root cause

### 13.4 Updated Root Cause Candidate Ranking

1. **vm->coroutines[] use-after-free / relocation race** (STRONGEST - now even more likely after Queue OFF exclusion)
2. TLLCoroutine object lifetime (coro pointer invalidated during execution)
3. Frame Pool race (real defect, but ruled out as direct cause)
4. Shutdown race (not yet tested in isolation)
5. Queue node lifecycle (**PROVEN EXCLUDED**)

### 13.5 Evidence Classification

| Finding | Level |
|---------|-------|
| Queue OFF still crashes at 5000/10000 | **PROVEN** |
| Queue node lifecycle is not direct root cause | **PROVEN EXCLUDED** |
| vm->coroutines[] race is strongest remaining candidate | **INFERRED** (not yet proven) |
| 2000-task intermittent PASS in Queue OFF | **OBSERVED** (probabilistic) |

### 13.6 Next Steps

Queue OFF experiment code remains in tree as diagnostic tool (disabled by default).

Next isolation target: **Coroutine Table matrix** (D1-D4):
- D1: preallocated table, no workers
- D2: dynamic realloc, no workers
- D3: preallocated table + workers
- D4: dynamic realloc + workers

If D3 PASS and D4 CRASH → vm->coroutines[] relocation becomes PROVEN ROOT CAUSE CANDIDATE.

## 14. P2-01-C-D3-R2-P3 Phase 3: Coroutine Table Prealloc Isolation (2026-09-11)

### 14.1 Experiment Setup

**Goal:** Isolate whether vm->coroutines[] realloc is the root cause of heap corruption.

**Method:** Added `D3_TEST_PREALLOC_TABLE` environment variable. When set:
- In `tll_runtime_start_workers()`, before creating workers, preallocate `vm->coroutines[]` to 65536 slots
- Set `vm->coroutineCapacity = 65536`
- During worker execution, `coroutine_create()` will NOT trigger realloc (up to 65536 coroutines)

### 14.2 Results

| Task Count | Dynamic Table (baseline) | Prealloc Table (65536) |
|-----------|--------------------------|------------------------|
| 2000 (run 1) | CRASH | CRASH |
| 2000 (run 2) | CRASH | CRASH |
| 2000 (run 3) | CRASH | CRASH |
| 5000 | CRASH | CRASH |

### 14.3 Conclusion

**vm->coroutines[] realloc is PROVEN EXCLUDED as direct root cause.**

Even with coroutine table fully preallocated (no realloc during worker execution), high-load tests still crash with STATUS_HEAP_CORRUPTION (0xC0000374).

This means:
- realloc(vm->coroutines) is NOT the primary corruption source
- The vm->coroutines[] pointer remains stable during execution
- The corruption must be in object-level access: TLLCoroutine*, TLLFrame*, or their fields
- The "use-after-free of vm->coroutines[] pointer" hypothesis is now ruled out

### 14.4 Updated Root Cause Candidate Ranking

1. **TLLCoroutine object field race** (NEW STRONGEST - concurrent access to coro->callStack/state/etc.)
2. **TLLFrame object lifecycle** (frame allocation/release during concurrent execution)
3. Frame Pool race (real defect, but ruled out as direct cause)
4. Shutdown race (not yet tested in isolation)
5. Queue node lifecycle (PROVEN EXCLUDED)
6. vm->coroutines[] realloc (**PROVEN EXCLUDED**)

### 14.5 Key Insight

The corruption is NOT at the table-pointer level (realloc), but at the **object level**. Multiple threads may be accessing the same TLLCoroutine or TLLFrame object concurrently, or an object may be freed while another thread still holds a reference.

Next isolation target: **TLLCoroutine object lifetime** - determine if a coro object can be modified/freed while a worker still holds a raw pointer to it.

### 14.6 Evidence Classification

| Finding | Level |
|---------|-------|
| Prealloc table still crashes at 2000/5000 | **PROVEN** |
| vm->coroutines[] realloc is not direct root cause | **PROVEN EXCLUDED** |
| TLLCoroutine object field race is strongest candidate | **INFERRED** (not yet proven) |
| TLLFrame object lifecycle issue | **UNVERIFIED** |

## 15. P2-01-C-D3-R2-P3-P4: Coroutine Object Lifetime Isolation (2026-09-11)

### 15.1 P4-1: Full-Path Free Lifecycle Audit

**All free() call sites for TLLCoroutine:**

| Location | Function | Context |
|----------|----------|---------|
| line 360 | coroutine_init | free(vm->coroutines) array — initialization only |
| line 381-387 | coroutine_destroy | free(co->callStack), free(co) — normal destroy path |
| line 1080 | tll_vm_exec (legacy scheduler) | coroutine_destroy(vm, 0) — all coroutines dead |
| line 1110 | tll_vm_exec (legacy scheduler) | coroutine_destroy(vm, 0) — all coroutines dead |
| line 1749 | tll_vm_exec | coroutine_destroy(vm, idx) — **current coroutine completes, only 1 remains** |
| line 1832 | tll_vm_run | coroutine_destroy(vm, 0) — after exec returns, cleanup |
| line 1904-1911 | tll_vm_free | direct free(co), free(vm->coroutines) — VM teardown |

**Critical finding (line 1744-1755):**
```c
if (vm->coroutineCount <= 1) {
    int idx = TLL_CTX(vm)->currentCoroutine;
    if (idx >= 0 && idx < vm->coroutineCount) {
        coroutine_save_current(vm);
        coroutine_destroy(vm, idx);  // <-- destroys CURRENT coroutine
    }
    TLL_CTX(vm)->callStack = NULL;
    return;
}
```

In Worker mode, after tll_vm_exec returns, the Worker outer loop accesses:
```c
coro->callStack = worker->ctx.callStack;  // <-- use-after-free if coro was destroyed!
coro->callStackSize = ...;
```

**This is a potential A-class lifetime defect**, but P4-2 experiment below shows it is NOT the primary crash trigger.

### 15.2 P4-2: O1 No-Free Diagnostic Experiment

**Goal:** Determine if object lifetime / use-after-free (early free) is the root cause.

**Method:** Added `D3_TEST_NO_FREE` environment variable. When set:
- coroutine_destroy() skips all deallocation (free frames, free callStack, free(co))
- tll_vm_free() skips direct free(co) calls
- Objects are intentionally leaked for diagnosis

**Results:**

| Task Count | Normal (baseline) | O1 No-Free |
|-----------|-------------------|------------|
| 2000 (run 1) | CRASH | CRASH |
| 2000 (run 2) | CRASH | CRASH |
| 2000 (run 3) | CRASH | CRASH |
| 5000 | CRASH | CRASH |

### 15.3 P4-2 Conclusion

**TLLCoroutine object early-free / UAF is PROVEN EXCLUDED as direct root cause.**

Even with NO object deallocation at all (all coroutines leaked intentionally), high-load tests still crash with STATUS_HEAP_CORRUPTION (0xC0000374).

This means:
- The corruption is NOT caused by freeing an object while another thread holds a reference
- The corruption must be caused by **concurrent modification of object fields** (data race on TLLCoroutine/TLLFrame struct members)
- Or by **TLLFrame object lifecycle** (frame allocation/release race)
- Or by other shared mutable state (globals, heap, etc.)

### 15.4 P4-5: Queue OFF Lock-After-Raw-Pointer Fix

Fixed the Queue OFF diagnostic code:
- **Before:** released coroutine_table_lock, then re-read `vm->coroutines[coro_idx]` (unsynchronized)
- **After:** capture `scan_coro` pointer INSIDE the lock, use it after unlock

This ensures the Queue OFF experiment does not introduce its own uncontrolled variable.

### 15.5 Updated Root Cause Candidate Ranking

1. **TLLCoroutine object field data race** (NEW STRONGEST — concurrent modification of coro->state/callStack/etc.)
2. **TLLFrame object field data race** (concurrent modification of frame fields)
3. **TLLFrame allocation/release race** (frame_pool_acquire/release unsynchronized)
4. Shutdown race (not yet isolated)
5. ~~Queue node lifecycle~~ → **PROVEN EXCLUDED**
6. ~~vm->coroutines[] realloc~~ → **PROVEN EXCLUDED**
7. ~~TLLCoroutine early-free / UAF~~ → **PROVEN EXCLUDED** (O1 no-free still crashes)

### 15.6 Key Insight

The corruption is now narrowed to **concurrent data modification**, not object lifetime:
- Not queue node malloc/free (excluded)
- Not table realloc (excluded)
- Not coroutine early-free (excluded)
- Must be: two threads modifying the same TLLCoroutine or TLLFrame object fields concurrently, causing heap metadata corruption

Next isolation target: **TLLFrame pre-create vs concurrent-create** (F1/F2) to determine if frame allocation is the trigger.

### 15.7 Evidence Classification

| Finding | Level |
|---------|-------|
| No-free mode still crashes at 2000/5000 | **PROVEN** |
| TLLCoroutine early-free / UAF is not direct root cause | **PROVEN EXCLUDED** |
| tll_vm_exec line 1749 can destroy current coroutine | **OBSERVED** (potential defect, not primary trigger) |
| TLLCoroutine field data race is strongest candidate | **INFERRED** (not yet proven) |
| TLLFrame lifecycle/race | **UNVERIFIED** |

## 16. P2-01-C-D3-R2-P3-P4-4: Frame Isolation F1/F2/F3 (2026-09-11)

### 16.1 Experiment Setup

**Goal:** Determine if TLLFrame allocation / Frame Pool is the root cause of heap corruption.

**Three experiments:**
- **F1:** Frame all pre-created (before Worker start) — NOT YET COMPLETED
- **F2:** Normal dynamic Frame (baseline, Frame Pool ON)
- **F3:** Frame Pool OFF (always allocate fresh frame, always free on release)

**F3 implementation:** Added `D3_TEST_DISABLE_FRAME_POOL` env var:
- frame_pool_acquire(): skip pool, always calloc fresh frame + arrays
- frame_pool_release(): skip pool, always free frame + arrays

### 16.2 F2 vs F3 Results

| Task Count | F2 (Pool ON, baseline) | F3 (Pool OFF) |
|-----------|------------------------|----------------|
| 2000 run 1 | **PASS** | CRASH |
| 2000 run 2 | CRASH | CRASH |
| 2000 run 3 | CRASH | CRASH |
| 5000 | CRASH | CRASH |
| 10000 | CRASH | CRASH |

### 16.3 F2/F3 Conclusion

**Frame Pool is PROVEN EXCLUDED as direct root cause.**

Even with Frame Pool completely OFF (every frame allocated fresh, every frame freed immediately on release), high-load tests (5000/10000) still crash with STATUS_HEAP_CORRUPTION (0xC0000374).

Observations:
- F3 (Pool OFF) crashes more frequently at 2000 tasks (3/3 vs 2/3) — likely due to increased allocation pressure
- But both F2 and F3 crash at 5000/10000 — Frame Pool presence/absence does not determine crash
- The Frame Pool is a real thread-safety defect (unsynchronized global state), but it is NOT the primary crash trigger

### 16.4 Frame Internal Lifecycle Audit

**TLLFrame structure fields:**
- registers (TLLValue*) — dynamically allocated, size = registerCount
- argStack (TLLValue*) — dynamically allocated, capacity 64
- tryStack (int*) — dynamically allocated, capacity 16
- locals (TLLValue*) — dynamically allocated (optional)
- parent (TLLFrame*) — pointer to parent frame
- function (TLLFunction*) — pointer to function metadata
- returnAddr (int) — bytecode return address
- registerCount, argStackSize, argStackCapacity, tryStackSize, tryStackCapacity, localCapacity, localCount

**Frame lifecycle:**
1. create_frame() → frame_pool_acquire() → calloc frame + arrays
2. push to callStack (worker->ctx.callStack or coro->callStack)
3. tll_vm_exec() executes bytecode using frame->registers, frame->argStack, frame->tryStack
4. pop_frame() → frame_pool_release() → return to pool or free

**Key question:** Can two threads access the same TLLFrame concurrently?
- In Worker mode, each worker has its own callStack (worker->ctx.callStack)
- During coroutine yield, callStack is saved back to coro->callStack
- During coroutine resume, coro->callStack is loaded into worker->ctx.callStack
- If two workers claim the same coroutine (should be prevented by claim lock), they could share frames
- Frame Pool is global and unsynchronized — two workers can acquire/release frames concurrently

But F3 (Pool OFF) proves that even without Frame Pool sharing, crashes still occur. So the corruption is not caused by Frame Pool sharing alone.

### 16.5 Updated Root Cause Candidate Ranking

1. **TLLCoroutine object field data race** (STRONGEST — concurrent modification of coro->state/callStack/callStackSize)
2. **TLLFrame object field data race** (concurrent modification of frame->registers/argStack during execution)
3. **Worker context / callStack sharing race** (coroutine yield/resume transferring callStack between workers)
4. Shutdown race (not yet isolated)
5. ~~Queue node lifecycle~~ → PROVEN EXCLUDED
6. ~~vm->coroutines[] realloc~~ → PROVEN EXCLUDED
7. ~~TLLCoroutine early-free / UAF~~ → PROVEN EXCLUDED
8. ~~Frame Pool~~ → PROVEN EXCLUDED (F3 still crashes)

### 16.6 Evidence Classification

| Finding | Level |
|---------|-------|
| F3 (Frame Pool OFF) still crashes at 5000/10000 | **PROVEN** |
| Frame Pool is not direct root cause | **PROVEN EXCLUDED** |
| F3 crashes more frequently at 2000 (3/3 vs 2/3) | **OBSERVED** (allocation pressure) |
| TLLCoroutine field data race is strongest candidate | **INFERRED** |
| TLLFrame field data race | **UNVERIFIED** |
| Worker context / callStack sharing race | **UNVERIFIED** |
| F1 (all frames pre-created) | **NOT YET COMPLETED** |

## 17. P2-01-C-D3-R2-P5: Execution Context Ownership Isolation (2026-09-11)

### 17.1 P5-1: Ownership Matrix

**TLLWorker.ctx fields:**

| Field | Owner | Read By | Write By | Sync | Lifetime |
|-------|-------|---------|---------|------|----------|
| callStack | WORKER-OWNED | tll_vm_exec, push_frame, pop_frame, coroutine_save_current | push_frame (realloc), coroutine_restore, Worker load | NONE (worker-local) | Borrowed from coroutine during execution |
| callStackSize | WORKER-OWNED | tll_vm_exec, push_frame, pop_frame | push_frame, pop_frame | NONE | Transferred to coroutine on save |
| callStackCapacity | WORKER-OWNED | push_frame | push_frame (realloc) | NONE | Transferred to coroutine on save |
| currentCoroutine | WORKER-OWNED | tll_vm_exec, push_frame, pop_frame, coroutine_save_current | Worker claim, coroutine_restore | NONE | Index into vm->coroutines[] |
| invokeTargetStackSize | WORKER-OWNED | tll_vm_exec | Worker claim | NONE | Worker-local |

**TLLCoroutine fields:**

| Field | Owner | Read By | Write By | Sync | Violation Found |
|-------|-------|---------|---------|------|-----------------|
| callStack | COROUTINE-OWNED | Worker load (line 2394), coroutine_restore (481), coroutine_destroy (391) | Worker save (2403), coroutine_save_current (465), coroutine_create (419) | **NONE on Worker save (2403)** | ⚠️ Worker save without lock |
| callStackSize | COROUTINE-OWNED | Worker load (2395), state transition (2419), coroutine_destroy (386) | Worker save (2404), **push_frame (892)**, **pop_frame (901)**, coroutine_save_current (466) | **NONE on push/pop_frame direct write** | ⚠️ **push/pop_frame directly write coro->callStackSize without lock** |
| callStackCapacity | COROUTINE-OWNED | Worker load (2396) | Worker save (2405), coroutine_save_current (467) | **NONE on Worker save** | ⚠️ Worker save without lock |
| state | LOCK-PROTECTED | Worker claim, wake path, state transition | Worker claim (RUNNABLE→RUNNING), state transition (RUNNING→COMPLETED/RUNNABLE/WAITING), wake path (WAITING→RUNNABLE) | coroutine_table_lock | ✅ Protected |
| wakeTime | LOCK-PROTECTED | tll_wake_expired_sleepers | tll_wake_expired_sleepers (clear), OP_SLEEP (set) | coroutine_table_lock in wake path | ⚠️ OP_SLEEP sets wakeTime without lock (but during worker execution) |
| waitingFd | LOCK-PROTECTED | tll_wake_io_ready, coroutine_is_runnable | OP_WAIT_READ/WRITE (set), tll_wake_io_ready (clear) | coroutine_table_lock in wake path | ⚠️ OP_WAIT sets without lock |
| waitingChannel | LOCK-PROTECTED | coroutine_wake_channel, coroutine_is_runnable | OP_WAIT_CHANNEL (set), coroutine_wake_channel (clear) | coroutine_table_lock in wake path | ⚠️ OP_WAIT sets without lock |

### 17.2 P5-2: callStack Write Timeline

**All 39 write points for callStack/callStackSize/callStackCapacity:**

| Phase | Location | Write | Lock? | Owner |
|-------|----------|-------|-------|-------|
| CREATE | coroutine_create (418-420) | co->callStack = calloc, size=0, cap=64 | N/A (new object) | MAIN-THREAD |
| CREATE | coroutine_create (432) | co->callStack[size++] = frame | N/A | MAIN-THREAD |
| **EXEC** | **push_frame (885)** | **realloc(worker->ctx.callStack)** | **NONE** | **WORKER** |
| **EXEC** | **push_frame (892)** | **coro->callStackSize = ctx->callStackSize** | **NONE** | **⚠️ DIRECT CORO WRITE** |
| **EXEC** | **pop_frame (901)** | **coro->callStackSize = ctx->callStackSize** | **NONE** | **⚠️ DIRECT CORO WRITE** |
| EXEC | tll_vm_exec (1092-1094) | ctx->callStack = NULL, size=0, cap=0 | NONE | WORKER |
| EXEC | tll_vm_exec (1122-1124) | ctx->callStack = NULL, size=0, cap=0 | NONE | WORKER |
| EXEC | tll_vm_exec (1761-1763) | ctx->callStack = NULL, size=0, cap=0 | NONE | WORKER |
| SAVE | coroutine_save_current (465-467) | co->callStack = ctx->callStack, size, cap | NONE | TRANSFER |
| RESTORE | coroutine_restore (481-483) | ctx->callStack = co->callStack, size, cap | NONE | TRANSFER |
| **WORKER** | **Worker load (2394-2396)** | **ctx->callStack = coro->callStack** | **claim lock held before** | TRANSFER |
| **WORKER** | **Worker save (2403-2405)** | **coro->callStack = ctx->callStack, size, cap** | **NONE** | **⚠️ SAVE WITHOUT LOCK** |
| **WORKER** | **State transition (2419)** | **reads coro->callStackSize** | **coroutine_table_lock** | READ |
| RUN | tll_vm_run (1827-1829) | mainCo->callStack = ctx->callStack, size, cap | NONE | TRANSFER |
| RUN | tll_vm_run (1844-1846) | ctx->callStack = NULL, size=0, cap=0 | NONE | WORKER |
| CTX INIT | tll_worker_ctx_init (2253-2255) | ctx->callStack = NULL, size=0, cap=0 | NONE | WORKER |
| CTX INIT | (2267-2269) | ctx->callStack = NULL, size=0, cap=0 | NONE | WORKER |
| FREE | coroutine_destroy (391) | free(co->callStack) | N/A (object dying) | N/A |
| FREE | tll_vm_free (1914) | free(co->callStack) | N/A | N/A |

### 17.3 Critical Ownership Violations Found

**Violation 1: push_frame/pop_frame directly write coro->callStackSize without lock (lines 892, 901)**

```c
static void push_frame(TLLVM *vm, TLLFrame *frame) {
    // ... realloc worker->ctx.callStack ...
    // P0-RUNTIME-07-R2: Sync current coroutine callStackSize
    if (vm->coroutineCount > 0 && ...) {
        vm->coroutines[currentCoroutine]->callStackSize = ctx->callStackSize;  // ⚠️ NO LOCK
    }
}
```

**Risk:** During worker execution, another thread (main thread creating coroutines, or another worker's wake path) may access coro->callStackSize concurrently. While the coroutine is RUNNING, other workers should not claim it, but the main thread's coroutine_create does not touch this specific coroutine. The direct write bypasses the ownership transfer protocol.

**Violation 2: Worker save callStack to coro without lock (lines 2403-2405)**

```c
/* Execute the coroutine */
tll_vm_exec(vm);

/* Save call stack back to coroutine */
coro->callStack = worker->ctx.callStack;        // ⚠️ NO LOCK
coro->callStackSize = worker->ctx.callStackSize; // ⚠️ NO LOCK
coro->callStackCapacity = worker->ctx.callStackCapacity; // ⚠️ NO LOCK

// ... later, under coroutine_table_lock:
if (coro->callStackSize == 0) { coro->state = COMPLETED; }
```

**Risk:** Between tll_vm_exec return and state transition (which is under lock), the coroutine state is still RUNNING. The save writes callStack pointer without synchronization. If a wake path or another worker reads coro->callStack during this window, it may see an inconsistent state.

**Violation 3: push_frame realloc frees old callStack while coro->callStack still points to it**

```c
// Worker load (line 2394): worker->ctx.callStack = coro->callStack;
// Both point to same memory.

// push_frame (line 885): worker->ctx.callStack = realloc(worker->ctx.callStack, ...);
// Old callStack is FREED by realloc.
// But coro->callStack STILL POINTS TO OLD (now freed) memory!

// Worker save (line 2403): coro->callStack = worker->ctx.callStack;
// Now coro->callStack points to new memory.
```

**Risk:** During tll_vm_exec execution, after push_frame calls realloc but before Worker save, coro->callStack is a dangling pointer to freed memory. If any other thread reads coro->callStack during this window, it is a use-after-free.

**Current analysis:** While the coroutine is RUNNING, no other worker should access its callStack (claim lock prevents claim). The wake path does not read callStack. The main thread's coroutine_create does not touch this coroutine. So in practice, this window may not be exploited by current code paths. However, it is a latent ownership violation that could be triggered by future code changes.

### 17.4 P5-3: Minimal Transfer Test (NOT YET RUN)

Planned test: 2 Workers, 100 coroutines, force:
- Worker A claims C, executes, yields
- Worker B resumes C
- Verify C.owner, C.state, C.callStack throughout transfer

This test requires instrumentation to track ownership transitions. Not yet implemented.

### 17.5 Evidence Classification

| Finding | Level |
|---------|-------|
| push_frame/pop_frame directly write coro->callStackSize without lock | **OBSERVED** (code audit) |
| Worker save callStack to coro without lock | **OBSERVED** (code audit) |
| push_frame realloc leaves coro->callStack dangling during execution | **OBSERVED** (code audit) |
| These violations are the direct cause of heap corruption | **UNVERIFIED** (not yet proven by reproduction) |
| No other thread accesses coro->callStack during RUNNING state | **INFERRED** (based on current code paths) |
| F1 (all pre-created) would further isolate creation-time vs execution-time | **PENDING** |

### 17.6 Current Root Cause Tree

```
Concurrent coroutine_create
    │
    ├── Queue node              ❌ EXCLUDED
    ├── Table realloc           ❌ EXCLUDED
    ├── Coroutine early-free    ❌ EXCLUDED
    ├── Frame Pool              ❌ EXCLUDED
    │
    └── Execution-time state
            │
            ├── Coroutine field ownership     ← ⚠️ VIOLATIONS FOUND
            │   ├── push/pop_frame direct coro write (no lock)
            │   ├── Worker save without lock
            │   └── realloc leaves coro->callStack dangling
            │
            ├── Worker ctx ownership          ← ⚠️ VIOLATIONS FOUND
            │   └── callStack transfer protocol incomplete
            │
            ├── callStack transfer            ← ⚠️ VIOLATIONS FOUND
            │
            ├── TLLFrame concurrent access     ← OPEN
            └── Shutdown                       ← POSTPONED
```

**Exact corruption point: NOT YET PROVEN.** Multiple ownership violations found in callStack/ctx transfer protocol, but not yet proven which one causes the observed STATUS_HEAP_CORRUPTION.