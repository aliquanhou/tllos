# P2-01-C Phase C — High-Frame Runtime Architecture Design

**Status:** ARCHITECTURE DESIGN — NOT IMPLEMENTATION
**Baseline:** `5b0bc5cf561b528c6fbc57aeb2e4ac048836e756` (main)
**Branch:** `feature/P2-01-C-high-frame-runtime-construction`
**Authority:** 于秋鸿
**Executor:** 豆包 / Agent A
**Phase:** C — Architecture Design (no source modification)

> **Critical Principle:** 4GB is a reference budget / optimization target, NOT a hard correctness constraint.
> Memory efficiency is an optimization goal. A design that uses slightly more memory but is simpler,
> more stable, higher performance, and easier to maintain is PREFERRED over an extreme memory-minimizing
> design that is complex, fragile, and hard to debug.

---

## Executive Summary

This document defines the complete architecture for evolving TLL Runtime from a "correct-but-coarse"
execution model toward a High-Frame Runtime. The design prioritizes:

1. **Correctness** — preserve all existing TLL semantics, ownership, coroutine, network, and native target behavior
2. **Clarity** — clean separation of concerns, explicit ownership, auditable concurrency model
3. **Concurrency** — true multi-worker parallel execution without global serialization
4. **Performance** — high function-call throughput, efficient coroutine scheduling, scalable worker model
5. **Memory Efficiency** — reduce unnecessary allocations while avoiding over-engineering
6. **Maintainability** — simple, stable, cross-platform, easy to debug and extend

**No Runtime source code is modified in this phase.** This is pure architecture design.

### Decision Confidence Levels

All architecture decisions are labeled: **PROVEN** (evidence-supported), **RECOMMENDED** (current best choice, needs validation), **PENDING** (requires experiments/proof/governance before finalization).

Key levels: Dynamic Frame=RECOMMENDED (return-register proof needed), Atomic RefCount=RECOMMENDED BASELINE (ThreadSanitizer validation needed), Scheduler=RECOMMENDED (D-1/D-2) + PENDING (D-3 work stealing), Opcode v1.2=PENDING FORMAL GOVERNANCE, Memory Efficiency=PROVEN (4GB is optimization target, not hard gate).

---

## C1 — Frame Model

### Current Reality (verified from source)

| Component | Location | Current Behavior |
|-----------|----------|-----------------|
| `TLLFunction.maxRegister` | `tllvm.h:52` | Compiler computes highest register index used by function |
| `TLLFrame.registers` | `tllvm.h:68` | `TLLValue *registers` — dynamically allocated pointer |
| `TLLFrame.registerCount` | `tllvm.h:69` | `int registerCount` — set to 4096 at allocation |
| Frame allocation | `vm.c:243-252` | `calloc(4096, sizeof(TLLValue))` — FIXED 4096 regardless of maxRegister |
| Frame Pool | `vm.c:231-270` | Global pool, INITIAL=64, MAX=512, pooled frames retain full 4096 allocation |
| `locals` | `tllvm.h:70-72` | Separate dynamic array, allocated on demand based on function localCount |
| `argStack` | `tllvm.h:73-75` | Initial capacity 64, grows dynamically |
| `tryStack` | `tllvm.h:76-78` | Initial capacity 16, grows dynamically |

**Key observation:** `TLLFunction.maxRegister` already exists and is computed by the compiler, but is
**not used** to size frame register storage. Every frame allocates fixed 4096 registers even if the
function only uses 3.

### Model Comparison

| Criterion | Model A: Fixed 4096 | Model B: Dynamic (maxRegister) | Model C: Small + Spill | Model D: Size-Class Pool |
|-----------|---------------------|--------------------------------|------------------------|--------------------------|
| **Memory per frame** | 4096 × 24 = **96 KB** (measured) | maxRegister × 24 (avg ~1-4 KB) | Small inline (e.g., 64) + heap spill | Class-based: 64/256/1024/4096 |
| **Allocation count** | 1 per frame | 1 per frame (sized) | 1 inline + N spills | 1 per frame (class) |
| **Cache locality** | Poor (large sparse array) | Good (tight allocation) | Good (inline hot path) | Good (class-aligned) |
| **Function call latency** | Low (fixed size, no sizing logic) | Low (one calloc with computed size) | Medium (spill logic on overflow) | Medium (class lookup) |
| **100K coroutine scalability** | **9.15 GB** (1 frame each, measured 24-byte TLLValue) — exceeds 4GB ref budget | ~100-400 MB (avg 1-4KB) — well within budget | ~50-200 MB (inline + selective spill) | ~100-300 MB (class average) |
| **Fragmentation** | High (many large allocations) | Low (varied sizes) | Medium (inline + heap) | Medium (fixed classes) |
| **Lifecycle complexity** | Low | Low | High (spill tracking) | Medium (class management) |
| **Debug difficulty** | Low | Low | High (spill bugs hard to trace) | Medium |
| **Ownership risk** | Low | Low | Medium (spill references) | Low |
| **Cross-platform** | Excellent | Excellent | Good (spill logic platform-independent) | Excellent |
| **Implementation complexity** | Low | Low (use existing maxRegister) | High | Medium |

### Recommended Model: **Model B — Dynamic Frame Sized by maxRegister**

**Rationale:**
1. `TLLFunction.maxRegister` already exists and is computed by the compiler — zero compiler change needed
2. Single `calloc(maxRegister + 1, sizeof(TLLValue))` replaces fixed `calloc(4096, ...)` — minimal VM change
3. **Measured `sizeof(TLLValue) = 24 bytes`** (MSVC 2022 x64). Fixed 4096-register frame = 96 KB; 100K frames = 9.15 GB. Dynamic sizing: 100K × 64 regs × 24B = 146.5 MiB; 100K × 128 regs × 24B = 293.0 MiB (64-128 avg is ASSUMPTION / PENDING MEASUREMENT from real TLL program corpus).
4. No spill logic, no size-class management, no complex lifecycle — simple and maintainable
5. Preserves all existing semantics — register indexing unchanged, only allocation size changes
6. Frame Pool can retain pooled frames but should reset `registerCount` and potentially reallocate if pooled frame's registerCount < required maxRegister (or simply free and reallocate on mismatch)
7. Cross-platform — pure C, no platform-specific code

**Implementation notes (for future phase, NOT this phase):**
- `frame_pool_acquire()`: if pooled frame has `registerCount >= required maxRegister`, reuse; else free pooled frame's registers and reallocate at required size
- `create_frame()`: pass `fn->maxRegister` to frame allocation
- **Return-register semantics MUST BE PROVEN before implementation.** Current code uses fixed `INVOKE_RET_REG = 4095` and accesses `parentFrame->registers[INVOKE_RET_REG]`. Cannot simply change to `fn->maxRegister` without proving: (a) all return-value paths use which register; (b) compiler guarantees `maxRegister` covers it; (c) parent frame always has it allocated. Semantic proof required.
- Verify compiler guarantees `maxRegister` includes all register indices actually used (including return register)

**Risk:** If compiler's `maxRegister` is inaccurate (e.g., doesn't account for some temporary registers), frame could be too small. Mitigation: add debug-mode assertion that register index < registerCount; verify with full test suite before release.

---

## C2 — Runtime Memory Efficiency Contract

### Definitions

| Term | Definition |
|------|-----------|
| **Logical Coroutine** | A coroutine object that exists in the coroutine table, may be alive/suspended/dead |
| **Simultaneously Live Execution Context** | A coroutine that currently has an active call stack and is either running, runnable, sleeping, or waiting on IO/channel |
| **Simultaneously Live Frame** | A frame that is currently on some coroutine's call stack |
| **Suspended Coroutine** | A coroutine that has yielded and is not currently executing, but retains its call stack |

### Scenario Analysis

| Scenario | Description | Memory Driver | Optimization Target |
|----------|-------------|---------------|---------------------|
| **A: Many logical, most suspended** | 100K coroutines created, 99% suspended with shallow call stack | Coroutine metadata + shallow call stacks | Reduce coroutine metadata size, shallow frame allocation |
| **B: Many concurrent execution contexts** | 10K coroutines simultaneously active with deep call stacks | Full frames × call stack depth | Dynamic frame sizing (C1), efficient frame pool |
| **C: Many simultaneously live frames** | Deep recursion across many coroutines | Frame count × frame size | Dynamic frame sizing, frame reuse |
| **D: Many short-lived function calls** | High function-call churn, frames created/destroyed rapidly | Allocation overhead, fragmentation | Frame pool reuse, avoid malloc/free in hot path |
| **E: Many workers** | 8+ worker threads each with execution context | Per-worker context overhead | Minimal worker context, shared read-only program |

