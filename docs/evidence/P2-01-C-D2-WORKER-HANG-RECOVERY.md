# P2-01-C-D2-WORKER-HANG-RECOVERY Evidence

## 1. 阶段概述

**目标**：定位并修复 `runtime.startWorkers()` 后进程不退出（HANG）的根因，使 startWorkers(1)/startWorkers(2) 能真实结束并返回。

**基线**：`ec6c914cc079545ad269bb950ea932ad09e92652`（Build Integrity Recovery）

**状态**：Construction Complete — 等待独立审计

---

## 2. HANG 根因定位

### 2.1 诊断过程

使用 `diag_hang.tll` 测试（通过 `io.eprintln` 输出 STEP 1~7 到 stderr），确认：

- main 函数全部 STEP 1~7 都执行完毕（含 STEP 7: DONE）
- 但进程不退出
- 结论：**Worker 线程阻止进程退出**

### 2.2 根因 1：tll_vm_free 未 shutdown Worker 线程

**位置**：`host/c/vm.c` 行 1910 `tll_vm_free()`

**问题**：
- `main.c` 调用 `tll_vm_run(vm)` → `sched_trace_dump()` → `tll_vm_free(vm)` → return
- `tll_vm_free()` 直接释放 vm->coroutines、vm->globals、vm
- **但没有调用 `tll_runtime_shutdown_workers(vm)`**
- 如果 `multi_worker_initialized == true`，Worker 线程继续运行，访问已释放内存（UAF），且进程不退出

**修复**：在 `tll_vm_free()` 开头添加：
```c
if (vm->multi_worker_initialized) {
    tll_runtime_shutdown_workers(vm);
}
```
并添加前置声明 `void tll_runtime_shutdown_workers(TLLVM *vm);`

### 2.3 根因 2：tll_vm_exec 中魔法数字 2 表示 dead，但 2=WAITING

**位置**：`host/c/vm.c` 行 1085、1096、1119、1765 等共 8 处

**问题**：
- `tllvm.h` 定义：`TLL_COROUTINE_RUNNABLE=0, RUNNING=1, WAITING=2, COMPLETED=3`
- 但 `tll_vm_exec()` 中使用 `state = 2; /* dead */` 标记 coroutine 完成
- main coroutine 完成后被标记为 **WAITING(2)** 而非 **COMPLETED(3)**
- `allDead` 检查 `state != 2` 逻辑混乱，无法正确判断所有 coroutine 完成
- 结果：`tll_vm_exec()` 无限循环 → `tll_vm_run()` 不返回 → `tll_vm_free()` 不被调用

**修复**：将 8 处魔法数字 2 全部替换为 `TLL_COROUTINE_COMPLETED`：
- 行 617：`state == 2` → `state == TLL_COROUTINE_COMPLETED`
- 行 690：`state == 2` → `state == TLL_COROUTINE_COMPLETED`
- 行 830：`state == 2` → `state == TLL_COROUTINE_COMPLETED`
- 行 842：`state != 2` → `state != TLL_COROUTINE_COMPLETED`
- 行 1085：`state = 2; /* dead */` → `state = TLL_COROUTINE_COMPLETED; /* completed */`
- 行 1096：`state != 2` → `state != TLL_COROUTINE_COMPLETED`
- 行 1119：`state == 2` → `state == TLL_COROUTINE_COMPLETED`
- 行 1765：`state = 2; /* dead */` → `state = TLL_COROUTINE_COMPLETED; /* completed */`

---

## 3. Clean Build Provenance

| 项目 | 值 |
|------|-----|
| Source Commit (base) | `ec6c914cc079545ad269bb950ea932ad09e92652` |
| Build Time | 2026-09-11 (Asia/Shanghai) |
| Compiler | MSVC 19.44.35224 (Visual Studio 2022 BuildTools) |
| Build Command | `build_all.bat` (Fail-Closed Build) |
| vm.c compile | SUCCESS |
| vm.obj SHA256 | `D99DE93F4BF48A3026BA8AFF8D8C439CD0B295706F6AB314E9E7068CB000D74D` |
| tllvm.exe SHA256 | `A5AFA7C119B606D0421536C014E8E972E109E6F8528D73184565733944E2A5FB` |
| link | SUCCESS |
| Build Result | `[BUILD] === BUILD SUCCESS ===` |

---

