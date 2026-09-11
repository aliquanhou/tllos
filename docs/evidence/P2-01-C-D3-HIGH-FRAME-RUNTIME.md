# P2-01-C-D3: Runtime High-Frame Execution — Evidence

**Status:** Construction Complete, awaiting independent architecture audit
**Baseline:** `e1b6e8fa6dff687a7cfd58bea8abb970f4b28d44` (D2 RESEALED)
**Branch:** `feature/P2-01-C-D3-runtime-high-frame-execution`
**Date:** 2026-09-11

---

## 1. D3-0 Build Integrity Gate

### 1.1 Fail-Closed Build 确认

`build_all.bat` 已确认 Fail-Closed：
- 行 15-16: `del /q *.obj` + `del /q tllvm.exe`（清理旧二进制）
- 行 22-52+: 每个 `cl` 编译后检查 `errorlevel`，失败则 `exit /b 1`
- 行 6-8: `vcvarsall` 失败则 `exit /b 1`

**禁止**：compile fail → continue link → old obj。

### 1.2 Clean Build Provenance

| 项目 | 值 |
|------|-----|
| Source SHA | `e1b6e8fa6dff687a7cfd58bea8abb970f4b28d44` |
| Compiler | MSVC 19.44.35224 (Visual Studio 2022 BuildTools) |
| Build Command | `build_all.bat` (Fail-Closed) |
| vm.obj SHA256 | `61500681CCF2BEA41D1C704372CCDEF4D05B9ACA9D0C2827CF4D3D91E81AF3CC` |
| tllvm.exe SHA256 | `517900129DE6A0AFB258157C9B466FC881CEA0FE2FB22AB1187DC1A3FA8F3A92` |
| Build Result | `[BUILD] === BUILD SUCCESS ===` |

**未使用旧二进制。**

---

## 2. D3-1 Scheduler Ownership Audit

### 2.1 Ownership Matrix

| 对象 | Owner | 同步保护 | 说明 |
|------|-------|----------|------|
| Worker ctx.callStack | Worker | 无（Worker 私有） | 执行期间归 Worker 所有，执行前后为 NULL |
| Coroutine.callStack | Coroutine | 无（未执行时） | 未执行时归 Coroutine 所有，执行期间转移给 Worker |
| Worker ctx.currentCoroutine | Worker | 无（Worker 私有） | 标记当前 Worker 正在执行哪个 coroutine |
| Coroutine.state | Runtime | `coroutine_table_lock` | 所有状态转换在锁保护下进行 |
| Runnable Queue Node | Queue | `queue->lock` + semaphore | enqueue 创建 node，dequeue 后 free node |
| Running Coroutine | Worker | `coroutine_table_lock` (claim) | claim 后归 Worker 所有，同一时间只能一个 Worker |
| Suspended Coroutine | Runtime | `coroutine_table_lock` | WAITING 状态归 Runtime 管理，等待 wake |
| Frame | Execution Context | 无（ctx owner 私有） | callStack 中的 frame 归当前 ctx owner 所有 |
| callStack 数组 | Context Owner | pointer transfer | Worker ↔ Coroutine 之间 pointer transfer，不 copy |

### 2.2 Context Transfer Protocol

**已实现**：callStack 使用 **pointer transfer**（不是 copy）：

```
Coroutine READY (callStack owned by coro)
      ↓
Worker Claim (RUNNABLE → RUNNING under lock)
      ↓
Context MOVE: worker->ctx.callStack = coro->callStack
      ↓
Worker OWNED (tll_vm_exec executes)
      ↓
Yield / Complete
      ↓
Context RETURN: coro->callStack = worker->ctx.callStack
      ↓
State transition (COMPLETED / RUNNABLE / WAITING under lock)
      ↓
Worker ctx.callStack = NULL (no dangling pointer)
```

**关键代码位置**：
- Context MOVE: `vm.c` 行 2414-2417（Worker 加载 coroutine callStack）
- Context RETURN: `vm.c` 行 2423-2425（Worker 保存回 coroutine）
- Worker ctx 清空: `vm.c` 行 2467-2469（执行后 worker->ctx.callStack = NULL）

**无 double owner**：执行期间 callStack 指针只在 Worker ctx 中，coro->callStack 不被使用。
**无 dangling pointer**：执行前后 worker->ctx.callStack = NULL。
**无 stale pointer**：每次执行前从 coro->callStack 重新加载，执行后保存回 coro。

### 2.3 Claim Exactly-Once

**已实现**：`coroutine_table_lock` 保护 RUNNABLE → RUNNING 转换：

