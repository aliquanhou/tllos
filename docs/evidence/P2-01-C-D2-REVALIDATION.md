# P2-01-C-D2-REVALIDATION Evidence

## 1. 阶段概述

**目标**：在 D2-WORKER-HANG-RECOVERY 修复后，重新验证 D2 原有 7 个核心 Worker Runtime 测试，确认 D2 功能完整无回归。

**基线**：`abdb4207d33324d5ed5bfcadbbfac1e9677b7f96`（D2-WORKER-HANG-RECOVERY）
**分支**：`feature/P2-01-C-D3-runtime-high-frame-execution`
**状态**：Construction Complete — 等待独立审计

---

## 2. 前置条件确认

### 2.1 D2-WORKER-HANG-RECOVERY 已独立审计通过

架构师裁决确认：
- Fail-Closed Build 有效
- Clean Build 成功
- startWorkers(1) PASS
- startWorkers(2) PASS
- 原始 HANG 已修复

### 2.2 D2 原有 7 个核心测试来源

从 `docs/evidence/P2-01-C-D2-TRUE-MULTI-WORKER.md` 第 19.4 节（D2-R3.1-closure Full Regression）确认 D2 最终 7 个核心测试：

1. multi_worker_parallel
2. multi_worker_overlap_proof
3. multi_worker_stress (2W/100T)
4. worker_global_test
5. simple_sleep_wakeup_test
6. worker_ownership_boundary
7. wake_list_300_coroutines

**未自行创造新测试替代历史测试。**

---

## 3. Clean Build Provenance

| 项目 | 值 |
|------|-----|
| Source SHA | `abdb4207d33324d5ed5bfcadbbfac1e9677b7f96` |
| Build Time | 2026-09-11 (Asia/Shanghai) |
| Compiler | MSVC 19.44.35224 (Visual Studio 2022 BuildTools) |
| Build Command | `build_all.bat` (Fail-Closed Build) |
| vm.c compile | SUCCESS |
| vm.obj SHA256 | `582D8A01ABE1F4178D80A8F88F12F207BAB9BF40B5A876B9CD543FF4F3BFE31C` |
| tllvm.exe SHA256 | `250982B0FD4D08F9601A52F6EC24CBD05946FBA466E0F0F02F16E991897C680A` |
| link | SUCCESS |
| Build Result | `[BUILD] === BUILD SUCCESS ===` |

**未使用旧二进制。**

---

## 4. D2 7/7 测试结果

### 测试 1: multi_worker_parallel (2 Workers, 2 Tasks)

| 项目 | 值 |
|------|-----|
| 超时 | 30s |
| 正常退出 | YES |
| 关键输出 | `TASK_1 END worker=0 sum=4999950000`, `All tasks completed: worker0=1 worker1=1`, `TEST_RESULT: PASS (2 tasks completed by workers)` |
| 结果 | **PASS** |

### 测试 2: multi_worker_overlap_proof

| 项目 | 值 |
|------|-----|
| 超时 | 30s |
| 正常退出 | YES |
| 关键输出 | `TEST_RESULT: PASS`, `Both tasks started`, `Ran on different workers (true multi-worker)`, `Overlap window proven via barrier`, `Both tasks completed without loss` |
| 结果 | **PASS** |

### 测试 3: multi_worker_stress_2w_100t (2 Workers, 100 Tasks)

| 项目 | 值 |
|------|-----|
| 超时 | 30s |
| 正常退出 | YES |
| 关键输出 | `Submitted 100 tasks`, `All tasks completed: worker0=50 worker1=50`, `Final: worker0=50 worker1=50 total=100`, `TEST_RESULT: PASS (100/100 tasks completed, no loss)` |
| 结果 | **PASS** |

### 测试 4: worker_global_test

| 项目 | 值 |
|------|-----|
| 超时 | 30s |
| 正常退出 | YES |
| 关键输出 | `startWorkers: 0`, `After: counter=42`, `Worker id seen: 0`, `Worker tasks completed: 1`, `TEST_RESULT: PASS - worker can modify global` |
| 结果 | **PASS** |

### 测试 5: simple_sleep_wakeup_test

| 项目 | 值 |
|------|-----|
| 超时 | 30s |
| 正常退出 | YES |
| 关键输出 | `waited=8`, `phase1_done=1`, `phase2_done=1`, `task_worker=0`, `TEST_RESULT: PASS - sleep wakeup works` |
| 结果 | **PASS** |

### 测试 6: worker_ownership_boundary

