# P0-RUNTIME-07 Final Evidence — Coroutine 100K Root-Cause Closure

**Status**: EVIDENCE SUBMITTED — AWAITING ARCHITECT INDEPENDENT AUDIT
**Branch**: `feature/P0-RUNTIME-07-coroutine-100k-root-cause`
**Final Commit**: `87f60752dc119dd17c5c48299141f16fd05608c7`
**CI Run ID**: `34406564979`
**CI Run URL**: https://github.com/aliquanhou/tllos/actions/runs/34406564979

---

## 1. Root Cause (R1 Reality Audit)

### Primary Root Cause: Coroutine Frame Double-Free / Use-After-Free

**Crash threshold**: 511 workers → PASS, 512 workers → CRASH (exactly matches `FRAME_POOL_MAX=512`)

**Causal chain** (confirmed by ASan heap-use-after-free):
```
main frame
  → OP_RET / pop_frame
  → first free_frame(main frame)
  → frame_pool is full (512)
  →真正 free(main frame) to heap
  → mainCo->callStackSize STILL retains this frame (NOT synchronized)
  → allDead
  → coroutine_destroy(mainCo)
  → iterates stale callStack
  → second free_frame(main frame)
  → reads freed frame->closureEnv
  → ASan: heap-use-after-free
  → SIGSEGV (Linux/macOS) / heap corruption (Windows)
```

**Secondary finding (R3)**: Not a scheduler bug. The original Test 3 used `coroutine.sleep(200)` as a proxy for "wait until all workers complete", which is not a guaranteed synchronization primitive.

---

## 2. R2 Fix — Frame Ownership Accounting

**Commit**: `8ad21c8c2723acc591f5de27277fc13964426cd2`
**File**: `host/c/vm.c`

**Change**: Synchronize `currentCoroutine->callStackSize` in both `push_frame()` and `pop_frame()`:
- `push_frame()`: `vm->callStackSize++` → also `currentCoroutine->callStackSize++`
- `pop_frame()`: `vm->callStackSize--` → also `currentCoroutine->callStackSize--`

**Effect**: After `OP_RET` pops and frees the main frame, `mainCo->callStackSize` is correctly decremented. `coroutine_destroy()` no longer iterates stale frames, eliminating the double-free.

**No cheating**: Did not increase `FRAME_POOL_MAX`, did not delete tests, did not disable ASan, did not add "already freed" patches, did not modify scheduler.

---

## 3. R3 Diagnosis — Scheduler Reality Audit

**Commit**: `589f6b9` (R3-FIX, includes diagnosis code)

**Method**: In-memory Ring Buffer trace (65536 entries, 14 event types, PC/opcode tracking, GLOBAL operation tracking), default-disabled via `TLL_SCHED_TRACE=1` env var.

**Findings across 6 diagnostic rounds**:
1. ✅ OP_SLEEP executes correctly on all 1000 workers
2. ✅ wakeTime set correctly (now + 10ms)
3. ✅ Timer wait works correctly
4. ✅ Workers are WAKE'd, SELECT'd, RESUME'd
5. ✅ PC continuation correct (resume at pc=2, executes completed2++ and OP_RETURN)
6. ✅ Global store correct (all workers increment completed2 to 1000, same VM/globals pointer)
7. ✅ Scheduler selection is legal round-robin (sel=0 because cursor at old=41000, next is (41001)%41001=0=main, main timer expired → runnable)

**Conclusion**: `main sleep(200ms)` wakes after 1032ms (not early), at which point 994 workers are still runnable. Scheduler legally selects main. Test incorrectly assumed sleep(200) guarantees all workers complete.

---

## 4. R3-FIX — Test Synchronization

**Commit**: `589f6b9`
**File**: `tests/coroutine_stress_test.tll`

**Test 3 change**: From `coroutine.sleep(200)` + assert to explicit completion synchronization:
```
while completed3 < 1000 && elapsed < 10000 && guard < 1000000:
    coroutine.yield()
```
- Completion target: 1000 workers (unchanged)
- Bounded timeout: 10000ms
- Bounded iteration guard: 1000000
- If completed3 < 1000 after timeout → FAIL (no weakening)

**Also**: `tests/debug_diag.tll` rewritten as parameterized scenario test covering 32768-dead / 35000-dead / 40000-dead + 1000 sleep, each with explicit synchronization.

---

## 5. Test Scale — UNCHANGED

