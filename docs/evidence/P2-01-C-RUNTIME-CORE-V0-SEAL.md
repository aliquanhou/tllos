# P2-01-C: Runtime Core v0 — Final Seal Document

**Status:** RUNTIME CORE V0 SEALED (Conditional)
**Project:** TLL OS — Runtime Foundation
**Date:** 2026-09-11
**Architect:** 于秋鸿博士
**Implementer:** 豆包A（施工方）

---

## 0. Executive Summary

**TLL Runtime Core v0 正式封板。**

经过 P2-01-C 三个阶段（D1 Dynamic Frame、D2 Multi-Worker、D3 High-Frame Runtime）的迭代开发和独立审计，TLL Runtime Core v0 已具备 AI Agent 执行底座的基础能力。

**核心能力：**
- ✅ Dynamic Frame（动态帧管理）
- ✅ True Multi-Worker Runtime（真正的多 Worker 并行执行）
- ✅ High-Frame Execution Infrastructure（高帧率执行基础设施）
- ✅ Runnable Queue System（全局/本地可运行队列）
- ✅ Context Transfer Protocol（执行上下文转移协议）
- ✅ Coroutine Migration（协程迁移）
- ✅ WAIT/WAKE Mechanism（Sleep/IO/Channel 等待唤醒）
- ✅ Build Integrity（可信构建闭环）

**已知限制：**
- ⚠️ A-GAP-1: 10K+ coroutine 高并发概率性崩溃（MITIGATED，非阻塞）
- ⚠️ B-GAPs: Channel/IO E2E 测试、ASan、Linux/macOS、Full Native regression 未验证

**适用场景：**
- AI Agent 执行引擎（中低并发，< 5000 coroutine）
- 桌面机器人操作系统的 Runtime 底座
- TLL 语言的原生自托管运行时
- 后续 Agent Runtime / Desktop Robot OS 的基础层

---

## 1. Module Status Summary

### 1.1 D1: Dynamic Frame

| 模块 | 状态 | 说明 |
|------|------|------|
| Dynamic Frame Allocation | ✅ PASS | frame_pool_acquire/release，动态分配/释放帧 |
| Frame Register Management | ✅ PASS | 按函数 maxRegister 分配寄存器 |
| Frame Locals Management | ✅ PASS | 动态 realloc locals 数组 |
| Frame Stack (callStack) | ✅ PASS | TLLFrame ** 数组，动态扩容 |
| Push/Pop Frame | ✅ PASS | push_frame/pop_frame，callStackSize 同步 |

**D1 状态：PASS WITH B-GAPS**（ASan、跨平台未验证）

### 1.2 D2: True Multi-Worker Runtime

| 模块 | 状态 | 说明 |
|------|------|------|
| Per-Worker ExecutionContext | ✅ PASS | TLLWorker 独立 TLLExecutionContext，TLS g_tll_current_worker |
| Global Runnable Queue | ✅ PASS | 全局可运行队列，semaphore 同步 |
| Worker Claim Exactly-Once | ✅ PASS | coroutine_table_lock 保护 RUNNABLE→RUNNING 转换 |
| Worker/Legacy Scheduler Boundary | ✅ PASS | Worker 模式下 coroutine_yield() 不内部切换 coroutine |
| WAIT/WAKE Mechanism | ✅ PASS | Sleep/IO/Channel 三种等待，wake list exact-once enqueue |
| Sleep Wake | ✅ PASS | tll_wake_expired_sleepers，wakeTime 到期唤醒 |
| Channel Wake | ✅ PASS | coroutine_wake_channel，waitingChannel 唤醒 |
| IO Wake | ✅ PASS | tll_wake_io_ready，select() + waitingFd 唤醒 |
| Wake List Exact-Once | ✅ PASS | 只记录实际 WAITING→RUNNABLE 的 coroutine，malloc fail-closed |
| Malloc Failure Fail-Closed | ✅ PASS | wakeList malloc 失败不改变 coroutine 状态 |
| State Semantics | ✅ PASS | RUNNABLE=0, RUNNING=1, WAITING=2, COMPLETED=3，无魔法数字 |
| Worker Shutdown | ✅ PASS | shutdown_workers，正确 join，VM free 前停止 Worker |
| 300 Coroutine Deterministic Test | ✅ PASS | 300/300 completed，1 Worker，sleep 30ms |

**D2 状态：PASS / RESEALED**（基线 e1b6e8f，7/7 核心测试 PASS）

