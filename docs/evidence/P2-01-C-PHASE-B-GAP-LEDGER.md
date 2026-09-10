# P2-01-C Phase B — GAP Ledger

**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756` (main)
**Branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Date:** 2026-09-10
**Status:** GAP LEDGER ESTABLISHED — Architecture decisions pending

> Every GAP is evidence-backed from the Phase A Reality Audit.
> No GAP is invented. No GAP is hidden. No claim without evidence.

---

## Governance GAPs

### GAP-C1 — Opcode Governance Drift

**Severity:** Architecture/Governance (must resolve before any new opcode)
**Status:** CONFIRMED DRIFT

**Evidence:**
- `spec/OPCODES.md`: Version 1.1, Status FROZEN, Total Opcodes 46 (0-45)
- `host/c/tllvm.h:120-188`: C runtime enum defines opcodes 0-62 (63 total)
- Opcodes 46-53: Bitwise (BAND, BOR, BXOR, BNOT, SHL, SHR, ROTR, ROTL) — P0-15
- Opcodes 54-56: Coroutine (SPAWN, YIELD, SLEEP) — P0-15.14/15
- Opcodes 57-59: IO-aware (WAIT_READ, WAIT_WRITE, WAIT_CHANNEL) — P0-15.16
- Opcode 60: MOV — P0-COMPILER-02
- Opcodes 61-62: Exception (CATCH_ENTER, FINALLY_END)

**Required Decision (one of):**
1. Classify existing 46-62 as "implementation/runtime extension" outside frozen v1.1 spec, with explicit version boundary (e.g., v1.1-runtime-ext)
2. Establish correct version/spec boundary: promote 46-62 to a new spec version (v1.2) with proper governance process
3. Document another evidence-backed resolution

**Forbidden:** Silently changing the frozen v1.1 opcode contract.

**Impact on P2-01-C:** If implementation can use existing opcodes 0-62, no new opcode needed. If a new opcode is genuinely required, must stop and obtain architecture decision first.

---

### GAP-C2 — Semantic VM Convergence

**Severity:** Architecture (must audit before claiming semantic equivalence)
**Status:** CONFIRMED GAP

**Evidence:**
- `runtime/vm.tll`: 39,045 chars, does NOT contain OP_SPAWN, OP_YIELD, OP_SLEEP, OP_WAIT_READ, OP_WAIT_WRITE, OP_MOV, OP_BAND
- `ARCHITECTURE.md`: states `runtime/vm.tll` is "executable language specification" and "Spec is the sole semantic authority"
- C Runtime (`vm.c`): fully implements opcodes 0-62 including coroutine, IO, bitwise, MOV, exception

**Capability Matrix:**

| Capability | Native C VM | Semantic VM (vm.tll) | Spec Authority | Status |
|------------|-------------|----------------------|----------------|--------|
| Opcodes 0-45 (frozen v1.1) | ✅ Implemented | ✅ Implemented | spec/OPCODES.md v1.1 | CONVERGED |
| Bitwise 46-53 | ✅ Implemented | ❌ Not present | None (runtime extension) | **GAP** |
| Coroutine 54-56 | ✅ Implemented | ❌ Not present | None (runtime extension) | **GAP** |
| IO-aware 57-59 | ✅ Implemented | ❌ Not present | None (runtime extension) | **GAP** |
| MOV 60 | ✅ Implemented | ❌ Not present | None (runtime extension) | **GAP** |
| Exception 61-62 | ✅ Implemented | ❌ Not present | None (runtime extension) | **GAP** |

**Required Decision:**
- For each capability in 46-62: either (a) update Semantic VM to implement it, or (b) explicitly classify as "host-runtime-only" with architecture decision recorded
- Do not silently normalize one side

**Impact on P2-01-C:** P2-01-C touches scheduler, IO wait, coroutine lifecycle — all in 46-62 range. Must either update Semantic VM or explicitly document host-runtime-only classification.

---

## Technical GAPs

### G1 — Frame Allocation Granularity

**Severity:** Performance + Memory (blocks 4GB at 100K scale)
**Status:** CONFIRMED

**Evidence:**
- `vm.c:244-245`: `frame->registerCount = 4096; frame->registers = (TLLValue*)calloc(4096, sizeof(TLLValue));`
- Every new frame allocates fixed 4096 registers regardless of function's actual `maxRegister`
- `TLLFunction.maxRegister` exists (`tllvm.h:52`) but is NOT used to size frame registers
- Frame Pool reuses frames but retains full 4096 allocation

**Memory Impact (preliminary):**
- Per frame: 4096 × sizeof(TLLValue) ≈ 4096 × 16 bytes = 64 KB (registers only)
- 100K coroutines × 1 frame = 6.4 GB — **EXCEEDS 4GB ceiling**
- 100K coroutines × 10 frames = 64 GB — catastrophic

**Required Action:**
- Evaluate frame models: fixed 4096 / dynamic sized / small-frame inline + spill / pooled / segmented
- Chosen model must preserve semantics and ownership correctness
- Must use `TLLFunction.maxRegister` to size register storage
- Do not optimize by deleting required registers or weakening correctness

---

### G2 — Execution-Context Ownership

**Severity:** Architecture (blocks g_vm_lock removal)
**Status:** CONFIRMED

**Evidence:**
- `TLLVM` struct (`tllvm.h:104-117`) mixes:
  - Read-only/shared: `program` (TLLProgram*)
  - Mutable execution state: `callStack`, `callStackSize`, `callStackCapacity`, `currentCoroutine`, `invokeTargetStackSize`
  - Shared mutable state: `globals`, `globalCount`
  - Per-VM scheduler: `coroutines`, `coroutineCount`, `coroutineCapacity`
- Currently only one TLLVM instance exists globally; worker threads serialize via g_vm_lock

**Required Action:**
- Define exact ownership for every mutable field before moving it
- Target model: Program (read-only/shared) → ExecutionContext (per-worker: callStack, currentCoroutine, frame state) → Shared State (globals, heap, scheduler with proper sync)
- No field may become shared merely because moving it is convenient

**Field Ownership Table (proposed):**

| Field | Current Owner | Proposed New Owner | Shared? | Synchronization | Lifetime |
|-------|--------------|-------------------|---------|-----------------|----------|
| program | TLLVM | Global/Shared (read-only) | Yes (read) | None (immutable) | Process |
| callStack | TLLVM | ExecutionContext (per-worker) | No | None (thread-local) | Worker |
| callStackSize/Capacity | TLLVM | ExecutionContext | No | None | Worker |
| globals | TLLVM | Shared Global State | Yes | Fine-grained (TBD) | Process |
| globalCount | TLLVM | Shared Global State | Yes | Fine-grained (TBD) | Process |
| invokeTargetStackSize | TLLVM | ExecutionContext | No | None | Worker |
| coroutines | TLLVM | Scheduler (shared or per-context) | TBD | TBD | TBD |
| coroutineCount/Capacity | TLLVM | Scheduler | TBD | TBD | TBD |
| currentCoroutine | TLLVM | ExecutionContext | No | None | Worker |

---

### G3 — Global VM Lock Serialization

**Severity:** Performance (primary bottleneck for parallel execution)
**Status:** CONFIRMED

**Evidence:**
- `builtin.c:126` (Windows): `static CRITICAL_SECTION g_vm_lock;`
- `builtin.c:222` (POSIX): `static pthread_mutex_t g_vm_lock = PTHREAD_MUTEX_INITIALIZER;`
- `builtin.c:391-399`: `tll_vm_invoke()` wrapped in g_vm_lock
- Worker pool (`builtin.c:149-160` Win, `257-265` POSIX): 8 worker threads
- All 8 workers serialize on g_vm_lock for any VM execution

**Current Model:**
```
Worker 0 ──┐
Worker 1 ──┤
Worker 2 ──┼──► 🔒 g_vm_lock ──► tll_vm_invoke() ──► VM execution
...        │
Worker 7 ──┘
```

**Required Action:**
- NOT merely delete g_vm_lock
- Must prove concurrent workers can execute independent TLL work without corrupting: call stacks, current coroutine, frame state, exception state, return state, scheduler state, heap ownership, global state
- Requires G2 (ExecutionContext) and G4 (heap atomic) and G5 (global state) first
- Do not replace one global lock with another hidden global lock

---

### G4 — Heap Atomic Ownership

**Severity:** Concurrency Safety (blocks g_vm_lock removal)
**Status:** CONFIRMED

**Evidence:**
- `tll_runtime.h:93`: `TLLArray.refCount` — plain `int`
- `tll_runtime.h:109`: `TLLMap.refCount` — plain `int`
- `tll_runtime.h:117`: `TLLUpvalue.refCount` — plain `int`
- `tll_runtime.h:127`: `TLLClosureEnv.refCount` — plain `int`
- String refCount: hidden in data header (`tll_runtime.h:67-69`), also plain `int`
- `tll_value_incref()` / `tll_value_free()` operate on plain int without atomic operations

**Data Race Scenario:**
```
Worker A: tll_value_incref(obj)   ──┐
                                      ├──► concurrent read-modify-write on refCount → data race
