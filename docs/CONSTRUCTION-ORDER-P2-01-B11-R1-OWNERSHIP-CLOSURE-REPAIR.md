# P2-01-B.11-R1 Construction Order — Native Ownership Closure Repair

**Repository:** `aliquanhou/tllos`  
**Baseline:** remote `main` at `ba6dc954e5a6feb07d0f9d0d6c1347458e3ae53d`  
**Prior milestone:** `P2-01-B11-PASS` (`f768d8f`) — **REVOKED AS AN ACCEPTANCE RESULT**; retained only as historical evidence  
**Authority:** Architecture review by GPT-5.6 Luna; final SEALED/CLOSED authority remains 于秋鸿博士.

---

## 0. Current architectural judgment

P2-01-B.11 is **REJECTED / REPAIR REQUIRED**.

The B.11 implementation established the Ownership framework and passed 11 cross-target tests, but the Native function-argument ownership path is not actually closed: `nl_localVars` tracks `let`/`const` locals but does not register function parameters. Therefore the generated Native function does not reliably release its parameter-owned reference at function exit, despite Contract v1.1 defining parameters as callee-owned for the duration of the call.

This is a semantic ownership defect, not a documentation-only issue.

Do **not** start B.12.

---

# 1. Sole goal

Close the Native function-argument ownership lifecycle and make the implementation, Contract, generated C, and Bytecode VM behavior agree.

Required invariant:

```text
caller owns reference
    ↓ retain/incref at call boundary
callee receives borrowed storage backed by caller retain
    ↓
callee owns/releases that call-lifetime reference
    ↓
callee exits
    ↓ release parameter reference exactly once
```

The implementation must preserve return-value ownership and must not introduce double-free, premature-free, leak, or dangling-reference behavior.

---

# 2. First task — prove the Bytecode authority again

Use the actual Bytecode VM implementation as semantic authority. Inspect and record evidence for:

1. argument push / `OP_PUSH`
2. `push_arg`
3. `do_call`
4. frame parameter initialization
5. `free_frame`
6. `OP_RET`
7. assignment (`OP_STORE_VAR` / equivalent)
8. `array_push`, `array_set`, `map_set`

Do not infer behavior from the existing Contract alone.

If the actual VM behavior differs from Contract v1.1, stop and report the discrepancy before changing semantics.

---

# 3. Fix Native parameter ownership tracking

Modify `compiler/native_lower.tll` so every generated function parameter participates in the same ownership cleanup model that the Contract specifies.

Requirements:

- Function parameters must be explicitly registered in the function-level ownership tracking state, or an equally clear mechanism must be used.
- Parameter cleanup must occur exactly once.
- Explicit return paths must retain the return value before releasing locals/parameters.
- Normal fall-through function exit must release parameters.
- Do not use a blanket textual cleanup that can double-release a parameter already transferred or returned.
- Preserve the safe ordering for alias cases such as `x = x`: retain the new reference before releasing the old reference.

Do not solve this by weakening ownership rules or removing cleanup.

---

# 4. Fix Contract v1.1 consistency

Update:

`docs/TLL-NATIVE-OWNERSHIP-REFCOUNT-CONTRACT-v1.1.md`

The document must match the actual implementation.

In particular, the Assignment section currently describes `free old → incref new → store`, while the implementation intentionally uses `incref new → free old → store` to make `x = x` safe. The Contract must describe the semantic requirement and safe ordering accurately.

Do not silently change the model. If a versioned Contract change is necessary, document the reason and preserve the historical v1.1 evidence rather than rewriting history.

---

# 5. Mandatory regression tests

Add at least these dedicated tests:

### `tests/native/11_ownership_function_argument.tll`

Must exercise:
- string argument
- array argument
- map argument
- multiple arguments
- repeated function calls with the same source value

### `tests/native/12_ownership_argument_return.tll`