**D2 7/7 Core Tests:**
1. multi_worker_parallel ✅
2. multi_worker_overlap_proof ✅
3. multi_worker_stress_2w_100t ✅
4. worker_global_test ✅
5. simple_sleep_wakeup_test ✅
6. worker_ownership_boundary ✅
7. wake_list_300_coroutines ✅

### 1.3 D3: High-Frame Runtime Execution

| 模块 | 状态 | 说明 |
|------|------|------|
| Build Integrity Gate | ✅ PASS | Fail-Closed Build，Clean Build provenance，binary SHA256 |
| Scheduler Ownership Audit | ✅ PASS | Ownership Matrix，所有共享对象分类 |
| Runnable Queue Layer | ✅ PASS | 6 个 Queue API，queue node 生命周期验证 |
| Local Queue Execution | ✅ PASS | local-first scheduling，执行完重新入本地队列 |
| Execution Context Isolation | ✅ PASS | Context Transfer Protocol，context_transfer_test PASS |
| Coroutine Migration Test | ✅ PASS | d3_migration_100: 100 coroutines, exec=200, no dual/lost |
| Regression Gate | ✅ PASS | D2 7/7 PASS |
| High Frame Stress (100/1000/5000) | ✅ PASS | 稳定 PASS |
| High Frame Stress (10000) | ⚠️ CONDITIONAL | 2/3 PASS，概率性 ACCESS_VIOLATION（A-GAP-1） |

**D3 状态：CONDITIONAL SEAL**（基线 437ff8b，A-GAP-1 MITIGATED）

---

## 2. A-GAP-1: Known Limitation

### 2.1 Status

```
A-GAP-1: MITIGATED / ROOT CAUSE PENDING
  ├── Trigger: Concurrent coroutine_create + Worker execution  [PROVEN]
  ├── Crash location: TLLCoroutine header offset 0-8            [PROVEN]
  ├── Original struct: overwrites callStack pointer              [PROVEN]
  ├── Nature: Probabilistic crash                                [PROVEN]
  ├── Not UAF                                                     [PROVEN]
  ├── Not partial publish (H4)                                    [PROVEN / RULED OUT]
  ├── Not memcpy size error (H2)                                  [PROVEN / RULED OUT]
  ├── Exact writer: NOT FOUND                                     [OPEN]
  ├── ROOT CAUSE: OPEN
  ├── MITIGATION: EXISTS (16-byte identity guard)
  └── FIX: NONE
```

### 2.2 Mitigation

**16 字节 magic+generation identity guard**（layout mitigation，非 memory safety fix）：

```c
typedef struct {
    unsigned long long magic;       /* offset 0-7: UAF detection */
    unsigned long long generation;  /* offset 8-15: reuse detection */
    TLLFrame **callStack;           /* offset 16-23: protected from OOB write */
    ...
} TLLCoroutine;
```

**作用：** OOB 写入（offset 4-7）只覆盖 magic 高 4 字节，不影响 callStack 指针。

### 2.3 Risk Assessment

| 规模 | 风险等级 | 说明 |
|------|----------|------|
| < 1000 coroutine | 🟢 LOW | 稳定 PASS |
| 1000-5000 coroutine | 🟡 MEDIUM | 稳定 PASS（测试次数有限） |
| 10000+ coroutine | 🟠 HIGH | 2/3 PASS，约 33% 概率性崩溃 |

### 2.4 Future Requirement

**Runtime Hardening 阶段必须解决 A-GAP-1：**
1. 找到 exact writer（OOB 写入源头）
2. 真正修复 OOB 写入（不是 layout mitigation）
3. 验证 10000 coroutine stress 稳定 PASS（20/20+）
4. 可选：移除 16 字节 identity guard（或保留作为额外安全层）

---

## 3. B-GAPs (Non-Blocking)

| B-GAP | 说明 | 状态 |
|-------|------|------|
| Channel/IO E2E TLL Tests | Channel/IO 完整端到端测试未验证 | NON-BLOCKING |
| ASan | AddressSanitizer 未集成/运行 | NON-BLOCKING |
| Linux/macOS | 跨平台测试未验证 | NON-BLOCKING |
| Full Native Regression | 完整原生回归测试未验证 | NON-BLOCKING |
| build_all.bat 绝对路径 | 含开发者机器绝对路径（C:\Users\Administrator\Doubao\tllos） | NON-BLOCKING |
| Work Stealing | 按计划后置 | NON-BLOCKING |
| Atomic Heap | 按计划后置 | NON-BLOCKING |
| IO Reactor 大改 | 按计划后置 | NON-BLOCKING |

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

