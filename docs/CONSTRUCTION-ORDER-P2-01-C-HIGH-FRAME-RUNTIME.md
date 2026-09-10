# P2-01-C High-Frame Runtime — Construction Order

**Status:** CONSTRUCTION ORDER — NOT SEALED
**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756` (main)
**Branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Authority:** 于秋鸿
**Executor:** 豆包 / assigned construction agent
**Scope:** Runtime execution-model upgrade only

> This document is the complete construction order for P2-01-C. It is intentionally placed on a feature branch and MUST NOT be merged into `main` as a construction order. Evidence produced by execution may enter `main` later through normal reviewed integration.

---

## 0. Command

P2-01-C is authorized to enter **implementation only after the executor completes the mandatory architecture preflight in this document**. The executor MUST NOT redesign the architecture by intuition and MUST NOT begin unrelated feature work.

The objective is to evolve the existing TLL Runtime from a correct-but-coarse execution model toward a **High-Frame Runtime** with:

```text
high execution throughput
+ real parallel execution
+ bounded memory
+ deterministic scheduler behavior
+ cross-target semantic consistency
+ reproducible evidence
```

The 4GB runtime-memory ceiling is a hard architectural constraint.

---

# 1. Non-Negotiable Governance

1. `main` baseline is exactly `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756` at construction start.
2. Work MUST remain on the feature branch until independently audited.
3. Do NOT modify `main` directly.
4. Do NOT declare PASS, SEALED, CLOSED, production-grade, or security-grade in executor evidence.
5. Do NOT rewrite or delete historical evidence merely because it is inconvenient.
6. Do NOT convert a B-GAP into PASS by omission.
7. No claim without reproducible evidence.
8. Every performance claim MUST include workload, platform, build mode, measurement method, raw result, and baseline comparison.
9. Every memory claim MUST include workload, peak RSS/working-set measurement method, platform, and result.
10. If a required environment is unavailable, record the exact limitation; do not simulate the result.
11. No force-push unless explicitly authorized by the architecture owner.
12. No generated binaries, temporary build outputs, local IDE state, or machine-specific paths may be committed.

---

# 2. Reality Baseline — Already Established

The following are known facts and MUST be treated as baseline, not rediscovered indefinitely:

- Frame Pool exists, but acquired frames still contain a coarse 4096-register allocation path.
- Historical benchmark: function-call throughput is approximately 9,790/sec while loop throughput is approximately 3,144,650/sec; this is diagnostic baseline, not a final performance target.
- `g_vm_lock` creates a global VM execution serialization point in existing worker-driven paths.
- `TLLVM` mixes program state with execution state such as call stack/current coroutine.
- Heap ownership uses ordinary reference-count fields and does not yet establish a complete multi-worker atomic ownership protocol.
- Globals are shared runtime state and do not yet have a complete fine-grained concurrency model.
- Coroutine, timer, and IO-aware scheduler primitives already exist and MUST be reused/extended rather than replaced without evidence.
- `spec/OPCODES.md` declares v1.1 opcodes 0–45 frozen, while the native runtime contains later runtime opcodes. This is GAP-C1 and MUST be resolved at the architecture/governance level before any new opcode is added.
- Semantic VM/runtime convergence is GAP-C2 and MUST be explicitly audited before claiming semantic equivalence.

---

# 3. Phase A — Mandatory Architecture Preflight

## A1. Repository Reality Audit

Before source modification, record the exact current implementation of:

- `TLLVM`
- `TLLFrame`
- `TLLCoroutine`
- frame pool
- call stack
- coroutine scheduler
- worker pool / `tll_vm_invoke`
- global state
- heap object/reference-count implementation
- IO wait state
- runtime shared value helpers
- benchmark harnesses
- current CI/runtime tests

Use actual source, not assumptions.

### A1 acceptance

Produce a machine-readable or tabular inventory containing:

```text
component | owner | mutable/shared? | thread-affinity | allocation path | synchronization | tests | evidence
```

Stop and report if reality differs materially from this construction order.

---

# 4. Phase B — GAP Ledger

Create/update an evidence-backed GAP ledger with at least these entries:

### GAP-C1 — Opcode Governance Drift

Known condition:

```text
Frozen v1.1 spec: 0–45
Native runtime: later runtime/concurrency opcodes exist
```

Required decision:

- classify existing later opcodes as implementation/runtime extension, or
- establish the correct version/spec boundary, or
- document another evidence-backed resolution.

**Forbidden:** silently changing the frozen v1.1 opcode contract.

Before adding any opcode, obtain an explicit architecture decision recorded in the feature evidence.

### GAP-C2 — Semantic VM Convergence

Audit whether `runtime/vm.tll` and native VM implement the same semantics for every runtime capability being touched.

Required output:

```text
capability | native implementation | semantic VM implementation | spec authority | status | evidence
```

If they disagree, do not silently normalize one side. Record the discrepancy and architecture decision.

### Additional mandatory GAPs

- G1 Frame allocation granularity
- G2 execution-context ownership
- G3 global VM lock serialization
- G4 heap atomic ownership
- G5 mutable global-state synchronization
- G6 scheduler fairness/progress
- G7 IO wakeup correctness under multiple workers
- G8 4GB memory ceiling
- G9 performance regression gate
- G10 cross-target consistency

---

# 5. Phase C — Memory Model First

**No performance implementation may start before the memory model is written.**

Define the memory budget for:

```text
TLLFrame
TLLCoroutine
ExecutionContext
Frame Pool
Coroutine table
Scheduler queues
IO wait structures
Shared heap objects
Globals
temporary call/argument storage
worker/thread metadata
allocator overhead
```

## C1. 4GB Hard Ceiling

The design MUST satisfy:

```text
worst_case_runtime_memory < 4 GiB
```

Use an explicit safety margin; do not design exactly to 4 GiB.

At minimum model:

```text
100 active coroutines
1,000 active coroutines
10,000 active coroutines
100,000 active coroutines
```

For each, calculate/measure:

- average frame footprint
- peak frame footprint
- coroutine metadata footprint
- execution-context footprint
- scheduler footprint
- heap footprint
- total estimated/observed RSS

Do not assume 4096 registers/frame is acceptable at 100K scale. Measure and model alternatives before selecting the representation.

## C2. Frame Model Decision

Evaluate, with evidence:

- fixed 4096-register frame
- dynamically sized register storage
- small-frame inline storage + spill/heap storage
- pooled frame storage
- segmented frame storage
- other bounded design

The chosen design MUST preserve semantics and ownership correctness.

Do not optimize by deleting required registers or weakening correctness.

---

# 6. Phase D — Execution Context Architecture

Separate read-mostly program state from per-execution mutable state.

Target conceptual model:

```text
                 Program / Code
                read-mostly/shared
                       |
        +--------------+--------------+
        |              |              |
 ExecutionContext  ExecutionContext  ExecutionContext
   Worker 0           Worker 1          Worker N
        |              |              |
   callStack       callStack        callStack
   current         current          current
   coroutine       coroutine        coroutine
   frame state     frame state      frame state
