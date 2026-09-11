# P2-01-C-D3: Conditional Seal Condition Document

**Status:** CONDITIONAL PASS / CONDITIONAL SEAL
**Branch:** `feature/P2-01-C-D3-runtime-high-frame-execution`
**Date:** 2026-09-11
**Architect Decision:** 于秋鸿博士

---

## 0. Executive Summary

**P2-01-C-D3 = CONDITIONAL PASS**（不是 FAILED，不是 SEALED）

D3 Runtime High-Frame Execution 基础设施全部通过，并发正确性验证完成。但 10K 规模稳定性存在已知概率性崩溃（A-GAP-1），当前通过 16 字节 identity guard 进行 layout mitigation，非真正 memory safety fix。

**裁决：允许进入 P2-01-C Final Seal（Runtime Core v0 封板），但要求未来 Runtime Hardening 阶段必须解决 A-GAP-1。**

---

## 1. D3 Module Status

### 1.1 已确认通过模块

| 模块 | 状态 | 证据 |
|------|------|------|
| D3-0 Build Integrity Gate | ✅ PASS | Fail-Closed Build, Clean Build provenance, binary SHA256 |
| D3-1 Scheduler Ownership Audit | ✅ PASS | Ownership Matrix, all shared objects classified |
| D3-2 Runnable Queue Layer | ✅ PASS | 6 Queue API, queue node lifecycle verified |
| D3-3 Local Queue Execution | ✅ PASS | local-first scheduling, requeue to local |
| D3-4 Execution Context Isolation | ✅ PASS | Context Transfer Protocol, context_transfer_test PASS |
| D3-5 Coroutine Migration Test | ✅ PASS | d3_migration_100: 100 coroutines, exec=200, no dual/lost |
| D3-7 Regression Gate | ✅ PASS | D2 7/7 PASS |

### 1.2 条件通过模块

| 模块 | 状态 | 条件 |
|------|------|------|
| D3-6 High Frame Stress Test | ⚠️ CONDITIONAL PASS | 100/1000/5000 PASS; 10000 2/3 PASS (probabilistic ACCESS_VIOLATION) |

---

## 2. D2 Status (Sealed, No Touch)

**P2-01-C-D2 = PASS / RESEALED** ✅

- Baseline Commit: `e1b6e8fa6dff687a7cfd58bea8abb970f4b28d44`
- D2 7/7 Core Tests PASS:
  1. multi_worker_parallel ✅
  2. multi_worker_overlap_proof ✅
  3. multi_worker_stress_2w_100t ✅
  4. worker_global_test ✅
  5. simple_sleep_wakeup_test ✅
  6. worker_ownership_boundary ✅
  7. wake_list_300_coroutines ✅

**D2 不再修改。**

---

## 3. A-GAP-1 Status (Known Limitation)

### 3.1 当前真实状态

```
A-GAP-1:
  ├── Trigger: Concurrent coroutine_create + Worker execution  [PROVEN]
  ├── Crash location: TLLCoroutine header offset 0-8            [PROVEN]
  ├── Original struct: overwrites callStack pointer              [PROVEN]
  ├── Nature: Probabilistic crash (not deterministic)            [PROVEN]
  ├── Not UAF: magic assert not triggered                        [PROVEN]
  ├── Not partial publish (H4): init_magic not triggered         [PROVEN / RULED OUT]
  ├── Not memcpy size error (H2): no OOB in Phase G audit       [PROVEN / RULED OUT]
  ├── Exact writer: NOT FOUND                                     [OPEN]
  ├── ROOT CAUSE: OPEN
  ├── MITIGATION: EXISTS (16-byte identity guard)
  └── FIX: NONE
```

### 3.2 Mitigation Details

**16 字节 magic+generation identity guard**（layout mitigation，非 memory safety fix）：

```c
typedef struct {
    unsigned long long magic;       /* offset 0-7: 0x544C4C434F524F = alive */
    unsigned long long generation;  /* offset 8-15: monotonically increasing */
    TLLFrame **callStack;           /* offset 16-23: protected from OOB write */
    ...
} TLLCoroutine;
```

**作用机制：**
- 原始结构：OOB 写入 offset 0-7 → 覆盖 callStack 指针 → 崩溃
- 当前结构：OOB 写入 offset 0-7 → 覆盖 magic → 暂时不影响执行

**这叫 layout mitigation，不是 memory safety fix。** OOB 写入仍然在发生，只是被 padding 吸收。

### 3.3 Risk Assessment

| 风险项 | 等级 | 说明 |
|--------|------|------|
| 100 coroutine stress | 🟢 LOW | 稳定 PASS |
| 1000 coroutine stress | 🟢 LOW | 稳定 PASS |
| 5000 coroutine stress | 🟡 MEDIUM | 稳定 PASS（测试次数有限） |
| 10000 coroutine stress | 🟠 HIGH | 2/3 PASS，约 33% 概率性 ACCESS_VIOLATION |
| 生产环境高并发 | 🟠 HIGH | 概率性崩溃可能影响稳定性 |

### 3.4 Write Source Candidates (Remaining)

| 候选 | 说明 | 状态 |
|------|------|------|
| H1: Coroutine index 越界写 | `vm->coroutines[id]` 中 id 越界 | **UNVERIFIED**（最可能剩余） |
| H3: 数组元素初始化错误 | calloc size 与访问 size 不匹配 | **UNVERIFIED** |
| 相邻 coroutine 数组越界 | callStack/locals/argStack 数组越界覆盖相邻 coroutine header | **INFERRED** |

---

## 4. Test Results Summary

### 4.1 D2 Regression (7/7 PASS)