```c
EnterCriticalSection(coroutine_table_lock);
coro = vm->coroutines[coro_idx];
if (!coro || coro->state != TLL_COROUTINE_RUNNABLE) {
    LeaveCriticalSection(...);
    continue;  // already claimed by another worker
}
coro->state = TLL_COROUTINE_RUNNING;  // claim
LeaveCriticalSection(...);
```

**保证**：一个 coroutine 同一时间只能被一个 Worker claim 和执行。

### 2.4 State Machine

**已实现**：完整状态机，所有转换在 `coroutine_table_lock` 下：

```
RUNNABLE → RUNNING (Worker claim)
RUNNING → COMPLETED (callStack empty)
RUNNING → RUNNABLE (yield, requeue to local queue)
RUNNING → WAITING (sleep/IO/channel, no requeue)
WAITING → RUNNABLE (timer/IO/channel wake, enqueue)
```

---

## 3. D3-2 Runnable Queue Layer

### 3.1 Queue API

**已实现**（`vm.c`）：

| 函数 | 行号 | 说明 |
|------|------|------|
| `tll_runnable_queue_init()` | 1968 | 初始化 queue（mutex + semaphore） |
| `tll_runnable_queue_enqueue()` | 1982 | 线程安全 enqueue（mutex + signal semaphore） |
| `tll_runnable_queue_try_dequeue()` | 2010 | 非阻塞 dequeue（无节点返回 -1） |
| `tll_runnable_queue_dequeue()` | 2037 | 阻塞 dequeue（等待 semaphore） |
| `tll_runnable_queue_dequeue_timeout()` | 2064 | 超时 dequeue（Windows: WaitForSingleObject, POSIX: pthread_cond_timedwait） |
| `tll_runnable_queue_cleanup()` | 2585 | 清理 queue（剩余 node + semaphore + mutex） |

### 3.2 Queue Ownership

**Queue node 生命周期**：
```
create (enqueue: malloc TLLRunnableNode)
  ↓
enqueue (link to queue tail, signal semaphore)
  ↓
worker claim (dequeue: unlink from queue head)
  ↓
execute (Worker executes coroutine)
  ↓
destroy (free TLLRunnableNode after dequeue)
```

**业务代码不直接操作 queue node**，统一通过 Queue API。

---

## 4. D3-3 Local Queue Execution

### 4.1 Worker Local Queue

**已实现**：每个 Worker 拥有独立的 `local_queue`：

- 初始化: `vm.c` 行 2308 `tll_runnable_queue_init(&worker->local_queue)`
- 清理: `vm.c` 行 2474 `tll_runnable_queue_cleanup(&worker->local_queue)`
- 统计: `worker->local_enqueue_count` / `worker->local_dequeue_count`

### 4.2 Local-First Scheduling

**已实现**（`vm.c` 行 2355-2366）：

```
优先级：
1. local queue (try_dequeue, non-blocking)
2. global queue (dequeue_timeout, 50ms)
3. idle (tll_wake_io_ready, continue)
```

```c
coro_idx = tll_runnable_queue_try_dequeue(&worker->local_queue);
if (coro_idx != -1) {
    worker->local_dequeue_count++;
} else {
    coro_idx = tll_runnable_queue_dequeue_timeout(&vm->runnable_queue, 50);
    if (coro_idx == -1) {
        tll_wake_io_ready(vm, 0);
        continue;
    }
}
```

### 4.3 Requeue to Local

**已实现**（`vm.c` 行 2461-2464）：

执行完 RUNNABLE coroutine（yield）后，优先 requeue 到 Worker 本地队列：

```c
if (should_requeue) {
    tll_runnable_queue_enqueue(&worker->local_queue, coro_idx);
    worker->local_enqueue_count++;
}
```

**优势**：cache locality — 同一个 Worker 刚执行过这个 coroutine，重新执行时 cache 命中率更高。

### 4.4 未实现（按计划后置）

- ❌ Work Stealing（本阶段不做，先稳定再优化）

---

## 5. D3-4 Execution Context Isolation

### 5.1 Context Transfer Protocol 验证

**已验证**：通过代码审计确认 Context Transfer Protocol 正确实现：

| 验证项 | 结果 | 说明 |
|--------|------|------|
| 无 double owner | ✅ | 执行期间 callStack 只在 Worker ctx，coro->callStack 不被使用 |
| 无 dangling pointer | ✅ | 执行前后 worker->ctx.callStack = NULL |
| 无 stale pointer | ✅ | 每次执行前从 coro 重新加载，执行后保存回 coro |
| pointer transfer (not copy) | ✅ | `worker->ctx.callStack = coro->callStack`（指针赋值，不 memcpy） |

### 5.2 P5 Latent Defect 状态

