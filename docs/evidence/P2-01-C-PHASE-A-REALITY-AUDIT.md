# P2-01-C Phase A — Repository Reality Audit Inventory

**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756` (main)
**Branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Audit Date:** 2026-09-10
**Auditor:** 豆包 / Agent A (construction executor)
**Status:** REALITY AUDIT COMPLETE — NOT YET IMPLEMENTATION

> This inventory is produced from actual source code inspection, not assumptions.
> Every component is verified against the current repository state at 5b0bc5c.

---

## 1. Core Data Structure Inventory

| Component | Owner/Location | Mutable/Shared? | Thread-Affinity | Allocation Path | Synchronization | Tests | Evidence |
|-----------|---------------|-----------------|-----------------|-----------------|-----------------|-------|----------|
| **TLLProgram** | `host/c/tllvm.h:55-62` | Read-only/shared after load | All workers share | `tll_load_program()` JSON parse | None (assumed immutable) | bootstrap, all tests | `tllvm.h:55` |
| **TLLVM** | `host/c/tllvm.h:104-117` | Mutable, mixed state | Per-VM instance (currently 1 global VM in worker model) | `tll_vm_create()` | `g_vm_lock` (global, serializes all invocation) | coroutine, vm tests | `tllvm.h:104` |
| **TLLFrame** | `host/c/tllvm.h:65-83` | Mutable, per-execution | Per call stack position | `frame_pool_acquire()` → `calloc(4096, sizeof(TLLValue))` for registers | Frame pool is global, no per-pool lock | frame tests, coroutine 100K | `tllvm.h:65`, `vm.c:238` |
| **TLLCoroutine** | `host/c/tllvm.h:86-101` | Mutable, per-VM | Per coroutine, scheduled by VM scheduler | `coroutine spawn` → calloc | Per-VM scheduler (single-threaded within VM) | coroutine tests, 100K stress | `tllvm.h:86` |
| **Frame Pool** | `host/c/vm.c:234-270` | Global static | Cross-VM, cross-worker | `g_frame_pool` static array, grows to `FRAME_POOL_MAX=512` | **NO LOCK** — global pool accessed without synchronization | frame pool tests | `vm.c:231-236` |
| **Call Stack** | `TLLVM.callStack` / `TLLCoroutine.callStack` | Mutable, per-VM/per-coroutine | Per execution context | `push_frame()` / `pop_frame()` | Per-VM (serialized by g_vm_lock) | all tests | `tllvm.h:106`, `tllvm.h:87` |
| **Coroutine Scheduler** | `host/c/vm.c:494-680` | Per-VM | Per VM instance | `coroutine_yield()` → round-robin + `select()` IO wait | Per-VM (single-threaded) | coroutine, IO, timer tests | `vm.c:494` |
| **Worker Pool** | `host/c/builtin.c:149-160` (Win), `257-265` (POSIX) | Global static | 8 worker threads | `CreateThread()` / `pthread_create()` | `g_queue_lock` (task queue), `g_vm_lock` (VM execution) | http server tests | `builtin.c:149` |
| **g_vm_lock** | `host/c/builtin.c:126` (Win CRITICAL_SECTION), `222` (POSIX pthread_mutex) | Global | All workers contend | Static init | **Global serialization point** — all `tll_vm_invoke()` serialized | http worker tests | `builtin.c:126`, `builtin.c:391-399` |
| **Global State (globals)** | `TLLVM.globals` / `globalCount` | Mutable, shared per VM | All coroutines/workers share same VM globals | `calloc(globalCount, sizeof(TLLValue))` | **NO FINE-GRAINED LOCK** — protected only by g_vm_lock | global tests, ownership 11/12 | `tllvm.h:109-110` |
| **Heap Objects** | `runtime/tll_runtime.h:89-128` | Shared, refcounted | Cross-coroutine, cross-worker | `tll_array()`, `tll_map()`, `tll_string()` → calloc | **refCount is plain `int`, NOT atomic** | ownership tests, native 20/20 | `tll_runtime.h:93`, `:109`, `:117`, `:127` |
| **IO Wait State** | `TLLCoroutine.waitingFd/waitingEvents/waitingChannel/waitDeadline/waitResult` | Per-coroutine | Per coroutine | Set on OP_WAIT_READ/WRITE/CHANNEL, cleared on wake | Per-VM scheduler | IO tests, P0-RUNTIME-08 tests | `tllvm.h:95-100` |
| **Shared Runtime Core** | `runtime/tll_runtime.h`, `runtime/value.c`, `runtime/arithmetic.c`, `runtime/io.c` | Shared, stateless helpers | Cross-target (Bytecode + Native) | Static/global | None (stateless functions, operate on caller-owned values) | all tests | `tll_runtime.h:1-31` |

---

## 2. Opcode Governance Inventory (GAP-C1)

| Source | Version | Status | Opcode Range | Key Opcodes |
|--------|---------|--------|--------------|-------------|
| **spec/OPCODES.md** | v1.1 | **FROZEN** | 0-45 (46 total) | LOAD_CONST through BOX_LOCAL |
| **C Runtime (tllvm.h:120-188)** | Implementation | Active | 0-62 (63 total) | 0-45 frozen + 46-53 bitwise + 54-56 coroutine + 57-59 IO + 60 MOV + 61-62 exception |
| **Semantic VM (runtime/vm.tll)** | Source of truth (per ARCHITECTURE.md) | **Stale** | 0-45 only | Does NOT contain OP_SPAWN, OP_YIELD, OP_SLEEP, OP_WAIT_READ, OP_WAIT_WRITE, OP_MOV, OP_BAND |

**GAP-C1 Verdict:** Drift confirmed. Frozen spec 0-45 vs C runtime 0-62. Semantic VM does not implement 46-62. Must be resolved at architecture/governance level before any new opcode.

---

## 3. Memory Footprint Inventory (for 4GB Contract)

| Component | Per-Instance Size | Count at 100K coroutines | Estimated Total | Notes |
|-----------|-------------------|---------------------------|-----------------|-------|
| **TLLFrame.registers** | 4096 × sizeof(TLLValue) | 1 per active frame | **~524 MB per 100K frames** (assuming 16 bytes/TLLValue) | Fixed 4096, allocated at frame creation |
| **TLLFrame.argStack** | 64 × sizeof(TLLValue) initial, grows | 1 per frame | ~10 MB per 100K (initial) | Dynamic realloc |
| **TLLFrame.tryStack** | 16 × int initial | 1 per frame | ~6 MB per 100K | Dynamic realloc |
| **TLLFrame.locals** | dynamic (function localCount) | 1 per frame | variable | NULL at pool acquire, allocated on demand |
| **TLLFrame struct** | ~80-100 bytes | 1 per frame | ~10 MB per 100K | |
| **TLLCoroutine** | ~80-100 bytes + callStack array | 1 per coroutine | ~10 MB per 100K + callStack | callStackCapacity grows |
| **TLLCoroutine.callStack** | TLLFrame* × capacity | 1 per coroutine | ~8 MB per 100K (initial 64) | Dynamic realloc |
| **Heap objects** | variable | shared | variable | refcounted, plain int |
| **Globals** | globalCount × TLLValue | 1 per VM | < 1 MB | |
| **Frame Pool** | up to 512 frames × full size | 1 global | ~2.6 MB (512 × 5MB) | Pooled frames retain full 4096 register allocation |

**Preliminary 4GB Assessment:** At 100K active coroutines with 1 frame each, frame registers alone consume ~524 MB. With deeper call stacks (e.g., 10 frames/coroutine), this reaches ~5.2 GB — **exceeds 4GB ceiling**. Frame model redesign is mandatory before 100K-scale concurrency.

---

## 4. Synchronization Inventory

| Lock | Location | Type | Protects | Contention Model | Can Be Removed? |
|------|----------|------|----------|------------------|-----------------|
| **g_vm_lock** | `builtin.c:126` (Win), `:222` (POSIX) | CRITICAL_SECTION / pthread_mutex | All `tll_vm_invoke()` calls | **Global bottleneck** — 8 workers serialize on VM execution | **Primary P2-01-C target** — requires ExecutionContext separation first |
| **g_queue_lock** | `builtin.c:142` (Win), `:233` (POSIX) | CRITICAL_SECTION / pthread_mutex | HTTP worker task queue | Low contention (task dispatch only) | Can remain, or replace with lock-free queue |
| **g_sqlite_mutex** | `sqlite_builtin.c:24` (Win), `:43` (POSIX) | CRITICAL_SECTION / pthread_mutex | SQLite builtin access | Low (only when SQLite used) | Out of scope |
| **Frame Pool** | `vm.c:234` | **NONE** | `g_frame_pool` global array | **UNPROTECTED** — concurrent access from multiple workers would corrupt pool | Must add protection or make per-context |
| **Heap refCount** | `tll_runtime.h` | **NONE (plain int)** | All refcounted objects | **UNPROTECTED** — concurrent incref/free is data race | Must become atomic or per-context ownership |
| **Globals** | `TLLVM.globals` | **NONE (only g_vm_lock)** | All global variables | Protected only by global VM lock | Need fine-grained model after g_vm_lock removal |

---

## 5. Test & Benchmark Inventory

| Category | Location | Count | Status | Notes |
|----------|----------|-------|--------|-------|
| **Native tests** | `tests/native/01-20` | 20 | PASS (Windows/MSVC) | Includes ownership 11/12, cross-target conformance |
| **Bytecode tests** | `tests/native/01-20` (bytecode mode) | 20 | PASS | Same sources, bytecode execution |
| **Cross-target conformance** | `scripts/cross-target-conformance.ps1` | 11/11 | PASS | 01-11, stdout/exit code comparison |
| **Coroutine stress** | `tests/coroutine_stress_test.tll` | 1 | PASS | 100K immediate-return, 10K×10 yield, 1K sleep |
| **Coroutine 512** | `tests/coroutine_512.tll` | 1 | PASS | Frame pool boundary test |
| **P0-RUNTIME-08 tests** | `tests/timed_wait_*.tll`, `handshake_blackhole.tll`, `connect_timeout_*.tll`, `p2p_retry_budget_*.tll` | 5 | PASS | Timed-wait, handshake blackhole, connect timeout, retry budget |
| **Blockchain tests** | `scripts/run-bc-network-test.ps1` | 3 (bc_node, bc_multi, bc_delayed) | PASS (Windows) | 4-node 5-block sync |
| **High-frame benchmark** | `benchmarks/high_frame_rate.tll` | 1 | Baseline only | Function call 9,790/sec, loop 3,144,650/sec — NOT a performance contract |
| **CI** | `.github/workflows/ci.yml` | 3 platforms | PASS (7501b72) | Ubuntu/Windows/macOS, native-build-test + coroutine-only-verify |
| **ASan** | attempted | — | B-GAP | MSVC ASan blocked by environment permission (tll_native.obj Permission denied) |

---

## 6. Reality Audit Summary

### Confirmed Baseline Facts (not to be rediscovered)

1. ✅ Frame Pool exists (64 initial, 512 max) but new frames still allocate fixed 4096 registers
2. ✅ `g_vm_lock` is the global VM execution serialization point (Windows CRITICAL_SECTION / POSIX pthread_mutex)
3. ✅ TLLVM mixes program state (read-only) with execution state (callStack, currentCoroutine, globals)
4. ✅ Heap refCount is plain `int`, NOT atomic — in TLLArray, TLLMap, TLLUpvalue, TLLClosureEnv, and string headers
5. ✅ Globals are shared runtime state with no fine-grained concurrency model (only g_vm_lock)
6. ✅ Coroutine/IO/timer scheduler already exists and is per-VM (single-threaded within VM)
7. ✅ GAP-C1: Opcode spec v1.1 frozen 0-45 vs C runtime 0-62 — drift confirmed
8. ✅ GAP-C2: Semantic VM (runtime/vm.tll) does not implement opcodes 46-62 — convergence gap confirmed
9. ✅ Frame Pool is global and **unprotected** (no lock) — concurrent worker access is unsafe
10. ✅ 4GB ceiling: at 100K coroutines × 10 frames, fixed 4096-register frames alone exceed 4GB — frame model redesign is mandatory

### What Does NOT Exist Yet

- ❌ Per-worker ExecutionContext (callStack/currentCoroutine/frame state per worker)
- ❌ Atomic heap ownership protocol
- ❌ Fine-grained global state synchronization
- ❌ Per-context frame pool (or protected global pool)
- ❌ Performance regression gate with defined targets
- ❌ Memory contract with measured/verified 4GB bound
- ❌ ThreadSanitizer evidence
- ❌ Semantic VM convergence for opcodes 46-62

### Stop Conditions Already Triggered (must be resolved in Architecture phase)

1. **4GB ceiling cannot be satisfied with current 4096-register frame model at 100K scale** — requires Frame Model Decision (Phase C2)
2. **Removing g_vm_lock reveals unprotected global frame pool and non-atomic heap refcount** — requires concurrency architecture (Phases D-G)
3. **GAP-C1/GAP-C2 must be resolved before any opcode changes** — requires governance decision (Phase I)

---

**Phase A Status: COMPLETE**
**Next: Phase B — GAP Ledger (GAP-C1/C2 + G1-G10)**
**No source code has been modified. This is architecture preflight only.**
