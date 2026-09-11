# TLL OS Architecture — Truth Document

> **本文档是 TLL OS 的架构真相层（Truth Layer）。**
> 任何 Agent 接入 TLL OS，必须先读取本文档，了解 TLL OS 的真实架构、已完成的能力边界、已知的限制和风险。
>
> **原则：没有 Evidence，不生成 Claim。**

---

## 1. TLL OS 是什么

TLL OS 是**全球独有的 AI-Native 操作系统**，从底层重新设计 AI Agent 的执行底座。

- **不是**：Linux 内核修改版、Windows 子系统、macOS 模拟器
- **不是**：某编程语言的运行时库、Web 框架、容器编排系统
- **是**：自主设计的操作系统 + 自主设计的编程语言（TLL）+ 自主设计的 Runtime

### 核心定位

```
TLL OS
├── TLL Language (全球独有编程语言)
├── TLL Runtime (AI Agent 执行底座)
├── Canonical Layer (Truth Layer / Identity / Engineering Protocol)
├── Agent Runtime (AI Agent 执行层)
└── Desktop Robot OS (AI Computer)
```

---

## 2. 分层架构

### 2.1 自底向上

```
┌─────────────────────────────────┐
│  Desktop Robot OS (AI Computer) │  ← P3 (未来)
│  Device / Vision / Audio / GUI  │
├─────────────────────────────────┤
│  Agent Runtime                  │  ← P2-03 (下一阶段)
│  Agent Lifecycle / Memory / Tool│
├─────────────────────────────────┤
│  Canonical Layer (Truth Layer)  │  ← P2-02 (当前阶段)
│  Identity / Truth / Engineering │
├─────────────────────────────────┤
│  Runtime Core v0 (Sealed)       │  ← P2-01-C (已封板)
│  Dynamic Frame / Multi-Worker   │
│  Scheduler / WAIT-WAKE          │
├─────────────────────────────────┤
│  TLL Language                   │  ← P0/P2-01-B (已完成)
│  Lexer / Parser / TypeChecker   │
│  Codegen / Linker / VM          │
└─────────────────────────────────┘
```

### 2.2 各层职责

| 层 | 职责 | 当前状态 |
|----|------|----------|
| TLL Language | 词法/语法/类型检查/代码生成 | 已完成（P0/P2-01-B） |
| Runtime Core v0 | 协程/帧/Worker/调度/WAIT-WAKE | 已封板（条件封板） |
| Canonical Layer | 身份/真相/工程协议/Agent 宪法 | 当前阶段（Genesis） |
| Agent Runtime | Agent 生命周期/记忆/工具调用/任务调度 | 下一阶段（P2-03） |
| Desktop Robot OS | 设备抽象/视觉/音频/传感器/GUI | 未来阶段（P3） |

---

## 3. Runtime Core v0 真相

### 3.1 已完成的能力

✅ **Dynamic Frame（动态帧管理）**
- frame_pool_acquire/release
- 动态寄存器分配
- locals 动态扩容
- callStack 动态扩容

✅ **True Multi-Worker Runtime**
- Per-Worker ExecutionContext
- Global Runnable Queue
- Worker Claim Exactly-Once
- Worker/Legacy Scheduler Boundary
- WAIT/WAKE Mechanism（Sleep/IO/Channel）
- Wake List Exact-Once enqueue
- Malloc Fail-Closed
- 16 字节 Coroutine Identity Guard（magic+generation）

✅ **Build Integrity**
- Fail-Closed Build（编译失败立即终止）
- Clean Build provenance（binary SHA256）
- 可信执行闭环（Source → Build → Binary → Test → Evidence）

### 3.2 已知限制

⚠️ **A-GAP-1: 10K+ coroutine 概率性崩溃**
- 触发条件：并发 coroutine_create + Worker 执行
- 崩溃位置：TLLCoroutine header offset 0-8
- 性质：概率性崩溃（~33% at 10K coroutine）
- 缓解：16 字节 magic+generation identity guard（layout mitigation，非真正修复）
- 状态：MITIGATED / ROOT CAUSE PENDING

⚠️ **B-GAPs（非阻塞）**
- Channel/IO E2E TLL 测试未验证
- AddressSanitizer 未集成
- Linux/macOS 未验证
- Full Native regression 未验证
- build_all.bat 含开发者机器绝对路径

### 3.3 测试结果真相

| 测试类别 | 结果 | 说明 |
|----------|------|------|
| D2 核心测试（7/7） | ✅ 全部 PASS | Clean Build 验证 |
| D3 基础设施测试 | ✅ 全部 PASS | Context Transfer / Migration 100 |
| Stress 100/1000/5000 | ✅ 稳定 PASS | |
| Stress 10000 | ⚠️ 2/3 PASS | 概率性 ACCESS_VIOLATION（A-GAP-1） |

