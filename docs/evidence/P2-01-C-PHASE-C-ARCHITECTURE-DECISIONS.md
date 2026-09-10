# P2-01-C Phase C — Architecture Decisions

**Status:** EXECUTOR COMPLETED — AWAITING INDEPENDENT AUDIT
**Executor:** 豆包 / Agent A
**Architecture authority:** 于秋鸿
**Implementation:** BLOCKED (pending independent audit)
**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756`
**Branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Full design document:** `docs/CONSTRUCTION-ORDER-P2-01-C-PHASE-C-ARCHITECTURE-DESIGN.md`

> This file contains the executor's completed architecture decision package.
> Every numerical claim is either measured or explicitly labeled as architecture assumption to be validated.
> This is NOT an acceptance result. Independent audit by 于秋鸿 is required before implementation.

---

## 1. Frame Model Decision

**Decision: Dynamic Frame Sized by `TLLFunction.maxRegister`**

| Aspect | Decision |
|--------|----------|
| Frame register allocation | `calloc(maxRegister + 1, sizeof(TLLValue))` instead of fixed 4096 |
| `TLLFunction.maxRegister` | Already computed by compiler; used directly for sizing |
| argStack | Initial capacity 64, grows dynamically (unchanged) |
| tryStack | Initial capacity 16, grows dynamically (unchanged) |
| locals | Dynamic allocation based on function localCount (unchanged) |
| Frame Pool | Retain pooled frames; if pooled frame's registerCount < required maxRegister, reallocate registers |
| INVOKE_RET_REG | Change from fixed 4095 to `fn->maxRegister` (compiler guarantees maxRegister includes return reg) |

**Rejected alternatives:**
- Fixed 4096: rejected — 10-50x memory waste for typical functions
- Small frame + spill/heap: rejected — too complex, hard to debug, ownership risk
- Segmented frame: rejected — complexity not justified by memory savings
- Size-class pool: optional future optimization, not initial implementation

**Invariant:** Register indexing semantics unchanged. Only allocation size changes.

**Evidence required for implementation acceptance:**
- Full test suite passes (Native 20/20, Bytecode 20/20, Cross-target 11/11)
- Debug assertion: register index < registerCount
- Frame allocation count / size measurement at 100/1K/10K/100K coroutines
- No regression in function-call throughput

---

## 2. Measured Runtime Object Sizes

**Measurement method:** MSVC 2022 (cl.exe), x64, `sizeof()` compile-time operator, actual compilation and execution.

| Object | Measured Size | Notes |
|--------|--------------|-------|
| `TLLValue` | **24 bytes** | type tag (4) + padding (4) + union (16: func struct = int fnIdx + padding + pointer env) |
| `TLLFrame` | **120 bytes** | struct only, excludes dynamically allocated registers/locals/argStack/tryStack |
| `TLLCoroutine` | **96 bytes** | struct only, excludes callStack dynamic array |
| `TLLVM` | **64 bytes** | full struct (pointers + ints) |
| `TLLArray` | **24 bytes** | items pointer + length + capacity + refCount |
| `TLLMap` | **24 bytes** | buckets pointer + bucketCount + size + refCount |
| `TLLClosureEnv` | **24 bytes** | upvalues pointer + count + capacity + refCount |
| `TLLUpvalue` | **32 bytes** | value (24) + refCount (4) + padding (4) |
| `TLLFunction` | **40 bytes** | name pointer + paramCount + instructions pointer + instructionCount + localCount + maxRegister |

**Derived measurements:**

| Calculation | Result |
|-------------|--------|
| Frame with 4096 registers (registers only) | 4096 × 24 = **98,304 bytes = 96 KB** |
| Full frame (struct + 4096 regs + argStack 64 + tryStack 16) | 120 + 98304 + 1536 + 64 = **100,024 bytes ≈ 97.7 KB** |
| 100K frames × 4096 registers | 100,000 × 96 KB = **9,375 MB = 9.15 GB** |
| 100K frames × 64 registers (typical small function) | 100,000 × 64 × 24 = **146.5 MB** |
| 100K frames × 256 registers (medium function) | 100,000 × 256 × 24 = **585.9 MB** |
| 100K coroutine metadata (struct only) | 100,000 × 96 = **9.16 MB** |
| 100K frame structs (no registers) | 100,000 × 120 = **11.44 MB** |

**Important correction:** Prior Phase A report used estimated 16 bytes for TLLValue, producing 524 MB / 100K frames. Actual measured size is 24 bytes, producing 9.15 GB / 100K frames. The prior figures were erroneous and are corrected here.

---

## 3. 4GB Memory Budget and Formula

**Critical governance correction (per 于秋鸿 latest instruction):**
4GB is **NOT** a hard constraint, correctness gate, or architecture veto condition. It is a **reference budget / optimization target / engineering observation metric**.

> "项目首先要搞好、搞顺；在正确性、稳定性和性能允许的情况下，尽量减少 Runtime Memory Footprint."
> "禁止为了'塞进 4GB'而选择明显更复杂、更脆弱、更难维护的 Runtime 架构."

**Memory formula (architecture model):**

```
Total Runtime Memory =
    Program (read-only, shared)
  + N_workers × ExecutionContext (per-worker: callStack ptr, currentCoroutine, invokeTarget, etc.)
  + N_live_frames × (sizeof(TLLFrame) + frame_register_count × sizeof(TLLValue) + argStack + tryStack + locals)
  + N_coroutines × (sizeof(TLLCoroutine) + callStack_capacity × sizeof(TLLFrame*))
  + Scheduler queues (per-worker local + global runnable queue)
  + IO wait structures (fd sets, reactor state)
  + Shared Heap (arrays, maps, strings, closures, upvalues — refcounted)
  + Globals (globalCount × sizeof(TLLValue))
  + Temporary call/argument storage
  + Allocator metadata / fragmentation overhead (estimate 10-20%)
  + Thread/worker metadata
