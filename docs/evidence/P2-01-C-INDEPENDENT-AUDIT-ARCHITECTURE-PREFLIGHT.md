# P2-01-C Independent Audit — Architecture Preflight

**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756`
**Audited commit:** `5a369393433e1c2635281ab537aba1475324d2fc`
**Branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Auditor:** 于秋鸿
**Status:** PASS WITH CORRECTIONS — ARCHITECTURE PHASE AUTHORIZED; IMPLEMENTATION NOT YET AUTHORIZED

## 1. Independent verification

The Phase A/B commit was inspected against the baseline source, including:

- `host/c/tllvm.h`
- `host/c/vm.c`
- `host/c/builtin.c`
- `spec/OPCODES.md`
- Phase A/B evidence documents

The central findings are supported by the repository:

1. `TLLVM` mixes program state with mutable execution state.
2. `TLLFrame` currently allocates 4096 `TLLValue` registers for a fresh frame.
3. `g_frame_pool` is process-global and has no synchronization.
4. `g_vm_lock` surrounds TLL handler invocation and is a global serialization point.
5. Heap reference counts are plain integers.
6. Opcode specification v1.1 is frozen at 0-45 while C runtime defines 0-62.
7. `runtime/vm.tll` does not converge with the C runtime extension set identified in the Phase A/B report.

## 2. Corrections required to the Phase A/B interpretation

### C1 — 4GB arithmetic table contains an internal inconsistency

The report contains one row stating approximately 524 MB for 100K frames while elsewhere calculating 4096 × 16 bytes × 100K = 6.4 GB. The latter calculation is correct under the report's stated 16-byte `TLLValue` assumption.

The architecture record MUST NOT use the 524 MB figure.

### C2 — Frame-pool memory estimate is incorrect

The report's frame-pool estimate of approximately 2.6 MB is inconsistent with 512 frames retaining 4096 × 16-byte registers. Registers alone would be approximately 32 MiB for 512 fully allocated frames under that assumption, before other arrays/allocator overhead.

The architecture record MUST recompute this from measured `sizeof(TLLValue)` and actual allocations instead of copying the preliminary estimate.

### C3 — 100K stress result versus 100K simultaneous live-frame memory

The existence of a 100K coroutine stress test does not by itself prove that 100K full register frames remain simultaneously live. Therefore the 4GB conclusion is an architectural worst-case constraint, not a claim about measured current RSS.

The implementation phase MUST add an explicit simultaneous-live-context memory test and record peak RSS/allocator accounting.

## 3. Architecture authorization

The Phase A/B work is sufficient to enter architecture design. It is NOT sufficient to begin source implementation.

Before Phase C implementation, the executor MUST produce and commit an architecture artifact that resolves, with explicit invariants and measurable budgets:

- Frame model and exact register-storage sizing strategy.
- ExecutionContext ownership for every mutable field.
- 4GB hard memory budget and safety margin, based on measured object sizes.
- Multi-worker concurrency model and removal strategy for `g_vm_lock`.
- Heap ownership/refcount atomicity and memory-ordering rules.
- Global-state classification and synchronization domains.
- Scheduler runnable/sleeping/IO ownership, wakeup uniqueness, migration and shutdown rules.
- Opcode governance boundary for 46-62.
- Semantic VM policy for 46-62: converge or explicitly classify host-runtime-only.
- Performance contract methodology and regression gate.
- Evidence/test matrix and cross-target acceptance criteria.

No new opcode may be added during this phase.

## 4. Independent verdict

**PASS WITH CORRECTIONS.**

The executor's Reality Audit and GAP Ledger are accepted as an adequate basis for architecture work, subject to the numerical corrections above. The executor is authorized to perform **architecture design only**.

**Implementation remains BLOCKED until the architecture artifact is independently audited.**

No PASS/SEALED/CLOSED claim is authorized for P2-01-C.
