# P2-01-B12 Construction Order — Native Target Final Seal + Mainline Integration

**Repository:** `aliquanhou/tllos`  
**Baseline:** `740fc9b459e383291dc3101694bbdc3e7dc5bc59`  
**Previous milestone:** P2-01-B11-R1 = **PASS WITH B-GAP**  
**Execution branch:** `feature/P2-01-B12-native-target-final-seal`  
**Authority:** Architecture review by GPT-5.6 Luna; final SEALED/CLOSED authority remains 于秋鸿博士.

> **重要：本文件是施工令，不代表 B12 已完成。执行 Agent 必须从 `740fc9b` 之后的真实仓库状态开始 Reality Audit。**

## 0. Architectural judgment

P2-01-B11-R1 has passed the core Native ownership semantic review. The ownership implementation is **not to be redesigned** in this order.

Remaining B-GAPs:
1. complete Native regression was not run; only targeted tests were spot-checked;
2. Native ASan / mature memory diagnostics were not run;
3. Linux/macOS Native execution was not verified;
4. the `740fc9b` commit is Evidence-only, so final integration history must be checked before mainline merge.

**Goal:** move Native Target from **PASS WITH B-GAP** to a defensible **FINAL SEAL candidate**, then prepare clean mainline integration.

## 1. Sole goal

Close or honestly record the remaining Native Target validation gaps and prepare controlled mainline integration. No SEALED/CLOSED claim may be made until actual evidence exists and is independently audited.

## 2. Freeze and verify baseline

Before changing anything:
- confirm HEAD is `740fc9b459e383291dc3101694bbdc3e7dc5bc59` or a descendant containing it;
- work only on `feature/P2-01-B12-native-target-final-seal`;
- confirm the working tree is clean except intentional B12 work;
- do not modify `main` directly during implementation;
- do not rewrite historical commits;
- preserve B11 Evidence and historical records;
- inspect branch divergence before integration.

If unrelated work is found, report it before touching it.

## 3. Reality Audit — find the actual Native pipeline

Inspect the current repository, not old construction-order assumptions. Record the actual:
- Native compiler entry point (`native_compile_driver.tll` or current equivalent);
- generated-C build path;
- Native runtime source set;
- Native test runner/build scripts;
- Cross-Target Conformance runner;
- Bootstrap Stage-0 procedure;
- `batch1_basic` procedure;
- Bytecode regression procedure;
- existing sanitizer/debug configuration.

If an expected script changed, use the current equivalent and document the mapping. Do not invent commands or claim execution from source inspection.

## 4. Mandatory complete Native regression

Run the **complete currently supported Native regression suite**. Do not stop after Tests 11/12.

At minimum include:
- existing 11/11 Cross-Target Conformance;
- `tests/native/11_ownership_function_argument.tll`;
- `tests/native/12_ownership_argument_return.tll`;
- all existing Native ownership tests;
- current Native basic/regression corpus;
- `batch1_basic`;
- existing Bytecode regression;
- Bootstrap Stage-0 / compiler self-host verification.

Determine the actual current test count from the repository at execution time; do not hard-code an obsolete count.

Capture for relevant tests: source, target, compile result, exit code, stdout/stderr summary, warnings/errors.

**No test deletion, weakening, exclusion, or semantic rewrite is permitted to obtain PASS.**

## 5. Cross-target conformance

Use the same TLL source through:

```text
TLL Source
   ├── Bytecode → tllbc → tllvm
   └── Native   → generated C → native compiler → executable
```

Compare exit code and normalized stdout where practical. Do not substitute hand-written C for TLL semantic evidence. Any meaningful divergence must be classified A/B/C and investigated.

## 6. Native memory-safety verification

Use mature tooling already available, in this priority:
1. MSVC AddressSanitizer if viable;
2. existing ASan configuration/toolchain;
3. Debug CRT / existing mature runtime diagnostics;
4. deterministic ownership stress tests if sanitizer tooling is genuinely unavailable.

Probe for UAF, double-free, premature release, returned-value destruction, parameter leak, dangling container references, and repeated-call/alias ownership failure.

**Do not build a custom memory checker.** If ASan is unavailable, record the exact attempted configuration and limitation. Do not claim ASan PASS.

## 7. Cross-platform Native verification

Attempt Native compile/run on every platform actually supported by the current repository/toolchain infrastructure.

Minimum priority:
- **Windows/MSVC:** mandatory and locally executed on the current Windows host;
- **Linux:** execute if a supported environment exists;
- **macOS:** execute if a supported environment exists.

Source inspection is not platform execution evidence. If Linux/macOS cannot be executed in the available environment, record each as a B-GAP with the exact reason. CI is auxiliary evidence only and is **not** the acceptance authority.

## 8. Build hygiene

Do not commit generated build artifacts unless repository policy explicitly tracks them. Normally forbidden:
- `.exe` files;
- temporary/generated `.c` files;
- temporary `.tllbc` files;
- build directories;
- debug dumps;
- backups;
- temporary logs.