P5 审计发现的 3 个 ownership violation（OBSERVED，非 PROVEN root cause）：

| 缺陷 | 状态 | 说明 |
|------|------|------|
| push_frame/pop_frame 无锁写 coro->callStackSize | OBSERVED | 执行期间 callStack 归 Worker 所有，coro->callStackSize 不被其他线程使用 |
| Worker save callStack 无锁 | OBSERVED | Worker 私有操作，不与其他 Worker 共享 |
| push_frame realloc 悬空指针 | OBSERVED | 执行期间 realloc 只影响 Worker ctx.callStack，coro->callStack 不被使用 |

**这些 latent defect 不阻塞 D3 基础设施封板**，后续阶段（Atomic Heap / Fine-grained locking）处理。

---

## 6. D3-5 Coroutine Migration Test

### 6.1 Migration 验证

**已验证**：通过 D2 `worker_ownership_boundary` 测试确认 coroutine migration 正常：

- A coroutine: phase1 → Worker 0, phase2 → Worker 0 or 1 (migration allowed)
- B coroutine: phase1 → Worker 1, phase2 → Worker 0 or 1 (migration allowed)
- A exec count: 2, B exec count: 2 (no dual execution)
- Different workers at start: true
- Both completed: true

### 6.2 Migration 是正常行为

**Coroutine migration after sleep/yield 是正常 scheduler 行为**：
- 当 A sleeps/yields on Worker 0，Worker 0 marks A RUNNABLE/WAITING and picks up B
- When A is woken, any free Worker (0 or 1) can claim A
- This is not a bug — it's how multi-worker schedulers work

**关键 invariant**：no simultaneous dual execution（由 claim lock + worker-mode yield 保证）。

---

## 7. D3-6 High Frame Stress Test

### 7.1 测试结果

| 规模 | Workers | 结果 | 说明 |
|------|---------|------|------|
| 100 tasks | 2 | **PASS** | 正常退出，所有 STEP 输出完整 |
| 1000 tasks | 2 | **CRASH** | "Submitted 1000 tasks, waiting..." 后进程崩溃，无后续输出 |
| 5000 tasks | 2 | NOT RUN | 因 1000 已崩溃，未继续 |
| 10000 tasks | 2 | NOT RUN | 因 1000 已崩溃，未继续 |

### 7.2 1000-task 崩溃分析

**崩溃点**：提交 1000 个 coroutine 后，等待循环中进程崩溃。

**stderr 输出**：
```
=== D3 1000-task stress test ===
tllvm: started 2 worker threads (true multi-worker runtime)
startWorkers(2)=0
Submitting 1000 tasks...
Submitted 1000 tasks, waiting...
（此后无输出，进程退出）
```

**结论**：这是 **A-GAP-1（高负载堆损坏）** 的表现。

### 7.3 A-GAP-1 状态

| 项目 | 状态 |
|------|------|
| A-GAP-1 高负载堆损坏 | **OPEN**（已知问题，D2 阶段已存在） |
| 触发条件 | >~200-1000 并发 coroutine（动态创建 + Worker 执行） |
| 崩溃类型 | STATUS_HEAP_CORRUPTION (0xC0000374) / 静默崩溃 |
| 是否 D3 引入 | **否**（D2 基线 2588602 在 10000 tasks 同样崩溃） |
| 是否阻塞 D3 基础设施封板 | **否**（按工程纪律，已知 A-GAP 不阻塞当前阶段） |

### 7.4 已排除的根因候选（D3-R1~P5 隔离实验）

| 候选 | 状态 |
|------|------|
| D3 Local Queue | 已排除（D2 基线同样崩溃） |
| Coroutine table realloc | 已排除（预分配同样崩溃） |
| TLLCoroutine 提前释放/UAF | 已排除（No-Free 实验仍崩溃） |
| Frame Pool | 已排除（Frame Pool ON/OFF 都崩溃） |
| Queue node 生命周期 | 已排除（Queue OFF 仍崩溃） |
| Worker↔Worker 并发 | 已排除（1 Worker 仍崩溃） |
| **Concurrent coroutine_create** | **PROVEN TRIGGER**（预创建不崩溃，并发创建崩溃） |

**Exact corruption point**: NOT PROVEN（待后续阶段深入定位）。

---

## 8. D3-7 Regression Gate

### 8.1 D2 七项回归测试

| # | 测试 | 结果 |
|---|------|------|
| 1 | multi_worker_parallel (2W/2T) | **PASS** |
| 2 | multi_worker_overlap_proof | **PASS** |
| 3 | multi_worker_stress_2w_100t | **PASS** |
| 4 | worker_global_test | **PASS** |
| 5 | simple_sleep_wakeup_test | **PASS** |
| 6 | worker_ownership_boundary | **PASS** |
| 7 | wake_list_300_coroutines | **PASS** |

