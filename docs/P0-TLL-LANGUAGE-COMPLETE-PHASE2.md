# P0-TLL-LANGUAGE-COMPLETE Phase 2: Interface / Trait / Protocol

> Status: IMPLEMENTED + VERIFIED
> Date: 2026-09-08
> Branch: p0-language-phase2-interface
> North Star: TLL Industrial Compiler (see docs/TLL-INDUSTRIAL-COMPILER-NORTH-STAR.md)

## 1. Capability Summary

TLL now supports Interface / Trait / Protocol minimal closed loop:

- **Interface declaration**: `interface Name { fn method(self) -> Type }`
- **Struct implementation**: `impl Interface for Struct { fn method(self) { ... } }`
- **Runtime method dispatch**: `obj.method()` automatically dispatches based on `__struct` type
- **Interface as parameter**: `fn show(x: Printable)` accepts any type implementing the interface
- **Multiple interfaces per type**: A struct can implement multiple interfaces
- **Collection of interface types**: Arrays of different types sharing an interface

## 2. Implementation Details

### 2.1 Lexer (compiler/lexer.tll)
- Registered `interface` and `impl` keywords in `getKeywordType()`
- Constants `TK_INTERFACE` and `TK_IMPL` were already defined

### 2.2 Parser (compiler/parser.tll)
- `parseInterfaceDeclaration()`: Parses interface name + method signatures
- `parseImplDeclaration()`: Parses `impl Interface for Type { fn ... }` blocks
- Impl methods are parsed via `parseFnDeclaration()` and stored with `implInterface` and `implType` metadata

### 2.3 Codegen (compiler/codegen.tll)
- **Function collection** (`cg_collectFunctions`): Impl methods are registered as mangled functions (`TypeName__methodName`)
- **Method dispatch** (`cg_compileCall`): When calling `obj.method()`:
  1. Traverse `cg_functions` to find all functions ending with `__methodName`
  2. Get object's `__struct` field via `OP_MEMBER_GET`
  3. Compare type name with each implementing type via `OP_EQ`
  4. Use `OP_JMP_IF_FALSE` + `cg_patchJump()` for conditional branching
  5. Push `self` + args, call matching function via `OP_CALL`
  6. Fallback to `null` if no type matches

### 2.4 Key Bug Fixes During Implementation
1. **OP_CALL parameter order**: Must be `[resultReg, fnIdx, argCount]`, not `[fnIdx, argCount, resultReg]`
2. **Field access opcode**: Must use `OP_MEMBER_GET` (not `OP_INDEX_GET`) for `__struct` field
3. **Jump/label API**: Correct names are `OP_JMP`, `OP_JMP_IF_FALSE`, `cg_newLabel()`, `cg_patchJump()` — NOT `OP_JUMP`, `OP_JUMP_IF_FALSE`, `cg_makeLabel()`, `cg_emitLabel()`
4. **Dispatch map issue**: `cg_methodDispatchMap` was not being populated correctly; switched to direct `cg_functions` traversal using suffix matching

## 3. Test Results

### Persistent Regression Test: tests/compiler/probe_interface_trait.tll

| Test | Result |
|------|--------|
| User.print() direct call | ✅ PASS |
| Product.print() direct call | ✅ PASS |
| show(User) interface param | ✅ PASS |
| show(Product) interface param | ✅ PASS |
| User.describe() multiple interfaces | ✅ PASS |
| printAll() collection of interface types | ✅ PASS |

**All 6/6 tests PASS.**

## 4. Known Limitations / GAPs

1. **Bootstrap issue**: The new compiler can compile itself, but the resulting bootstrap compiler fails with "Unknown command:" when run. This is a self-hosting regression that needs investigation.
2. **No compile-time interface checking**: The compiler does not verify that a struct implementing an interface actually provides all required methods.
3. **No interface type annotations**: `fn show(x: Printable)` syntax is parsed but not enforced at compile time (currently dynamic dispatch only).
4. **No generic constraints**: `fn show<T: Printable>(x: T)` is not yet supported.
5. **No ADT impl**: Interfaces can only be implemented by structs, not by ADT/enum types.
6. **No trait inheritance**: `interface B extends A` is not supported.

## 5. Regression Status

- P0-COMPILER-01 Function Definition: Need verification
- P0-COMPILER-02 Control Flow: Need verification
- P0-COMPILER-03 Data & Type: Need verification
- P0-TLL-LANGUAGE-COMPLETE Phase 1 (Tuple/Destructuring/Generic/ADT): Need verification

## 6. Files Modified

- `compiler/lexer.tll` — keyword registration
- `compiler/parser.tll` — interface/impl parsing
- `compiler/codegen.tll` — function mangling + runtime method dispatch
- `tests/compiler/probe_interface_trait.tll` — persistent regression test
- `docs/TLL-INDUSTRIAL-COMPILER-NORTH-STAR.md` — long-term strategy document

## 7. Next Phase Candidates

Per ladder: Error/Resource Enhancement → Module/Package → Concurrency → Compiler IR → Optimization → Backend

Decision: pending architect review.

---

*This capability is part of the TLL Industrial Compiler initiative.
The current 180-function compiler is a bootstrap/development tool;
the final goal is an industrial-grade, self-hosting, optimizing, multi-backend compiler.*