### 4.2 D3 Infrastructure Tests

| Test | Result |
|------|--------|
| context_transfer_test | PASS |
| d3_migration_100 | PASS (100 coroutines, exec=200, no dual/lost) |
| hello_test | PASS |
| gate2_single_coroutine | PASS |
| gate3_single_worker | PASS |
| gate4_two_workers | PASS |

### 4.3 D3 Stress Tests

| Scale | Result | Note |
|-------|--------|------|
| 100 tasks | PASS | 稳定 |
| 1000 tasks | PASS | 稳定 |
| 5000 tasks | PASS | 稳定 |
| 10000 tasks | 2/3 PASS | 概率性 ACCESS_VIOLATION（A-GAP-1） |

### 4.4 Build Integrity

- Clean Build: SUCCESS
- Fail-Closed Build: 有效（编译失败立即终止，不链接旧 .obj）
- Binary SHA256: 已记录
- Source Commit: 可追溯

---

## 5. Capability Boundaries

### 5.1 Supported Use Cases

✅ **AI Agent 执行引擎**（中低并发，< 5000 coroutine）
- 多 Agent 并行执行
- Agent 间通信（Channel）
- Agent 睡眠/唤醒（Sleep）
- Agent IO 等待（IO WAIT）

✅ **桌面机器人操作系统 Runtime 底座**
- 任务调度
- 设备控制协程
- 传感器数据处理
- 事件循环

✅ **TLL 语言原生自托管运行时**
- TLL 字节码执行
- 动态内存管理
- 多 Worker 并行

### 5.2 Not Recommended Use Cases

❌ **10K+ 高并发生产环境**（无额外稳定性保障）
- A-GAP-1 概率性崩溃
- 需要等待 Runtime Hardening 阶段

❌ **硬实时系统**
- 无实时调度保证
- 无优先级调度

❌ **跨平台生产部署**（Linux/macOS 未验证）
- 当前仅 Windows 验证
- 需要跨平台测试

---

## 6. Architecture Summary

### 6.1 Runtime Architecture

```
TLL Runtime Core v0
│
├── Execution Layer
│   ├── TLLVM (Virtual Machine)
│   ├── TLLFrame (Dynamic Frame)
│   ├── TLLCoroutine (Coroutine)
│   └── TLLExecutionContext (Per-Worker Context)
│
├── Scheduler Layer
│   ├── Global Runnable Queue
│   ├── Worker Local Queue
│   ├── Worker Claim (exactly-once)
│   └── WAIT/WAKE Mechanism
│       ├── Sleep Wake (wakeTime)
│       ├── IO Wake (waitingFd + select)
│       └── Channel Wake (waitingChannel)
│
├── Worker Layer
│   ├── TLLWorker (Worker Thread)
│   ├── TLS g_tll_current_worker
│   ├── Worker/Legacy Scheduler Boundary
│   └── Shutdown Protocol
│
└── Safety Layer
    ├── Coroutine Identity Guard (magic+generation)
    ├── Coroutine Table Lock
    ├── Wake List Exact-Once
    ├── Malloc Fail-Closed
    └── Build Integrity (Fail-Closed Build)
```

### 6.2 Key Design Decisions

1. **Per-Worker ExecutionContext**：每个 Worker 独立上下文，避免共享状态竞争
2. **Global + Local Queue**：全局队列提交，本地队列优先执行（local-first）
3. **Worker Claim Exactly-Once**：coroutine_table_lock 保护 RUNNABLE→RUNNING 转换
4. **Worker/Legacy Boundary**：Worker 模式下 coroutine_yield() 不内部切换 coroutine，返回 Worker outer loop
5. **Wake List Exact-Once**：只记录实际 WAITING→RUNNABLE 的 coroutine，不扫描全部 RUNNABLE
6. **Malloc Fail-Closed**：wakeList malloc 失败不改变 coroutine 状态，不丢 wake
7. **Coroutine Identity Guard**：16 字节 magic+generation，检测 UAF 和复用，同时吸收 OOB 写入
8. **Fail-Closed Build**：编译失败立即终止，不链接旧 .obj，保证执行二进制可信

---

## 7. Evidence Documents

