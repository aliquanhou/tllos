# P2-01-C Phase C — Architecture Design Construction Order

**Executor:** 豆包 / Agent A
**Architecture authority:** 于秋鸿
**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756`
**Starting branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Current audit gate:** `257ac4cf1b8ce7f8df3a01d03a5f9449421e9edb`

## Mission

Produce the complete architecture decision package for P2-01-C High-Frame Runtime. This phase is architecture-only. Do not modify Runtime source code, compiler semantics, opcode numbers, or tests except for documentation/measurement tooling required to establish architecture facts.

## Phase C1 — Architecture decision record

Create one canonical architecture document covering all decisions below. Every decision must state: current fact, decision, invariant, rejected alternatives, migration impact, and evidence required for implementation acceptance.

### C1.1 Frame model

Evaluate fixed 4096, function-sized, segmented/spill, compact-inline, and pooled variants. The selected design MUST use actual function register demand (`TLLFunction.maxRegister`) and preserve register/ownership semantics.

Measure actual `sizeof(TLLValue)`, `sizeof(TLLFrame)`, coroutine metadata, and allocation overhead before final memory arithmetic. Do not use the erroneous 524 MB or 2.6 MB preliminary figures from the Phase A report.

### C1.2 4GB memory contract

Define a hard runtime RSS budget below 4 GiB with explicit safety margin. Model:

`Program + ExecutionContexts + live Frames + Coroutines + Scheduler + IO wait state + Shared Heap + Globals + temporary storage + allocator/thread overhead`

Define mandatory test points at 100, 1K, 10K and 100K active logical coroutines, including a simultaneous-live-frame scenario. A historical stress test is not sufficient evidence of current peak RSS.

### C1.3 ExecutionContext ownership

Define exact ownership for every mutable field currently in `TLLVM`, `TLLFrame`, and `TLLCoroutine`. Separate immutable Program/Code from per-worker execution state and shared runtime state. No mutable field may remain accidentally shared.

### C1.4 Concurrency model

Define worker ownership, task execution, coroutine ownership, migration rules, critical sections, and synchronization domains. Removing `g_vm_lock` must not merely replace it with another hidden global serialization lock.

### C1.5 Heap ownership

Define the multi-worker ownership protocol. If atomic reference counting is selected, specify exact atomic type, increment/decrement memory order, destruction ordering, object publication, reclamation, and interaction with arrays/maps/strings/upvalues/closures. Preserve the accepted B11 ownership semantics exactly.

### C1.6 Global state

Classify globals into immutable, read-mostly, mutable shared, and thread-local where semantically valid. Define synchronization at the smallest practical domain. Define behavior for concurrent read/write and aliasing.

### C1.7 Scheduler / IO

Define runnable ownership, sleep/timer ownership, IO waiter ownership, wakeup ownership, duplicate-wakeup prevention, fairness/progress, worker handoff, coroutine migration, cancellation/shutdown/drain, and lost-wakeup prevention. Preserve P0-RUNTIME-08 timed wait semantics.

### C1.8 Opcode governance

Resolve GAP-C1 without silently changing frozen v1.1. Determine the authoritative version/boundary for existing opcodes 46-62. Do not add any opcode in Phase C.

### C1.9 Semantic VM convergence

Resolve GAP-C2 for existing 46-62. For each capability, explicitly choose convergence in `runtime/vm.tll` or a documented host-runtime-only boundary. Do not claim semantic equivalence without evidence.

### C1.10 Performance contract

Define reproducible benchmarks and regression gates. Record commit, platform, compiler/build mode, CPU/thread count, workload, warmup, iterations, wall time, throughput, peak memory and output/checksum. Historical 9,790 function calls/sec etc. are baseline evidence only.

### C1.11 Evidence contract

Define exact acceptance tests for:

- single-worker semantic regression;
- independent multi-worker execution;
- shared read-only Program;
- frame reuse/allocation;
- heap ownership race stress;
- mutable global synchronization;
- scheduler fairness/progress;
- IO wait/wake;
- coroutine migration;
- 100K simultaneous logical coroutines and memory ceiling;
- performance regression;
- Windows/Linux/macOS where executable environments exist;
- sanitizer evidence where supported.

## Phase C2 — Architecture self-review

Before implementation:

1. Verify every GAP-C1/C2 and G1-G10 has an explicit disposition.
2. Verify no design depends on an unmeasured object size.
3. Verify the 4GB model has a margin, not an exact 4GB target.
4. Verify `g_vm_lock` removal has no hidden replacement global lock.
5. Verify B11 ownership invariants are preserved.
6. Verify no new opcode is introduced.
7. Verify rejected alternatives and migration risks are documented.

## Phase C3 — Commit and report

Commit only the architecture artifacts and any strictly necessary measurement scripts/documentation. Do not change Runtime implementation.

Required report:

- commit SHA;
- changed files;
- architecture decisions;
- exact memory formula and measured sizes;
- GAP disposition matrix;
- implementation dependencies;
- unresolved risks;
- explicit statement: **IMPLEMENTATION NOT YET AUTHORIZED**.

Then stop and wait for independent audit by 于秋鸿.

## STOP CONDITIONS

Immediately stop and report if:

- actual source contradicts the Phase A inventory materially;
- a decision would require changing frozen v1.1 semantics without governance resolution;
- the 4GB ceiling cannot be demonstrated with a defensible model;
- concurrency correctness requires an unspecified ownership rule;
- an opcode addition appears necessary;
- the architecture requires broad unrelated refactoring.

## Forbidden

- No Runtime source implementation.
- No `g_vm_lock` deletion yet.
- No atomic refcount implementation yet.
- No frame allocator implementation yet.
- No scheduler rewrite yet.
- No global-state rewrite yet.
- No new opcode.
- No weakening/deletion of tests.
- No `|| true` or equivalent failure suppression.
- No PASS/SEALED/CLOSED declaration.

**施工令签发：于秋鸿**