### Memory Components to Measure (future implementation phase)

| Component | Measurement Method | Current Estimate | Notes |
|-----------|-------------------|------------------|-------|
| `sizeof(TLLValue)` | compile-time `sizeof` | **24 bytes** (MEASURED: MSVC 2022 x64) | type tag 4 + padding 4 + union 16 |
| `sizeof(TLLFrame)` | compile-time `sizeof` | **120 bytes** (MEASURED) | Excludes dynamically allocated arrays |
| `sizeof(TLLCoroutine)` | compile-time `sizeof` | **96 bytes** (MEASURED) | Excludes callStack array |
| Register allocation | `frame->registerCount × sizeof(TLLValue)` | 4096 × 24 = **96 KB** (current fixed) | Will reduce with Model B (dynamic maxRegister) |
| argStack allocation | `argStackCapacity × sizeof(TLLValue)` | 64 × 24 = **1.5 KB** initial | Grows dynamically |
| tryStack allocation | `tryStackCapacity × sizeof(int)` | 16 × 4 = 64 bytes initial | Grows dynamically |
| Frame Pool overhead | `pool_size × sizeof(TLLFrame*)` + pooled frame memory | 512 × 8 = 4KB (pointers) + pooled frames | Pooled frames retain full allocation |
| Allocator metadata | malloc overhead per allocation | ~16-32 bytes per allocation | Platform-dependent |
| Peak RSS | OS-level measurement | TBD (not yet measured) | Must be measured in implementation phase |
| Heap usage | Custom allocator tracking or OS API | TBD | TBD |

**Important:** These are estimates for architecture planning. Actual measurements MUST be performed
in the implementation phase. No claim of measured memory footprint is made in this phase.

### Memory Efficiency Principles

1. **Avoid meaningless fixed large allocations** — size allocations to actual need (e.g., maxRegister)
2. **Prioritize actual-demand allocation** — don't allocate 4096 registers if function uses 10
3. **Avoid all coroutines having full large frames** — suspended coroutines with shallow stacks need less
4. **Avoid duplicating immutable data** — program/constants shared read-only across workers
5. **Reasonable frame reuse** — frame pool reduces allocation churn, but don't retain oversized frames
6. **Control allocator fragmentation** — varied allocation sizes can cause fragmentation; monitor
7. **Control worker context overhead** — per-worker context should be minimal; share read-only state
8. **Control scheduler queue overhead** — efficient queue data structures, avoid per-coroutine large allocations
9. **Control heap metadata overhead** — refcount headers, allocator metadata add up at scale
10. **Don't trade simplicity for marginal memory gains** — if a complex data structure saves 5% memory but doubles debug difficulty, prefer the simpler design

---

## C3 — ExecutionContext Ownership Matrix

### Current TLLVM Structure (from tllvm.h:104-117)

```c
typedef struct {
    TLLProgram *program;           // read-only, shareable
    TLLFrame **callStack;          // mutable, per-execution
    int callStackSize;             // mutable, per-execution
    int callStackCapacity;         // mutable, per-execution
    TLLValue *globals;             // shared mutable
    int globalCount;               // shared (effectively immutable after load)
    int invokeTargetStackSize;     // mutable, per-execution
    TLLCoroutine **coroutines;     // scheduler state (shared or per-context TBD)
    int coroutineCount;            // scheduler state
    int coroutineCapacity;         // scheduler state
    int currentCoroutine;          // mutable, per-execution
} TLLVM;
```

### Ownership Matrix

| Field | Current Owner | Proposed Owner | Shared? | Read By | Write By | Thread Safe? | Synchronization | Lifetime | Migration Allowed? |
|-------|--------------|----------------|---------|---------|---------|-------------|-----------------|----------|---------------------|
| `program` | TLLVM | Global/Shared (read-only) | Yes (read) | All workers/contexts | None after load | ✅ (immutable) | None | Process | No (shared) |
| `callStack` | TLLVM | ExecutionContext (per-worker) | No | Owner worker only | Owner worker only | ✅ (thread-local) | None | Worker | No (per-worker) |
| `callStackSize` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Worker | No |
| `callStackCapacity` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Worker | No |
| `globals` | TLLVM | Shared Global State | Yes | All workers | All workers (mutable) | ❌ (needs sync) | Fine-grained model (C6) | Process | No (shared) |
| `globalCount` | TLLVM | Shared Global State | Yes | All workers | None after load (immutable) | ✅ | None | Process | No |
| `invokeTargetStackSize` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Worker/invocation | No |
| `coroutines` | TLLVM | Scheduler (shared or per-worker TBD by C7) | TBD | Scheduler | Scheduler | TBD | Scheduler model (C7) | Process/scheduler | TBD |
| `coroutineCount` | TLLVM | Scheduler | TBD | Scheduler | Scheduler | TBD | Scheduler model | Process | TBD |
| `coroutineCapacity` | TLLVM | Scheduler | TBD | Scheduler | Scheduler | TBD | Scheduler model | Process | TBD |
| `currentCoroutine` | TLLVM | ExecutionContext | No | Owner worker | Owner worker | ✅ | None | Worker | No |

### TLLCoroutine Field Ownership (from tllvm.h:86-101)

| Field | Owner | Shared? | Synchronization | Notes |
|-------|-------|---------|-----------------|-------|
| `callStack` | Coroutine (per-coroutine) | No (owned by coroutine) | Coroutine lifecycle | Moves with coroutine if migration allowed |
| `callStackSize/Capacity` | Coroutine | No | None | |
| `state` | Coroutine | TBD (scheduler accesses) | Scheduler model (C7) | 0=alive, 2=dead |
| `result` | Coroutine | No | None | Return value |
| `invokeTargetStackSize` | Coroutine | No | None | |
| `wakeTime` | Coroutine | TBD (scheduler reads for timer) | Scheduler model | 0=runnable, >0=sleeping |
| `waitingFd` | Coroutine | TBD (IO reactor reads) | Scheduler/IO model | 0=not waiting |
| `waitingEvents` | Coroutine | TBD | Scheduler/IO model | 1=READ, 2=WRITE, 4=ERROR |
| `waitingChannel` | Coroutine | TBD | Scheduler model | NULL=not waiting |
| `waitDeadline` | Coroutine | TBD | Scheduler model | 0=no timeout |
| `waitResult` | Coroutine | No (written by scheduler, read by coroutine) | Scheduler model | 1=ready, 0=timeout |

### Execution Context Ownership Contract v1

**Principle:** Every mutable field has exactly one owner. Shared mutable fields have explicit synchronization.
No field is shared "by convenience."

**ExecutionContext (per-worker) contains:**
- `callStack` / `callStackSize` / `callStackCapacity`
- `currentCoroutine`
- `invokeTargetStackSize`
- Worker-local scheduler state (if per-worker queues in C7)

**Shared (read-only) contains:**
- `program` (TLLProgram*, immutable after load)
- `globalCount` (immutable after load)
- Function/constant tables (part of program)

**Shared (mutable, synchronized) contains:**
- `globals` (TLLValue*, synchronized per C6 model)
- Coroutine table / scheduler state (per C7 model)
- Heap objects (per C5 atomic ownership model)

---

## C4 — Multi-Worker Concurrency Model

### Current Reality

| Component | Current Behavior |
|-----------|-----------------|
| Worker count | 8 (hardcoded in `init_worker_pool()`) |
| Worker creation | Windows: `CreateThread()`; POSIX: `pthread_create()` |
| Task queue | Global queue protected by `g_queue_lock` |
| VM invocation | `tll_vm_invoke()` wrapped in `g_vm_lock` (global CRITICAL_SECTION/pthread_mutex) |
| VM instance | Single global TLLVM shared by all workers |
| Actual parallelism | **NONE for VM execution** — all workers serialize on g_vm_lock |

**Key finding:** 8 workers do NOT achieve 8-way VM execution. They achieve 8-way IO/accept parallelism,
but VM execution is fully serialized by `g_vm_lock`.

### Model Comparison

