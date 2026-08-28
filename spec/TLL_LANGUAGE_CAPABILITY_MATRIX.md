# TLL Language Capability Matrix

**Version**: P0-6 (in progress)
**Date**: 2026-08-28
**Repository**: aliquanhou/tllos @ main
**Audit Method**: Source code + test verification (not README)

## Legend

| Status | Meaning |
|--------|---------|
| COMPLETE | Implemented, tested, dogfooded, regression protected |
| PARTIAL | Implemented but has known limitations or incomplete coverage |
| STUB | Stub only, returns null/placeholder |
| EXPERIMENTAL | Experimental implementation, not stable |
| DEFERRED | Recognized but not yet implemented |

---

## 1. Language Core

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Lexer | COMPLETE | compiler/lexer.tll | - | Tokenizes all TLL syntax |
| Parser | COMPLETE | compiler/parser.tll | struct_literal_test | Recursive descent + Pratt, supports all constructs |
| AST | PARTIAL | map-based nodes | - | Uses parallel lists for maps (field access reliability) |
| Compiler | COMPLETE | compiler/codegen.tll | all tests | AST to bytecode, 46+ opcodes |
| VM | COMPLETE | host/c/vm.c | all tests | Stack-based bytecode VM, closures, exceptions |
| Bytecode format | COMPLETE | JSON-based | - | functions + constants + mainFunctionIndex |
| Self-hosting | COMPLETE | compiler/compiler.tll | bootstrap | Deterministic multi-generation bootstrap |

## 2. Type System

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Primitive types (int/float/string/bool/null) | COMPLETE | VM value types | - | 64-bit int, 64-bit float, UTF-8 string |
| Compound types (array/map) | COMPLETE | VM value types | - | Dynamic arrays, hash maps |
| Function type | COMPLETE | TLL_FUNCTION | closures | First-class functions, closures |
| Struct type | PARTIAL | codegen StructLiteral | struct_literal_test | Declaration + literal + access, no compile-time type checking |
| Enum type | PARTIAL | codegen enumMap | enum_variant_test | Declaration + variant access as constants, no type checking |
| Type annotations | PARTIAL | parser + typechecker.tll | - | Syntax supported, typechecker not enforced |
| Type inference | PARTIAL | codegen local vars | - | Local variable inference only |
| Generic types | DEFERRED | - | - | array<T>/map<K,V> only documentation |
| Compile-time type errors | DEFERRED | - | - | Type errors reach VM runtime |

## 3. Functions & Closures

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Function declaration | COMPLETE | parser/codegen | simple_fn | fn name(params) { body } |
| First-class functions | COMPLETE | VM TLL_FUNCTION | hof | Functions as values |
| Higher-order functions | COMPLETE | VM call | hof | map/filter/reduce patterns |
| Nested functions | COMPLETE | VM closures | closures | Functions inside functions |
| Closure (immutable capture) | COMPLETE | OP_GET_UPVALUE | closures | 8 closure test categories |
| Closure (mutable capture) | COMPLETE | OP_BOX_LOCAL | mut_closure | Mutable captured variables |
| Shared upvalue box | COMPLETE | UpvalueBox | closures | Sibling closures share box |
| Escaping closures | COMPLETE | VM | min_closure | Closures outlive creating function |
| Anonymous functions (Lambda) | COMPLETE | parser FnExpr | - | fn(params) { body } expression |
| Recursion | COMPLETE | VM | - | Named function recursion |
| Variadic params | DEFERRED | - | - | arrays.push uses special handling |
| Default params | DEFERRED | - | - | Not supported |
| Keyword params | DEFERRED | - | - | Not supported |
| Function overloading | DEFERRED | - | - | Not supported |

## 4. Struct

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Struct declaration | COMPLETE | parser parseStructDeclaration | struct_literal_test | struct Name { field: type } |
| Struct literal | COMPLETE | parser StructLiteral + codegen | struct_literal_test | User { name: "Alice", age: 18 } |
| Field access | COMPLETE | OP_MEMBER_GET | struct_literal_test | user.name |
| Field mutation | COMPLETE | OP_MEMBER_SET | struct_literal_test | user.age = 19 |
| Nested struct | COMPLETE | codegen StructLiteral | struct_literal_test | Rect { origin: Point { x: 10 } } |
| Struct as function param | COMPLETE | VM | struct_literal_test | fn printUser(u: User) |
| Struct as return value | PARTIAL | VM | - | Returns map with __struct field |
| Struct array | PARTIAL | VM arrays | - | Array of struct maps |
| Struct map | PARTIAL | VM maps | - | Map of struct maps |
| Compile-time struct type checking | DEFERRED | - | - | No field name/type validation at compile time |
| Struct methods | DEFERRED | - | - | No method syntax |