```

The executor MUST define exact ownership for every mutable field before moving it.

Required output:

```text
field | current owner | new owner | shared? | synchronization | lifetime
```

No field may become shared merely because moving it is convenient.

---

# 7. Phase E — Remove the Global Execution Bottleneck

The objective is NOT merely to delete `g_vm_lock`.

The executor MUST prove that concurrent workers can execute independent TLL work without corrupting:

- call stacks
- current coroutine
- frame state
- exception state
- return state
- scheduler state
- heap ownership
- global state

## E1. Required architecture

Define a worker-safe invocation model such as:

```text
Worker
  -> ExecutionContext
      -> call stack
      -> current coroutine
      -> frame ownership
      -> scheduler interaction
```

Shared program/code MUST remain immutable/read-mostly where possible.

## E2. Lock audit

For every existing VM/runtime lock:

```text
lock | protects | contention | owner | can be removed? | replacement
```

Do not replace one global lock with another hidden global lock.

---

# 8. Phase F — Heap Ownership / Atomic Reference Counting

Establish an explicit multi-worker ownership protocol.

Required semantics:

```text
retain/incref
release/decref
zero-ref destruction
alias safety
transfer/return safety
```

If reference counts become atomic, document:

- atomic type
- memory ordering
- destruction synchronization
- ABA/reuse considerations where relevant
- interaction with object fields
- interaction with closures/upvalues
- interaction with arrays/maps/strings/other refcounted values

Do NOT perform a broad refcount redesign unrelated to the runtime concurrency goal.

Existing B11 ownership semantics are frozen as a correctness baseline. P2-01-C MUST NOT regress them.

---

# 9. Phase G — Global State Concurrency

Classify every global:

```text
immutable
read-mostly
mutable
thread-local
```

For mutable shared state, define the smallest practical synchronization domain.

Do not introduce a single replacement global mutex unless the architecture proves it is not a throughput bottleneck and documents why.

Tests MUST include concurrent reads/writes where semantics permit them.

---

# 10. Phase H — Scheduler / Event Model

Reuse existing coroutine and IO-aware scheduler foundations.

Define:

- runnable queue ownership
- sleeping coroutine ownership
- IO waiter ownership
- wakeup ownership
- timer deadline handling
- cancellation behavior if supported by existing semantics
- fairness policy
- starvation prevention
- worker handoff policy
- duplicate wake prevention
- shutdown/drain behavior

Required invariant:

```text
one logical wakeup -> at most one runnable transition
```

No lost wakeups.

No duplicate execution of the same coroutine.

No busy-spin introduced to hide scheduler bugs.

---

# 11. Phase I — Opcode / Semantic Boundary

P2-01-C MUST NOT casually add new language opcodes.

If implementation can be completed using existing runtime mechanisms, prefer that.

If a new opcode is genuinely required:

1. stop implementation at that boundary;
2. document GAP-C1 impact;
3. identify the language-version/specification authority;
4. update the architecture/evidence plan;
5. only then implement.

The frozen v1.1 contract MUST NOT be silently rewritten.

For every touched opcode/capability, verify native VM and Semantic VM behavior or explicitly document why the capability is host-runtime-only.

---

# 12. Phase J — Performance Contract

The historical 9,790 frames/sec number is only a baseline.

Build a reproducible benchmark matrix:

| Workload | Baseline | Target | Regression Gate |
|---|---:|---:|---:|
| function call | measured at baseline | architecture-defined | defined before final test |
| coroutine spawn/resume | measured | defined | defined |
| scheduler yield | measured | defined | defined |
| timer wake | measured | defined | defined |
| IO wait/wake | measured | defined | defined |
| independent parallel calls | measured | defined | defined |
| shared-state workload | measured | defined | defined |
| memory at 100K coroutines | measured | <4GB | hard gate |

Targets MUST be based on measured baseline and realistic architecture, not invented marketing numbers.

Every benchmark records:

```text
commit
platform
compiler/build mode
CPU/thread count
workload size
warmup
iterations
wall time
throughput
peak memory
result checksum/output
```

---

# 13. Phase K — Test Matrix

At minimum retain all existing regression suites and add focused P2-01-C tests.

Required categories:

### K1 Frame

- nested calls
- deep calls
- variable frame sizes
- frame reuse
- frame pool exhaustion
- frame pool reuse correctness
- exception unwinding
- return cleanup

### K2 Parallel execution

- 2 workers
- 4 workers
- 8 workers
- repeated parallel execution
- independent programs/functions
- deterministic result comparison

### K3 Ownership

- concurrent retain/release
- aliasing
- return values
- arrays/maps/closures where applicable
- zero-ref destruction exactly once

### K4 Scheduler

- yield/resume
- sleep/wake
- many timers
- IO wait/wake
- mixed timer + IO
- no lost wakeups
- no duplicate wakeups

### K5 Memory

- 100
- 1K
- 10K
- 100K active coroutine scenarios where the environment can execute them

If 100K cannot execute in an available environment, do not fake it. Provide deterministic lower-scale evidence plus a documented limitation and analytical memory bound.

### K6 Regression

Run and preserve existing:

- Native regression corpus
- Bytecode regression
- Cross-target conformance
- Bootstrap/self-host evidence where practical
- existing coroutine tests
- existing IO/network tests
- ownership tests 11/12
- existing CI gates

No test may be deleted or weakened merely to make P2-01-C green.

---

# 14. Phase L — Sanitizer / Memory-Safety Evidence

Use mature platform tooling where available:

- MSVC AddressSanitizer / Debug CRT as applicable
- Clang/GCC AddressSanitizer on supported Unix environments
- ThreadSanitizer where supported and practical
- UndefinedBehaviorSanitizer where supported

If unavailable because of environment/toolchain limitations, record the exact error and fallback evidence.

Do not build a custom fake sanitizer or custom “memory checker” merely to claim safety.

---

# 15. Phase M — Cross-Target Contract

The runtime architecture MUST preserve the existing TLL semantic contract.

At minimum validate on available platforms:

```text
Windows
Linux
macOS
```

The absence of a local platform is a B-GAP unless CI or another reproducible evidence source closes it.

Compare:

```text
stdout
exit code
error behavior
ownership-visible behavior
scheduler-visible deterministic results
```

Do not claim cross-platform PASS from compilation alone.

---

# 16. Phase N — Evidence Contract

Create:

```text
`docs/evidence/P2-01-C-HIGH-FRAME-RUNTIME.md`
```

Evidence MUST contain:

1. exact baseline commit
2. exact implementation commits
3. reality audit
4. GAP ledger
5. architecture decisions
6. memory calculations
7. benchmark methodology/results
8. test matrix/results
9. sanitizer results
10. cross-target results
11. artifact hygiene
12. known limitations
13. B-GAPs
14. explicit statement that executor has no SEALED authority

Required truth rule:

```text
No Evidence -> No Claim
```

---

# 17. Phase O — Commit Discipline

Preferred commit sequence:

```text
O1 architecture/evidence preflight
O2 memory/execution-context foundation
O3 concurrency/ownership implementation
O4 scheduler/global-state hardening
O5 benchmark/test/evidence closure
```

Do not create meaningless micro-commits solely to inflate history.

Each commit must be independently understandable and auditable.

Before each source commit:

```text
git diff --check
git status
targeted tests
```

Before final report:

```text
git status --short
git diff --check
full required tests
artifact hygiene
exact HEAD SHA
```

---

# 18. Forbidden Scope

The following are explicitly OUT OF SCOPE unless a new architecture order is issued:

- new user-facing language features
- String API expansion
- For/Break/Continue language expansion
- Closure redesign
- unrelated Coroutine semantic redesign
- unrelated Network API expansion
- FFI redesign
- LLVM backend
- GPU
- desktop/robot integrations
- blockchain feature expansion
- package-manager redesign
- broad refcount rewrite unrelated to P2-01-C concurrency
- website / agent portal
- TLL OS product UI
- unrelated repository creation

Do not use P2-01-C as a pretext to reopen sealed B11/B12 work.

---

# 19. Stop Conditions

Immediately STOP and report to the architecture owner if any of the following occurs:

1. Frozen v1.1 semantics must change.
2. A new opcode appears necessary without a governance decision.
3. Semantic VM and Native VM have a material disagreement that cannot be classified as host-runtime-only.
4. The 4GB ceiling cannot be satisfied by the current architecture.
5. Removing `g_vm_lock` reveals undocumented shared mutable state.
6. Atomic ownership semantics would change B11 behavior.
7. Existing regression tests must be weakened/deleted.
8. A platform result is unavailable but the executor is tempted to claim it.
9. A benchmark result cannot be reproduced.
10. The proposed fix requires a broad redesign outside this scope.
11. The executor discovers that the baseline differs materially from `5b0bc5c`.

A stop is not failure. A documented architecture blocker is preferable to an unsupported implementation.

---

# 20. Final Acceptance Gate

The executor MUST NOT declare P2-01-C sealed.

The executor may report **IMPLEMENTATION COMPLETE — AWAITING INDEPENDENT AUDIT** only when all applicable evidence exists.

Architecture acceptance requires independent verification of:

```text
[ ] baseline integrity
[ ] GAP-C1 disposition
[ ] GAP-C2 disposition
[ ] Frame architecture
[ ] ExecutionContext separation
[ ] global-lock bottleneck resolution
[ ] heap ownership concurrency safety
[ ] global-state synchronization
[ ] scheduler correctness
[ ] 4GB memory contract
[ ] benchmark contract
[ ] regression tests
[ ] sanitizer evidence
[ ] cross-target evidence
[ ] artifact hygiene
[ ] no forbidden scope leakage
```

Only the architecture owner / independent auditor may subsequently decide:

```text
PASS
PASS WITH B-GAP
REQUEST CHANGES
FINAL SEALED
```

---

# 21. Executor Final Report Format

The final report MUST use this structure:

```text
# P2-01-C High-Frame Runtime Construction Report

## 1. Baseline
## 2. Reality Audit
## 3. GAP Ledger
## 4. Architecture Decisions
## 5. Memory Model / 4GB Evidence
## 6. ExecutionContext / Concurrency Implementation
## 7. Scheduler / IO Evidence
## 8. Ownership / Global State Evidence
## 9. Performance Benchmarks
## 10. Regression Matrix
## 11. Sanitizer Evidence
## 12. Cross-Target Evidence
## 13. Artifact Hygiene
## 14. Known B-GAPs
## 15. Exact Git Commits / HEAD
## 16. Executor Conclusion

Implementation complete; waiting for independent architecture audit.

施工完成，等待架构师审查与于秋鸿最终验收。
```

No “SEALED” wording is permitted in the executor conclusion.

---

# 22. Command Authority

This construction order is issued by:

**于秋鸿**

Architecture / Acceptance Authority

Date: 2026-09-09

**Instruction:** Begin with Phase A Reality Audit and Phase B GAP Ledger. Do not jump directly to source implementation. Once the architecture preflight is recorded, implementation may proceed within this order.
