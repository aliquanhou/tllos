# P0-COMPILER-06 Async / Concurrency Capability Probe — Evidence

**Date:** 2026-09-07
**Branch:** p0-compiler-keyword-fix
**Commit:** (pending)
**Status:** PROBE COMPLETE — 19/19 PASS

---

## 1. Executive Summary

P0-COMPILER-06 performed a comprehensive capability probe of TLL's async/concurrency primitives. The probe covered coroutine spawn, yield scheduling, sleep, channel communication, lifecycle, concurrency stress, error handling in coroutines, and shared state.

**Result: 19/19 probes PASS.**

No compiler/runtime code modifications were required for the probe itself. Two pre-existing issues were discovered and documented as Known Issues (not blocking this probe).

---

## 2. Existing Capability Audit

Before probing, the existing async/concurrency infrastructure was audited:

### VM Layer
- **OP_SPAWN (54)**: Spawn a new coroutine from a function
- **OP_YIELD (55)**: Yield current coroutine to scheduler
- **OP_SLEEP (56)**: Sleep current coroutine for N ms
- **OP_WAIT_READ (57)**: Wait for socket readable
- **OP_WAIT_WRITE (58)**: Wait for socket writable
- **OP_WAIT_CHANNEL (59)**: Wait on channel for wakeup
- **Unified scheduler**: per-VM, IO-aware, timer-aware, channel-aware
- **coroutine_is_runnable()**: checks dead/sleeping/IO-waiting/channel-waiting
- **coroutine_wake_channel()**: wakes all coroutines waiting on a specific channel

### Codegen Layer
- `coroutine.spawn/yield/sleep/waitRead/waitWrite/waitChannel` are special-cased in codegen.tll to emit direct VM opcodes (not function calls)
- `coroutine.wakeChannel` is mapped to builtin index 144

### Stdlib Layer
- **stdlib/task.tll**: Channel implementation (ring buffer) with createChannel/sendChannel/recvChannel/tryRecvChannel
- **stdlib/future.tll**: Future/Promise implementation (future_create/future_resolve/future_reject)
- **stdlib/eventbus.tll**: Event bus implementation

### Existing Tests
- tests/coroutine_*.tll (multiple coroutine tests)
- tests/minimal_spawn_test.tll
- tests/simple_spawn_test.tll
- tests/io_aware_scheduler_test.tll
- tests/coroutine_sleep_test.tll
- tests/coroutine_channel_test.tll

---

## 3. Probe Matrix

### Section 1: Basic Coroutine Spawn (3/3 PASS)

| ID | Test | Result |
|----|------|--------|
| 1.1 | basic spawn runs coroutine | PASS |
| 1.2 | spawn with argument | PASS |
| 1.3 | spawn with multiple arguments | PASS |

### Section 2: Yield and Scheduling (2/2 PASS)

| ID | Test | Result |
|----|------|--------|
| 2.1 | yield enables round-robin scheduling | PASS |
| 2.2 | multiple yields progress coroutine | PASS |

### Section 3: Sleep (2/2 PASS)

| ID | Test | Result |
|----|------|--------|
| 3.1 | sleep yields to other coroutines | PASS |
| 3.2 | sleep coroutine eventually completes | PASS |

### Section 4: Channel Communication (3/3 PASS)

| ID | Test | Result |
|----|------|--------|
| 4.1 | basic channel send/recv | PASS |
| 4.2 | channel multiple messages in order | PASS |
| 4.3 | channel buffered send/recv | PASS |

### Section 5: Coroutine Lifecycle (3/3 PASS)

| ID | Test | Result |
|----|------|--------|
| 5.1 | coroutine completes normally | PASS |
| 5.2 | coroutine can set shared state | PASS |
| 5.3 | nested spawn from within coroutine | PASS |

### Section 6: Concurrency Stress (2/2 PASS)

| ID | Test | Result |
|----|------|--------|
| 6.1 | 20 coroutines all execute | PASS |
| 6.2 | channel ping-pong 5 rounds | PASS |

### Section 7: Error Handling in Coroutines (2/2 PASS)

| ID | Test | Result |
|----|------|--------|
| 7.1 | try/catch works inside coroutine | PASS |
| 7.2 | finally works inside coroutine | PASS |

### Section 8: Shared State (2/2 PASS)

| ID | Test | Result |
|----|------|--------|
| 8.1 | coroutines share array state | PASS |
| 8.2 | coroutines share map state | PASS |

### Total: 19/19 PASS

---

## 4. Issues Discovered

### Known Issue 1: coroutine.yield() loop does not wake sleeping coroutines

**Severity:** Medium
**Status:** DOCUMENTED — workable with standard pattern

**Description:**
When the main coroutine uses a `coroutine.yield()` loop to wait for a sleeping coroutine, the sleeping coroutine is not woken up. The standard pattern (used in all existing tests) is to use `coroutine.sleep()` in the main coroutine to wait, which works correctly.

**Reproduction:**
```
let done = false
coroutine.spawn(fn() {
    coroutine.sleep(30)
    done = true
})
// This does NOT work:
let i = 0
while i < 50 {
    coroutine.yield()
    i = i + 1
}
// done remains false

// This DOES work (standard pattern):
coroutine.sleep(50)
// done is true
```

**Root Cause:**
Under investigation. The scheduler's `coroutine_yield()` function has a two-pass design: first pass finds runnable coroutines, second pass waits for IO/timers if no runnable found. The issue appears to be in the timer-wait path when only sleepers exist (no IO).