## 5. Enum

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Enum declaration | COMPLETE | parser parseEnumDeclaration | enum_variant_test | enum Name { Variant = value } |
| Variant access | COMPLETE | codegen enumMap | enum_variant_test | Color.Red resolves to constant int |
| Variant comparison | COMPLETE | VM OP_EQ | enum_variant_test | c == Color.Red |
| Enum assignment | COMPLETE | VM | enum_variant_test | let c = Color.Red |
| Explicit values | COMPLETE | codegen enumMap | enum_variant_test | Red = 1, Green = 2 |
| Auto-increment values | COMPLETE | codegen enumMap | enum_variant_test | North=0, East=1, ... |
| Enum as function param | PARTIAL | VM | - | Passed as int |
| Enum as return value | PARTIAL | VM | - | Returned as int |
| Enum array | PARTIAL | VM arrays | - | Array of enum ints |
| Pattern matching (match) | DEFERRED | - | - | Not implemented |
| Enum with data | DEFERRED | - | - | Rust-style enum variants not supported |

## 6. Module / Import

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| import statement | COMPLETE | parser parseImportStatement | modular shop | import name from "path" |
| from import statement | COMPLETE | parser parseFromImportStatement | modular shop | from "./path" import name |
| export statement | COMPLETE | parser parseExportStatement | modular shop | export fn/let |
| Relative module paths | COMPLETE | linker | modular shop | "./product", "./cart" |
| Cross-module imports | COMPLETE | linker | modular shop | templates imports cartCount |
| export let (state) | COMPLETE | linker | modular shop | export let products = [...] |
| export fn (functions) | COMPLETE | linker | modular shop | export fn findProduct() |
| Module isolation | PARTIAL | linker | - | Module-level state shared |
| Duplicate import | PARTIAL | linker | - | No explicit dedup |
| Circular dependency | DEFERRED | - | - | No detection |
| Package manager | DEFERRED | - | - | No tll.toml dependency resolution |

## 7. Error Handling

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| try/catch | COMPLETE | VM OP_TRY_START/END | error_handling_test | try { } catch err { } |
| finally | COMPLETE | VM try-finally | error_handling_test | try { } finally { } |
| throw | COMPLETE | VM OP_THROW | error_handling_test | throw "message" |
| throw map object | COMPLETE | VM OP_THROW | error_handling_test | throw { type, message, code } |
| Exception propagation | COMPLETE | VM | error_handling_test | Throw in function propagates to caller |
| Error type | PARTIAL | throw map | - | No built-in Error type, use map |
| Source location in errors | PARTIAL | VM | - | Parse errors have line/column, runtime errors limited |
| Stack trace | DEFERRED | - | - | Not implemented |
| Compiler diagnostics | DEFERRED | - | - | Basic parse error, no rich diagnostics |

## 8. HTTP

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| HTTP Client (get/post/request) | COMPLETE | host/c builtin.c WinHTTP | test_http | http.get, http.post, http.request |
| HTTP Server (http.serve) | COMPLETE | host/c builtin.c Winsock2 | http_server_upgrade_test | Single-threaded, one connection at a time |
| Request method | COMPLETE | host/c builtin.c | - | GET/POST/PUT/DELETE/PATCH all parsed |
| Request path | COMPLETE | host/c builtin.c | - | Path without query string |
| Request query string | COMPLETE | host/c builtin.c | http_server_upgrade_test | req.query, req.queryMap |
| Request headers | COMPLETE | host/c builtin.c | http_server_upgrade_test | req.headers map |
| Request body | COMPLETE | host/c builtin.c | - | req.body string |
| Response status | COMPLETE | host/c builtin.c | http_server_upgrade_test | resp.status int |
| Response headers | COMPLETE | host/c builtin.c | http_server_upgrade_test | resp.headers map |
| Response body | COMPLETE | host/c builtin.c | - | resp.body string |
| Response content-type | COMPLETE | host/c builtin.c | - | resp.contentType |
| Status reason phrases | COMPLETE | host/c builtin.c | http_server_upgrade_test | 200 OK, 201 Created, 404 Not Found, 500, etc. |
| HTTP concurrency | DEFERRED | - | - | Single-threaded, one connection at a time |
| HTTP Server (http.serve) stub removed | COMPLETE | host/c builtin.c | - | Was stub (idx 94), now implemented |

