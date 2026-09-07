# P0-COMPILER-06 BUG Root Cause Analysis

**Date:** 2026-09-07
**Branch:** p0-compiler-keyword-fix
**Status:** BUG-A ROOT CAUSE CONFIRMED | BUG-B ROOT CAUSE UNDER INVESTIGATION

---

## BUG-A: Scheduler Timer-Wait

### Classification: BUG (semantic design issue)

### Symptom

When the main coroutine uses a `coroutine.yield()` loop to wait for a sleeping coroutine, the sleeping coroutine is **not woken up** until system time naturally passes its wakeTime.

- A1 FAIL: 20ms sleeper not woken after 100 yields (fast execution)
- A2 PASS (control): main uses `coroutine.sleep(50)` — sleeper woken correctly
- A3 FAIL: 10ms sleeper not woken after 200 yields (fast execution)

**Note:** With debug fprintf output added (slowing execution), A1/A3 become PASS after 32/41 yields because system time naturally passes. This confirms the issue is timing-dependent, not a hard failure.

### Root Cause (CONFIRMED via 501-line debug trace)

In `coroutine_yield()` (vm.c:270-395):

1. Main coroutine (index 0) calls `coroutine.yield()`
2. Scheduler saves main coroutine state
3. **Pass 0**: Wake expired sleepers — sleeper (index 1) not yet expired
4. **Pass 0**: Search for next runnable coroutine using ring search:
   ```
   idx = (old + 1 + i) % coroutineCount
   ```
   - i=0: idx=1 (sleeper) → runnable=0 (sleeping)
   - i=1: idx=0 (main) → runnable=1 (**main itself is runnable!**)
   - **Found next=0, restore main coroutine**
5. **Never enters the "wait for IO/timer" path** because a runnable coroutine (main itself) was found in pass 0.

### Key Evidence from Debug Trace

```
[YIELD] ENTER: old=0, coroutineCount=2
[YIELD]   pass=0 co[0]: state=0 wakeTime=0 runnable=1    ← main is runnable
[YIELD]   pass=0 co[1]: state=0 wakeTime=1788775844983 runnable=0  ← sleeper
[YIELD]   pass=0 search: idx=1 runnable=0
[YIELD]   pass=0 search: idx=0 runnable=1                  ← finds main itself
[YIELD]   pass=0 FOUND runnable: next=0, restoring         ← restores main
```

This pattern repeats for every yield — main always finds itself runnable and never enters the timer-wait path.

### Contrast: Why A2 (main sleep) Works

When main calls `coroutine.sleep(50)`:
1. Main's wakeTime is set to now+50 → main is **NOT runnable**
2. Pass 0: search finds no runnable coroutine (both sleeping)
3. Enters "wait for IO/timer" path:
   ```
   [YIELD]   ONLY SLEEPERS: minWake=... now=... sleepMs=20
   [YIELD]   CALLING Sleep(20)
   [YIELD]   LOOP BACK to pass=1
   [YIELD]   WAKING co[1]: wakeTime ... <= now ...
   [YIELD]   pass=1 FOUND runnable: next=1, restoring
   ```
4. Sleeper is woken and restored correctly.

### Minimal Fix Options (for总指挥裁决)

**Option 1: Modify coroutine_yield() ring search**
- When the ring search wraps around and finds only the calling coroutine itself as runnable, and there are sleeping coroutines, enter the timer-wait path instead of immediately restoring self.
- Risk: Changes yield semantics; may affect performance.

**Option 2: Add coroutine.wait() function**
- New function with explicit "block until other coroutines are runnable" semantics.
- `coroutine.yield()` remains non-blocking "cooperative yield".
- Risk: API addition; users need to know which to use.

**Option 3: Document current semantics**
- `coroutine.yield()` is non-blocking; use `coroutine.sleep()` or channel-based synchronization for waiting.
- Risk: User expectation mismatch; "yield loop waiting" is a common pattern.

---

## BUG-B: Closure × Coroutine × try/catch

### Classification: BUG (root cause under investigation)

### Symptom

When a coroutine spawned inside a function modifies a captured local variable **inside a try/catch block**, the modification is **not visible** to the enclosing function.

- B4-1 FAIL: function + coroutine + try/catch + modify captured local → `result` stays "initial"
- B4-2 PASS: module-level + coroutine + try/catch + modify captured local → works
- B4-3 PASS: function + coroutine + modify captured local (NO try/catch) → works
- B4-4 PASS: function + coroutine + shared mutation (NO try/catch) → works

### Minimal Reproduction

**Test 1 (FAIL):** `tests/compiler/bugb_test1_trycatch.tll`
```tll
fn testWithTryCatch() {
    let result = "initial"
    fn coroBody() {
        try {
            throw "test"
        } catch e {
            result = "modified"
        }
    }
    coroutine.spawn(coroBody)
    coroutine.yield()
    coroutine.yield()
    return result  // returns "initial" — BUG
}
```

**Test 2 (PASS):** `tests/compiler/bugb_test2_notrycatch.tll`
```tll
fn testWithoutTryCatch() {
    let result = "initial"
    fn coroBody() {
        result = "modified"
    }
    coroutine.spawn(coroBody)
    coroutine.yield()
    coroutine.yield()
    return result  // returns "modified" — correct
}
```

### Preliminary Root Cause Analysis

**OP_SPAWN implementation** (vm.c:1014-1050):
- Closure environment (`env`) is obtained from the **function value** (`fnVal.as.func.env`), NOT from the current frame.
- `env->refCount++` then `coroutine_create(vm, fn, args, argCount, env)`.

**Hypothesis:** The try/catch codegen interferes with closure variable capture/boxing:

1. Without try/catch: `result` is correctly boxed (OP_BOX_LOCAL) and captured by `coroBody`'s closure env. Modifications via OP_SET_UPVALUE are visible to both.

2. With try/catch: The try/catch codegen may create a new scope or modify the upvalue map such that `result` is **not correctly boxed** or `coroBody`'s closure env points to a **stale/duplicate** location.

**Key areas to investigate in codegen.tll:**
- `cg_compileTry()` (line 974): How does it save/restore closure context?
- `cg_upvalueMap` / `cg_parentUpvalueMap`: Does try/catch reset or modify these?
- OP_BOX_LOCAL emission: Is `result` boxed before the try block?
- OP_SET_UPVALUE in catch block: Does it target the correct upvalue slot?

### Next Steps for BUG-B

1. Add debug output to VM to trace OP_SET_UPVALUE in catch block — verify which upvalue slot is being modified and whether it matches the enclosing function's `result` location.
2. Compare generated bytecode instructions between test1 and test2 (need disassembler or bytecode dump).
3. Check `cg_compileTry()` for any closure context save/restore that might isolate the catch block.

---

## Summary

| Bug | Classification | Root Cause | Status |
|-----|---------------|------------|--------|
| A: Scheduler Timer-Wait | BUG (semantic) | Main coroutine finds itself runnable in pass 0, never enters timer-wait path | **CONFIRMED** |
| B: Closure × Coroutine × try/catch | BUG | try/catch interferes with closure variable capture/boxing (hypothesis) | **UNDER INVESTIGATION** |

Both bugs have stable minimal reproducers committed to the repository:
- `tests/compiler/probe_a_scheduler_timer.tll` (BUG-A)
- `tests/compiler/probe_b4_try_catch_closure.tll` (BUG-B, comprehensive)
- `tests/compiler/bugb_test1_trycatch.tll` (BUG-B minimal)
- `tests/compiler/bugb_test2_notrycatch.tll` (BUG-B control)