## 4. Gate 测试结果

### Gate-1: hello.tll

| 项目 | 值 |
|------|-----|
| 测试文件 | `tests/hello_test.tll` |
| 超时 | 10s |
| 正常退出 | YES |
| stdout | `Hello World`, `Step 1`, `Step 2`, `DONE` |
| 结果 | **PASS** |

### Gate-2: 单 coroutine

| 项目 | 值 |
|------|-----|
| 测试文件 | `tests/gate2_single_coroutine.tll` |
| 超时 | 10s |
| 正常退出 | YES |
| stdout | `=== Gate-2: single coroutine ===`, `spawned coroutine: 1`, `=== Gate-2 PASS ===` |
| 结果 | **PASS** |

### Gate-3: runtime.startWorkers(1)

| 项目 | 值 |
|------|-----|
| 测试文件 | `tests/gate3_simple.tll` |
| 超时 | 10s |
| 正常退出 | YES |
| stderr | `GATE3 STEP1: before startWorkers`, `tllvm: started 1 worker threads`, `GATE3 STEP2: after startWorkers, rc=0`, `GATE3 STEP3: DONE` |
| startWorkers 返回 | YES (rc=0) |
| 结果 | **PASS** |

### Gate-4: runtime.startWorkers(2)

| 项目 | 值 |
|------|-----|
| 测试文件 | `tests/gate4_two_workers.tll` |
| 超时 | 10s |
| 正常退出 | YES |
| stderr | `GATE4 STEP1: before startWorkers`, `tllvm: started 2 worker threads`, `GATE4 STEP2: after startWorkers, rc=0`, `GATE4 STEP3: DONE` |
| startWorkers 返回 | YES (rc=0) |
| 结果 | **PASS** |

### 附加验证：diag_hang.tll（之前 HANG 的测试）

| 项目 | 值 |
|------|-----|
| 测试文件 | `tests/diag_hang.tll` |
| 之前状态 | HANG（main 执行完毕但进程不退出） |
| 当前状态 | 10s 内正常退出 |
| 结果 | **PASS（HANG 已修复）** |

---

## 5. 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `host/c/vm.c` | 1. 添加 `tll_runtime_shutdown_workers` 前置声明<br>2. `tll_vm_free()` 开头添加 shutdown workers 调用<br>3. 8 处魔法数字 `state=2`/`state==2`/`state!=2` 替换为 `TLL_COROUTINE_COMPLETED` |

---

## 6. 已知限制与 B-GAP

| 项目 | 状态 | 说明 |
|------|------|------|
| A-GAP-1 高负载堆损坏 | OPEN | >1000 并发任务时 STATUS_HEAP_CORRUPTION 0xC0000374，待 D2 HANG 修复后继续 |
| D2/D3 历史 Evidence provenance | UNVERIFIED | Build Integrity 阶段已标记，待逐步重新验证 |
| ASan | B-GAP | 未运行 |
| Linux/macOS | B-GAP | 未验证 |
| Channel/IO E2E 测试 | B-GAP | 未验证 |
| build_all.bat 绝对路径 | B-GAP | 含开发者机器路径 `C:\Users\Administrator\Doubao\tllos`，非阻塞 |

---

## 7. 证据等级

| 结论 | 等级 |
|------|------|
| tll_vm_free 未 shutdown Worker 是 HANG 根因之一 | PROVEN |
| 魔法数字 2 导致 allDead 检查失败是 HANG 根因之一 | PROVEN |
| 修复后 startWorkers(1)/startWorkers(2) 能正常退出 | PROVEN（本地测试） |
| 修复后无回归 | OBSERVED（Gate-1~4 通过，完整回归待独立审计） |

---

## 8. 停止条件

已完成：
- [x] HANG 根因定位（2 个根因）
- [x] 最小修复（tll_vm_free shutdown + 魔法数字修复）
- [x] Clean Build（Fail-Closed，0 error）
- [x] Gate-1 hello PASS
- [x] Gate-2 单 coroutine PASS
- [x] Gate-3 startWorkers(1) PASS
- [x] Gate-4 startWorkers(2) PASS
- [x] Evidence 文档
- [ ] commit + push（待执行）

**不自行宣布 PASS / SEALED。等待独立审计。**

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*施工方：豆包A（施工方）*
*审计方：于秋鸿博士（待独立审计）*