| 项目 | 值 |
|------|-----|
| 超时 | 30s |
| 正常退出 | YES |
| 关键输出 | `TEST_RESULT: PASS`, `A and B started on different workers (true multi-worker)`, `No dual execution (each coroutine executes exactly 2 phases)`, `Both tasks completed without loss`, `Coroutine migration after sleep is normal scheduler behavior` |
| 结果 | **PASS** |

### 测试 7: wake_list_300_coroutines (1 Worker, 300 Coroutines)

| 项目 | 值 |
|------|-----|
| 超时 | 120s |
| 正常退出 | YES |
| 关键输出 | `startWorkers(1): 0`, `Submitted 300 coroutines`, `waited=7`, `completed_count=300 / 300`, `TEST_RESULT: PASS - all 300 coroutines woken and executed (300 > 256, no cap)` |
| 结果 | **PASS** |

---

## 5. 汇总表

| # | 测试 | Workers | Tasks | 结果 | 退出 |
|---|------|---------|-------|------|------|
| 1 | multi_worker_parallel | 2 | 2 | **PASS** | YES |
| 2 | multi_worker_overlap_proof | 2 | 2 | **PASS** | YES |
| 3 | multi_worker_stress_2w_100t | 2 | 100 | **PASS** | YES |
| 4 | worker_global_test | 1 | 1 | **PASS** | YES |
| 5 | simple_sleep_wakeup_test | 1 | 1 | **PASS** | YES |
| 6 | worker_ownership_boundary | 2 | 2 | **PASS** | YES |
| 7 | wake_list_300_coroutines | 1 | 300 | **PASS** | YES |

**7/7 PASS**

---

## 6. 验证结论

### 6.1 D2 核心功能完整

所有 D2 原有 7 个核心测试在 Clean Build（基于 abdb420）下全部 PASS：

- ✅ True Multi-Worker 并行执行（测试 1、2）
- ✅ 高负载并发正确性（测试 3：100/100 no loss）
- ✅ Worker 可修改全局状态（测试 4）
- ✅ Sleep WAITING → RUNNABLE 唤醒闭环（测试 5）
- ✅ Coroutine Ownership Boundary（测试 6：no dual execution）
- ✅ Wake List Exact-Once Enqueue（测试 7：300/300, no 256 cap）

### 6.2 无回归

D2-WORKER-HANG-RECOVERY 修复（tll_vm_free shutdown + 魔法数字 2 修复）未引入任何 D2 核心功能回归。

### 6.3 HANG 已修复

所有 7 个测试均在超时时间内正常退出，无 HANG / DEADLOCK。

---

## 7. 已知限制（B-GAP，不阻塞）

按照施工令特别纪律，以下问题只记录为 B-GAP，**不阻塞** D2 重新封板：

| 项目 | 状态 | 说明 |
|------|------|------|
| A-GAP-1 高负载堆损坏 | OPEN | >1000 并发任务时 STATUS_HEAP_CORRUPTION，待 D3 阶段处理 |
| ASan | B-GAP | 未运行 |
| Linux/macOS | B-GAP | 未验证 |
| Channel/IO E2E 测试 | B-GAP | 代码闭环已验证，端到端 TLL 测试未做 |
| 10K/100K 压测 | B-GAP | 本阶段不做 |
| Work Stealing | B-GAP | 本阶段不做 |
| IO Reactor | B-GAP | 本阶段不做 |
| build_all.bat 绝对路径 | B-GAP | 含开发者机器路径，非阻塞 |

---

## 8. 证据等级

| 结论 | 等级 |
|------|------|
| D2 7 个核心测试全部 PASS | PROVEN（本地 Clean Build 实测） |
| D2-WORKER-HANG-RECOVERY 未引入回归 | PROVEN |
| D2 核心功能完整 | PROVEN |
| D2 可重新封板 | 待独立审计确认 |

---

## 9. 停止条件

已完成：
- [x] 从 D2 Evidence 恢复原有 7 个核心测试集合
- [x] Clean Build（Fail-Closed，0 error）
- [x] 记录 Source SHA / Compiler / vm.obj SHA256 / tllvm.exe SHA256
- [x] 依次运行 D2 7 个核心测试
- [x] 每个测试记录 Result / Exit Code / 关键输出
- [x] 7/7 PASS
- [x] Evidence 文档
- [ ] commit + push（待执行）

**按照施工令要求，7/7 PASS 后立即停止。**
- 未做 ASan
- 未做 Linux/macOS
- 未做 10K/100K
- 未做 Work Stealing
- 未做 IO Reactor
- 未启动 D3

---

## 10. 建议最终状态

如果独立审计确认本 Revalidation 结果：

**P2-01-C-D2 = PASS / RESEALED**

然后暂停，下一阶段再进入 D3。

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*施工方：豆包A（施工方）*
*审计方：于秋鸿博士（待独立审计）*