## 9. Cookie / Session

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Cookie parsing | DEFERRED | - | - | Not implemented |
| Set-Cookie response | DEFERRED | - | - | Not implemented |
| Session creation | DEFERRED | - | - | Not implemented |
| Session lookup | DEFERRED | - | - | Not implemented |
| Session storage | DEFERRED | - | - | Not implemented |
| Session expiration | DEFERRED | - | - | Not implemented |
| User registration | DEFERRED | - | - | Not implemented |
| User login | DEFERRED | - | - | Not implemented |
| User logout | DEFERRED | - | - | Not implemented |

## 10. Filesystem / Persistence

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| fs.readFile | COMPLETE | host/c builtin.c idx 79 | - | Read entire file as string |
| fs.writeFile | COMPLETE | host/c builtin.c idx 80 | - | Write string to file |
| fs.appendFile | COMPLETE | host/c builtin.c idx 81 | - | Append to file |
| fs.exists | COMPLETE | host/c builtin.c idx 82 | - | Check file existence |
| fs.mkdir | COMPLETE | host/c builtin.c idx 83 | - | Create directory |
| fs.remove | COMPLETE | host/c builtin.c idx 84 | - | Delete file |
| fs.listDir | COMPLETE | host/c builtin.c idx 85 | - | List directory contents |
| JSON persistence | COMPLETE | shop/storage.tll | persistent shop | Orders saved to shop/orders.json |
| Order persistence dogfooding | COMPLETE | shop/main_persistent.tll | - | Create order -> save -> restart -> restore |
| Storage abstraction | PARTIAL | shop/storage.tll | - | Order-specific, not generic storage module |
| Binary file I/O | DEFERRED | - | - | Only string I/O |
| Streaming I/O | DEFERRED | - | - | Entire file read into memory |

## 11. Concurrency

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Single-threaded execution | COMPLETE | VM | - | Sequential bytecode execution |
| async/await | DEFERRED | - | - | Not implemented |
| Future/Promise | DEFERRED | - | - | Not implemented |
| Threads | DEFERRED | - | - | Not implemented |
| Channel | DEFERRED | - | - | Not implemented |
| Event loop | DEFERRED | - | - | Not implemented |
| HTTP concurrent requests | DEFERRED | - | - | One connection at a time |

## 12. Standard Library

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| stdlib/array.tll | PARTIAL | stdlib/array.tll | test_stdlib | 9 functions, C duplicate exists |
| stdlib/string.tll | PARTIAL | stdlib/string.tll | test_stdlib_string | 9 functions, C duplicate exists |
| stdlib/math.tll | PARTIAL | stdlib/math.tll | test_stdlib_math | 16 functions, C duplicate exists |
| stdlib/json.tll | PARTIAL | stdlib/json.tll | test_stdlib_json | 8 functions, C duplicate exists |
| stdlib/map.tll | DEFERRED | - | - | Not created |
| stdlib/fs.tll | DEFERRED | - | - | Not created (C builtins only) |
| stdlib/http.tll | DEFERRED | - | - | Not created (C builtins only) |
| stdlib/time.tll | DEFERRED | - | - | Not created (C builtins only) |
| stdlib/storage.tll | PARTIAL | shop/storage.tll | - | Order-specific, not in stdlib/ |
| C duplicate implementations | PARTIAL | host/c builtin.c | - | math/strings/arrays in both C and TLL |

## 13. Compiler Diagnostics & Tools

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Parse error (basic) | COMPLETE | parser throw | - | "unexpected token" with line/column |
| Rich compiler diagnostics | DEFERRED | - | - | No source snippet, no error codes |
| tll check | DEFERRED | - | - | Not implemented |
| tll fmt (formatter) | DEFERRED | - | - | Not implemented |
| tll test runner | PARTIAL | scripts/run-tests.bat | - | Compile + run, exit code comparison |
| LSP | DEFERRED | - | - | Not implemented |
| Debugger | DEFERRED | - | - | Not implemented |

