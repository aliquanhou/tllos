# P0-COMPILER-03: Data & Type Capability Probe - Evidence

**Date**: 2026-09-07
**Branch**: p0-compiler-keyword-fix
**Compiler**: tllc_final.tllbc (174 functions, 3953 constants)
**VM**: tllvm.exe with OP_MOV = 60

## Executive Summary

P0-COMPILER-03 performed a complete capability probe of data types and type operations through the full pipeline: Source -> Lexer -> Parser -> AST -> Codegen -> Runtime -> Expected Result.

**Key Finding**: No compiler bugs were discovered in data type handling. All 62 probes passed after correcting API usage in the test itself.

**API Corrections in Test** (not compiler bugs):
1. `arrays.set(arr, idx, val)` does not exist - use direct index assignment `arr[idx] = val` (compiles to OP_INDEX_SET)
2. `maps.new()` does not exist - use object literal `{}`
3. `maps.get(m, key)` / `maps.set(m, key, val)` do not exist - use bracket notation `m[key]` / `m[key] = val`

These are documented in `docs/architecture/language-core-freeze.md`.

## Probe Results Matrix

### Section 1: Primitive Types

| Probe | Feature | Status |
|-------|---------|--------|
| 1.1.1 | int literal equality | PASS |
| 1.1.2 | int addition | PASS |
| 1.1.3 | int subtraction | PASS |
| 1.1.4 | int multiplication | PASS |
| 1.1.5 | int division returns float | PASS (language design: division always returns float) |
| 1.1.6 | int modulo | PASS |
| 1.1.7 | negative int | PASS |
| 1.2.1 | float literal comparison | PASS |
| 1.2.2 | float addition | PASS |
| 1.2.3 | float multiplication | PASS |
| 1.3.1 | true literal | PASS |
| 1.3.2 | false literal | PASS |
| 1.3.3 | bool negation | PASS |
| 1.3.4 | bool negation false | PASS |
| 1.3.5 | bool and | PASS |
| 1.3.6 | bool or | PASS |
| 1.4.1 | string literal equality | PASS |
| 1.4.2 | string concatenation | PASS |
| 1.4.3 | int to string | PASS |
| 1.4.4 | bool to string | PASS |
| 1.5.1 | null return and equality | PASS |
| 1.6.1 | bytes hex escape | PASS |

### Section 2: Collections

| Probe | Feature | Status |
|-------|---------|--------|
| 2.1.1 | array sum via index | PASS |
| 2.1.2 | array length | PASS |
| 2.1.3 | array get index | PASS |
| 2.1.4 | array mutation via index assignment | PASS |
| 2.2.1 | nested array sum | PASS |
| 2.3.1 | map set and get string | PASS |
| 2.3.2 | map set and get int | PASS |
| 2.4.1 | nested map access | PASS |
| 2.5.1 | map containing array | PASS |

### Section 3: Struct / Object

| Probe | Feature | Status |
|-------|---------|--------|
| 3.1.1 | struct construction | PASS |
| 3.2.1 | struct field read x | PASS |
| 3.2.2 | struct field read y | PASS |
| 3.3.1 | struct field write | PASS |
| 3.4.1 | nested struct field access | PASS |
| 3.5.1 | struct as function parameter | PASS |
| 3.6.1 | struct return value x | PASS |
| 3.6.2 | struct return value y | PASS |

### Section 4: Type Operations

| Probe | Feature | Status |
|-------|---------|--------|
| 4.1.1 | int equality true | PASS |
| 4.1.2 | int equality false | PASS |
| 4.1.3 | string equality true | PASS |
| 4.1.4 | string equality false | PASS |
| 4.1.5 | bool equality true | PASS |
| 4.1.6 | null equality | PASS |
| 4.2.1 | greater than true | PASS |
| 4.2.2 | greater than false | PASS |
| 4.2.3 | less than true | PASS |
| 4.2.4 | greater equal | PASS |
| 4.2.5 | less equal | PASS |
| 4.3.1 | operator precedence | PASS |
| 4.3.2 | parentheses | PASS |
| 4.3.3 | left associativity | PASS |
| 4.4.1 | array indexing | PASS |
| 4.5.1 | int parameters and return | PASS |
| 4.5.2 | string parameters and return | PASS |