| Criterion | Model A: Global VM Lock | Model B: One VM per Worker | Model C: Shared Program + Per-Worker ExecutionContext | Model D: Actor/Ownership-Based |
|-----------|-------------------------|----------------------------|-------------------------------------------------------|--------------------------------|
| **Program sharing** | Shared (1 VM) | Duplicated (N VMs) | Shared read-only | Shared read-only |
| **Globals** | Shared (1 set) | Per-VM (N sets, inconsistent) | Shared (synchronized) | Per-actor (message passing) |
| **Heap** | Shared (1 heap) | Per-VM (N heaps) | Shared (atomic refcount) | Per-actor (ownership transfer) |
| **Coroutine migration** | N/A (1 VM) | No (fixed to VM) | Yes (scheduler can migrate) | Yes (actor migration) |
| **Frame migration** | N/A | No | Yes (with coroutine) | Yes (with actor) |
| **Worker context independence** | None (all share) | Full (independent VMs) | Full (per-worker ExecutionContext) | Full (per-actor) |
| **Native call handling** | Shared (serialized) | Per-VM (can parallelize) | Per-worker (can parallelize) | Per-actor |
| **Blocking syscall handling** | Blocks all VM execution | Blocks only that VM | Blocks only that worker | Blocks only that actor |
| **Memory overhead** | Low (1 VM) | High (N full VMs) | Medium (shared program + per-worker context) | Medium-High (per-actor state) |
| **Implementation complexity** | Low (current) | Medium | Medium-High | High |
| **True parallelism** | ❌ None | ✅ N-way (but isolated) | ✅ N-way (shared state) | ✅ N-way (message passing) |
| **Global consistency** | ✅ (1 set) | ❌ (N inconsistent sets) | ✅ (synchronized shared) | ✅ (message passing) |
| **Backward compatibility** | ✅ (current) | ❌ (breaks shared globals) | ✅ (preserves shared globals semantics) | ⚠️ (changes concurrency model) |

### Recommended Model: **Model C — Shared Program + Per-Worker ExecutionContext**

**Rationale:**
1. **Preserves shared globals semantics** — TLL programs expect globals to be shared across all execution; Model B would break this
2. **True parallelism** — each worker has independent ExecutionContext (callStack, currentCoroutine, frame state), so VM execution can proceed in parallel without global lock
3. **Shared read-only program** — functions, constants, bytecode are immutable and shared across all workers, saving memory
4. **Coroutine migration possible** — scheduler can migrate coroutines between workers for load balancing (if designed in C7)
5. **Native calls / blocking syscalls** — only block the calling worker, not all workers
6. **Backward compatible** — preserves all existing TLL semantics; globals remain shared (with synchronization per C6)
7. **Incremental implementation path** — can start with per-worker ExecutionContext + coarse global state lock, then refine

**Architecture:**

```
                    TLL Program (read-only, shared)
                   ┌──────────────────────────────┐
                   │ functions, constants, bytecode │
                   └──────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
  ┌───────▼───────┐      ┌───────▼───────┐      ┌───────▼───────┐
  │ ExecutionCtx 0 │      │ ExecutionCtx 1 │      │ ExecutionCtx N │
  │ Worker 0       │      │ Worker 1       │      │ Worker N       │
  │                │      │                │      │                │
  │ callStack      │      │ callStack      │      │ callStack      │
  │ currentCoroutine│     │ currentCoroutine│     │ currentCoroutine│
  │ frame state    │      │ frame state    │      │ frame state    │
  │ invokeTarget   │      │ invokeTarget   │      │ invokeTarget   │
  └───────┬───────┘      └───────┬───────┘      └───────┬───────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                   ┌──────────────▼──────────────┐
                   │    Shared Mutable State      │
                   │                               │
                   │  globals (C6 sync model)     │
                   │  heap (C5 atomic refcount)   │
                   │  scheduler (C7 model)         │
                   │  IO reactor (C7/C8)          │
                   └──────────────────────────────┘
```

**Key design decisions:**
- `TLLVM` struct is split: read-only program becomes global shared; mutable execution state moves to `TLLEXecutionContext` (per-worker)
- Workers pull tasks from global queue (existing `g_queue_lock` can remain, or be replaced with lock-free queue)
- Each worker creates/uses its own `TLLEXecutionContext` for VM execution
- `g_vm_lock` is eliminated; replaced by fine-grained synchronization on shared mutable state (globals per C6, heap per C5, scheduler per C7)

---

## C5 — Heap Ownership / Atomic RefCount

### Current Reality

| Component | Location | Current Behavior |
|-----------|----------|-----------------|
| `TLLArray.refCount` | `tll_runtime.h:93` | `int refCount` — plain int, non-atomic |
| `TLLMap.refCount` | `tll_runtime.h:109` | `int refCount` — plain int |
| `TLLUpvalue.refCount` | `tll_runtime.h:117` | `int refCount` — plain int |
| `TLLClosureEnv.refCount` | `tll_runtime.h:127` | `int refCount` — plain int |
| String refCount | `tll_runtime.h:67-69` | Hidden int header before data — plain int |
| `tll_value_incref()` | `runtime/value.c` | Direct `obj->refCount++` — non-atomic |
| `tll_value_free()` | `runtime/value.c` | Direct `if (--obj->refCount == 0) destroy` — non-atomic |

**Data race scenario under Model C (multi-worker):**
```
Worker A: tll_value_incref(obj)   → read refCount → increment → write
Worker B: tll_value_free(obj)     → read refCount → decrement → write
                                    → concurrent read-modify-write → LOST UPDATE
```

### Recommended Baseline: Atomic RefCount (PENDING IMPLEMENTATION EVIDENCE)

With Model C (shared heap across workers), reference counts SHOULD be atomic to prevent data races. This is the **recommended baseline**, not a proven final model. Must be validated with microbenchmarks, concurrency stress tests, and ThreadSanitizer before finalization.

### Atomic Memory Ordering (Recommended Baseline — PENDING VALIDATION)

| Operation | Memory Order | Rationale |
|-----------|-------------|-----------|
| **retain (incref)** | `memory_order_relaxed` | Retain only needs to increment; if we hold a reference, the object can't be freed concurrently. Relaxed is sufficient for counting. |
| **release (decref)** | `memory_order_acq_rel` (or `memory_order_release` on decrement + `memory_order_acquire` on zero-check) | Decrement must synchronize with the final zero-check to ensure all writes to the object are visible before destruction. `acq_rel` provides this. |
| **zero transition check** | `memory_order_acquire` (implied by acq_rel decrement) | When refCount reaches zero, the thread performing the final decrement must see all prior writes to the object before destroying it. |

**Cross-platform implementation:**
- Windows MSVC: `_InterlockedIncrement()` / `_InterlockedDecrement()` (built-in atomics)
- POSIX (gcc/clang): `__atomic_add_fetch()` / `__atomic_sub_fetch()` with `__ATOMIC_RELAXED` / `__ATOMIC_ACQ_REL`
- Or C11 `<stdatomic.h>`: `atomic_fetch_add_explicit()` / `atomic_fetch_sub_explicit()` (if C11 available)

**Recommended abstraction:**
```c
// In tll_runtime.h (design only, NOT implementation in this phase)
typedef struct { int refCount; } TLLAtomicRefCount;  // or use C11 atomic_int

#define TLL_REFCOUNT_INCR(obj)   atomic_increment(&(obj)->refCount)
#define TLL_REFCOUNT_DECR(obj)   atomic_decrement(&(obj)->refCount)  // returns new value
```

### Destruction Synchronization

**Problem:** When refCount reaches zero, who destroys the object?
- The thread that performs the final decrement (sees zero) is responsible for destruction
- `memory_order_acq_rel` on decrement ensures all prior writes to the object are visible to the destroying thread
- No additional lock needed for destruction

**ABA / Reuse Considerations:**
- TLL heap objects are not currently recycled from a free list (destroyed → free())
- No ABA problem from object reuse (memory is freed, not cached)
- If future object pooling is introduced, must handle ABA with either: tagged pointers, hazard pointers, or deferred reclamation

### Object Publication

**Problem:** How does a newly created object become visible to other workers?
- Object creation: `calloc()` → initialize fields → `refCount = 1` → publish (store in shared location)
- Publication must use `memory_order_release` to ensure initialization writes are visible before the pointer is published
- Reader must use `memory_order_acquire` when loading the published pointer
- This is handled by the synchronization mechanism of the shared container (globals per C6, scheduler queues per C7)

### B11 Ownership Compatibility

**Critical:** P2-01-B11-R1 ownership semantics MUST NOT regress.