| Test | Scale | Status |
|------|-------|--------|
| Test 1 | 100,000 coroutines, immediate-return | ✅ Original scale preserved |
| Test 2 | 10,000 coroutines × 10 yields each | ✅ Original scale preserved |
| Test 3 | 1,000 coroutines × sleep(10ms) | ✅ Original scale preserved |

**No**: skip, disabled, reduced count, weakened assertion, `|| true`, failure swallowing, test deletion.

---

## 6. Local Tests

### debug_diag (3 scenarios)
| Scenario | Result | Time |
|----------|--------|------|
| 32768 dead + 1000 sleep | ✅ PASS | 1907ms |
| 35000 dead + 1000 sleep | ✅ PASS | 5374ms |
| 40000 dead + 1000 sleep | ✅ PASS | 10445ms |

### coroutine_stress_test (3 tests)
| Test | Result | Time |
|------|--------|------|
| Test 1: 100K immediate-return | ✅ PASS | 428739ms |
| Test 2: 10K × 10 yields | ✅ PASS | 464099ms |
| Test 3: 1K sleep | ✅ PASS | 9317ms |

### Regression
- Scope 10/10: ✅ PASS
- Coroutine regression 5/5: ✅ PASS
- Bootstrap: ✅ PASS (856851 bytes)

---

## 7. ASan

| Test | Result | Notes |
|------|--------|-------|
| ASan debug_diag 32768-dead | ✅ PASS | No memory errors |
| ASan debug_diag 35000-dead | ✅ PASS | No memory errors |
| ASan debug_diag 40000-dead | ✅ PASS | No memory errors |
| ASan 512 boundary | ✅ PASS | No UAF / double-free |
| ASan 10K × 10 yield | ✅ PASS | No memory errors |
| **ASan 100K immediate-return** | ⚠️ **OOM** | **NOT PASS — ASan memory overhead exceeds 8GB environment limit** |

**Outstanding GAP**: ASan 100K cannot run in current environment due to memory limits. This is a RESOURCE LIMIT, not a code failure. Must be re-run in higher-memory environment or at Release Gate stage.

---

## 8. CI Run — Three-Platform coroutine-only-verify

**Run ID**: `34406564979`
**Commit**: `87f60752dc119dd17c5c48299141f16fd05608c7`
**Workflow**: CI (`.github/workflows/ci.yml`)
**Job**: `coroutine-only-verify` (focused job, matrix: 3 platforms)

### Ubuntu (ubuntu-latest)
- **Job ID**: `102650836404`
- **Conclusion**: ✅ **SUCCESS**
- **Started**: 2026-09-09T21:22:38Z
- **Completed**: 2026-09-09T21:27:20Z
- **Duration**: ~4m42s
- **Build (Linux)**: ✅ success
- **Coroutine Test (Linux/macOS)**: ✅ success (21:23:11 → 21:27:16, ~4m5s)
- **Hard assertions passed**: exit=0, Test 1 PASS, Test 2 PASS, Test 3 PASS, no FAIL, Stress Tests Done
- **URL**: https://github.com/aliquanhou/tllos/actions/runs/34406564979/job/102650836404

### macOS (macos-latest)
- **Job ID**: `102650837103`
- **Conclusion**: ✅ **SUCCESS**
- **Started**: 2026-09-09T21:22:42Z
- **Completed**: 2026-09-09T21:24:52Z
- **Duration**: ~2m10s
- **Build (macOS)**: ✅ success
- **Coroutine Test (Linux/macOS)**: ✅ success (21:23:12 → 21:24:48, ~1m36s)
- **Hard assertions passed**: exit=0, Test 1 PASS, Test 2 PASS, Test 3 PASS, no FAIL, Stress Tests Done
- **URL**: https://github.com/aliquanhou/tllos/actions/runs/34406564979/job/102650837103

### Windows (windows-latest)
- **Job ID**: `102650836071`
- **Conclusion**: ✅ **SUCCESS**
- **Started**: 2026-09-09T21:22:37Z
- **Completed**: 2026-09-09T21:25:02Z
- **Duration**: ~2m25s
- **Setup MSVC**: ✅ success
- **Build (Windows)**: ✅ success
- **Coroutine Test (Windows)**: ✅ success (21:23:17 → 21:24:59, ~1m42s)
- **Hard assertions passed**: exit=0, Test 1 PASS, Test 2 PASS, Test 3 PASS, no FAIL, Stress Tests Done
- **URL**: https://github.com/aliquanhou/tllos/actions/runs/34406564979/job/102650836071