| 文档 | 说明 | Commit |
|------|------|--------|
| P2-01-C-D2-TRUE-MULTI-WORKER.md | D2 完整 Evidence | e1b6e8f |
| P2-01-C-D3-BUILD-INTEGRITY-RECOVERY.md | Build Integrity Recovery | ec6c914 |
| P2-01-C-D2-WORKER-HANG-RECOVERY.md | D2 Worker HANG Recovery | abdb420 |
| P2-01-C-D2-REVALIDATION.md | D2 Revalidation (7/7) | e1b6e8f |
| P2-01-C-D3-HIGH-FRAME-RUNTIME.md | D3 完整 Evidence | 0723eac |
| P2-01-C-D3-A-GAP1-ROOT-CAUSE.md | A-GAP1 Root Cause Isolation | 364c917 |
| P2-01-C-D3-A-GAP1-SOURCE-TRACE.md | A-GAP1 Source Trace | 5849d0c |
| P2-01-C-D3-A-GAP1-FINAL-SOURCE-PROOF.md | A-GAP1 Final Source Proof | 4357eb0 |
| P2-01-C-D3-SEAL-CONDITION.md | D3 Conditional Seal | 437ff8b |
| P2-01-C-RUNTIME-CORE-V0-SEAL.md | 本文件（Runtime Core v0 总封板） | (当前提交) |

---

## 8. Roadmap

### 8.1 Immediate Next Steps

1. **Runtime Core v0 封板** ✅（本文档）
2. **TLL Canonical Layer 启动**（并行）
   - tllos.com 官网
   - Language / Runtime / Agent Protocol / Engineering Evidence
3. **Agent Runtime 设计**
   - AI Agent Execution Layer
   - Agent 通信协议
   - Agent 调度策略

### 8.2 Runtime Hardening Phase (Future)

**必须解决 A-GAP-1：**
- 找到 exact writer（OOB 写入源头）
- 真正修复 OOB 写入
- 10000 coroutine stress 稳定 PASS
- ASan 集成
- 跨平台验证（Linux/macOS）

### 8.3 Desktop Robot OS Phase

```
TLL Runtime Core v0
    ↓
TLL Agent Runtime
    ↓
Desktop Computer Control
    ↓
Robot Hardware Abstraction
    ↓
Desktop Robot OS
    ↓
AI Computer
```

**需要新增：**
- Device abstraction
- Vision pipeline
- Audio
- Sensor bus
- Robot memory
- Agent scheduler
- GUI compositor
- Hardware driver ABI

---

## 9. Architect Sign-off

**裁决人：** 于秋鸿博士
**日期：** 2026-09-11
**裁决：** P2-01-C Runtime Core v0 = SEALED (Conditional)

> TLL Runtime Core v0 经过 D1/D2/D3 三个阶段的迭代开发和独立审计，已具备 AI Agent 执行底座的基础能力。D2 Multi-Worker 完全封板，D3 High-Frame Runtime 条件封板（A-GAP-1 MITIGATED）。
>
> A-GAP-1 为已知概率性崩溃（10K+ coroutine，约 33% 崩溃率），通过 16 字节 identity guard 进行 layout mitigation，非真正 memory safety fix。允许进入后续阶段，但要求未来 Runtime Hardening 阶段必须解决 A-GAP-1。
>
> 不要继续陷入 A-GAP-1 黑洞。把 TLL Runtime v0 封板，把燃料点燃，进入 AI Computer / Desktop Robot OS 阶段。

---

## 10. Implementer Sign-off

**施工方：** 豆包A（施工方）
**日期：** 2026-09-11
**确认：**

- ✅ 所有源码修改已提交并 push 到远程仓库
- ✅ 所有 Evidence 文档已提交
- ✅ D2 7/7 回归测试 PASS
- ✅ D3 基础设施测试 PASS
- ✅ D3 stress 100/1000/5000 PASS
- ✅ D3 stress 10000 2/3 PASS（A-GAP-1，已知限制）
- ✅ Build Integrity 有效（Fail-Closed Build）
- ✅ A-GAP-1 状态如实记录（MITIGATED / ROOT CAUSE PENDING）
- ✅ B-GAPs 如实记录（非阻塞）
- ✅ 未自行宣布 Production Ready
- ✅ 未自行宣布 A-GAP-1 已修复

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*TLL OS Runtime Core v0 — Final Seal*
*项目：TLL OS（aliquanhou/tllos）*
*分支：feature/P2-01-C-D3-runtime-high-frame-execution*