| B11 Semantic | Atomic RefCount Impact | Compatibility |
|-------------|------------------------|---------------|
| Parameter ownership (caller incref, callee owns, callee releases) | Same semantics, just atomic increment/decrement | ✅ Compatible |
| Return ownership (callee incref return, then cleanup params, caller owns return) | Same order, atomic operations | ✅ Compatible |
| Assignment (`tll_assign`: incref new → free old → store) | Same order, atomic operations | ✅ Compatible |
| Aliasing (multiple references to same object) | Atomic refCount correctly tracks all references | ✅ Compatible |
| Array element ownership | Atomic operations on array elements' refCounts | ✅ Compatible |
| Map value ownership | Atomic operations on map values' refCounts | ✅ Compatible |
| Closure/env/upvalue ownership | Atomic operations on closure/env/upvalue refCounts | ✅ Compatible |

**Key point:** Atomic refCount is a drop-in replacement for plain int refCount. It does not change
ownership semantics — it only makes existing semantics safe under concurrent access. B11 ownership
contract is fully preserved.

---

## C6 — Global State Model

### Current Reality

| Component | Location | Current Behavior |
|-----------|----------|-----------------|
| `TLLVM.globals` | `tllvm.h:109` | `TLLValue *globals` — shared array, allocated at VM creation |
| `TLLVM.globalCount` | `tllvm.h:110` | `int globalCount` — set at program load, effectively immutable |
| OP_LOAD_GLOBAL (40) | `vm.c` | Direct read from `globals[idx]` — no synchronization |
| OP_STORE_GLOBAL (41) | `vm.c` | Direct write to `globals[idx]` — no synchronization (but g_vm_lock serializes all access) |
| Protection | — | Only `g_vm_lock` (global VM lock) — removed in Model C |

### Global Classification

| Global Type | Description | Example | Synchronization Need |
|-------------|-------------|---------|---------------------|
| **Immutable** | Set once at program load, never modified | Function references, constant tables, `globalCount` | None (read-only) |
| **Read-mostly** | Written rarely (initialization), read frequently | Configuration values, cached lookups | RCU or write-side lock + read-side atomic |
| **Mutable** | Frequently read and written | Program variables stored as globals | Fine-grained synchronization |
| **Per-Worker** | Logically global but actually worker-local | Worker-specific caches, thread-local storage | None (thread-local) |
| **Shared Heap** | Globals that reference heap objects | Global array/map/string variables | Atomic refCount (C5) + value synchronization |

### Model Comparison

| Criterion | Global Lock | RW Lock | Atomic Per-Element | Copy-on-Write | Per-Worker (TLS) |
|-----------|-------------|---------|---------------------|----------------|-------------------|
| **Read contention** | High (all readers block) | Low (readers share) | None (per-element) | Low (read atomic pointer) | None (thread-local) |
| **Write contention** | High | Medium (writer exclusive) | Low (only that element) | Medium (copy + publish) | None |
| **Implementation complexity** | Low | Medium | Medium | High | Low |
| **Memory overhead** | Low | Low | Medium (atomic per element) | High (copies) | Medium (per-worker copies) |
| **Consistency model** | Strong | Strong | Per-element strong | Eventual (snapshot) | Weak (per-worker) |
| **Backward compatibility** | ✅ | ✅ | ✅ | ⚠️ (snapshot semantics) | ❌ (breaks shared globals) |
| **Debug difficulty** | Low | Low | Medium | High | Medium |

### Recommended Model: **Hybrid — Atomic Per-Element for Mutable Globals + Immutable for Read-Only**

**Rationale:**
1. **Most globals are actually immutable after initialization** — function references, constants, etc. These need no synchronization.
2. **Mutable globals are typically few** — programs that use mutable globals usually have a small number. Per-element atomic operations avoid global lock contention.
3. **TLLValue is 24 bytes (measured)** — cannot be atomically loaded/stored on most platforms; this justifies per-element synchronization (mutex stripe) rather than naive atomic load/store.
4. **Backward compatible** — preserves shared globals semantics; programs see consistent global state.
5. **Simple to implement and debug** — no complex RCU or copy-on-write machinery.

**Design:**
- `globals` array remains shared
- Each `globals[idx]` is a `TLLValue` (24 bytes, measured)
- **Read (OP_LOAD_GLOBAL):** atomic load of `globals[idx]` with `memory_order_acquire`
- **Write (OP_STORE_GLOBAL):**
  1. incref(new value) (atomic, C5)
  2. atomic store new value to `globals[idx]` with `memory_order_release`
  3. decref(old value) (atomic, C5)
- This follows the same `tll_assign` ownership pattern (incref new → store → decref old), applied atomically per element

**Platform note:** 16-byte atomic store/load may not be available on all platforms. Fallback options:
- Per-element spinlock (small `char lock` per global, or a small array of spinlocks covering ranges of globals)
- Global-level seqlock for writes (readers retry if sequence changed)
- For initial implementation: a small array of mutexes (e.g., 16 mutexes, global[idx] protected by mutex[idx % 16]) — reduces contention vs single global lock, simple and portable

**Recommended initial implementation:** 16-mutex stripe array (simple, portable, low contention for typical workloads). Can later optimize to per-element atomic if profiling shows mutex contention.

---

## C7 — Scheduler Model

### Current Reality

| Component | Location | Current Behavior |
|-----------|----------|-----------------|
| Scheduler location | `vm.c:494-680` | `coroutine_yield()` — called on yield/sleep/wait |
| Scheduling algorithm | `vm.c:537` | Round-robin: `idx = (old + 1 + i) % coroutineCount` |
| Runnable detection | `vm.c:536-548` | `state != 2 && wakeTime == 0 && waitingFd == 0 && waitingChannel == NULL` |
| Timer wakeup | `vm.c:517-531` | Scan all coroutines, wake if `wakeTime <= now` |
| IO wait | `vm.c:568-645` | Collect all `waitingFd`, call `select()` with timeout from earliest sleeper |
| Channel wait | `tllvm.h:97` | `waitingChannel` pointer, woken by `coroutine_wake_channel()` |
| Pass structure | `vm.c:515` | 2-pass: pass 0 find runnable, pass 1 after IO/timer wait |
| Self-exclusion | `vm.c:546` | Pass 0 excludes self (P0-COMPILER-06 BUG-A fix) |
| Worker model | — | Single VM thread; no multi-worker scheduler |

### Coroutine States

| State | Meaning | Current Implementation |
|-------|---------|----------------------|
| **Runnable** | Ready to execute | `state=0, wakeTime=0, waitingFd=0, waitingChannel=NULL` |
| **Running** | Currently executing | Implicit (currentCoroutine index) |
| **Sleeping** | Waiting for timer | `wakeTime > 0` (ms timestamp) |
| **Waiting IO** | Waiting for fd readable/writable | `waitingFd > 0, waitingEvents` set |
| **Waiting Channel** | Waiting for channel send | `waitingChannel != NULL` |
| **Completed/Dead** | Finished execution | `state == 2` |
| **Cancelled** | — | Not currently implemented |

### Design Decisions

#### Runnable Queue Ownership

**Recommended: Per-Worker Local Queue + Global Queue (work-stealing)**

- Each worker has a local runnable queue (LIFO or deque)
- Global queue for coroutines created from non-worker contexts (e.g., main thread spawning)
- Workers first check local queue, then global queue, then steal from other workers
- Reduces contention on a single global runnable queue
- Coroutine migration IS allowed (work-stealing moves coroutines between workers)

#### Worker Local Queue

- **Yes** — each worker has a local runnable queue to avoid global contention
- Local queue operations are lock-free (only owner accesses)
- Steal operations require synchronization (CAS or lock on victim's queue)

#### Global Queue

- **Yes** — for coroutines spawned from outside worker pool (main thread, IO reactor thread)
- Workers check global queue when local queue is empty
- Global queue can be lock-free (MPMC queue) or mutex-protected (low contention if workers prefer local)

#### Work Stealing (Phase D-3 Optimization — PENDING)

- **Phase D-3 optimization** — when a worker's local and global queues are empty, it steals from a random other worker
- Steal from the victim's queue tail (opposite end from victim's push/pop) to minimize contention
- Work stealing provides automatic load balancing

#### Coroutine Migration