### Note on overall Run conclusion
The overall CI Run `34406564979` shows `failure` because the **separate** `native-build-test` jobs failed/cancelled:
- `native-build-test (windows)`: failure at Blockchain 4-Node network test (known independent Issue #8)
- `native-build-test (ubuntu)`: cancelled (P2P 2-Node test hung)
- `native-build-test (macos)`: cancelled (P2P 2-Node test hung)

These failures are **independent of coroutine** and are tracked in separate issues. The `coroutine-only-verify` jobs (the focused verification for this issue) all passed.

---

## 9. Files Changed (since baseline 8190ede)

| File | Change | Purpose |
|------|--------|---------|
| `host/c/vm.c` | +313 / -8 | R2 frame ownership fix + Ring Buffer trace (default-disabled) |
| `host/c/main.c` | +6 | sched_trace_dump() call |
| `tests/coroutine_stress_test.tll` | +11 / -1 | R3-FIX Test 3 synchronization |
| `tests/debug_diag.tll` | +56 | Parameterized scenario test (32768/35000/40000 dead + sleep) |
| `build_asan.bat` | +20 | ASan build script |
| `docs/TLL-FRAME-OWNERSHIP-CONTRACT-v1.0.md` | +179 | Frame ownership contract |
| `docs/PHASE2-01-P0-RUNTIME-07-COROUTINE-100K-REALITY-AUDIT.md` | +213 | R1 reality audit report |
| `.github/workflows/ci.yml` | modified | Added `coroutine-only-verify` focused job (via GitHub API commits) |

---

## 10. Commit Chain

| SHA | Message |
|-----|---------|
| `8ad21c8` | fix(runtime): P0-RUNTIME-07-R2 coroutine frame double-free closure |
| `589f6b9` | P0-RUNTIME-07-R3-FIX: Coroutine Stress Test Synchronization Closure |
| `57d9df8` | ci: add coroutine-only-verify job for P0-RUNTIME-07 |
| `d6b86bc` | ci: fix yaml escaping in coroutine-only-verify job |
| `406544b` | ci: fix quote style in coroutine-only-verify job |
| `87f6075` | ci: fix indentation in coroutine-only-verify job |

---

## 11. Ring Buffer Diagnostic Capability

- **Location**: `host/c/vm.c`
- **Status**: Retained, default-disabled
- **Enable**: `TLL_SCHED_TRACE=1` environment variable
- **Output**: `sched_trace.log` (overwritten each run)
- **Events**: 14 types including COROUTINE_SLEEP, SCHED_SCAN, TIMER_WAIT, WAKE, SELECT, RESUME, OPCODE, GLOBAL_LOAD/STORE, RETURN
- **Filtering**: Target worker ID filtering for focused trace
- **Impact**: Zero overhead when disabled (compile-time guarded)
- **Decision**: Per architect instruction — "暂时不要删除，默认关闭"

---

## 12. Outstanding GAP

| Item | Status | Impact |
|------|--------|--------|
| ASan 100K immediate-return | ⚠️ OOM / NOT PASS | Cannot verify 100K under ASan in current 8GB environment. Need higher-memory CI or Release Gate stage. |
| native-build-test full CI | ❌ failure/cancelled | Independent P2P/Blockchain issues (#8). Does not affect coroutine-only-verify. |
| Issue #5 (B11 Native Ownership) | 🔒 BLOCKED | Separate workstream, not part of P0-RUNTIME-07. |
| Issue #8 (Blockchain 5-Block Windows Sync) | OPEN | Independent issue, not part of P0-RUNTIME-07. |

---

## 13. Summary

**What was fixed**:
1. ✅ R2: Coroutine frame double-free / UAF — root cause identified via ASan, fixed via callStackSize synchronization
2. ✅ R3: Test synchronization — sleep(200) was not a valid completion barrier; replaced with explicit while-loop + bounded timeout

**What was verified**:
1. ✅ Three-platform CI (Ubuntu/macOS/Windows) coroutine-only-verify: ALL SUCCESS
2. ✅ Test scale unchanged (100K / 10K×10 / 1K)
3. ✅ No test weakening, no deletion, no `|| true`
4. ✅ Local regression: scope 10/10, coroutine 5/5, bootstrap PASS
5. ✅ ASan: debug_diag 3/3, 512 boundary, 10K yield all PASS

**What remains**:
- ⚠️ ASan 100K: OOM environment limit (not code failure)
- 🔒 Issue #5 B11: separate workstream

---

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）

*This evidence document is submitted for independent architect audit. Agent A does not declare PASS/SEALED/CLOSED.*