Must exercise:
- argument passed to a function and returned
- argument transformed then returned
- returned argument stored by caller
- argument used in a container before return
- multiple calls / aliases where supported

Every test must run from the same TLL source through both targets:

```text
TLL Source
 ├── Bytecode → tllbc → tllvm
 └── Native   → generated C → MSVC → executable
```

Compare stdout and exit code automatically.

Do not write hand-crafted equivalent C as the primary evidence.

---

# 6. Memory-safety evidence

Where the existing environment permits, use mature tooling such as:

- AddressSanitizer / ASan
- MSVC AddressSanitizer
- Debug CRT diagnostics

Prioritize detecting:

- leak
- double free
- use-after-free
- premature release
- returned value destroyed by callee cleanup
- parameter not released
- container reference becoming dangling

Do **not** build a custom memory checker.

If the Windows toolchain cannot provide a useful sanitizer configuration, record the limitation honestly and use deterministic ownership instrumentation/tests instead.

---

# 7. Mandatory full regression

All of the following must remain green:

- existing 11/11 Cross-Target Conformance
- new ownership tests
- Bootstrap Stage-0
- `batch1_basic`
- existing Bytecode regression
- MSVC build with 0 errors and 0 warnings where the current baseline requires this

No test deletion, weakening, exclusion, or semantic rewrite is allowed merely to obtain green CI.

The known B9 limitation that Array/Map literals are only supported in Let/Const must remain a documented limitation; do not disguise it as an ownership fix.

---

# 8. Scope boundary — strictly prohibited

Do **not** enter:

- B.12 feature expansion
- String API expansion
- For / Break / Continue
- Closure
- Coroutine
- Network
- FFI
- LLVM
- Linux
- GPU
- High-Frame Runtime
- TLL OS
- new repository
- new OS capabilities

This repair is only about closing the Native Ownership function-argument lifecycle and its directly necessary evidence.

---

# 9. Required report

The Agent A report must include:

1. exact files changed
2. Bytecode ownership evidence with source locations
3. exact Native parameter ownership model
4. generated-C before/after explanation
5. why cleanup happens exactly once
6. `11_ownership_function_argument` result
7. `12_ownership_argument_return` result
8. existing 11/11 result
9. Bootstrap / VM regression result
10. sanitizer or memory-safety evidence
11. any remaining ownership GAPs
12. commit SHA
13. explicit statement that B.11-R1 is **not SEALED/CLOSED** by Agent A

Required ending:

> 施工完成，等待架构师审查与于秋鸿博士最终验收。

---

# 10. PASS criteria

B.11-R1 may be proposed as PASS only when:

- Bytecode parameter ownership is directly evidenced
- Native parameter ownership matches that behavior
- parameters are actually included in Native cleanup ownership tracking
- explicit return does not destroy the returned value
- normal function exit releases parameters
- no known double-free / premature-free / UAF / parameter-leak blocker remains in the tested ownership paths
- new ownership tests pass on both targets
- existing 11/11 remain PASS
- Bootstrap and VM regression remain PASS
- Contract and implementation are consistent
- no tests were weakened or removed

**B.11-R1 PASS is not Native Target SEALED.**

---

# 11. Git discipline

Do not modify `main` directly for the repair.

Create a feature branch from the current remote `main`, for example:

`feature/P2-01-B11-R1-ownership-closure`

Commit only formal source, tests, and documentation. Exclude:

- `.exe`
- `.tllbc`
- generated `.c`
- evidence scratch files
- debug programs
- temporary backups
- build directories

Do not create another PASS tag until architecture review confirms the repair.

---

# 12. Architecture route after repair

```text
P2-01-B11-R1
      ↓
Ownership Semantic Closure
      ↓
Architecture Review
      ↓
PASS
      ↓
P2-01-B12 Native Target Hardening
      ↓
Native Target Seal
      ↓
P2-01-C High-Frame Runtime
```

No work beyond B.11-R1 is authorized by this construction order.