- **Allowed** — coroutines can migrate between workers via work-stealing
- Migration requires: coroutine's callStack, state, all fields move with it (they're part of TLLCoroutine struct)
- No worker-specific state is stored in the coroutine (design invariant)
- Frames migrate with the coroutine's callStack

#### Wakeup Responsibility

- **Timer wakeup:** Dedicated timer thread or each worker checks timers on scheduler pass
  - Recommended: each worker checks expired timers when it runs out of runnable work; no dedicated timer thread needed
  - Timer data structure: min-heap or simple sorted list keyed by wakeTime
- **IO wakeup:** Dedicated IO reactor thread (or each worker has its own epoll/IOCP)
  - Recommended: shared IO reactor thread that calls select()/epoll()/IOCP and pushes ready coroutines to global queue
  - This preserves P0-RUNTIME-08 timed-wait semantics (waitReadWithTimeout / waitWriteWithTimeout)
- **Channel wakeup:** `coroutine_wake_channel()` pushes waiting coroutines to runnable queue
  - Called from builtin `coroutine.wakeChannel(channelMap)`
  - Must prevent duplicate wakeups (coroutine already runnable)

#### Duplicate Wakeup Prevention

**Invariant: `one logical wakeup -> at most one runnable transition`**

- Each coroutine has an atomic state field
- Wakeup: CAS state from WAITING to RUNNABLE; if CAS fails (already runnable), skip
- This prevents: timer fires + IO ready simultaneously → coroutine woken twice → duplicate execution
- Atomic state with `memory_order_acq_rel`

#### IO Wakeup → Runnable

- IO reactor detects fd ready → finds coroutine waiting on that fd → sets `waitResult = 1` → CAS state to RUNNABLE → push to global runnable queue
- Deadline expiry: reactor/scheduler detects waitDeadline passed → sets `waitResult = 0` → CAS state to RUNNABLE → push to queue
- Coroutine resumes, reads `waitResult` to determine ready vs timeout (P0-RUNTIME-08 semantics preserved)

#### Timer Scheduling

- Min-heap keyed by `wakeTime` (ms timestamp)
- When worker runs out of runnable work, peek at min-heap; if top expired, pop and wake
- If no expired timers and no runnable coroutines, worker can park (wait on condition variable) until next timer or IO wakeup
- Shutdown: drain all queues, wake all waiting coroutines with cancellation status

#### Shutdown / Drain

- Shutdown signal: atomic flag `shutdown_requested`
- Workers: finish current coroutine, check shutdown flag, if set: drain local queue (execute remaining), then exit
- IO reactor: stop accepting new IO, wake all waiting coroutines with shutdown/cancellation, exit
- Timer: cancel all pending timers, wake with cancellation
- Final: all workers exited, all coroutines completed/cancelled, VM can be freed

#### Cancellation

- **Not implemented in current TLL** — no OP_CANCEL or cancellation API
- P2-01-C does NOT add cancellation (out of scope)
- Shutdown uses "drain and exit" rather than forcible cancellation
- If cancellation is needed in future, requires new opcode + governance decision (C8)

#### Worker Crash / Abnormal Exit

- **Not currently handled** — if a worker crashes (segfault), whole process crashes
- P2-01-C does NOT add fault isolation (out of scope; would require process isolation or SEH)
- Best practice: workers should not crash; all TLL-level errors are exceptions (handled by try/catch)
- Native calls that could crash should be audited (future hardening)

### P0-RUNTIME-08 Compatibility

**Critical:** P0-RUNTIME-08 network/IO timeout semantics MUST NOT break.

| P0-RUNTIME-08 Capability | Preservation Strategy |
|---------------------------|----------------------|
| `coroutine.waitReadWithTimeout(fd, timeout)` | IO reactor handles deadline; `waitResult=1` ready, `waitResult=0` timeout |
| `coroutine.waitWriteWithTimeout(fd, timeout)` | Same as above, for write events |
| `tcp.connectNonBlocking()` + `waitWriteWithTimeout` | Non-blocking connect → waitWrite → SO_ERROR check (unchanged) |
| Handshake timeout (2s) | Application-level timeout using waitReadWithTimeout (unchanged) |
| Bounded retry (5 attempts, 200/400/600/800 backoff) | Application-level in p2p.tll (unchanged) |
| `waitDeadline` / `waitResult` fields | Preserved in TLLCoroutine struct; scheduler/reactor uses them |

---

## C8 — Opcode Governance

### Current Reality

| Source | Version | Status | Opcode Range | Count |
|--------|---------|--------|--------------|-------|
| `spec/OPCODES.md` | v1.1 | **FROZEN** | 0-45 | 46 |
| `host/c/tllvm.h` | Implementation | Active | 0-62 | 63 |
| `runtime/vm.tll` | Semantic VM | Stale | 0-45 (verified: no 46-62) | 46 |

### Opcodes 46-62 Classification

| Range | Opcodes | Origin | Category |
|-------|---------|--------|----------|
| 46-53 | BAND, BOR, BXOR, BNOT, SHL, SHR, ROTR, ROTL | P0-15 (blockchain stress test gap) | Arithmetic/Logic extension |
| 54-56 | SPAWN, YIELD, SLEEP | P0-15.14/15 (VM-level coroutine) | Concurrency extension |
| 57-59 | WAIT_READ, WAIT_WRITE, WAIT_CHANNEL | P0-15.16 (IO-aware scheduler) | IO/Concurrency extension |
| 60 | MOV | P0-COMPILER-02 (ternary/branch result unification) | Compiler support |
| 61-62 | CATCH_ENTER, FINALLY_END | Exception handling | Exception extension |

### Governance Decision Options

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A: v1.1 extension** | Declare 46-62 as "v1.1 runtime extension" outside frozen core | Minimal governance change; preserves frozen core | Vague version boundary; extension could grow indefinitely |
| **B: v1.2** | Promote 46-62 to new spec version v1.2, properly documented | Clean version boundary; spec catches up with implementation | Requires full spec documentation for 46-62; formal version process |
| **C: runtime-private opcode** | Declare 46-62 as runtime-private (not part of language spec), implementation detail | Clean separation: language spec vs runtime implementation | Semantic VM can't implement them (they're "private"); ambiguity for native target |
| **D: Historical but must formalize** | Acknowledge 46-62 were added without governance, now formally纳入 spec | Honest about history; forces proper documentation | Requires retroactive governance process |
| **E: Other** | Hybrid or alternative model | Flexible | Needs definition |

### Recommended Decision: **B + D Hybrid — Formally Promote 46-62 to v1.2 with Retroactive Documentation**

**Rationale:**
1. **46-62 are already implemented and tested** — they're not hypothetical; coroutine, IO, bitwise, exception opcodes are actively used by existing tests and programs
2. **Semantic VM needs to implement them** — if they're "runtime-private" (Option C), the Semantic VM (vm.tll) can't implement them, breaking the "vm.tll is canonical semantic authority" principle
3. **Clean version boundary is good governance** — v1.1 = frozen core (0-45), v1.2 = concurrency/IO/bitwise/exception extension (46-62). Future extensions go to v1.3+.
4. **Honest about history** — document that 46-62 were added during P0-15/P0-COMPILER phases without formal version bump; now formally ratified as v1.2
5. **P2-01-C does NOT add new opcodes** — this decision only formalizes existing 46-62. Any future new opcode requires explicit architecture decision + version bump.

**Formal Governance Decision:**

```
TLL Opcode Specification Governance:

- v1.1 (FROZEN): Opcodes 0-45 — core language (arithmetic, control flow, functions,
  arrays, maps, closures, basic exception THROW/TRY)
- v1.2 (PROPOSED EXTENSION — PENDING FORMAL GOVERNANCE): Opcodes 46-62 — runtime extension
  scheduler, MOV, structured exception CATCH/FINALLY)
  - These were implemented during P0-15, P0-15.14/15/16, P0-COMPILER-02 phases
  - Proposed as v1.2 extension during P2-01-C Phase C; formal ratification requires Specification/Governance process (architecture agent cannot unilaterally ratify language versions)
  - Semantic VM (vm.tll) MUST be updated to implement v1.2 opcodes (GAP-C2 resolution)
- Future opcodes: Must go through formal architecture decision + version bump (v1.3+)
- Frozen v1.1 semantics: MUST NOT be silently modified. Any change to v1.1 opcode
  semantics requires new version.
```