---

## 4. 能力边界真相

### 4.1 TLL OS 现在能做什么

✅ AI Agent 执行引擎（中低并发，< 5000 coroutine）
- 多 Agent 并行执行
- Agent 间通信（Channel）
- Agent 睡眠/唤醒（Sleep）
- Agent IO 等待（IO WAIT）

✅ 桌面机器人操作系统的 Runtime 底座
- 任务调度
- 设备控制协程
- 传感器数据处理
- 事件循环

✅ TLL 语言原生自托管运行时
- TLL 字节码执行
- 动态内存管理
- 多 Worker 并行

### 4.2 TLL OS 现在不能做什么

❌ 10K+ 高并发生产环境（A-GAP-1 概率性崩溃）
❌ 硬实时系统（无实时调度保证）
❌ 跨平台生产部署（仅 Windows 验证）
❌ 商业级稳定性（无工业级测试覆盖）

---

## 5. 工程原则真相

### 5.1 没有 Evidence，不生成 Claim

这是 TLL OS 的第一工程原则：
- 任何功能声明必须有 Evidence 支撑
- Evidence 必须包含：commit SHA + test result + CI status + risk assessment
- 证据等级必须明确区分：OBSERVED / INFERRED / UNVERIFIED / PROVEN / RULED OUT
- 禁止把猜测写成结论，禁止把"可能"写成"已证明"

### 5.2 小步实现，每阶段独立验收

- 每个阶段（Phase）都有明确的目标和验收标准
- 每个阶段完成后，由独立审计方（架构师）审计真实代码，不直接采信施工方报告
- 审计 PASS 后才进入下一阶段
- 禁止一次把所有功能做完再验收

### 5.3 封板保护

- 已封板的阶段（如 D2）不随意修改
- 新功能在新分支上开发
- 新功能通过独立审计后才能合并
- 禁止为了通过测试而修改测试或 Evidence

### 5.4 如实记录风险

- 已知限制（A-GAPs / B-GAPs）必须如实记录
- 禁止把"已缓解"写成"已修复"
- 禁止把"条件通过"写成"完全通过"
- 禁止把"开发基线"写成"生产就绪"

---

## 6. 路线图真相

### 6.1 已完成

```
P0-RUNTIME-07/08: 基础 Runtime ✅ SEALED
P2-01-B11/B12: 所有权系统 / Native Target ✅ SEALED
P2-01-C: Runtime Foundation
  ├── D1 Dynamic Frame ✅ PASS WITH B-GAPS
  ├── D2 Multi-Worker ✅ PASS / RESEALED
  └── D3 High-Frame Runtime ⚠️ CONDITIONAL SEAL
```

### 6.2 当前阶段

```
P2-02: Canonical Layer (当前)
  ├── Identity (Genesis / Runtime Identity / Protocol Version)
  ├── Truth (Architecture / Evidence Rules / Engineering Protocol)
  └── Agents (Agent Contract / Agent Capability)
```

### 6.3 未来阶段

```
P2-03: Agent Runtime Foundation (下一阶段)
  ├── Agent Lifecycle
  ├── Agent Memory
  ├── Tool Calling
  ├── Task Scheduling
  └── Permission Model

P3: Desktop Robot OS (未来)
  ├── Device Abstraction
  ├── Vision Pipeline
  ├── Audio / Sensor Bus
  ├── Robot Memory
  ├── Agent Scheduler
  ├── GUI Compositor
  └── Hardware Driver ABI
```

---

## 7. 外部 Agent 接入指南

任何 Agent（Claude / 豆包 / OpenClaw / Codex / 未来机器人 Agent）接入 TLL OS，必须：

1. **读取 Genesis**：了解 TLL OS 是什么、不是什么
2. **读取 Runtime Identity**：了解 Runtime Core v0 的真实能力边界
3. **读取 Evidence Rules**：了解 TLL OS 的工程证据规范
4. **读取 Engineering Protocol**：了解如何生成 Claim 和 Evidence
5. **读取 Agent Contract**：了解 Agent 接入 TLL OS 的权利和义务
6. **读取 Agent Capability**：了解 Agent 可以调用哪些能力

**禁止：**
- 不读文档就声称"我已经了解 TLL OS"
- 把 TLL OS 等同于其他操作系统或编程语言
- 基于假设生成 Claim
- 隐瞒已知限制和风险

---

*本文档是 TLL OS 的 Truth Layer，任何与本文档不一致的说法，以本文档为准。*
*最后更新：2026-09-11*
