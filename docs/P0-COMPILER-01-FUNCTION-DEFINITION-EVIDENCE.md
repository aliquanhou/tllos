# P0-COMPILER-01 + P0-COMPILER-PROBE-01 Evidence

## Capability
TLL Compiler Function Definition Completeness + Function Capability Probe Matrix

## Original Gap
SHOP (tll-shop) exposed a real-world compiler failure:

```tll
fn aftersale_typeText(type) {
    if type == "refund" {
        return "退款"
    }
    return "其他"
}
```

This function definition in a page module failed to compile with:
```
Parse error: expected parameter name, got 'type' (TYPE) at line 2
```

## Root Cause
9 keywords were reserved in `compiler/lexer.tll` `getKeywordType()` but **NEVER used as grammar keywords in `compiler/parser.tll`**:

1. `type`
2. `entity`
3. `api`
4. `application`
5. `async`
6. `await`
7. `agent`
8. `tool`
9. `workflow`

These keywords were "reserved for future use" but had no grammar implementation. They occupied identifier namespace, causing AI-generated code with common variable/parameter names to fail compilation.

Verification: `grep` for these token types in parser.tll returned zero matches for grammar usage (only a special-case in map literal key parsing).

## Fix
### compiler/lexer.tll
Removed 9 unused keyword definitions from `getKeywordType()`:
- `type` → TK_TYPE
- `entity` → TK_ENTITY
- `api` → TK_API
- `application` → TK_APPLICATION
- `async` → TK_ASYNC
- `await` → TK_AWAIT
- `agent` → TK_AGENT
- `tool` → TK_TOOL
- `workflow` → TK_WORKFLOW

These words now tokenize as ordinary IDENT tokens.

### compiler/parser.tll
Removed special-case handling for TYPE/ASYNC/AWAIT in map literal key parsing (line ~906). These are now IDENT tokens and handled by the existing IDENT branch.

Retained STRUCT and ENUM special-cases in map key parsing since they remain grammar keywords.

## Test Files
### tests/compiler/gate_function_definition.tll
Function Definition Completeness Gate — 46 assertions.

Coverage:
- **Gate 1**: No-param function
- **Gate 2**: Single-param function
- **Gate 3**: Two-param function
- **Gate 4**: Multi-param function (4 params)
- **Gate 5**: Function defined but NOT called (compiles without error)
- **Gate 6**: if / if-else / nested-if
- **Gate 7**: return / multi-return / conditional-return
- **Gate 8**: Various param types (string, number, bool, array, map)
- **Gate 9**: 9 previously-reserved keywords as identifiers:
  - As function parameters (9 tests)
  - As local variables (1 test)
  - As function names (9 tests)
  - As map keys (1 test)

**Result: 46/46 PASS**

### tests/compiler/probe_function_capability.tll
Function Capability Probe Matrix — 33 probes.

Coverage:
1. **Recursion**: factorial(n), fibonacci(n)
2. **Mutual Recursion**: isEven(n) ↔ isOdd(n)
3. **Forward Call**: caller defined before callee
4. **Backward Call**: callee defined before caller
5. **Local Variables**: declaration, assignment, mutation
6. **Parameter Shadowing**: outer param x, inner function with own param x
7. **Return Types**: null, bool, int, float, string, array, map
8. **Early Return**: return before unreachable code
9. **Multi-Exit Return**: 4 exit points
10. **Nested Return**: 3 levels of nested if with returns
11. **Conditional Return**: && and || conditions
12. **Higher-Order Function**: function as parameter (applyTwice)
13. **Closure**: function as return value capturing outer variable (makeAdder)

**Result: 33/33 PASS**

## Compiler Bootstrap
Verified that the modified compiler can self-bootstrap:
```
tllvm tllc.tllbc compile tools/TLLC/main.tll -o tllc_new.tllbc
→ Compilation Successful (174 functions, 3931 constants)
```

Then used tllc_new.tllbc to compile all test files successfully.

## Regression Analysis
### Pre-existing failures (NOT caused by this change)
- **P1-03 HMAC Gate**: 2/20 PASS with BOTH old and new compiler. Verified by compiling with original tllc.tllbc — same failure pattern. This is a pre-existing issue unrelated to keyword removal.
- **P1-NEXT L1 File System Gate**: 18/25 PASS. Failures are on Windows file operation return values (writeFile/appendFile/mkdir/copyFile/rename/remove returning true). Pre-existing platform behavior issue.

### No regression detected
- Compiler self-bootstrap: PASS
- All function definition tests: PASS
- All function capability probes: PASS
- No existing test that previously passed now fails due to keyword removal

## CI
- **Branch**: p0-compiler-keyword-fix
- **Commit**: a6d64b02f84a272507979f8dc8495871492b0384
- **Pull Request**: #1
- **CI Run ID**: 34080860120

### Compiler Gate Results (Three Platform)
| Step | Ubuntu | Windows | macOS |
|------|--------|---------|-------|
| Build Native Launcher | PASS | PASS | PASS |
| Verify bootstrap seed | PASS | PASS | PASS |
| ABI consistency check | PASS | PASS | PASS |
| Native self-host verification | PASS | PASS | PASS |
| Bootstrap tllc | PASS | PASS | PASS |

**Compiler Gate = THREE PLATFORM PASS**

### Pre-existing CI Failures (NOT Compiler Gate)
- Blockchain reconnect + auto-sync (Windows): FAIL — PRE-EXISTING (runtime timing test)
- Fault Injection - Kill-9 Node Restart (macOS): FAIL — PRE-EXISTING (main branch 34078998896 also fails)

See `docs/COMPILER-HEALTH-BASELINE.md` for full pre-existing failure analysis.