**Action items (future phases, NOT this phase):**
- Update `spec/OPCODES.md` to document v1.2 opcodes 46-62 (with operand format and semantics)
- Update `runtime/vm.tll` to implement v1.2 opcodes (resolve GAP-C2)
- Add version metadata to bytecode format (so VM can check compatibility)

---

## C9 — Semantic VM Convergence

### Current Reality

| Component | Status | Opcodes Implemented |
|-----------|--------|---------------------|
| `spec/OPCODES.md` | v1.1 FROZEN | 0-45 (documented) |
| `host/c/vm.c` (Native VM) | Active implementation | 0-62 (full implementation) |
| `runtime/vm.tll` (Semantic VM) | Stale | 0-45 only (verified: no OP_SPAWN/YIELD/SLEEP/WAIT_READ/WRITE/MOV/BAND) |
| `compiler/codegen.tll` | Active | Generates 0-62 (including coroutine/IO/MOV opcodes) |

### Canonical Semantic Authority

**Question:** Which is the canonical semantic authority?

**Answer (per ARCHITECTURE.md):** `runtime/vm.tll` is the "executable language specification" and "Spec is the sole semantic authority."

**Problem:** `vm.tll` does not implement 46-62, but the Native VM (`vm.c`) and compiler (`codegen.tll`) do. This means:
- For opcodes 0-45: `vm.tll` is authoritative, `vm.c` must match
- For opcodes 46-62: `vm.tll` has no implementation, so `vm.c` is de facto authoritative (but this violates the governance principle)

### Convergence Strategy

**Recommended: Update Semantic VM to implement v1.2 opcodes (resolve GAP-C2)**

| Capability | Native VM (vm.c) | Semantic VM (vm.tll) Target | Spec Authority |
|------------|-------------------|-------------------------------|----------------|
| Opcodes 0-45 | ✅ Implemented | ✅ Already implemented | spec/OPCODES.md v1.1 |
| Bitwise 46-53 | ✅ Implemented | ❌ Need to add | spec/OPCODES.md v1.2 (after C8 update) |
| Coroutine 54-56 | ✅ Implemented | ❌ Need to add | spec/OPCODES.md v1.2 |
| IO-aware 57-59 | ✅ Implemented | ❌ Need to add (may need IO primitives in vm.tll) | spec/OPCODES.md v1.2 |
| MOV 60 | ✅ Implemented | ❌ Need to add | spec/OPCODES.md v1.2 |
| Exception 61-62 | ✅ Implemented | ❌ Need to add | spec/OPCODES.md v1.2 |

### Implementation Notes (future phase)

- **Bitwise (46-53):** Straightforward to add to vm.tll — simple arithmetic operations
- **MOV (60):** Straightforward — register copy
- **Exception (61-62):** CATCH_ENTER clears exception_pending; FINALLY_END rethrows if pending. Requires exception state tracking in vm.tll.
- **Coroutine (54-56):** SPAWN creates new coroutine; YIELD switches; SLEEP sets wakeTime. Requires coroutine scheduler in vm.tll (can be simplified — single-threaded cooperative scheduler)
- **IO-aware (57-59):** WAIT_READ/WRITE/CHANNEL require IO primitives. vm.tll may need to mock/simplify IO (e.g., use a simulated event loop) or use host IO builtins. This is the hardest to converge.

### Classification: Host-Runtime-Only vs Semantic

**Decision:** All v1.2 opcodes should be implemented in Semantic VM for full convergence.
However, IO-aware opcodes (57-59) may require host IO support in the Semantic VM environment.
If full Semantic VM implementation of IO is impractical, document as "host-runtime-assisted" with
explicit architecture decision — but this should be a last resort, not the default.

**Current status:** GAP-C2 is CONFIRMED. Semantic VM convergence is a future implementation task,
not resolved in this architecture phase.

---

## C10 — Performance Contract

### Historical Baseline (from P0-9 report, NOT current measurement)

| Workload | Historical Baseline | Notes |
|----------|---------------------|-------|
| Function call | ~9,790 calls/sec | Single-threaded, global lock era |
| Loop | ~3,144,650 iterations/sec | Baseline for comparison |
| Map update | ~81,633 updates/sec | |
| Event | ~9,615 events/sec | |

**Important:** These are historical baseline numbers from P0-9. They are NOT current measurements.
P2-01-C implementation phase MUST re-measure all benchmarks at the new commit.

### Performance Metrics to Measure

| Metric | Definition | Measurement Method |
|--------|-----------|-------------------|
| **Function calls/sec** | Number of empty function calls per second | `benchmarks/high_frame_rate.tll` Test 1 |
| **Coroutine create/sec** | Number of coroutine spawns per second | New benchmark (future) |
| **Coroutine resume/sec** | Number of yield/resume cycles per second | New benchmark (future) |
| **Coroutine switch/sec** | Scheduler context switch rate | New benchmark (future) |
| **Scheduler throughput** | Coroutines scheduled per second (with N runnable) | New benchmark (future) |
| **IO wakeup throughput** | IO events → coroutine wakeups per second | New benchmark (future) |
| **Worker scaling** | Speedup as worker count increases | 1/2/4/8 worker comparison |
| **Heap retain/release throughput** | Atomic incref/decref operations per second | New benchmark (future) |
| **Global state contention** | Overhead from concurrent global reads/writes | New benchmark (future) |

### Worker Scaling Plan

| Worker Count | Expected Speedup (ideal) | Contention Factors |
|-------------|--------------------------|-------------------|
| 1 | 1x (baseline) | None |
| 2 | ~1.8-2.0x | Global state lock, heap atomic, scheduler queue |
| 4 | ~3.0-3.8x | Increased contention on shared state |
| 8 | ~5.0-7.0x | Diminishing returns from contention; Amdahl's law |

**Scalability metrics:**
- Speedup = (time with 1 worker) / (time with N workers)
- Efficiency = speedup / N
- Contention = 1 - efficiency (fraction of time lost to synchronization)
- CPU utilization = (busy time) / (wall time × N)
- Latency = average time for a single operation
- Tail latency = p99/p999 latency

### Performance Contract Principles

1. **No invented targets** — all targets based on measured baseline + realistic architecture
2. **No marketing numbers** — every claim has workload, platform, build mode, measurement method, raw result
3. **Regression gate** — define minimum acceptable performance before final test; if regression exceeds threshold, block merge
4. **Baseline comparison** — always compare against baseline (pre-P2-01-C) at same platform/build
5. **Single-threaded must not regress** — even if multi-worker improves, single-worker performance must not significantly degrade (overhead from atomic operations, etc.)
6. **Microbenchmarks ≠ real workload** — microbenchmarks show peak throughput; real workloads have mixed operations. Both should be measured.

---

## C11 — Memory Efficiency Contract

### Memory Efficiency Principles

1. **Avoid meaningless fixed large allocations** — don't allocate 4096 registers if function uses 10 (C1 Model B)
2. **Prioritize actual-demand allocation** — size allocations to computed need (maxRegister, localCount, etc.)
3. **Avoid all coroutines having full large frames** — suspended coroutines with shallow stacks need less; dynamic sizing helps
4. **Avoid duplicating immutable data** — program/constants/bytecode shared read-only across workers (C4 Model C)
5. **Reasonable frame reuse** — frame pool reduces allocation churn; but don't retain oversized frames in pool (reallocate if pooled frame too small for new function)
6. **Control allocator fragmentation** — varied allocation sizes can cause fragmentation; monitor with allocator stats; consider size-class allocator if fragmentation is severe
7. **Control worker context overhead** — per-worker ExecutionContext should be minimal (callStack pointer + few ints); shared read-only program avoids duplication
8. **Control scheduler queue overhead** — efficient queue data structures (deque for local, bounded MPMC for global); avoid per-coroutine large allocations in scheduler
9. **Control heap metadata overhead** — refcount headers (4 bytes per object), allocator metadata (16-32 bytes per allocation); these add up at 100K+ object scale
10. **Don't trade simplicity for marginal memory gains** — if a complex data structure saves 5% memory but doubles debug difficulty, prefer simpler design. Memory is optimization target, not correctness gate.

### Memory Efficiency vs Complexity Tradeoff