### Section 5: Memory / Value Semantics

| Probe | Feature | Status |
|-------|---------|--------|
| 5.1.1 | int assignment is value copy | PASS |
| 5.2.1 | array assignment is reference (aliasing) | PASS |
| 5.3.1 | map assignment is reference (aliasing) | PASS |
| 5.4.1 | array passed by reference to function | PASS |
| 5.5.1 | int passed by value to function | PASS |
| 5.6.1 | struct assignment is reference (aliasing) | PASS |

**Total: 62/62 PASS**

## Language Design Observations (Not Bugs)

1. **Integer division returns float**: `10 / 3` returns `3.33333`, not truncated `3`. This is consistent language design - use `10 % 3` for modulo or explicit conversion for integer division.

2. **Array/Map/Struct assignment is reference**: `b = a` creates an alias, not a copy. Mutations through `b` affect `a`. This is standard for complex types.

3. **Primitive assignment is value copy**: `b = a` for int/float/bool creates an independent copy.

4. **No `arrays.set` builtin**: Use direct index assignment `arr[idx] = val`.

5. **No `maps` module**: Use object literal `{}` and bracket notation `m[key]`.

## Regression Results

- **P0-COMPILER-01 Function Definition Gate**: 46/46 PASS
- **P0-COMPILER-01 Function Capability Probe**: 33/33 PASS
- **P0-COMPILER-02 Control Flow Probe**: 66/67 PASS (Probe 6.4 for iterate string = known limitation)

## Compiler Bootstrap

No compiler changes in this phase. Existing compiler (tllc_final.tllbc) used.

## Files Modified

1. `tests/compiler/probe_data_type.tll` - NEW: Data & Type Capability Probe Matrix (62 tests across 5 sections)
2. `docs/P0-COMPILER-03-DATA-TYPE-EVIDENCE.md` - NEW: Evidence document

**No compiler/runtime code changes** - this phase was pure capability verification.

## Test Commands

```bash
# Compile probe test
tllvm tools/TLLC/tllc_final.tllbc compile tests/compiler/probe_data_type.tll -o tests/compiler/probe_data_type.tllbc

# Run probe test
tllvm tests/compiler/probe_data_type.tllbc

# Expected output
Total: 62
Passed: 62
Failed: 0
ALL DATA & TYPE PROBES PASSED
```

## Known Limitations (Carried Forward)

1. **for loop only supports array iteration** - string iteration returns 0 (from P0-COMPILER-02)
2. **switch/match not implemented** - parser has no syntax (from P0-COMPILER-02)
3. **String multiplication (`"x" * N`) has bug** - returns garbage instead of repeated string (from P0-COMPILER-02, marked UNKNOWN/NEEDS INDEPENDENT PROBE)
4. **if cannot be used as expression** - `let x = if ...` compiles fail (known language design)
5. **Historical CI failures** (PRE-EXISTING): HMAC / FS Windows / Blockchain reconnect / Fault Injection

## Areas for Future Probe (Not Covered)

1. **Type inference** - explicit vs inferred typing
2. **Explicit type conversion** - int<->float, string<->int, etc.
3. **Type checking at compile time** - type errors detection
4. **Generics / parametric types**
5. **Union types / sum types**
6. **Type reflection / runtime type checking**
7. **Array typed (e.g., list<int>)**
8. **Map typed (e.g., map<string, int>)**

## Conclusion

**P0-COMPILER-03 Data & Type Capability Probe = READY FOR SEAL**

All 62 probes passed. No compiler bugs discovered in data type handling. The phase confirmed that TLL's primitive types, collections (array/map), structs, type operations, and memory/value semantics are all functioning correctly.

Key API usage patterns verified:
- Array: `arr[idx] = val` for mutation, `arrays.get(arr, idx)` for read
- Map: `{}` for creation, `m[key] = val` for set, `m[key]` for get
- Struct: `StructName{field: value}` for construction, `.field` for access
- Reference semantics: array/map/struct assignment creates aliases
- Value semantics: primitive (int/float/bool) assignment creates copies