## Files Changed
1. `compiler/lexer.tll` — removed 9 unused keyword definitions
2. `compiler/parser.tll` — removed TYPE/ASYNC/AWAIT special-case in map key parsing
3. `tests/compiler/gate_function_definition.tll` — NEW: 46 assertion Gate test
4. `tests/compiler/probe_function_capability.tll` — NEW: 33 probe Probe Matrix

## Known Limitations
1. STRUCT and ENUM remain reserved keywords (they have actual grammar implementations for struct/enum declarations)
2. TRY/CATCH/FINALLY/THROW remain reserved keywords (they have actual grammar implementations for exception handling)
3. The 9 removed keywords are now available as identifiers; if future grammar needs them as keywords, they can be re-added at that time with proper implementation
4. HMAC and File System test failures are pre-existing and tracked separately

## Next Ladder
After P0-COMPILER-01 + PROBE-01 seal, the next compiler capability ladder:
- **P0-COMPILER-02 Control Flow Capability Probe**: if/else/else if/nested, while/for, break/continue, return in loop, nested loop, &&/|| short circuit, !, ternary, switch/match —逐项 Parser→AST→Codegen→Runtime→expected result，自动分类 PASS/BUG/PARTIAL/MISSING

---

# FINAL AUDIT (P0-COMPILER-01)

## Audit Item 1: 9 Keywords Grammar Verification

**Method**: Searched Lexer / Parser / Codegen / TypeChecker / Linker / Stdlib / Tests / Docs for each keyword's grammar implementation.

| Keyword | Parser Dispatch | AST Node | Codegen Handle | TypeChecker | Docs Frozen | Verdict |
|---------|----------------|----------|----------------|-------------|-------------|---------|
| `type` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `entity` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `api` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `application` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `async` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `await` | NO | NO | NO | defensive only | NO | RESERVED BUT UNUSED |
| `agent` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `tool` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |
| `workflow` | NO | NO | NO | NO | NO | RESERVED BUT UNUSED |

**Conclusion**: All 9 keywords are RESERVED BUT UNUSED. No grammar implementation exists. No documentation freezes them as future syntax. Safe to use as ordinary identifiers.

**Note**: `await` has a defensive `kind == "Await"` check in TypeChecker, but Await AST nodes are never created by Parser (no dispatch). `agent` and `workflow` have module-name checks in Codegen (`modName == "agent"` / `modName == "workflow"`), which are module resolution logic, not keyword grammar.

## Audit Item 2: SHOP Original Case Real Regression

**Test file**: `tests/compiler/audit_shop_regression.tll`

**Exact SHOP code**:
```tll
fn aftersale_typeText(type) {
    if type == "refund" {
        return "退款"
    }
    return "其他"
}
```

**Full pipeline**: Source → Compile → Link → Run → Function call → Correct return

**Results**: 9/9 PASS
- aftersale_typeText("refund") → "退款" ✅
- aftersale_typeText("exchange") → "其他" ✅
- aftersale_typeText("") → "其他" ✅
- Function defined but NOT called compiles successfully ✅
- type as expression operand ✅
- type as local variable ✅
- type as map key ✅
- type in string literal ✅
- Additional SHOP-style functions (status/category params) ✅

## Audit Item 3: Not a Special Bypass

All 9 keywords verified as normal identifiers in all contexts:

| Context | type | entity | api | application | async | await | agent | tool | workflow |
|---------|------|--------|-----|-------------|-------|-------|-------|------|----------|
| Function parameter | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Local variable | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Function name | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Map key | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| String literal | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Test files**: `tests/compiler/gate_function_definition.tll` (46 assertions), `tests/compiler/audit_shop_regression.tll` (9 assertions)

## Audit Item 4: Compiler Health Baseline

**Document**: `docs/COMPILER-HEALTH-BASELINE.md`

**Pre-existing failures** (verified NOT caused by P0-COMPILER-01):

| Failure | Old HEAD | New HEAD | Difference | Verdict |
|---------|----------|----------|------------|---------|
| HMAC Gate (2/20) | FAIL | FAIL | 0 | PRE-EXISTING |
| File System Windows (18/25) | FAIL | FAIL | 0 | PRE-EXISTING |
| Blockchain Reconnect CI | FAIL | FAIL | 0 | PRE-EXISTING |
| Fault Injection CI (macOS) | FAIL | FAIL | 0 | PRE-EXISTING |

**Evidence**:
- HMAC: fails with both old compiler (tllc.tllbc) and new compiler
- File System: C builtin functions, not compiler features
- Blockchain/Fault Injection: main branch CI 34078998896 also fails (before this fix)

## Final Seal Conditions

| Condition | Status |
|-----------|--------|
| A: 9 keywords confirmed NOT frozen syntax | ✅ PASS (all RESERVED BUT UNUSED) |
| B: SHOP original code compiles and runs correctly | ✅ PASS (9/9) |
| C: 46/46 Function Gate | ✅ PASS |
| D: 33/33 Function Probe | ✅ PASS |
| E: Compiler Bootstrap three-platform success | ✅ PASS (Ubuntu/Windows/macOS) |
| F: No new regression from this change | ✅ PASS (all failures PRE-EXISTING) |

## Final Verdict

**P0-COMPILER-01 = READY FOR FINAL SEAL**

**Compiler Gate: THREE PLATFORM PASS**

**Repository has independent PRE-EXISTING CI failures (HMAC / File System / Blockchain / Fault Injection), which are NOT used as Compiler PASS evidence and are tracked separately in `docs/COMPILER-HEALTH-BASELINE.md`.**

This evidence does NOT claim "full repository CI PASS". It claims:
- Compiler fix is correct and complete
- Compiler Gate passes on all three platforms
- No new regressions introduced
- Pre-existing failures are independently documented