Worker B: tll_value_free(obj)       ──┘
```

**Required Action:**
- Establish explicit multi-worker ownership protocol
- If reference counts become atomic: document atomic type, memory ordering, destruction synchronization, ABA/reuse considerations, interaction with object fields, closures/upvalues, arrays/maps/strings
- Do NOT perform broad refcount redesign unrelated to runtime concurrency goal
- Existing B11 ownership semantics are frozen as correctness baseline — MUST NOT regress

---

### G5 — Mutable Global-State Synchronization

**Severity:** Concurrency Safety (blocks g_vm_lock removal)
**Status:** CONFIRMED

**Evidence:**
- `TLLVM.globals`: `TLLValue *globals` — shared array, no per-element locking
- `TLLVM.globalCount`: `int` — shared
- Currently protected only by g_vm_lock (which serializes ALL VM execution)
- OP_LOAD_GLOBAL (40) / OP_STORE_GLOBAL (41) access globals directly

**Required Action:**
- Classify every global: immutable / read-mostly / mutable / thread-local
- For mutable shared state, define smallest practical synchronization domain
- Do not introduce a single replacement global mutex unless architecture proves it is not a throughput bottleneck
- Tests MUST include concurrent reads/writes where semantics permit them

---

### G6 — Scheduler Fairness/Progress

**Severity:** Correctness under concurrency
**Status:** PARTIALLY CONFIRMED (current per-VM scheduler is single-threaded)

**Evidence:**
- `vm.c:494-680`: `coroutine_yield()` implements round-robin scheduler
- 2-pass: pass 0 find runnable, pass 1 after IO/timer wait
- `vm.c:537`: `int idx = (old + 1 + i) % vm->coroutineCount;` — round-robin from old+1
- `vm.c:546`: pass 0 excludes self (P0-COMPILER-06 BUG-A fix)
- No runnable → collect WAITING_IO fds → `select()` with timeout from earliest sleeper

**Current Limitations:**
- Single-threaded within one VM (no concurrent scheduler access)
- No worker handoff policy (coroutines cannot migrate between workers)
- No duplicate wake prevention mechanism documented
- Shutdown/drain behavior not explicitly defined

**Required Action:**
- Define runnable queue ownership, sleeping coroutine ownership, IO waiter ownership, wakeup ownership
- Define fairness policy, starvation prevention, worker handoff policy, duplicate wake prevention, shutdown/drain behavior
- Required invariant: `one logical wakeup -> at most one runnable transition`
- No lost wakeups, no duplicate execution, no busy-spin

---

### G7 — IO Wakeup Correctness Under Multiple Workers

**Severity:** Correctness under concurrency
**Status:** CONFIRMED GAP (current design is single-VM)

**Evidence:**
- `TLLCoroutine.waitingFd`, `waitingEvents`, `waitingChannel`, `waitDeadline`, `waitResult` — per-coroutine
- `vm.c:568-645`: scheduler collects all WAITING_IO fds into fd_set, calls `select()`
- `select()` is called from within `coroutine_yield()` which runs on the single VM thread
- No mechanism for multiple workers to concurrently wait on different fd sets
- `coroutine_wake_channel()` (`tllvm.h:229`) wakes all coroutines waiting on a channel — no per-coroutine wake targeting

**Required Action:**
- Define how IO wait works when multiple workers exist
- Each worker may need its own select()/epoll()/IOCP loop, or a shared IO reactor
- Must prevent: lost wakeups, duplicate wakeups, fd set corruption from concurrent access
- Must preserve existing P0-RUNTIME-08 timed-wait semantics (waitReadWithTimeout / waitWriteWithTimeout)

---

### G8 — 4GB Memory Ceiling

**Severity:** Hard Architectural Constraint
**Status:** CONFIRMED — current design violates at 100K scale

**Evidence:**
- Fixed 4096 registers per frame (G1)
- 100K coroutines × 1 frame × 64 KB = 6.4 GB > 4 GB
- Frame Pool retains full allocation for pooled frames
- Coroutine callStack arrays grow dynamically
- Heap objects shared but variable size

**Preliminary Memory Model (current design):**

| Scale | Frames (1/coroutine) | Registers Only | + argStack/tryStack | + Coroutine Metadata | Estimated Total |
|-------|----------------------|----------------|---------------------|---------------------|-----------------|
| 100 | 100 | 6.4 MB | ~7 MB | ~1 MB | ~8 MB |
| 1,000 | 1,000 | 64 MB | ~70 MB | ~10 MB | ~80 MB |
| 10,000 | 10,000 | 640 MB | ~700 MB | ~100 MB | ~800 MB |
| 100,000 | 100,000 | 6.4 GB | ~7.0 GB | ~1 GB | **~8 GB > 4GB** |

**Required Action:**
- Design MUST satisfy: `worst_case_runtime_memory < 4 GiB` with explicit safety margin
- Do not design exactly to 4 GiB
- Must model: TLLFrame, TLLCoroutine, ExecutionContext, Frame Pool, Coroutine table, Scheduler queues, IO wait structures, Shared heap objects, Globals, temporary call/argument storage, worker/thread metadata, allocator overhead
- Frame model decision (G1) is the primary lever for staying under 4GB

---

### G9 — Performance Regression Gate

**Severity:** Engineering (no defined targets yet)
**Status:** CONFIRMED GAP

**Evidence:**
- `benchmarks/high_frame_rate.tll` exists but explicitly states: "VM has global lock. These are single-threaded numbers. True parallel execution requires per-worker callStack + fine-grained locking."
- Historical baseline: function call 9,790/sec, loop 3,144,650/sec, map update 81,633/sec, event 9,615/sec
- No CI performance regression gate exists
- No defined performance targets for P2-01-C

**Required Action:**
- Build reproducible benchmark matrix with: workload, baseline, target, regression gate
- Targets MUST be based on measured baseline and realistic architecture, not invented marketing numbers
- Every benchmark records: commit, platform, compiler/build mode, CPU/thread count, workload size, warmup, iterations, wall time, throughput, peak memory, result checksum/output
- Do not treat benchmark numbers as performance contracts until gate is defined

---

### G10 — Cross-Target Consistency

**Severity:** Correctness (Bytecode vs Native semantic equivalence)
**Status:** PARTIALLY VERIFIED (11/11 cross-target conformance on Windows)

**Evidence:**
- `scripts/cross-target-conformance.ps1`: runs TLL source through Bytecode and Native, compares stdout/exit code
- 11/11 PASS for tests 01-11 (B12-R1 evidence)
- Native 20/20 PASS (Windows/MSVC)
- Bytecode 20/20 PASS
- Linux/macOS Native execution: B-GAP (not verified locally)
- Semantic VM (vm.tll) does not implement opcodes 46-62 (GAP-C2)

**Required Action:**
- Runtime architecture MUST preserve existing TLL semantic contract
- At minimum validate on available platforms: Windows, Linux, macOS
- Absence of local platform is B-GAP unless CI or another reproducible evidence source closes it
- Compare: stdout, exit code, error behavior, ownership-visible behavior, scheduler-visible deterministic results
- Do not claim cross-platform PASS from compilation alone

---

## GAP Dependency Map

```
G8 (4GB ceiling) ──────► requires G1 (Frame model)
                              │