| Design Option | Memory Savings | Complexity Increase | Debug Difficulty | Recommendation |
|---------------|---------------|-------------------|-----------------|----------------|
| Dynamic frame (maxRegister) | High (10-50x typical) | Low | Low | ✅ RECOMMEND (C1) |
| Frame pool reuse | Medium (reduces alloc churn) | Low | Low | ✅ RECOMMEND (existing) |
| Size-class frame pool | Medium | Medium | Medium | ⚠️ Optional (if fragmentation issue) |
| Small frame + spill | Very High | Very High | Very High | ❌ NOT recommend (too complex) |
| Segmented frame | High | High | High | ❌ NOT recommend (too complex) |
| Per-worker frame pool | Low-Medium | Medium | Medium | ⚠️ Optional (if global pool contention) |
| Object pooling (heap) | Medium | High | High | ❌ NOT recommend (ABA issues, complexity) |

**Principle:** Prefer simple, high-impact optimizations (dynamic frame sizing, frame pool reuse)
over complex, marginal optimizations (spill, segmentation, object pooling).

---

## C12 — Evidence Contract

### Functional Evidence

| Category | Tests | Evidence Type |
|----------|-------|--------------|
| Existing regression | Native 20/20, Bytecode 20/20 | stdout + exit code |
| Cross-target conformance | 11/11 (tests 01-11) | Bytecode vs Native stdout/exit comparison |
| Coroutine | coroutine_stress_test (100K/10K×10/1K), coroutine_512, simple, 100 workers | PASS/FAIL + output |
| Network/IO | P0-RUNTIME-08 tests (timed_wait, handshake_blackhole, connect_timeout, p2p_retry_budget) | PASS/FAIL + timing evidence |
| Ownership | tests 11/12 (function argument, argument return) | refcount instrumentation + PASS/FAIL |
| FFI | Existing FFI tests | PASS/FAIL |
| Blockchain | bc_node, bc_multi, bc_delayed | 4-node 5-block sync result |

### Concurrency Evidence

| Worker Count | Tests | Evidence Type |
|-------------|-------|--------------|
| 1 worker | All functional tests | Baseline performance + correctness |
| 2 workers | Parallel execution tests, concurrent globals, concurrent heap | Correctness + speedup |
| 4 workers | Above + stress tests (many concurrent coroutines) | Correctness + scaling |
| 8 workers | Above + long-running stability test | Correctness + scaling + no deadlock |

**Concurrency test categories:**
- Independent parallel calls (no shared state) — verify true parallelism
- Shared-state workload (concurrent global reads/writes) — verify synchronization
- Concurrent retain/release (heap ownership) — verify atomic refcount
- Coroutine migration (work stealing) — verify coroutines can move between workers
- No lost wakeups (timer + IO mixed) — verify scheduler invariant
- No duplicate wakeups — verify atomic state transitions
- No deadlocks (stress with many workers + many coroutines) — long-running test

### Memory Evidence

| Scale | Measurements | Evidence Type |
|-------|-------------|--------------|
| 100 logical coroutines | RSS, heap usage, frame count, coroutine count | OS measurement + internal counters |
| 1,000 logical coroutines | Above + allocation count, peak memory | OS measurement + internal counters |
| 10,000 logical coroutines | Above + fragmentation estimate | OS measurement + internal counters |
| 100,000 logical coroutines | Above (if environment can execute) | OS measurement + documented limitation if not |

**Must distinguish:**
- Logical coroutine count (created)
- Simultaneously live execution contexts (active call stacks)
- Simultaneously live frames (on call stacks)

**Memory measurement method:**
- RSS: OS API (Windows `GetProcessMemoryInfo`, POSIX `getrusage`/`/proc/self/status`)
- Heap usage: custom allocator tracking or OS API
- Allocation count: instrument `malloc`/`calloc`/`realloc`/`free` (debug build)
- Peak memory: maximum RSS over test duration
- Frame count: internal counter (`g_frame_pool_size` + active frames)
- Coroutine count: `vm->coroutineCount`

### Performance Evidence

| Metric | Required Fields |
|--------|----------------|
| Baseline | commit SHA, platform, compiler, optimization flags, CPU/thread count, workload size, warmup, iterations, wall time, throughput |
| New result | Same fields as baseline, at new commit |
| Delta | Absolute delta, percentage delta, statistical significance (if multiple runs) |
| Environment | OS version, CPU model, RAM, compiler version, build mode (debug/release) |

### Evidence Integrity Rules

1. **No `|| true`** — test failures must propagate
2. **No fake pass** — `if failure: print("PASS")` is forbidden
3. **No estimated as measured** — estimates must be labeled "ESTIMATE"; measurements must be labeled "MEASURED"
4. **No hidden failures** — all test results reported, including failures
5. **If test unavailable** — document exact reason (environment limitation, missing dependency, etc.)
6. **Reproducibility** — every measurement includes enough info to reproduce (commit, platform, command, flags)

---

## C13 — Backward Compatibility Contract

### Protected Capabilities

| Capability | Source | Status | P2-01-C Impact | Compatibility Strategy |
|-----------|--------|--------|-----------------|----------------------|
| Coroutine 100K root cause fix | P0-RUNTIME-07 | SEALED | Scheduler changes could affect coroutine lifecycle | Preserve frame ownership fix; test with coroutine_stress_test |
| Frame double-free/UAF fix | P0-RUNTIME-07 | SEALED | Frame model changes (C1) could affect frame lifecycle | Preserve push_frame/pop_frame callStackSize sync; test with ownership tests |
| Windows Blockchain 5-block sync | P0-RUNTIME-08 | PASS WITH B-GAP | Scheduler/IO changes could affect network timing | Preserve waitReadWithTimeout/waitWriteWithTimeout semantics; test with bc_multi/bc_delayed |
| Timed-wait runtime capability | P0-RUNTIME-08 | PASS | IO model changes (C7) could affect timeout | Preserve waitDeadline/waitResult fields and semantics; test with timed_wait/handshake_blackhole |
| Non-blocking connect + bounded retry | P0-RUNTIME-08 | PASS | Transport layer not changed by P2-01-C | No impact (p2p.tll / builtin.c TCP unchanged) |
| Function argument/return ownership | P2-01-B11-R1 | PASS WITH B-GAP | Heap atomic refcount (C5) could affect ownership | Atomic refcount is drop-in replacement; preserve incref/release order; test with tests 11/12 |
| Native target 20/20 | P2-01-B12 | FINAL SEALED | Runtime changes could affect native target | Native target uses Shared Runtime Core; changes must be binary-compatible; test full native regression |
| Cross-target 11/11 | P2-01-B12-R1 | PASS | Semantic changes could break cross-target conformance | Preserve bytecode/native semantic equivalence; test cross-target conformance |
| ABI integrity | P2-01-B12-R2 | PASS | TLLValue/TLLArray/TLLMap struct changes could break ABI | DO NOT change struct field order/size; Binary Compatibility Guarantee in tll_runtime.h |
| Native ABI | builtin.c 0-222 | Active | New builtins not added in P2-01-C | No ABI changes; check-abi.sh continues to pass |

### Compatibility Invariants

1. **TLLValue binary layout unchanged** — type tag + union field order/size must remain identical
2. **TLLArray/TLLMap/TLLClosureEnv/TLLUpvalue struct layout unchanged** — refCount field position unchanged (atomic type may change size — must verify)
3. **Bytecode format unchanged** — opcode numbers, operand formats unchanged (no new opcodes in P2-01-C)
4. **Ownership semantics unchanged** — caller/callee/return/assignment ownership rules identical (B11)
5. **Coroutine semantics unchanged** — spawn/yield/sleep/wait behavior identical
6. **IO timeout semantics unchanged** — waitReadWithTimeout/waitWriteWithTimeout behavior identical (P0-RUNTIME-08)
7. **Native target output unchanged** — same TLL source produces same output in bytecode and native (cross-target conformance)
8. **Existing tests pass** — all existing regression tests continue to pass without modification

### If Compatibility Break is Necessary

- **Stop and report** — do not silently break compatibility
- **Document exact impact** — which capability, which tests, which behavior changes
- **Architecture decision required** — compatibility break needs explicit approval from architecture owner
- **Version bump** — if bytecode/ABI changes, require version metadata and migration path
- **P2-01-C should NOT require compatibility breaks** — all design decisions above are backward compatible

---

## C14 — Architecture Decision Matrix

