# P0-COMPILER-02: Control Flow Capability Probe - Evidence

**Date**: 2026-09-07
**Branch**: p0-compiler-keyword-fix
**Compiler**: tllc_final.tllbc (174 functions, 3953 constants)
**VM**: tllvm.exe with OP_MOV = 60

## Executive Summary

P0-COMPILER-02 performed a complete capability probe of 16 control flow features through the full pipeline: Source -> Lexer -> Parser -> AST -> Codegen -> Runtime -> Expected Result.

**4 real Compiler Bugs were discovered and fixed:**
1. Ternary operator completely non-functional
2. AND/OR operators lacked short-circuit evaluation
3. `break` in `for` loop caused VM crash (unknown opcode)
4. `continue` in `for` loop caused infinite loop

**Final Probe Results (Probes 1-15): 66/67 PASS**
- Only failure: Probe 6.4 (for iterate string chars) - known limitation, TLL `for` only supports array iteration

**Probe 16 (switch/match): MISSING** - parser has no syntax implementation, compile fails as expected.

## Bug Discovery and Fix Details

### Bug 1: Ternary Operator Non-Functional
**Symptom**: `5 > 0 ? "yes" : "no"` always returned empty string.

**Root Cause**:
- `cg_compileExpression` had no `kind == "Ternary"` dispatch
- `cg_compileTernary` always returned `consequentReg`, but false path result was in `alternateReg`; when branches had different complexity, wrong register was returned

**Fix**:
- Added `OP_MOV = 60` VM instruction (register-to-register move with reference counting)
- Added `kind == "Ternary"` dispatch to `cg_compileExpression`
- Fixed `cg_compileTernary` to pre-allocate `resultReg`, both consequent and alternate branches end with `OP_MOV` moving result to `resultReg`

### Bug 2: AND/OR No Short-Circuit Evaluation
**Symptom**: `false and side_effect()` still called `side_effect()`.

**Root Cause**: `cg_compileBinary` compiled both `left` and `right` before entering the `op == "&&"` branch, causing `right` to be compiled twice; VM `OP_AND`/`OP_OR` instructions themselves were non-short-circuit.

**Fix**: Moved AND/OR special handling to before `let rightReg = cg_compileExpression(expr.right)`, using `OP_JMP_IF_FALSE` (AND) or `OP_NOT`+`OP_JMP_IF_FALSE` (OR) to implement jump-based short-circuit.

### Bug 3: break in for Loop Caused VM Crash
**Symptom**: Probe 7 (break) crashed with "unknown opcode" / ACCESS_VIOLATION.

**Root Cause**: `cg_compileWhile` correctly handled `cg_breakPatchList`, but `cg_compileFor` had **no break patch handling at all** - break statement emitted `OP_JMP [-1]`, jump target was never patched, jumping to invalid address -1.

**Fix**: Added break patch logic to `cg_compileFor` (same as `cg_compileWhile`): save -> clear -> compile body -> patch all breaks to after loop -> restore. Patch position is after increment index, before `OP_JMP`.

### Bug 4: continue in for Loop Caused Infinite Loop
**Symptom**: `continue` in `for` loop caused infinite loop / timeout.

**Root Cause**: `continue` jumped to condition check (`startIdx`), but skipped the index increment (`idx++`), causing `idx` to never change.

**Fix**:
- Added global `cg_continuePatchList`
- Modified continue handling to support for loop forward-reference patching (`cg_currentContinueLabel == -2` emits `OP_JMP [-1]` and records position)
- Modified `cg_compileFor` to set `cg_currentContinueLabel = -2` and patch continue statements to jump to **before** the increment index (so increment executes before condition check)
- Fixed `compile` function to initialize `cg_continuePatchList = []` (was missing, could contain stale data)

## Probe Results Matrix

| Probe | Feature | Status | Details |
|-------|---------|--------|---------|
| 1 | if (basic) | PASS | 3/3 assertions |
| 2 | if / else | PASS | 3/3 assertions |
| 3 | else if (chain) | PASS | 4/4 assertions |
| 4 | nested if | PASS | 4/4 assertions |
| 5 | while loop | PASS | 4/4 assertions |
| 6 | for loop | PARTIAL | 3/4 PASS; 6.4 for iterate string = MISSING (known limitation) |
| 7 | break | PASS | 4/4 assertions (including break in for) |
| 8 | continue | PASS | 3/3 assertions (including continue in for) |
| 9 | return in loop | PASS | 4/4 assertions |
| 10 | nested loop | PASS | 5/5 assertions |
| 11 | && (and) | PASS | 4/4 assertions |
| 12 | || (or) | PASS | 4/4 assertions |
| 13 | short-circuit | PASS | 8/8 assertions |
| 14 | ! (logical not) | PASS | 5/5 assertions |
| 15 | ternary | PASS | 8/8 assertions |
| 16 | switch / match | MISSING | Parser has no syntax; compile fails as expected |

**Total (Probes 1-15): 66/67 PASS**

## Additional Bug Discovered (Not Fixed - Recorded for Future)

### String Multiplication Bug
**Symptom**: `"=" * 60` returned garbage number (`93179037515760`) instead of 60 "=" characters.

**Status**: NOT FIXED in this phase. Workaround used in test: explicit string literal. Recorded as separate string operation bug for future phase.

## Regression Results

### P0-COMPILER-01 Regression
- Function Definition Gate: **46/46 PASS**
- Function Capability Probe: **33/33 PASS**

### P1 Regression (to be verified in CI)
- P1-01 Secure Random
- P1-02 Password Hashing
- P1-03 HMAC/SHA256
- P1-04 HTTP Client L1-4

## Compiler Bootstrap

- Old compiler (tllc.tllbc): 172 functions, 3911 constants
- New compiler (tllc_final.tllbc): 174 functions, 3953 constants
- Bootstrap: PASS (old -> new -> new2, all successful)

## Known Limitations

1. **for loop only supports array iteration** - string iteration returns 0 (Probe 6.4)
2. **switch/match not implemented** - parser has no syntax (Probe 16)
3. **String multiplication (`"x" * N`) has bug** - returns garbage instead of repeated string
4. **if cannot be used as expression** - `let x = if ...` compiles fail (known language design)
5. **Historical CI failures** (PRE-EXISTING, not caused by this phase):
   - HMAC (pre-existing)
   - File System / Windows (pre-existing)
   - Blockchain reconnect (pre-existing)
   - Fault Injection (pre-existing)

## Files Modified

1. `compiler/codegen.tll` - ternary fix, short-circuit AND/OR, break in for, continue in for, OP_MOV constant, cg_continuePatchList initialization
2. `host/c/tllvm.h` - OP_MOV = 60 enum
3. `host/c/vm.c` - OP_MOV implementation (with incref/free)
4. `tests/compiler/probe_control_flow.tll` - NEW: Control Flow Probe Matrix (Probes 1-15)
5. `tests/compiler/probe_switch_match.tll` - NEW: Probe 16 switch/match (confirms MISSING)

## Conclusion

P0-COMPILER-02 Control Flow Capability Probe is **READY FOR SEAL** with the following caveats:
- Probe 6.4 (for iterate string) = PARTIAL (known limitation, not a regression)
- Probe 16 (switch/match) = MISSING (correctly identified as not implemented)
- String multiplication bug = recorded for future phase

All 4 discovered Compiler Bugs have been fixed and verified.