Commit only intentional source, tests, scripts, and Evidence/documentation.

## 9. Freeze accepted B11 ownership semantics

Do not broad-rewrite refcounting. Accepted semantics for this phase:
- Native parameters participate in ownership cleanup tracking;
- caller retains user-function arguments;
- callee releases call-lifetime parameter references;
- explicit return retains the return value before local/parameter cleanup;
- normal fall-through releases tracked locals/parameters;
- assignment preserves `incref(new) → free(old) → store(new)` ordering for alias safety.

Only modify this area if new reproducible evidence demonstrates an A-class defect. If found, isolate the smallest necessary fix and rerun affected regression.

## 10. Contract and Evidence consistency

Inspect the current ownership contract and B11 Evidence. Separate verified facts, current results, remaining GAPs, historical results, and final-seal status.

Do not rewrite history to make B11 appear stronger than it was. If B12 closes a GAP, update Evidence with exact command/result/commit information. If a GAP remains, record it explicitly.

## 11. Mainline integration preparation

Only after validation:
1. inspect `git log --graph --decorate`;
2. inspect branch divergence from current `main`;
3. inspect exact diff against intended integration base;
4. verify no unrelated changes;
5. verify no forbidden generated artifacts;
6. verify B11 Evidence remains traceable;
7. prepare a normal PR/integration path.

**Do not force-push or rewrite mainline history.** Prefer feature branch → PR → independent architecture audit → merge.

## 12. Final Seal criteria

B12 may be proposed as **FINAL SEAL** only with actual evidence for all applicable criteria.

### Functional
- Native compiler entry point works;
- generated C builds;
- Tests 11/12 pass;
- complete current Native regression passes;
- Bytecode regression passes;
- Bootstrap Stage-0 passes;
- `batch1_basic` passes;
- existing 11/11 Cross-Target Conformance remains green.

### Semantic
No known parameter leak, double-free, UAF, premature release, returned-value destruction, or Native/Bytecode ownership contradiction.

### Memory safety
Mature sanitizer/debug evidence passes, **or** exact toolchain limitation is honestly documented and deterministic memory-safety evidence is supplied. No ASan claim without actual execution.

### Platform
Windows/MSVC verified. Other supported platforms verified where executable environments are available; unavailable platforms remain explicit GAPs.

### Repository hygiene
No forbidden generated artifacts, no weakened tests, no unrelated feature work, clean integration diff.

## 13. A/B/C acceptance discipline

**A — Must Fix Now:** reproducible UAF, double-free, supported-path leak, semantic contradiction, compiler/runtime regression, broken test falsely reporting PASS.

**B — GAP, Record and Move:** unavailable platform execution, unavailable sanitizer tooling, non-critical warning with no semantic effect, auxiliary evidence unavailable in the current environment.

**C — Defer:** cosmetic cleanup, broader hardening outside this seal, future optimization.

Do not inflate B into A. Do not downgrade A into B merely to finish.

## 14. Scope boundary — strict

Do **not** start:
- High-Frame Runtime;
- TLL OS feature expansion;
- new language features;
- String API expansion;
- For/Break/Continue;
- Closure;
- Coroutine redesign;
- Network expansion;
- FFI expansion;
- LLVM expansion;
- GPU work;
- desktop robot implementation;
- new repository;
- broad refcount redesign;
- commercial dependency acquisition.

The newly established **4GB TLL OS Core memory ceiling is a future architecture constraint**, not a reason to expand B12. Do not alter working Native code solely to pursue an unmeasured memory target in this phase.

## 15. Required final report

The Agent A report must contain:
1. baseline SHA;
2. final commit SHA;
3. branch name;
4. exact files changed;
5. actual Native build entry point;
6. complete Native regression results;
7. Test 11 result;
8. Test 12 result;
9. existing 11/11 result;
10. Bootstrap Stage-0 result;
11. `batch1_basic` result;
12. Bytecode regression result;
13. memory-safety/ASan result with actual commands;
14. Windows result;
15. Linux result or explicit B-GAP;
16. macOS result or explicit B-GAP;
17. generated-artifact hygiene result;
18. remaining A/B/C GAPs;
19. branch/main divergence and integration plan;
20. explicit statement that Agent A has **no final SEALED/CLOSED authority**;
21. proposed Native Target Seal status.

Required ending:

> 施工完成，等待架构师审查与于秋鸿博士最终验收。

## 16. Operating principle

**Evidence first. Claims second.**

Do not write PASS because a command was expected to pass. Do not write cross-platform verified from source inspection. Do not write ASan verified without actual sanitizer execution. Do not rewrite/delete tests to obtain green output.

The repository's actual behavior is the authority.

> **No Evidence, No Claim.**

## 17. Final route

```text
P2-01-B11-R1
        ↓
PASS WITH B-GAP       ← current state
        ↓
P2-01-B12
Native Target Final Seal
        ↓
Architecture Audit
        ↓
FINAL SEAL
        ↓
Mainline Integration
        ↓
P2-01-C
High-Frame Runtime
```

**于秋鸿**