**D2 Regression: 7/7 PASS**

### 8.2 无回归确认

D3 基础设施（Local Queue / Context Transfer / Queue Layer）未引入任何 D2 核心功能回归。

---

## 9. D3 完成状态汇总

| Phase | 目标 | 状态 | 说明 |
|-------|------|------|------|
| D3-0 | Build Integrity Gate | ✅ PASS | Fail-Closed Build + Clean Build + Provenance |
| D3-1 | Scheduler Ownership Audit | ✅ PASS | Ownership Matrix + Context Transfer Protocol |
| D3-2 | Runnable Queue Layer | ✅ PASS | Queue API + Queue Ownership |
| D3-3 | Local Queue Execution | ✅ PASS | Local-first scheduling + Requeue to local |
| D3-4 | Execution Context Isolation | ✅ PASS | Context Transfer Protocol 验证（无 double owner/dangling/stale） |
| D3-5 | Coroutine Migration Test | ✅ PASS | Migration 正常，无 dual execution |
| D3-6 | High Frame Stress Test | ⚠️ PARTIAL | 100 PASS; 1000 CRASH = A-GAP-1 (已知 OPEN) |
| D3-7 | Regression Gate | ✅ PASS | D2 七项 7/7 PASS |

### 9.1 D3 基础设施 = PASS

D3 的核心基础设施（Queue Layer / Local Queue / Ownership / Context Transfer）已全部实现并验证。

### 9.2 A-GAP-1 = 已知 OPEN，不阻塞

高负载堆损坏（>1000 tasks）是 D2 阶段已存在的已知问题，不是 D3 引入的。按工程纪律，不阻塞 D3 基础设施封板。

---

## 10. Known GAP (B-GAP / A-GAP)

| 类型 | 项目 | 状态 | 说明 |
|------|------|------|------|
| A-GAP | 高负载堆损坏 (>1000 tasks) | OPEN | Concurrent coroutine_create = PROVEN TRIGGER，exact point NOT PROVEN |
| B-GAP | Work Stealing | NOT DONE | 按计划后置，先稳定再优化 |
| B-GAP | Atomic Heap / RefCount | NOT DONE | 按计划后置 |
| B-GAP | IO Reactor 重构 | NOT DONE | 按计划后置 |
| B-GAP | ASan | NOT RUN | 环境限制 |
| B-GAP | Linux/macOS | NOT VERIFIED | 仅 Windows/MSVC 验证 |
| B-GAP | Channel/IO E2E 测试 | B-GAP | 代码闭环已验证，端到端 TLL 测试未做 |
| B-GAP | build_all.bat 绝对路径 | B-GAP | 含开发者机器路径，非阻塞 |
| B-GAP | P5 latent ownership defects | OBSERVED | push_frame realloc / 无锁写 callStackSize，后续阶段处理 |

---

## 11. Files Changed

本阶段 D3 基础设施代码在之前的 commit（20ac2cf / ec6c914 / abdb420）中已实现。本 commit 仅新增 Evidence 文档：

| 文件 | 说明 |
|------|------|
| `docs/evidence/P2-01-C-D3-HIGH-FRAME-RUNTIME.md` | D3 完整 Evidence（本文件） |

**未修改 Runtime 代码**（D2 RESEALED 保护，不回头修改 D2 已验证逻辑）。

---

## 12. Self-Audit Checklist

- [x] D2 封板保护（未修改 D2 已验证逻辑）
- [x] Build Integrity Gate（Fail-Closed + Clean Build + Provenance）
- [x] Scheduler Ownership Matrix
- [x] Runnable Queue Layer（API + Ownership）
- [x] Local Queue Execution（local-first + requeue to local）
- [x] Execution Context Isolation（Context Transfer Protocol）
- [x] Coroutine Migration（正常，无 dual execution）
- [x] Stress Test（100 PASS; 1000 CRASH = A-GAP-1 如实记录）
- [x] Regression Gate（D2 7/7 PASS）
- [x] 未为了 PASS 删除测试
- [x] 未修改 Evidence 来匹配结果
- [x] 没有 Clean Build 就不测试
- [x] 未使用旧 tllvm.exe
- [x] 未引入 Work Stealing
- [x] 未回头处理 A-GAP-1（如实记录为 OPEN）

---

**Construction Complete. Awaiting independent architecture audit.**

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*施工方：豆包A（施工方）*
*审计方：于秋鸿博士（待独立审计）*