| Test | Result |
|------|--------|
| multi_worker_parallel | PASS |
| multi_worker_overlap_proof | PASS |
| multi_worker_stress_2w_100t | PASS |
| worker_global_test | PASS |
| simple_sleep_wakeup_test | PASS |
| worker_ownership_boundary | PASS |
| wake_list_300_coroutines | PASS |

### 4.2 D3 Stress

| Scale | Result | Note |
|-------|--------|------|
| 100 tasks | PASS | 稳定 |
| 1000 tasks | PASS | 稳定 |
| 5000 tasks | PASS | 稳定 |
| 10000 tasks (run 1) | FAIL | ACCESS_VIOLATION 0xC0000005 |
| 10000 tasks (run 2) | PASS | |
| 10000 tasks (run 3) | PASS | |

**10000 tasks: 2/3 PASS（概率性崩溃，约 33% 崩溃率）**

### 4.3 D3 Infrastructure Tests

| Test | Result |
|------|--------|
| context_transfer_test | PASS |
| d3_migration_100 | PASS (100 coroutines, exec=200, no dual/lost) |
| hello_test | PASS |
| gate2_single_coroutine | PASS |
| gate3_single_worker | PASS |
| gate4_two_workers | PASS |

---

## 5. Conditional Seal Decision

### 5.1 Decision

**P2-01-C-D3 = CONDITIONAL SEAL**

允许进入 P2-01-C Final Seal（Runtime Core v0 封板）。

### 5.2 Conditions

1. **A-GAP-1 记录为已知限制**：MITIGATED / ROOT CAUSE PENDING，非阻塞
2. **16 字节 identity guard 保留**：作为 layout mitigation，不得移除
3. **10K 规模稳定性限制**：当前不保证 10K+ coroutine 高并发稳定性
4. **未来 Runtime Hardening 阶段必须解决 A-GAP-1**：找到 exact writer 并真正修复

### 5.3 Allowed Scope

✅ 允许：
- 进入 P2-01-C Final Seal
- 进入 Agent Runtime / Desktop Robot OS 设计
- 使用 TLL Runtime Core v0 作为 AI Agent 执行底座（中低并发场景）

❌ 不允许：
- 宣称 D3 完全 SEALED / Production Ready
- 在 10K+ 高并发生产环境部署（无额外稳定性保障）
- 移除 16 字节 identity guard
- 宣称 A-GAP-1 已修复

---

## 6. Future Requirements (Runtime Hardening Phase)

### 6.1 Must Resolve A-GAP-1

未来 Runtime Hardening 阶段必须：
1. 找到 exact writer（OOB 写入源头）
2. 真正修复 OOB 写入（不是 layout mitigation）
3. 验证 10000 coroutine stress 稳定 PASS（20/20 或更多）
4. 可选：移除 16 字节 identity guard（或保留作为额外安全层）

### 6.2 Recommended Tools

- PageHeap / Application Verifier full trace
- WinDbg kernel heap trace
- ASan (clang-cl / MSVC AddressSanitizer)
- Intel Inspector
- 运行时 canary（header/tail canary + guard page）

### 6.3 Estimated Effort

- 定位 exact writer: 1~3 周
- 修复 + 验证: 几天
- 总计: 2~4 周

---

## 7. P2-01-C Runtime Core v0 Status

### 7.1 Module Summary

| 模块 | 状态 | Commit |
|------|------|--------|
| D1 Dynamic Frame | ✅ PASS WITH B-GAPS | (历史提交) |
| D2 Multi Worker | ✅ PASS / RESEALED | e1b6e8f |
| D3 High Frame Runtime | ⚠️ CONDITIONAL SEAL | 4357eb0 |

### 7.2 Next Step

**进入 P2-01-C Final Seal（Runtime Core v0 封板）**

需要：
1. 汇总 D1 + D2 + D3 全部 Evidence
2. 建立 P2-01-C-RUNTIME-CORE-V0-SEAL.md
3. 记录已知限制（A-GAP-1, B-GAPs）
4. 定义 Runtime Core v0 的能力边界和使用场景
5. commit + push

---

## 8. Evidence Documents

| 文档 | 说明 | Commit |
|------|------|--------|
| P2-01-C-D2-TRUE-MULTI-WORKER.md | D2 完整 Evidence | e1b6e8f |
| P2-01-C-D3-HIGH-FRAME-RUNTIME.md | D3 完整 Evidence | 0723eac |
| P2-01-C-D3-A-GAP1-ROOT-CAUSE.md | A-GAP1 Root Cause Isolation | 364c917 |
| P2-01-C-D3-A-GAP1-SOURCE-TRACE.md | A-GAP1 Source Trace | 5849d0c |
| P2-01-C-D3-A-GAP1-FINAL-SOURCE-PROOF.md | A-GAP1 Final Source Proof | 4357eb0 |
| P2-01-C-D3-SEAL-CONDITION.md | 本文件（条件封板） | (当前提交) |

---

## 9. Architect Sign-off

**裁决人：** 于秋鸿博士
**日期：** 2026-09-11
**裁决：** P2-01-C-D3 = CONDITIONAL SEAL

> D3 基础设施全部通过，并发正确性验证完成。A-GAP-1 为已知概率性崩溃，通过 16 字节 identity guard 进行 layout mitigation。允许进入 P2-01-C Final Seal，未来 Runtime Hardening 阶段必须解决 A-GAP-1。不要继续陷入 A-GAP-1 黑洞，把 TLL Runtime v0 封板，进入 AI Computer 阶段。

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*施工方：豆包A（施工方）*
*裁决方：于秋鸿博士*
