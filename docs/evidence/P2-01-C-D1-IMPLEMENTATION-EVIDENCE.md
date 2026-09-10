# P2-01-C-D1 High-Frame Runtime Implementation Evidence

**Status:** Construction complete, awaiting independent architecture audit  
**Baseline:** d33f8dfef8da7c037b590a061d8d191811dc28a0  
**Branch:** feature/P2-01-C-high-frame-runtime-construction  
**Date:** 2026-09-10

---

## 1. Implementation Summary

D-1 implements three core components of the High-Frame Runtime:

### 1.1 Dynamic Frame (C1)
- **Before:** Fixed 4096 registers per frame (96 KB per frame at 24 bytes/TLLValue)
- **After:** Dynamic allocation based on `TLLFunction.maxRegister + 1`
- **Changes:**
  - `frame_pool_acquire(int requiredRegCount)`: accepts required register count; pooled frames with insufficient capacity are reallocated
  - `create_frame()`: computes `requiredRegCount = (fn->maxRegister > 0 ? fn->maxRegister : 1) + 1`
  - `tll_vm_invoke()`: `INVOKE_RET_REG` changed from hardcoded 4095 to dynamic `parentFrame->registerCount - 1`

### 1.2 Per-Worker ExecutionContext (C3)
- **New structure:** `TLLExecutionContext` containing execution-local mutable state:
  - `callStack`, `callStackSize`, `callStackCapacity`
  - `currentCoroutine`
  - `invokeTargetStackSize`
- **TLLVM refactored:** execution-local fields moved into `ctx` field
- **Shared state preserved:** `program` (read-only), `globals`, `coroutines` (shared mutable, deferred to later phases)

### 1.3 Minimal Scheduler Ownership
- Scheduler now accesses execution state through `vm->ctx.*`
- No changes to scheduler algorithm, work stealing, or IO reactor (deferred to D-2/D-3)

---

## 2. INVOKE_RET_REG Semantic Proof

**Problem:** Changing `INVOKE_RET_REG` from 4095 to dynamic value requires proof that the return register slot is never used by program code.

**Proof:**
1. `json.c:237`: `fn->maxRegister = maxR + 1` — maxRegister is **register count**, not max index
2. Program uses register indices `0` to `maxRegister - 1`
3. Dynamic frame allocates `maxRegister + 1` registers (`registerCount = maxRegister + 1`)
4. `INVOKE_RET_REG = registerCount - 1 = maxRegister`
5. `maxRegister` is an index program never uses (program only uses `0..maxRegister-1`)
6. Therefore `INVOKE_RET_REG = maxRegister` is safe — cannot overwrite program data

**Status:** PROVEN

---

## 3. Memory Efficiency

### 3.1 Measured Object Sizes (MSVC 2022 x64)
| Object | Size |
|--------|------|
| `TLLValue` | 24 bytes |
| `TLLFrame` (struct only) | 120 bytes |
| `TLLCoroutine` | 96 bytes |
| `TLLVM` | 64 bytes |
| `TLLExecutionContext` | 40 bytes |

### 3.2 Frame Memory Comparison
| Configuration | Per Frame | 100K Frames |
|---------------|-----------|--------------|
| Fixed 4096 (before) | 4096 × 24 = 96 KB | 9.15 GB |
| Dynamic avg 64 regs | 65 × 24 = 1.56 KB | 152 MB |
| Dynamic avg 128 regs | 129 × 24 = 3.10 KB | 302 MB |

**Note:** 64-128 average register count is ASSUMPTION (pending real corpus measurement).

### 3.3 4GB Status
- 4GB is **NOT** a hard constraint, correctness gate, or PASS/FAIL condition
- 4GB is a **reference budget / optimization target / engineering observation metric**
- Memory efficiency is an optimization target, not a correctness ceiling

---

## 4. Test Results

### 4.1 Acceptance Tests (8/8 PASS)
| Test | Result |
|------|--------|
| 01_hello | PASS |
| 02_variables | PASS |
| 03_functions | PASS |
| 04_control_flow | PASS |
| 05_arrays | PASS |
| 06_maps | PASS |
| 07_recursion | PASS |
| 08_strings | PASS |

### 4.2 Dynamic Frame Test (PASS)
- **File:** `tests/dynamic_frame_test.tll`
- **Coverage:**
  - Small register function (simple arithmetic)
  - Medium register function (multiple locals)
  - Large register function (many locals + array)
  - Recursive function (factorial, deep call stack)
  - Multiple return paths (classify)
  - Nested calls (inner → middle → outer)
  - Return parameter directly (identity, tests INVOKE_RET_REG)
  - Map return (container + return)
  - Frame pool reuse (100 repeated calls)