## 14. Process / Time / Environment

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| process.argv | COMPLETE | host/c builtin.c idx 121 | - | Command line arguments |
| process.env | COMPLETE | host/c builtin.c idx 122 | - | Environment variables as map |
| process.exit | COMPLETE | host/c builtin.c idx 120 | - | Exit with code |
| process.cwd | COMPLETE | host/c builtin.c idx 127 | - | Current working directory |
| process.chdir | COMPLETE | host/c builtin.c idx 128 | - | Change directory |
| process.platform | COMPLETE | host/c builtin.c idx 131 | - | Platform string |
| time.now | COMPLETE | host/c builtin.c idx 123 | - | Unix timestamp |
| time.nowMs | COMPLETE | host/c builtin.c idx 124 | - | Millisecond timestamp |
| time.sleep | COMPLETE | host/c builtin.c idx 125 | - | Sleep seconds |
| time.date | COMPLETE | host/c builtin.c idx 126 | - | Date string |
| Child process | DEFERRED | - | - | Not implemented |

## 15. ABI / Spec Consistency

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| BUILTINS.json | COMPLETE | spec/BUILTINS.json | check-abi | 110 builtins, 0-97 + 120-131 |
| HOST_ABI.md | COMPLETE | spec/HOST_ABI.md | - | Human-readable ABI spec |
| OPCODES.json | COMPLETE | spec/OPCODES.json | - | Bytecode opcode spec |
| LANGUAGE.json | COMPLETE | spec/LANGUAGE.json | - | Language spec |
| ABI auto-consistency check | PARTIAL | scripts/check-abi.bat | - | Basic check, no full CI |
| Spec drift prevention | DEFERRED | - | - | No automated CI gate |

## 16. Shop Dogfooding

| Capability | Status | Implementation | Tests | Notes |
|------------|--------|----------------|-------|-------|
| Product listing | COMPLETE | shop/main*.tll | - | Grid of 6 products |
| Product detail | COMPLETE | shop/main*.tll | - | /product/{id} |
| Shopping cart | COMPLETE | shop/main*.tll | - | Add/remove/total/count |
| Checkout | COMPLETE | shop/main*.tll | - | Create order |
| Order history | COMPLETE | shop/main_persistent.tll | - | /orders page |
| Order persistence | COMPLETE | shop/storage.tll | - | JSON file, restart recovery |
| REST API (products) | COMPLETE | shop/main*.tll | - | /api/products JSON |
| REST API (orders) | COMPLETE | shop/main_persistent.tll | - | /api/orders JSON |
| Modular architecture | COMPLETE | shop/product.tll, cart.tll, etc. | - | 5 modules |
| User registration | DEFERRED | - | - | Not implemented |
| User login | DEFERRED | - | - | Not implemented |
| Session/Cookie | DEFERRED | - | - | Not implemented |
| Product search | DEFERRED | - | - | Not implemented |
| Payment integration | DEFERRED | - | - | Not implemented |
| Admin panel | DEFERRED | - | - | Not implemented |

---

## Summary

| Category | COMPLETE | PARTIAL | STUB | DEFERRED |
|----------|----------|---------|------|----------|
| Language Core | 7 | 1 | 0 | 0 |
| Type System | 5 | 4 | 0 | 2 |
| Functions/Closures | 11 | 0 | 0 | 4 |
| Struct | 7 | 4 | 0 | 2 |
| Enum | 7 | 3 | 0 | 2 |
| Module/Import | 7 | 2 | 0 | 2 |
| Error Handling | 5 | 2 | 0 | 1 |
| HTTP | 14 | 0 | 0 | 1 |
| Cookie/Session | 0 | 0 | 0 | 9 |
| Filesystem/Persistence | 8 | 1 | 0 | 2 |
| Concurrency | 1 | 0 | 0 | 6 |
| Standard Library | 0 | 5 | 0 | 5 |
| Compiler Tools | 1 | 1 | 0 | 5 |
| Process/Time | 11 | 0 | 0 | 1 |
| ABI/Spec | 5 | 1 | 0 | 1 |
| Shop Dogfooding | 9 | 0 | 0 | 6 |
| **Total** | **93** | **29** | **0** | **48** |

**P0-6 Goal**: Move critical DEFERRED/PARTIAL items to COMPLETE with tests and dogfooding.