G3 (g_vm_lock removal) ──► requires G2 (ExecutionContext)
                              ├─ requires G4 (heap atomic)
                              ├─ requires G5 (global state sync)
                              └─ requires G6/G7 (scheduler/IO under concurrency)

GAP-C1 (opcode governance) ──► must resolve before any new opcode
GAP-C2 (semantic VM) ─────────► must audit for all touched capabilities

G9 (performance gate) ──────► can be defined in parallel with implementation
G10 (cross-target) ──────────► verification phase, after implementation
```

## Implementation Order (proposed)

1. **Phase C**: Memory Model + Frame Model Decision (resolves G1, G8)
2. **Phase D**: ExecutionContext Architecture (resolves G2)
3. **Phase E**: Remove Global Bottleneck (resolves G3, depends on D/F/G)
4. **Phase F**: Heap Atomic Ownership (resolves G4)
5. **Phase G**: Global State Concurrency (resolves G5)
6. **Phase H**: Scheduler/Event Model (resolves G6, G7)
7. **Phase I**: Opcode/Semantic Boundary (resolves GAP-C1, GAP-C2)
8. **Phase J**: Performance Contract (resolves G9)
9. **Phase K-N**: Tests, Sanitizer, Cross-Target, Evidence (resolves G10, verification)

---

**Phase B Status: COMPLETE**
**GAPs identified: 12 (GAP-C1, GAP-C2, G1-G10)**
**Next: Phase C — Memory Model First (4GB Hard Ceiling + Frame Model Decision)**
**No source code has been modified. Architecture preflight only.**