```

**Memory scenarios (using MEASURED 24-byte TLLValue):**

| Scenario | Frames | Registers/frame | Frame Memory | Coroutine Metadata | Heap (est.) | Total (est.) | vs 4GB |
|----------|--------|-----------------|--------------|-------------------|-------------|--------------|--------|
| 100 coroutines, shallow | 100 | 64 (avg) | 1.5 MB | 0.01 MB | ~5 MB | ~7 MB | ✅ Well under |
| 1K coroutines, medium | 1,000 | 128 (avg) | 29.3 MB | 0.09 MB | ~20 MB | ~50 MB | ✅ Well under |
| 10K coroutines, medium | 10,000 | 128 (avg) | 293 MB | 0.9 MB | ~100 MB | ~400 MB | ✅ Under |
| 100K coroutines, shallow (suspended) | 100K | 16 (avg, suspended shallow) | 36.6 MB | 9.2 MB | ~200 MB | ~250 MB | ✅ Under (dynamic frame helps) |
| 100K coroutines, 10 frames each, medium | 1M | 128 (avg) | 2.93 GB | 9.2 MB | ~500 MB | ~3.5 GB | ⚠️ Near 4GB reference |
| 100K coroutines, 10 frames each, 4096 fixed | 1M | 4096 (fixed) | 93.75 GB | 9.2 MB | ~500 MB | ~94 GB | ❌ Way over (fixed frame is the problem) |

**Key insight:** Dynamic frame sizing (C1) is the primary memory optimization. With fixed 4096 registers, 100K coroutines × 10 frames = 94 GB — clearly infeasible. With dynamic sizing (avg 128 registers), same scenario = ~3.5 GB — within reasonable range.

**Safety margin:** If 4GB reference budget is to be respected, design should target <3.5 GB worst-case (12-15% margin). But this is an optimization target, not a correctness gate.

**Test points (mandatory for implementation phase):**
- 100 active logical coroutines: measure RSS
- 1,000 active logical coroutines: measure RSS
- 10,000 active logical coroutines: measure RSS
- 100,000 active logical coroutines: measure RSS (if environment permits; if not, document limitation + analytical bound)
- Simultaneous-live-frame scenario: 10K coroutines × 10 frames = 100K live frames

---

## 4. ExecutionContext Ownership Matrix

**Decision: Split TLLVM into shared read-only Program + per-worker TLLEXecutionContext + shared mutable runtime state.**

| Field | Current Owner | New Owner | Shared? | Read By | Write By | Thread Safe? | Synchronization | Lifetime | Migration Allowed? |
|-------|--------------|-----------|---------|---------|---------|-------------|-----------------|----------|---------------------|
| `program` | TLLVM | Global shared (read-only) | Yes (read) | All workers | None after load | ✅ Immutable | None | Process | No |
| `callStack` | TLLVM | ExecutionContext (per-worker) | No | Owner worker | Owner worker | ✅ Thread-local | None | Worker | No |
| `callStackSize/Capacity` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Worker | No |
| `globals` | TLLVM | Shared Global State | Yes | All workers | All workers | ❌ Needs sync | Per-element sync (C7) | Process | No |
| `globalCount` | TLLVM | Shared Global State | Yes | All workers | None after load | ✅ Immutable | None | Process | No |
| `invokeTargetStackSize` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Invocation | No |
| `coroutines` | TLLVM | Scheduler (shared) | Yes | Scheduler | Scheduler | TBD | Scheduler model (C8) | Process | TBD |
| `coroutineCount/Capacity` | TLLVM | Scheduler | Yes | Scheduler | Scheduler | TBD | Scheduler model | Process | TBD |
| `currentCoroutine` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Worker | No |

**TLLCoroutine field ownership:**

| Field | Owner | Shared? | Synchronization |
|-------|-------|---------|-----------------|
| `callStack` / size / capacity | Coroutine (moves with it) | No | Coroutine lifecycle |
| `state` | Coroutine | TBD (scheduler accesses) | Atomic CAS (C8) |
| `result` | Coroutine | No | None |
| `invokeTargetStackSize` | Coroutine | No | None |
| `wakeTime` | Coroutine | TBD (scheduler reads) | Scheduler model |
| `waitingFd/Events/Channel` | Coroutine | TBD (IO reactor reads) | Scheduler/IO model |
| `waitDeadline` | Coroutine | TBD | Scheduler model |
| `waitResult` | Coroutine | No (written by scheduler, read by coroutine) | Scheduler model |

**Invariant:** Every mutable field has exactly one owner. No field is shared "by convenience."

---

## 5. Multi-Worker Concurrency Model

**Decision: Shared Program + Per-Worker ExecutionContext (Model C)**

| Aspect | Decision |
|--------|----------|
| Program/Code | Shared read-only across all workers |
| ExecutionContext | Per-worker (callStack, currentCoroutine, frame state, invokeTarget) |
| Worker count | Configurable (default 8, matching current) |
| Task queue | Global queue (existing g_queue_lock can remain, or lock-free MPMC) |
| Coroutine migration | Allowed via work-stealing (C8) |
| Frame migration | Allowed (frames move with coroutine's callStack) |
| Native calls | Per-worker (can execute in parallel, no global VM lock) |
| Blocking syscalls | Block only calling worker, not all workers |
| g_vm_lock | **Eliminated** — replaced by per-worker ExecutionContext + fine-grained shared state sync |

**Rejected alternatives:**
- Model A (Global VM Lock): rejected — no true parallelism, current bottleneck
- Model B (One VM per Worker): rejected — breaks shared globals semantics, memory overhead (N full VMs), inconsistent global state
- Model D (Actor/ownership-based): rejected — changes concurrency model too fundamentally, message passing overhead, backward compatibility risk

**Invariant:** Removing g_vm_lock does NOT replace it with another hidden global serialization lock. All shared mutable state has explicit, fine-grained synchronization.

---

## 6. Heap Ownership / Atomicity Model

**Recommended Baseline: Atomic RefCount (candidate memory ordering: relaxed incref, acq_rel decref — PENDING ThreadSanitizer + microbenchmark validation).**

| Aspect | Decision |
|--------|----------|
| Atomic type | C11 `atomic_int` or MSVC `_InterlockedIncrement/Decrement` / GCC `__atomic_add_fetch/sub_fetch` |
| Increment (retain) | `memory_order_relaxed` — if we hold a reference, object can't be freed concurrently |
| Decrement (release) | `memory_order_acq_rel` — ensures all prior writes visible before destruction; zero-check uses acquire |
| Zero transition | Thread performing final decrement (sees zero) destroys object |
| Object publication | `memory_order_release` on pointer store; `memory_order_acquire` on pointer load |
| Reclamation | Direct free() on zero (no object pooling, no ABA problem) |
| ABA/reuse | Not applicable — objects are freed, not recycled |

**B11 ownership compatibility (verified):**

| B11 Semantic | Atomic RefCount Impact | Compatible? |
|-------------|------------------------|------------|
| Parameter ownership (caller incref, callee owns, callee releases) | Same semantics, atomic operations | ✅ |
| Return ownership (incref return → cleanup params → caller owns) | Same order, atomic | ✅ |
| Assignment (tll_assign: incref new → free old → store) | Same order, atomic | ✅ |
| Aliasing (multiple references) | Atomic correctly tracks all references | ✅ |
| Array/map element ownership | Atomic on element refCounts | ✅ |
| Closure/env/upvalue ownership | Atomic on closure/env/upvalue refCounts | ✅ |

**Invariant:** Atomic refCount is a drop-in replacement for plain int. Does not change ownership semantics. B11 contract fully preserved.

---

## 7. Global State Synchronization Model

**Decision: Hybrid — immutable for read-only + per-element synchronization for mutable.**

| Global Type | Examples | Synchronization |
|-------------|----------|-----------------|
| Immutable | Function references, constants, `globalCount` | None (read-only after load) |
| Read-mostly | Configuration values, cached lookups | Atomic loads / RCU (future) |
| Mutable shared | Program variables stored as globals | Per-element synchronization |
| Per-worker | Worker-specific caches | Thread-local (if semantically valid) |

**Initial implementation: 16-mutex stripe array**
- `globals[idx]` protected by `mutex[idx % 16]`
- Reduces contention vs single global lock
- Simple, portable, easy to debug
- Can later optimize to per-element atomic if profiling shows mutex contention

**Read (OP_LOAD_GLOBAL):**
- Lock stripe mutex → read `globals[idx]` → incref (atomic) → unlock → return

**Write (OP_STORE_GLOBAL):**
- Lock stripe mutex → incref(new) → store new → decref(old) → unlock

**Invariant:** Follows tll_assign ownership pattern (incref new → store → decref old), applied per element with stripe mutex.

---

## 8. Scheduler / IO / Wakeup Model

**Decision: Per-worker local runnable queue + global queue (D-1/D-2 required) + work stealing (D-3 optimization, PENDING) + shared IO reactor.**

| Aspect | Decision |
|--------|----------|
| Runnable queue ownership | Per-worker local queue (LIFO/deque) + global queue |
| Worker local queue | Yes — lock-free, only owner accesses |
| Global queue | Yes — for coroutines spawned from non-worker context; low-contention MPMC or mutex |
| Work stealing | Phase D-3 optimization (PENDING) — when local+global empty, steal from random other worker's queue tail |
| Coroutine migration | Allowed — coroutines move between workers via work stealing |
| Wakeup ownership | IO reactor / timer / channel wake → push to global queue or target worker's local queue |
| Duplicate wakeup prevention | Atomic coroutine state CAS (WAITING → RUNNABLE); if CAS fails, skip |
| Fairness/progress | Round-robin within worker; work-stealing provides global fairness |
| Starvation prevention | Work stealing + global queue ensures no coroutine permanently starved |
| Worker handoff | Via global queue or work stealing |
| IO reactor | Shared IO reactor thread (select/epoll/IOCP) — detects fd ready/deadline expiry → sets waitResult → CAS state to RUNNABLE → pushes to queue |
| Timer | Min-heap keyed by wakeTime; workers check expired timers when out of runnable work |

**P0-RUNTIME-08 compatibility:**
- `waitReadWithTimeout(fd, timeout)` → IO reactor handles deadline; `waitResult=1` ready, `waitResult=0` timeout
- `waitWriteWithTimeout(fd, timeout)` → same for write events
- `waitDeadline` / `waitResult` fields preserved in TLLCoroutine struct
- Non-blocking connect + waitWrite + SO_ERROR pattern unchanged

**Invariant: `one logical wakeup → at most one runnable transition`** (enforced by atomic CAS).

---

## 9. Coroutine Migration and Shutdown Model

| Aspect | Decision |
|--------|----------|
| Coroutine migration | Allowed via work stealing; coroutine's entire state (callStack, registers, fields) moves with it |
| No worker-specific state in coroutine | Design invariant — coroutine never stores worker ID or worker-local pointer |
| Frame migration | Frames are on coroutine's callStack; migrate automatically |
| Shutdown signal | Atomic flag `shutdown_requested` |
| Shutdown behavior | Workers finish current coroutine → check flag → drain local queue (execute remaining) → exit |
| IO reactor shutdown | Stop accepting new IO → wake all waiting coroutines with shutdown status → exit |
| Timer shutdown | Cancel all pending timers → wake with cancellation status |
| Cancellation | NOT implemented in P2-01-C (no OP_CANCEL, no cancellation API) — out of scope |
| Worker crash | Not handled (process-level crash); TLL exceptions handled by try/catch; native calls audited separately |
| Drain on shutdown | All workers drain local queues before exit; no coroutine left unexecuted |

**Invariant:** Shutdown is "drain and exit," not forcible cancellation. All runnable coroutines complete before workers exit.

---

## 10. GAP-C1 Opcode Governance Decision

**Decision: v1.1 FROZEN (0-45) + v1.2 PROPOSED EXTENSION (46-62, PENDING FORMAL GOVERNANCE).**

| Range | Version | Status | Opcodes |
|-------|---------|--------|---------|
| 0-45 | v1.1 | FROZEN | Core language (arithmetic, control flow, functions, arrays, maps, closures, basic exception THROW/TRY) |
| 46-53 | v1.2 | PROPOSED | Bitwise (BAND, BOR, BXOR, BNOT, SHL, SHR, ROTR, ROTL) — P0-15 |
| 54-56 | v1.2 | PROPOSED | Coroutine (SPAWN, YIELD, SLEEP) — P0-15.14/15 |
| 57-59 | v1.2 | PROPOSED | IO-aware (WAIT_READ, WAIT_WRITE, WAIT_CHANNEL) — P0-15.16 |
| 60 | v1.2 | PROPOSED | MOV — P0-COMPILER-02 |
| 61-62 | v1.2 | PROPOSED | Structured exception (CATCH_ENTER, FINALLY_END) |

**Rationale:**
- 46-62 are already implemented, tested, and used by existing programs/tests
- Clean version boundary: v1.1 = frozen core, v1.2 = runtime extension
- Semantic VM (vm.tll) can implement v1.2 (resolves GAP-C2)
- Honest about history: 46-62 were added during P0-15/P0-COMPILER phases without formal version bump; now formally ratified as v1.2 during P2-01-C

**Forbidden:** Silently changing frozen v1.1 semantics. Any change to v1.1 opcode semantics requires new version.

**Future opcodes:** Must go through formal architecture decision + version bump (v1.3+). No new opcodes in P2-01-C.

---

## 11. GAP-C2 Semantic VM Convergence Decision

**Decision: Update `runtime/vm.tll` to implement v1.2 opcodes (future implementation phase).**

| Capability | Native VM (vm.c) | Semantic VM (vm.tll) | Target |
|------------|-------------------|----------------------|--------|
| Opcodes 0-45 | ✅ Implemented | ✅ Implemented | Converged |
| Bitwise 46-53 | ✅ Implemented | ❌ Not present | Add to vm.tll |
| Coroutine 54-56 | ✅ Implemented | ❌ Not present | Add to vm.tll (simplified cooperative scheduler) |
| IO-aware 57-59 | ✅ Implemented | ❌ Not present | Add to vm.tll (may need host IO assistance or simulated event loop) |
| MOV 60 | ✅ Implemented | ❌ Not present | Add to vm.tll (straightforward) |
| Exception 61-62 | ✅ Implemented | ❌ Not present | Add to vm.tll |

**Canonical semantic authority:** `runtime/vm.tll` remains the executable language specification per ARCHITECTURE.md. It must be updated to match native VM for all opcodes.

**IO opcode challenge:** WAIT_READ/WRITE/CHANNEL require IO primitives. vm.tll may need host IO builtins or a simulated event loop. If full implementation in vm.tll is impractical, document as "host-runtime-assisted" with explicit architecture decision — but this is last resort, not default.

**Current status:** GAP-C2 direction set. Implementation is future work (post-P2-01-C core or parallel). Not resolved in this architecture phase.

---

## 12. Performance Contract

**Metrics and measurement plan:**

| Metric | Definition | Baseline (historical) | Target |
|--------|-----------|----------------------|--------|
| Function calls/sec | Empty function call throughput | ~9,790/sec (P0-9, single-threaded) | Re-measure at implementation; no regression >10% single-worker |
| Coroutine create/sec | SPAWN throughput | TBD (re-measure) | TBD |
| Coroutine resume/sec | Yield/resume cycle | TBD | TBD |
| Coroutine switch/sec | Scheduler context switch | TBD | TBD |
| Scheduler throughput | Coroutines scheduled/sec (N runnable) | TBD | TBD |
| IO wakeup throughput | IO events → coroutine wakeups/sec | TBD | TBD |
| Worker scaling | Speedup at 1/2/4/8 workers | N/A (current = 1x due to g_vm_lock) | >1x at 2 workers, scaling to 4-8 workers |
| Heap retain/release throughput | Atomic incref/decref/sec | TBD | TBD |
| Global state contention | Overhead from concurrent global R/W | TBD | TBD |

**Worker scaling plan:**

| Workers | Expected Speedup (ideal) | Contention Factors |
|---------|--------------------------|-------------------|
| 1 | 1x (baseline) | None |
| 2 | ~1.8-2.0x | Global state stripe mutex, heap atomic, scheduler queue |
| 4 | ~3.0-3.8x | Increased shared-state contention |
| 8 | ~5.0-7.0x | Diminishing returns (Amdahl's law) |

**Principles:**
- No invented targets — all targets based on measured baseline + realistic architecture
- Single-worker must not regress (atomic overhead, etc. must be <10%)
- Microbenchmarks ≠ real workloads — measure both
- Every measurement records: commit, platform, compiler, build mode, CPU/thread count, workload, warmup, iterations, wall time, throughput, peak memory, output checksum
- Regression gate: defined before final test; if regression exceeds threshold, block merge

---

## 13. Evidence/Test Contract

**Mandatory acceptance tests:**

| Category | Tests | Evidence Type |
|----------|-------|--------------|
| Single-worker semantic regression | Native 20/20, Bytecode 20/20, Cross-target 11/11 | stdout + exit code |
| Independent multi-worker execution | 2/4/8 workers, independent programs/functions | Correctness + speedup |
| Shared read-only Program | Multiple workers executing same program | No corruption, consistent output |
| Frame reuse/allocation | Frame pool tests, allocation count measurement | Internal counters + RSS |
| Heap ownership race stress | Concurrent incref/decref, aliasing, return values | Stress test + no crash/UAF |
| Mutable global synchronization | Concurrent global R/W, stripe mutex contention | Correctness + no data race |
| Scheduler fairness/progress | Many runnable coroutines, no starvation | All coroutines complete, fair distribution |
| IO wait/wake | P0-RUNTIME-08 tests (timed_wait, handshake_blackhole, connect_timeout, p2p_retry_budget) | PASS/FAIL + timing |
| Coroutine migration | Work stealing test, coroutines move between workers | Migration observed + correct execution |
| 100K logical coroutines + memory | 100K coroutine stress + RSS measurement | RSS + frame count + coroutine count |
| Performance regression | Benchmark matrix (function call, coroutine, scheduler, IO, worker scaling) | Baseline vs new, delta |
| Windows | All above on Windows/MSVC | Actual execution |
| Linux/macOS | Where executable environments exist (CI) | CI evidence or documented B-GAP |
| Sanitizer | ASan where supported (Linux/macOS Clang/GCC); MSVC ASan if environment permits | Sanitizer output or documented limitation |

**Evidence integrity rules:**
- No `|| true` or equivalent failure suppression
- No fake passes (`if failure: print("PASS")`)
- Estimates labeled "ESTIMATE"; measurements labeled "MEASURED"
- All test results reported, including failures
- If test unavailable: document exact reason (environment limitation, missing dependency, etc.)
- Reproducibility: every measurement includes enough info to reproduce

---

## 14. Cross-Target and Sanitizer Strategy

**Cross-target:**

| Platform | Execution Environment | Evidence |
|----------|----------------------|----------|
| Windows | MSVC 2022, x64 — available locally | Full test suite execution |
| Linux | GCC/Clang — available via CI | CI evidence or documented B-GAP if local unavailable |
| macOS | Clang — available via CI | CI evidence or documented B-GAP |

**Cross-target conformance:**
- Existing 11/11 cross-target conformance (Bytecode vs Native) must continue to pass
- New P2-01-C tests must run in both Bytecode and Native modes
- Semantic VM convergence (GAP-C2) strengthens cross-target consistency

**Sanitizer:**

| Sanitizer | Platform | Status |
|-----------|----------|--------|
| MSVC AddressSanitizer | Windows | Attempted in B12 — blocked by environment permission (tll_native.obj Permission denied). B-GAP. Retry if environment changes. |
| Clang/GCC AddressSanitizer | Linux/macOS | Available via CI — run if CI environment supports |
| ThreadSanitizer | Linux/macOS | Available via CI — highly relevant for P2-01-C concurrency; run if supported |
| UndefinedBehaviorSanitizer | Linux/macOS | Available via CI — run if supported |

**Strategy:** Use mature platform tooling. Do NOT build custom fake sanitizer. If unavailable due to environment, record exact error and use fallback evidence (deterministic ownership tests, refcount instrumentation, stress tests).

---

## 15. Rejected Alternatives

| Domain | Rejected Alternative | Reason for Rejection |
|--------|---------------------|---------------------|
| Frame | Fixed 4096 registers | 10-50x memory waste; 100K×10 frames = 94 GB with measured 24-byte TLLValue |
| Frame | Small frame + spill/heap | Too complex; hard to debug; ownership risk; spill bugs hard to trace |
| Frame | Segmented frame | Complexity not justified by memory savings; fragmentation risk |
| Worker | Global VM Lock (current) | No true parallelism; 8 workers serialize on g_vm_lock |
| Worker | One VM per Worker | Breaks shared globals semantics; N full VMs memory overhead; inconsistent global state |
| Worker | Actor/ownership-based | Changes concurrency model too fundamentally; message passing overhead; backward compatibility risk |
| Heap | Non-atomic refcount | Data race under multi-worker concurrent incref/free |
| Heap | Hazard pointers / RCU | Overkill for refcount; complexity not justified |
| Heap | Object pooling | ABA problem; complexity; not needed (direct free is fine) |
| Global | Single replacement global mutex | Re-creates the same bottleneck as g_vm_lock |
| Global | Copy-on-write globals | Snapshot semantics may break TLL global semantics; high memory overhead |
| Scheduler | Single global runnable queue | Contention bottleneck under many workers |
| Scheduler | Per-worker only (no stealing) | Load imbalance; some workers idle while others busy |
| IO | Per-worker epoll/IOCP (no shared reactor) | Complex; fd registration across workers; duplicate wakeup risk |
| Opcode | Silently extend v1.1 to include 46-62 | Violates frozen v1.1 governance; no clean version boundary |
| Opcode | Declare 46-62 as runtime-private | Semantic VM can't implement them; breaks "vm.tll is canonical authority" principle |
| Memory | 4GB as hard correctness gate | Per 于秋鸿 latest instruction: correctness > memory; simplicity > marginal savings |

---

## 16. Migration / Compatibility Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| TLLValue struct size change (24 bytes) | Binary compatibility | NO change to struct layout — 24 bytes is current measured size, not a change |
| Frame register sizing change (4096 → maxRegister) | INVOKE_RET_REG must change; frame pool reuse logic | Compiler guarantees maxRegister includes return reg; full test suite; debug assertions |
| g_vm_lock removal | Shared state data races | Fine-grained sync (C5-C8); full concurrency stress tests; ThreadSanitizer |
| Atomic refcount overhead | Single-worker performance regression | Measure overhead; target <10% regression; relaxed incref minimizes overhead |
| Global state stripe mutex | Contention at high concurrency | 16 stripes reduces contention; can optimize to per-element atomic if needed |
| Scheduler work stealing | Race conditions in queue access | Lock-free local queue; CAS for steal operations; duplicate wakeup prevention |
| IO reactor thread | New thread, lifecycle management | Explicit startup/shutdown; drain on shutdown; no orphaned threads |
| Coroutine migration | Worker-local state in coroutine | Design invariant: no worker-specific state in coroutine; verify in code review |
| Bytecode format | No change (no new opcodes) | P2-01-C adds no new opcodes; bytecode format unchanged |
| Native ABI | No change (no new builtins) | P2-01-C adds no new builtins; ABI unchanged |
| B11 ownership semantics | Must not regress | Atomic refcount is drop-in replacement; full ownership test suite (tests 11/12) |
| P0-RUNTIME-08 IO timeout | Must not break | waitDeadline/waitResult preserved; IO reactor preserves timeout semantics |
| P0-RUNTIME-07 coroutine lifecycle | Must not break | Frame ownership fix preserved; full coroutine stress test |

---

## 17. GAP Disposition Matrix

| GAP | Description | Disposition | Status |
|-----|-------------|-------------|--------|
| GAP-C1 | Opcode Governance Drift (spec 0-45 vs runtime 0-62) | v1.1 FROZEN + v1.2 PROPOSED EXTENSION (46-62, pending formal governance) | **DIRECTION SET (pending formal governance ratification)** |
| GAP-C2 | Semantic VM Convergence (vm.tll doesn't implement 46-62) | Update vm.tll to implement v1.2 (future implementation) | **DIRECTION SET, implementation pending** |
| G1 | Frame Allocation Granularity (fixed 4096) | Dynamic frame sizing by maxRegister | **RESOLVED (architecture decision)** |
| G2 | Execution-Context Ownership (TLLVM mixes state) | Split: shared program + per-worker ExecutionContext | **RESOLVED (architecture decision)** |
| G3 | Global VM Lock Serialization (g_vm_lock) | Remove g_vm_lock, replace with per-worker context + fine-grained sync | **RESOLVED (architecture decision)** |
| G4 | Heap Atomic Ownership (plain int refCount) | Atomic refCount (RECOMMENDED BASELINE — relaxed incref, acq_rel decref candidate, pending ThreadSanitizer + microbenchmark validation) | **RECOMMENDED (pending implementation validation)** |
| G5 | Mutable Global-State Sync (no fine-grained lock) | Hybrid: immutable + per-element sync (16-mutex stripe initial) | **RESOLVED (architecture decision)** |
| G6 | Scheduler Fairness/Progress (single-VM) | Per-worker local queue + global queue (D-1/D-2 required) + work stealing (D-3 optimization, PENDING) + atomic state | **RECOMMENDED (phased implementation)** |
| G7 | IO Wakeup Under Multiple Workers (single-VM select) | Shared IO reactor thread + per-worker local queues | **RESOLVED (architecture decision)** |
| G8 | Runtime Memory Efficiency (formerly "4GB Memory Ceiling") | Dynamic frame sizing (primary) + 10 efficiency principles; 4GB = optimization target, NOT hard gate | **CORRECTED + RESOLVED (architecture direction)** |
| G9 | Performance Regression Gate (no defined targets) | Measurable contract + regression gate + worker scaling | **RESOLVED (architecture decision)** |
| G10 | Cross-Target Consistency (11/11 Windows, Linux/macOS B-GAP) | Preserve existing conformance; Semantic VM convergence strengthens; CI for Linux/macOS | **PRESERVED + strengthened** |

---

## 18. Explicit Unresolved Risks / Architecture Decisions Pending

| Item | Status | Evidence Needed | Phase |
|------|--------|-----------------|-------|
| Exact frame pool reallocation policy (reuse vs reallocate on size mismatch) | PENDING | Frame size distribution measurement | Implementation |
| IO reactor scalability (single reactor vs per-worker epoll at high IO concurrency) | PENDING | High IO concurrency benchmark | Implementation |
| Global state mutex stripe count (16 vs 32 vs 64) | PENDING | Contention benchmark | Implementation |
| Work-stealing threshold (when to steal vs park) | PENDING | Scheduler benchmark | Implementation |
| Atomic refcount performance overhead (single-worker) | PENDING | Microbenchmark (incref/decref throughput) | Implementation |
| Semantic VM IO opcode implementation feasibility in vm.tll | PENDING | Prototyping in vm.tll | Future (post-P2-01-C core) |
| 100K simultaneous live frames memory measurement | PENDING | Actual RSS measurement at 100K coroutines × 10 frames | Implementation (if environment permits) |
| ThreadSanitizer validation of concurrency model | PENDING | TSAN run on Linux/macOS CI | Implementation/CI |
| MSVC ASan environment (permission issue from B12) | B-GAP | Environment fix or documented limitation | Future hardening |

---

## 19. Implementation Status Statement

**IMPLEMENTATION REMAINS BLOCKED pending independent audit by 于秋鸿.**

This architecture decision package is complete and submitted for review. No Runtime source code has been modified. No implementation has begun. The executor (豆包 / Agent A) has no authority to authorize implementation.

**Next steps (after independent audit):**
1. 于秋鸿 reviews this document + full design document
2. Architecture decisions accepted, modified, or rejected
3. If accepted: implementation authorization issued with explicit scope and order
4. Implementation proceeds in dependency order: Frame Model → Atomic RefCount → ExecutionContext/Worker → Global State → Scheduler/IO → Evidence/Performance
5. Each implementation phase produces evidence and awaits independent audit

**Explicit statement:** The executor does NOT declare PASS, SEALED, CLOSED, or implementation-authorized. This is architecture design only, awaiting independent audit.

---

**Measured object sizes (Section 2) were obtained by actual MSVC compilation and execution on 2026-09-10.**
**All other numerical claims are architecture assumptions or derived calculations, explicitly labeled as such.**
**No Runtime source code was modified in this phase.**

施工完成，等待架构师审查与于秋鸿博士最终验收。