**Impact:**
- Does not affect existing tests (all use `coroutine.sleep()` pattern)
- Does not affect channel-based synchronization (channels use explicit wakeChannel)
- Only affects the specific pattern of using `yield()` loop to wait for a `sleep()`-based coroutine

**Workaround:**
Use `coroutine.sleep()` in the waiting coroutine instead of a `yield()` loop.

### Known Issue 2: Closure variable capture from function-scoped coroutines

**Severity:** Medium
**Status:** DOCUMENTED — module-level spawn works correctly

**Description:**
Coroutines spawned inside a function may not correctly modify outer local variables via closure capture. Coroutines spawned at module level work correctly.

**Reproduction:**
```
fn test() {
    let caught = false
    coroutine.spawn(fn() {
        caught = true  // This may not affect the outer 'caught'
    })
    coroutine.yield()
    // caught may remain false
}

// Module-level works:
let caught2 = false
coroutine.spawn(fn() {
    caught2 = true
})
coroutine.yield()
// caught2 is true
```

**Root Cause:**
Under investigation. Likely related to how closure environments are captured when a coroutine is spawned from within a function frame.

**Impact:**
- Does not affect module-level coroutine spawn (the most common pattern)
- Does not affect shared state via arrays/maps (passed by reference)
- Only affects direct closure variable mutation from function-scoped coroutines

**Workaround:**
Use module-level variables or shared containers (arrays/maps) for state that needs to be modified by coroutines.

---

## 5. Regression Results

All historical probes were re-run to confirm no regression:

| Probe | Result | Notes |
|-------|--------|-------|
| P0-01 Function Definition Gate | 46/46 PASS | |
| P0-01 Function Capability Probe | 33/33 PASS | |
| P0-02 Control Flow Probe | 66/67 PASS | 1 known failure: for-string iteration limit |
| P0-03 Data & Type Probe | 62/62 PASS | |
| P0-04 Module / Package Probe | 22/22 PASS | |
| P0-05 Error / Resource Probe | 23/23 PASS | |

**No new regressions introduced.**

---

## 6. Compiler Bootstrap

No compiler/runtime code was modified in this probe. The existing compiler (tllc_final.tllbc) and VM (tllvm.exe) were used throughout.

Bootstrap status: UNCHANGED — no modifications required.

---

## 7. Test File

- **tests/compiler/probe_async_concurrency.tll** — 19 probes covering all sections above

---

## 8. Capability Truth Classification

| Capability | Status | Evidence |
|------------|--------|----------|
| coroutine.spawn (basic) | SEALED | 1.1, 1.2, 1.3 |
| coroutine.spawn (nested) | SEALED | 5.3 |
| coroutine.yield (round-robin) | SEALED | 2.1, 2.2 |
| coroutine.sleep (yield) | SEALED | 3.1 |
| coroutine.sleep (completion) | SEALED | 3.2 |
| Channel create/send/recv | SEALED | 4.1, 4.2, 4.3 |
| Channel ping-pong | SEALED | 6.2 |
| Coroutine lifecycle | SEALED | 5.1, 5.2 |
| Concurrency (20 coroutines) | SEALED | 6.1 |
| try/catch in coroutine | SEALED | 7.1 |
| finally in coroutine | SEALED | 7.2 |
| Shared array state | SEALED | 8.1 |
| Shared map state | SEALED | 8.2 |
| yield-loop waiting for sleep | PARTIAL | Known Issue 1 — use sleep() pattern |
| Function-scoped closure capture | PARTIAL | Known Issue 2 — use module-level or containers |
| Future/Promise | NOT TESTED | stdlib/future.tll exists but not probed |
| EventBus | NOT TESTED | stdlib/eventbus.tll exists but not probed |
| Async/await syntax | MISSING | No language-level async/await |
| True parallelism | MISSING | Coroutines are cooperative, not preemptive |
| Worker threads | MISSING | No multi-threaded worker model |

---

## 9. Recommendations

### Immediate (next probe)
- **P0-COMPILER-07**: IO / Network / Database capability probe — building on the async foundation to probe real-world IO capabilities

### Short-term (follow-up fixes)
- Investigate and fix Known Issue 1 (yield-loop waiting for sleep) — this is a scheduler correctness issue
- Investigate and fix Known Issue 2 (function-scoped closure capture) — this affects AI-generated code patterns

### Medium-term
- Probe Future/Promise and EventBus stdlib modules
- Consider async/await syntax sugar on top of coroutine primitives
- Consider true parallelism via worker threads (separate from cooperative coroutines)

---

## 10. Conclusion

P0-COMPILER-06 Async / Concurrency Capability Probe is **COMPLETE** with **19/19 probes PASS**.

TLL has a solid cooperative concurrency foundation:
- Coroutine spawn/yield/sleep work correctly
- Channel-based synchronization works correctly
- Error handling (try/catch/finally) works inside coroutines
- Shared state via arrays/maps works correctly
- 20 concurrent coroutines execute reliably

Two pre-existing issues were discovered and documented (not blocking):
1. yield-loop waiting for sleep (use sleep() pattern as workaround)
2. Function-scoped closure capture (use module-level or containers as workaround)

**No compiler/runtime code modifications were required.** No regressions were introduced.

**Status: READY FOR REVIEW**