| Domain | Current Reality | Options Considered | Recommended | Reason | Risk | Evidence Needed |
|--------|----------------|-------------------|-------------|--------|------|-----------------|
| **Frame** | Fixed 4096 registers, global pool | A: Fixed / B: Dynamic / C: Small+Spill / D: Size-class | **B: Dynamic (maxRegister)** | maxRegister already exists; 10-50x memory reduction; simple; preserves semantics | Compiler maxRegister accuracy | Full test suite + debug assertion |
| **Memory** | 4GB treated as hard ceiling (incorrect) | Hard constraint / Optimization target | **Optimization target / reference budget** | Correctness > memory; simplicity > marginal savings | None (correction of prior error) | N/A (governance correction) |
| **ExecutionContext** | TLLVM mixes program + execution state | Keep mixed / Split per-worker | **Split: shared program + per-worker ExecutionContext** | Enables true parallelism; preserves shared globals; incremental path | Migration of all TLLVM references | Full regression + concurrency tests |
| **Worker** | Global VM lock (no parallelism) | A: Global lock / B: One VM/worker / C: Shared prog+per-worker ctx / D: Actor | **C: Shared Program + Per-Worker ExecutionContext** | True parallelism; shared globals; backward compatible; coroutine migration | Shared state synchronization complexity | Concurrency tests + scaling benchmarks |
| **Heap** | Plain int refCount (non-atomic) | Keep non-atomic / Atomic refcount | **Atomic refCount (RECOMMENDED BASELINE — pending validation)** | Required for shared heap under multi-worker; drop-in replacement; B11 compatible | Atomic operation overhead; memory ordering correctness | Concurrency stress + ownership tests + ThreadSanitizer + microbenchmarks |
| **Global** | Shared globals, only g_vm_lock protection | Global lock / RW lock / Atomic per-element / COW / TLS | **Hybrid: atomic per-element for mutable + immutable for read-only** (initial: 16-mutex stripe) | Reduces contention; preserves semantics; simple; portable | Mutex stripe contention (low for typical workloads) | Concurrent global tests + benchmarks |
| **Scheduler** | Per-VM round-robin + select, single-threaded | Global queue / Per-worker local + work stealing | **Per-worker local queue + global queue (D-1/D-2 required); work stealing (D-3 optimization, PENDING)** | Reduces contention; load balancing; coroutine migration allowed; phased to avoid 10 variables at once | Work-stealing complexity; duplicate wakeup prevention | Scheduler stress + no-lost-wakeup tests |
| **IO** | select() in VM thread, single IO wait | Per-worker epoll / Shared IO reactor | **Shared IO reactor thread** + per-worker local queues | Preserves P0-RUNTIME-08 semantics; centralized IO; scalable | Reactor thread bottleneck (mitigated by batching) | IO stress + timeout tests |
| **Opcode** | Spec 0-45 frozen, runtime 0-62 (drift) | A: v1.1 ext / B: v1.2 / C: runtime-private / D: formalize | **B+D: Propose 46-62 as v1.2 extension (PENDING FORMAL GOVERNANCE)** | Clean version boundary; Semantic VM can implement; honest about history; architecture agent cannot unilaterally ratify | Requires spec documentation + vm.tll update (future) + formal governance process | Spec update + Semantic VM convergence |
| **Semantic VM** | vm.tll implements 0-45 only, runtime 0-62 | Leave as-is / Update vm.tll / Declare host-only | **Update vm.tll to implement v1.2** (future implementation) | vm.tll is canonical semantic authority; must match runtime | IO opcodes hardest to implement in vm.tll | Semantic VM tests + cross-validation |
| **Performance** | Historical baseline only, no contract | No targets / Define contract | **Define measurable contract + regression gate** | Prevents performance regression; enables data-driven decisions | Targets may be too optimistic (set based on measurement) | Benchmark suite + baseline measurement |
| **Evidence** | Ad-hoc test results | Continue ad-hoc / Formal evidence contract | **Formal evidence contract** (functional/concurrency/memory/performance) | Reproducibility; auditability; no fake passes | More work to produce evidence | Evidence documents + test automation |

---

## C15 — Final Architecture Decisions

### Explicit Architecture Choices

```
FRAME MODEL              = Dynamic Frame Sized by TLLFunction.maxRegister (Model B)
EXECUTION CONTEXT MODEL  = Shared Read-Only Program + Per-Worker TLLEXecutionContext (Model C)
WORKER MODEL             = Per-Worker ExecutionContext + Global Task Queue + Work-Stealing Scheduler
HEAP MODEL               = Shared Heap with Atomic RefCount (RECOMMENDED BASELINE — pending validation)
                           (relaxed incref, acq_rel decref — candidate memory ordering, must be validated)
GLOBAL STATE MODEL       = Hybrid: Immutable for read-only + Per-Element Synchronization for mutable
                           (initial implementation: 16-mutex stripe array)
SCHEDULER MODEL          = Per-Worker Local Runnable Queue + Global Queue (D-1/D-2 required)
                           + Atomic Coroutine State (duplicate wakeup prevention)
IO MODEL                 = Shared IO Reactor Thread (select/epoll/IOCP) + Per-Worker Local Queues
                           + Preserved P0-RUNTIME-08 timed-wait semantics
OPCODE GOVERNANCE MODEL  = v1.1 FROZEN (0-45) + v1.2 PROPOSED EXTENSION (46-62, PENDING FORMAL GOVERNANCE)
                           + Future opcodes require formal version bump
SEMANTIC VM MODEL        = Update runtime/vm.tll to implement v1.2 opcodes (future implementation)
                           + vm.tll remains canonical semantic authority
MEMORY EFFICIENCY MODEL  = Optimization target (NOT hard constraint)
                           + Dynamic frame sizing + frame pool reuse + shared read-only program
                           + Simplicity preferred over marginal memory gains
PERFORMANCE MODEL        = Measurable contract + regression gate + worker scaling (1/2/4/8)
                           + Historical baseline preserved + re-measure at implementation
EVIDENCE MODEL           = Formal contract: Functional + Concurrency + Memory + Performance
                           + No fake passes + reproducibility + all results reported
```

### Architecture Decisions Pending (require future evidence)

| Decision | Status | Evidence Needed |
|----------|--------|----------------|
| Exact frame pool reallocation policy (reuse vs reallocate on size mismatch) | PENDING | Implementation-phase measurement of frame size distribution |
| IO reactor scalability (single reactor vs per-worker epoll) | PENDING | Implementation-phase benchmark at high IO concurrency |
| Global state mutex stripe count (16 vs 32 vs 64) | PENDING | Implementation-phase contention benchmark |
| Work-stealing threshold (when to steal vs park) | PENDING | Implementation-phase scheduler benchmark |
| Atomic refcount performance overhead | PENDING | Implementation-phase microbenchmark (incref/decref throughput) |
| Semantic VM IO opcode implementation feasibility | PENDING | Implementation-phase prototyping of IO in vm.tll |

### No Architecture Decision Needed (already resolved by current design)

- Coroutine state fields (wakeTime, waitingFd, waitingEvents, waitingChannel, waitDeadline, waitResult) — preserved as-is
- Timer model (ms timestamp, wakeTime == 0 = runnable) — preserved
- Channel wakeup model (coroutine_wake_channel) — preserved
- Frame lifecycle (push_frame/pop_frame, callStackSize sync from P0-RUNTIME-07) — preserved
- Ownership model (B11: caller incref, callee owns, return incref-before-cleanup, tll_assign order) — preserved
- Native target ABI (TLLValue struct layout, builtin indices) — preserved (no changes)
- Bytecode format (opcode numbers, operand formats) — preserved (no new opcodes in P2-01-C)

---

## Self-Audit Checklist

- [x] No Runtime source modification
- [x] No VM implementation
- [x] No Frame Pool implementation
- [x] No atomic refcount implementation
- [x] No Scheduler rewrite
- [x] No g_vm_lock deletion
- [x] No new opcode
- [x] No test deletion
- [x] No test weakening
- [x] No `|| true`
- [x] No fake measurement
- [x] 4GB NOT treated as hard constraint (corrected to optimization target)
- [x] No claim of current RSS measurement
- [x] No claim of 100K full frame simultaneously live
- [x] No modification of P2-01-B11/B12
- [x] No modification of P0-RUNTIME-07/08
- [x] All architecture decisions explicitly stated
- [x] Pending decisions clearly labeled with evidence needed
- [x] Backward compatibility contract defined
- [x] Evidence contract defined

**Self-Audit Result: PASS**

---

**Phase C Status: ARCHITECTURE DESIGN COMPLETE**
**No source code modified. Pure architecture design.**
**Awaiting independent architecture audit before implementation phase.**

施工完成，等待架构师审查与于秋鸿博士最终验收。