- **Result:** ALL TESTS PASSED

### 4.3 Async/Coroutine Test (PASS)
- **File:** `tests/d18-async/d18_async_verify.tll`
- **Coverage:** Future, EventBus, Observable, Timeout, Cancellation, multi-task scheduling
- **Result:** D18-ASYNC-PARALLELISM-PASS (exit code 0)
- **Note:** Some features MISSING/PARTIAL are pre-existing capability gaps, not regressions

### 4.4 Performance Benchmark
- **File:** `tests/perf_dynamic_frame.tll`
- **Results:**
  - 100K `add_one` calls: ~100,000 calls/sec
  - Historical baseline (P0-9): ~9,790 function calls/sec
  - **Observed improvement:** ~10x (comparison is approximate; different test methodology)
- **Note:** Performance numbers are MEASURED on current hardware; not a formal performance contract

---

## 5. Compatibility Verification

### 5.1 No Changes To (Prohibited Scope)
- ✅ `tcp.connect()` — not modified
- ✅ Consensus — not modified
- ✅ Block validation — not modified
- ✅ Chain selection — not modified
- ✅ Coroutine/Scheduler algorithm — not modified (only field access refactored)
- ✅ Native ownership semantics — not modified
- ✅ ABI layout — not modified
- ✅ Opcode numbering — not modified
- ✅ `height=5` test — not modified
- ✅ Original 4-node test — not modified

### 5.2 Build
- **Compiler:** MSVC 2022 (BuildTools) x64
- **Result:** 0 errors, 0 warnings (pre-existing C4819 code page warnings only)
- **All source files compile successfully**

---

## 6. Files Changed

| File | Change |
|------|--------|
| `host/c/tllvm.h` | Added `TLLExecutionContext` struct; refactored `TLLVM` to use `ctx` field |
| `host/c/vm.c` | Dynamic Frame: `frame_pool_acquire(requiredRegCount)`, `create_frame()` dynamic sizing, dynamic `INVOKE_RET_REG`; ExecutionContext: 143 field accesses changed from `vm->xxx` to `vm->ctx.xxx` |
| `tests/dynamic_frame_test.tll` | New: comprehensive Dynamic Frame test |
| `tests/perf_dynamic_frame.tll` | New: performance benchmark |

---

## 7. Evidence Classification

| Claim | Classification |
|-------|----------------|
| Dynamic Frame allocates maxRegister+1 registers | PROVEN (code + tests) |
| INVOKE_RET_REG = registerCount-1 is safe | PROVEN (semantic proof + tests) |
| Frame pool reallocates on insufficient capacity | PROVEN (code) |
| TLLExecutionContext contains execution-local state | PROVEN (code) |
| All acceptance tests pass | PROVEN (measured) |
| Coroutine/async tests pass | PROVEN (measured) |
| ~10x function call improvement | MEASURED (approximate comparison) |
| 64-128 average register count | ASSUMPTION (pending corpus measurement) |
| 100K frames = 152-302 MB | CALCULATED (based on assumption) |
| No regression in networking/blockchain | NOT VERIFIED (tests not run in this session) |
| Cross-platform (Linux/macOS) | NOT VERIFIED (Windows-only build) |

---

## 8. Outstanding GAPs (B-GAP, recorded for later)

1. **Native 20/20 full regression** — not run in this session (B12 evidence exists from prior commit)
2. **Cross-target 11/11** — not run in this session
3. **Networking/blockchain regression** — not run in this session
4. **Linux/macOS build and test** — not verified (Windows-only)
5. **ASan/memory safety** — not run (environment permission issue, B-GAP from B12)
6. **Real corpus register count measurement** — 64-128 average is assumption
7. **Formal performance contract** — current numbers are measured, not contractual
8. **coroutine_100K** — not run (known resource-intensive test)

---

## 9. Self-Audit Checklist

- [x] No `tcp.connect()` modification
- [x] No Consensus modification
- [x] No Block validation modification
- [x] No Chain selection modification
- [x] No Coroutine/Scheduler algorithm modification
- [x] No infinite retry
- [x] No sleep masking
- [x] No `height=5` modification
- [x] No original test deletion
- [x] No `|| true` swallowing failures
- [x] No fake evidence
- [x] 4GB is NOT hard constraint
- [x] No claimed PASS/SEALED/CLOSED
- [x] Git clean (only source/tests/docs changes)

---

**Construction complete, awaiting independent architecture audit.**
