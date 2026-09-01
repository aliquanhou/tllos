# TLL AI Engineering Foundation v0.4 — Root of Trust & Engineering Cognition Architecture

> 版本: 0.4 (Draft)
> 日期: 2026-09-01
> 状态: 架构评审阶段，待评审后进入 v0.5 或 Phase 1 施工
> 基线: v0.3 (commit 5f0688c) + 架构评审意见

---

## 一、v0.3 评审结论

### 1.1 v0.3 通过的部分

v0.3 的工程世界模型与信任架构方向 **PASS**：

| 设计 | 评审结论 |
|------|----------|
| Identity / Authority / Claim / Evidence / World Model 单独定义 | ✅ 正确 |
| 身份 ≠ 权限 ≠ 可信度 | ✅ 正确拆开 |
| CI 通过 ≠ 生产就绪 | ✅ 正确拆开 |
| World Model 支持工程决策，不只是图数据库 | ✅ 方向正确 |
| 防自升权机制 | ✅ 方向正确 |

### 1.2 v0.3 未解决的最底层问题

v0.3 现在更像一份非常完整的架构宪法，还不是可以直接施工的最终基座。

**最核心的问题**: 谁来验证 Identity Root 本身？

v0.3 的链条：
```
Identity Root → Identity → Authority Token → Agent Action → Evidence → Verification → Truth
```

这个链条已经很好。但是最上面的 **Identity Root** 本身仍然是一个信任锚。

如果最终还是：
- 某个文件
- 某个 JSON
- 某个数据库
- 某个管理员账号
- 某个 Git commit

那么我们只是把：
> "README 是真相"

升级成：
> "Identity Root 文件是真相"

这还没有真正解决问题。

### 1.3 v0.4 目标

v0.4 只解决三个问题：

| # | 问题 | 回答 |
|---|------|------|
| ① | **Root of Trust** | TLL 最终相信什么？为什么相信它？ |
| ② | **Engineering Cognition Layer** | Agent 到底如何"认识"一个 TLL 项目？ |
| ③ | **Trust Transition** | 到底在哪一个瞬间，一个"可能正确的东西"才变成"Canonical Truth"？ |

这三个问题解决了，TLL 的 AI Engineering Foundation 才真正站住。

---

## 二、Root of Trust（信任根）

### 2.1 核心问题

> TLL 最终相信什么？为什么相信它？

**错误答案**:
- ❌ "相信 Identity Root 文件"（文件可以被篡改）
- ❌ "相信管理员账号"（管理员可以作恶或被盗）
- ❌ "相信 Git commit"（Git 历史可以被重写）
- ❌ "相信 GitHub"（第三方平台可以被攻击或修改）
- ❌ "相信某个 Agent"（Agent 可以出错或被攻击）

**正确答案**:

> **TLL 最终相信的不是任何"东西"，而是"可以被独立复现的过程"。**

### 2.2 可复现性根（Reproducibility Root）

TLL 的 Root of Trust 是 **可复现性**：

> 一个声明成为 Canonical Truth，当且仅当它可以被独立复现。

**什么是可复现**:
1. 有明确的验证步骤（测试代码/脚本/命令）
2. 有明确的运行环境定义（OS/编译器/版本/依赖）
3. 任何人在相同环境下运行相同步骤，得到相同结果
4. 结果被记录为 Evidence，有哈希和溯源链

**可复现性为什么是最终信任根**:
- 它不依赖任何个人、组织、文件、系统
- 任何人都可以独立验证
- 即使所有记录都被销毁，真相仍然可以通过重新复现来重建
- 它是数学证明式的信任：真理不是"某本书说的"，而是"可以被独立验证的证明"

### 2.3 四层信任架构

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 0: Reproducibility Root（可复现性根）                 │
│  ─────────────────────────────────────────────────────────   │
│  最终相信：可以被独立复现的工程事实                            │
│  验证方式：任何人重新运行测试，得到相同结果                    │
│  不依赖：任何个人、文件、系统、平台                            │
│                                                               │
│  核心原则：真相不由任何层"定义"，真相由可复现性"保证"。       │
│  各层的作用是"记录、验证、授权"，不是"定义真相"。             │
└──────────────────────────┬──────────────────────────────────┘
                           │ 记录和验证
┌──────────────────────────▼──────────────────────────────────┐
│  Layer 1: Identity Root（身份根）                            │
│  ─────────────────────────────────────────────────────────   │
│  作用：记录谁在什么时候做了什么验证                            │
│  不是：定义真相                                                │
│  防篡改：哈希链 + 签名 + 只追加                                │
│  被篡改的后果：验证记录不可信，但真相仍可通过重新复现验证      │
└──────────────────────────┬──────────────────────────────────┘
                           │ 授权变更记录
┌──────────────────────────▼──────────────────────────────────┐
│  Layer 2: Authority Root（授权根）                           │
│  ─────────────────────────────────────────────────────────   │
│  作用：授权谁可以提交变更记录                                  │
│  不是：授权真相                                                │
│  防篡改：Authorization Token + 范围限制 + 时间限制            │
│  被篡改的后果：变更记录不可信，但真相仍可通过重新复现验证      │
└──────────────────────────┬──────────────────────────────────┘
                           │ 定义验证流程
┌──────────────────────────▼──────────────────────────────────┐
│  Layer 3: Protocol Root（协议根）                            │
│  ─────────────────────────────────────────────────────────   │
│  作用：定义验证和变更的流程                                    │
│  不是：定义真相                                                │
│  防篡改：不可变核心规则 + 特殊授权修改                          │
│  被篡改的后果：流程不可信，但真相仍可通过重新复现验证          │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 关键原则：真相不由任何层定义

| 层 | 作用 | 不是 |
|----|------|------|
| Reproducibility Root | 保证真相可被独立验证 | 不定义真相，真相是验证的结果 |
| Identity Root | 记录谁做了验证 | 不定义真相，只记录验证者身份 |
| Authority Root | 授权谁可以提交记录 | 不定义真相，只授权记录提交 |
| Protocol Root | 定义验证流程 | 不定义真相，只定义如何验证 |

**核心洞察**:

> 即使 Identity Root 被篡改，也只能篡改"谁做了验证"的记录。
> 不能篡改"验证结果是否可复现"。
> 任何人都可以重新运行测试，验证 Truth 声明是否成立。
> 
> 这就是可复现性作为最终信任根的力量。

### 2.5 可复现性的具体要求

一个声明要成为 Canonical Truth，必须满足：

| 要求 | 说明 | 验证方式 |
|------|------|----------|
| **明确的验证步骤** | 测试代码/脚本/命令，可被任何人执行 | 测试文件存在且可运行 |
| **明确的环境定义** | OS/编译器/版本/依赖 | environment.json 或 CI 配置 |
| **确定性结果** | 相同输入得到相同输出 | 多次运行结果一致 |
| **完整的 Evidence** | 结果记录有哈希和溯源链 | Evidence 结构完整 |
| **独立可验证** | 不依赖特定个人或系统 | 第三方可以重新运行 |

**不可复现的声明**:
- ❌ "Agent 说它测试通过了"（没有测试代码）
- ❌ "在我的机器上可以运行"（没有环境定义）
- ❌ "有时候可以通过"（非确定性）
- ❌ "需要特定账号才能验证"（不独立）

这些都不能成为 Canonical Truth，只能标记为 `unverified` 或 `anecdotal`。

### 2.6 可复现性的等级

| 等级 | 说明 | 示例 |
|------|------|------|
| **R0: 不可复现** | 没有验证步骤或环境定义 | Agent 自报"测试通过" |
| **R1: 理论可复现** | 有验证步骤，但环境不明确 | 有测试代码，但没说用什么 OS |
| **R2: 环境可复现** | 有验证步骤和环境定义 | 测试代码 + CI 配置 |
| **R3: 实际复现** | 已在多个环境中复现 | Ubuntu + Windows + macOS 都通过 |
| **R4: 独立复现** | 第三方独立复现 | 非原作者的人/Agent 重新运行通过 |

**成为 Canonical Truth 至少需要 R2（环境可复现），推荐 R3（实际复现）。**

---

## 三、Engineering Cognition Layer（工程认知层）

### 3.1 核心问题

> Agent 到底如何"认识"一个 TLL 项目？

**错误答案**:
- ❌ 让 Agent 读 500 个 Markdown 文档
- ❌ 训练一个"TLL 小模型"
- ❌ RAG 检索文档片段

**正确答案**:

> 让 Agent 能够查询工程世界：What is this? Why does it exist? What depends on it? What proves it? What constrains it? What changed it? What can I safely change? What must I verify after changing it?

### 3.2 关于"神经网络"的修正

**之前的说法**: "我们需要一个丰富的神经网络，让各种 LLM 理解 TLL。"

**修正**: 不建议现在真的把它定义成 Neural Network。

如果现在就叫 "TLL Neural Network"，很容易走偏到：
- 训练模型
- 参数/权重
- Embedding
- RAG
- Fine-tuning

最后花大量时间造一个"小模型"。

**这不是我们真正缺的东西。**

我们真正缺的是 **Engineering Cognition Layer**（工程认知层）。

它表现得像一个神经网络：
| 神经网络概念 | 工程认知对应 |
|-------------|-------------|
| 节点 (Node) | 工程事实（模块/函数/测试/能力/约束/证据） |
| 边 (Edge) | 工程关系（依赖/调用/验证/约束/历史） |
| 权重 (Weight) | 证据强度/可信度/影响程度 |
| 时间 (Time) | 历史演化/版本 |
| 反馈 (Feedback) | CI 结果/测试结果/验证结果 |

但底层首先是 **机器可验证的工程世界模型**。

未来如果真的需要 Neural Model，再让模型建立在这个世界模型之上。

**这个顺序非常重要**:
```
先有机器可验证的工程世界模型
    ↓
再有工程认知层（查询/分析/推理）
    ↓
最后才有神经网络模型（建立在世界模型和认知层之上）
```

不能反过来。

### 3.3 Engineering Cognition Layer 的组成

```
Engineering Cognition Layer
│
├── Query Interface（查询接口）
│   ├── What is X?（身份查询）
│   ├── Why does X exist?（目的查询）
│   ├── What depends on X?（依赖查询）
│   ├── What proves X?（证据查询）
│   ├── What constrains X?（约束查询）
│   ├── What changed X?（历史查询）
│   ├── What can I safely change?（安全变更查询）
│   └── What must I verify after changing X?（验证查询）
│
├── Cognition Model（认知模型）
│   ├── Entity（实体）：模块/函数/测试/能力/约束/证据
│   ├── Relation（关系）：依赖/调用/验证/约束/历史
│   ├── Weight（权重）：证据强度/可信度/影响程度
│   ├── Time（时间）：历史演化/版本
│   └── Feedback（反馈）：CI 结果/测试结果/验证结果
│
├── Impact Analysis Engine（影响分析引擎）
│   ├── 变更影响范围计算
│   ├── 受影响的测试/能力/约束识别
│   ├── 必须重新执行的验证推荐
│   ├── 禁止修改的区域识别
│   └── 类似历史变更/Bug 查询
│
├── Evidence Chain Verifier（证据链验证器）
│   ├── Claim → Evidence 完整性验证
│   ├── Evidence 证明范围匹配验证
│   ├── Evidence 可信度评估
│   ├── 矛盾证据检测
│   └── 可复现性等级评估
│
└── History Tracer（历史追溯器）
    ├── 实体完整演化历史
    ├── 变更原因追溯
    ├── 类似 Bug/变更历史查询
    ├── 历史状态重建
    └── 回归风险评估（基于历史类似变更）
```

### 3.4 八个核心查询

**查询 1: What is X?（身份查询）**
```
输入: "coroutine scheduler"
输出:
  - 模块: runtime/coroutine
  - 核心函数: scheduler_run, scheduler_schedule, scheduler_wakeup
  - 职责: 协程调度，管理协程状态转换和执行顺序
  - 类型: Runtime 核心组件
  - 状态: active, production-ready (scope-limited)
```

**查询 2: Why does X exist?（目的查询）**
```
输入: "coroutine scheduler"
输出:
  - 存在原因: 为 TLL 提供并发能力
  - 设计目标: IO-aware 调度，高吞吐，低延迟
  - 被依赖: P2P/Blockchain 等需要并发的模块
  - 不可替代性: 是 TLL 并发模型的核心，没有替代方案
```

**查询 3: What depends on X?（依赖查询）**
```
输入: "coroutine scheduler"
输出:
  直接依赖:
    - stdlib/coroutine.tll
    - stdlib/task.tll
    - stdlib/p2p.tll
  间接依赖:
    - stdlib/blockchain.tll
    - stdlib/blockchain_node.tll
    - stdlib/mempool.tll
  测试依赖:
    - tests/scope/scope_07_coroutine.tll
    - tests/coroutine_stress_test.tll
    - tests/bc_*.tll (所有区块链测试)
    - tests/fi_*.tll (所有故障注入测试)
    - tests/lrs_*.tll (所有长稳测试)
  能力依赖:
    - capability: runtime.coroutine
    - capability: p2p.network
    - capability: blockchain.network
```

**查询 4: What proves X?（证据查询）**
```
输入: "coroutine scheduler supports 100K concurrent coroutines"
输出:
  Claim: "在 CI 环境下，coroutine scheduler 能正确调度 100K 协程"
  Evidence:
    - ev-001: CI Run #123, Ubuntu, 100K coroutine test pass
    - ev-002: CI Run #123, Windows, 100K coroutine test pass
    - ev-003: CI Run #123, macOS, 100K coroutine test pass
  Evidence scope:
    proves: "100K immediate-return coroutines complete without crash in CI"
    does_not_prove:
      - "production readiness"
      - "memory safety under all conditions"
      - "long-term stability (>10 minutes)"
      - "100K concurrent active coroutines"
  Reproducibility level: R3 (实际复现，3 平台)
  Confidence: high
```

**查询 5: What constrains X?（约束查询）**
```
输入: "coroutine scheduler"
输出:
  约束:
    - C001: 不可破坏现有协程语义（scope_07 测试守护）
    - C002: 不可降低 100K 协程性能（perf_coroutine 基准守护）
    - C003: 不可破坏 IO-aware 调度（P2P/Blockchain 测试守护）
    - C004: 协程创建/yield/resume 的 ABI 接口不可变
  不可变项:
    - coroutine.create() 签名
    - coroutine.yield() 语义
    - coroutine.resume() 语义
  性能约束:
    - coroutine 创建 <= 200us/个 (当前 95.4us)
    - yield/resume <= 5us/次 (当前 2.19us)
```

**查询 6: What changed X?（历史查询）**
```
输入: "coroutine scheduler"
输出:
  历史变更:
    - P0-15.16: IO-aware Scheduler 重构
      原因: 原调度器不支持 IO 等待
      影响: 所有使用 coroutine + IO 的模块
      回归: scope_07, coroutine_stress, bc_*, fi_*, lrs_*
    - P0-15.18.1: 100K Coroutine Stress 修复
      原因: 100K 协程测试发现调度延迟问题
      影响: scheduler 内部实现
      回归: coroutine_stress_test
  类似历史 Bug:
    - sleep coroutine 调度延迟问题（已修复，P0-15.18.1）
    - 高并发下 coroutine 对象泄漏（已修复，P0-15.18.1）
  回归风险: 高（核心组件，被大量测试和模块依赖）
```

**查询 7: What can I safely change?（安全变更查询）**
```
输入: "I want to modify coroutine scheduler"
输出:
  ✅ 安全变更:
    - 调度算法内部实现（不改变 ABI 和语义）
    - 性能优化（不改变语义，性能不退化）
    - 代码重构（不改变外部行为）
    - 注释和文档更新
  
  ⚠️ 谨慎变更:
    - 协程状态转换逻辑（需完整回归）
    - 调度优先级策略（需验证所有依赖模块）
    - 内存管理（需验证无泄漏）
  
  ❌ 禁止变更:
    - coroutine.create()/yield()/resume() 的 ABI 接口
    - 协程语义（scope_07 定义的行为）
    - 与 IO 系统的接口契约
    - 不可变核心规则中定义的任何项
```

**查询 8: What must I verify after changing X?（验证查询）**
```
输入: "I modified coroutine scheduler"
输出:
  必须执行:
    1. tests/scope/scope_07_coroutine.tll
       原因: 协成语义正确性
    2. tests/coroutine_stress_test.tll
       原因: 100K 协程压力，无崩溃无泄漏
    3. tests/perf_coroutine.tll
       原因: 性能基准，不可退化
    4. tests/bc_stress.tll
       原因: Blockchain 压力，依赖协程调度
    5. tests/fi_kill9.tll
       原因: 故障注入，依赖协程调度和恢复
    6. tests/lrs_a.tll + lrs_b.tll + lrs_c.tll + lrs_d.tll
       原因: 长稳测试，依赖协程长期运行
  
  建议执行:
    - 全部 34 个测试（完整回归）
    - 三平台 CI（Ubuntu/Windows/macOS）
    - 多次运行（检测非确定性问题）
  
  完成后必须产生:
    - Evidence: 测试结果报告（所有必须执行的测试）
    - Evidence: 性能对比报告（修改前后，证明无退化）
    - Claim: "coroutine scheduler 变更后，所有测试通过，性能不退化"
    - Truth Version: 新版本（如果 Claim 通过所有信任转换检查点）
  
  禁止:
    - 跳过任何必须执行的测试
    - 降低测试标准
    - 用 continue-on-error 掩盖失败
    - 只在一个平台测试就声称通过
```

### 3.5 Engineering Cognition Layer 的价值

**传统方式**:
```
Agent 想修改 coroutine scheduler
  ↓
读 500 个 Markdown 文档
  ↓
猜测影响范围
  ↓
猜测需要运行哪些测试
  ↓
可能遗漏关键测试
  ↓
可能破坏不可变项
  ↓
可能引入回归
```

**Engineering Cognition Layer 方式**:
```
Agent 想修改 coroutine scheduler
  ↓
查询 World Model: "What can I safely change?"
  ↓
得到明确的安全/谨慎/禁止变更清单
  ↓
查询 World Model: "What must I verify after changing it?"
  ↓
得到明确的必须执行测试清单和原因
  ↓
修改后运行所有必须执行的测试
  ↓
产生 Evidence
  ↓
通过 Trust Transition 检查点
  ↓
成为新的 Canonical Truth
```

**核心价值**: 不是让 LLM 变得更聪明，而是让聪明的 LLM 第一次拥有一个可靠的工程世界可以依附。

---

## 四、Trust Transition（信任转换）

### 4.1 核心问题

> 到底在哪一个瞬间，一个"可能正确的东西"才变成"Canonical Truth"？

**错误答案**:
- ❌ "Agent 说它正确的时候"
- ❌ "测试通过的时候"
- ❌ "CI 变绿的时候"
- ❌ "某个权威宣布的时候"
- ❌ "Git commit 的时候"

**正确答案**:

> 信任转换不是一个"瞬间"，而是一个"过程"，有多个检查点。一个"可能正确的东西"变成"Canonical Truth"，需要通过所有检查点。
> 
> 没有任何个人或系统可以"定义"真相，只有通过所有信任转换检查点的声明才能成为真相。

### 4.2 七个信任转换检查点

```
代码变更（可能正确，也可能错误）
    │
    ▼ 【CP1: 可复现性检查】
    │   检查: 测试结果是否可复现？
    │   通过: 任何人重新运行得到相同结果
    │   失败: 标记为 unreproducible，不能成为 Truth
    │
    ▼ 【CP2: Evidence 完整性检查】
    │   检查: Evidence 是否有完整的溯源链？
    │   通过: 哈希正确，溯源链完整，范围明确
    │   失败: 标记为 incomplete，不能成为 Truth
    │
    ▼ 【CP3: Verification 检查】
    │   检查: Evidence 是否被验证过？
    │   通过: 验证者身份可验证，验证范围明确
    │   失败: 标记为 unverified，不能成为 Truth
    │
    ▼ 【CP4: Claim-Evidence 匹配检查】
    │   检查: Claim 的 scope 是否在 Evidence 的 proves 范围内？
    │   通过: Claim scope ⊆ Evidence proves scope
    │   失败: 标记为 overclaim，需要缩小 Claim 或增加 Evidence
    │
    ▼ 【CP5: 无矛盾证据检查】
    │   检查: 是否存在矛盾的 Evidence？
    │   通过: 无矛盾证据，或矛盾已解决
    │   失败: 标记为 disputed，不能成为 Truth
    │
    ▼ 【CP6: 授权合规检查】
    │   检查: Truth 变更是否有合法授权？
    │   通过: Authorization Token 有效，操作在范围内
    │   失败: 拒绝变更，记录违规
    │
    ▼ 【CP7: 不可变项检查】
    │   检查: 是否修改了不可变项？
    │   通过: 不可变项未被修改
    │   失败: 拒绝变更
    │
    ▼
Canonical Truth（在当前证据下成立的声明）
```

### 4.3 检查点详细说明

**CP1: 可复现性检查（Reproducibility Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | 测试结果是否可复现 |
| 通过条件 | 有明确的验证步骤 + 环境定义 + 确定性结果 + 独立可验证 |
| 最低等级 | R2（环境可复现） |
| 推荐等级 | R3（实际复现，多平台） |
| 失败处理 | 标记为 `unreproducible`，不能成为 Truth，需要补充复现步骤 |
| 防绕过 | 不能用"Agent 说可复现"代替实际复现 |

**CP2: Evidence 完整性检查（Evidence Completeness Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | Evidence 是否有完整的结构和溯源链 |
| 通过条件 | Evidence 包含: id/type/source/timestamp/platform/result/hash/provenance_chain/claim_scope |
| 失败处理 | 标记为 `incomplete`，不能成为 Truth，需要补充 Evidence 字段 |
| 防绕过 | 不能用"测试通过了"代替结构化 Evidence |

**CP3: Verification 检查（Verification Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | Evidence 是否被验证过 |
| 通过条件 | 验证者身份可验证（Identity Root 注册 + 签名）+ 验证范围明确 + 验证时间记录 |
| 验证方式 | automated / human / multi_agent / reproducible |
| 失败处理 | 标记为 `unverified`，不能成为 Truth，需要补充验证 |
| 防绕过 | 不能用"Evidence 存在"代替"Evidence 被验证" |

**CP4: Claim-Evidence 匹配检查（Claim-Evidence Match Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | Claim 的 scope 是否在 Evidence 的 proves 范围内 |
| 通过条件 | Claim.scope.proves ⊆ Evidence.claim_scope.proves |
| 失败处理 | 标记为 `overclaim`，需要缩小 Claim scope 或增加 Evidence |
| 示例 | Evidence 只证明"CI 环境下 100K 协程通过"，Claim 不能说"生产就绪" |
| 防绕过 | 不能用 CI 通过证明生产就绪，不能用单平台通过证明多平台兼容 |

**CP5: 无矛盾证据检查（No Contradictory Evidence Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | 是否存在与 Claim 矛盾的 Evidence |
| 通过条件 | 无矛盾证据，或矛盾已解决（有解释或新 Evidence 解决矛盾） |
| 失败处理 | 标记为 `disputed`，不能成为 Truth，需要解决矛盾 |
| 示例 | 一个 Evidence 说"测试通过"，另一个 Evidence 说"同样测试失败" → 矛盾 |
| 防绕过 | 不能忽略矛盾 Evidence，不能只选择支持 Claim 的 Evidence |

**CP6: 授权合规检查（Authorization Compliance Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | Truth 变更是否有合法授权 |
| 通过条件 | Identity 已验证 + Authorization Token 有效 + 操作在 Token scope 内 + 时间未过期 |
| 失败处理 | 拒绝变更，记录违规，可能暂停 Agent 身份 |
| 防绕过 | 不能跳过授权检查，不能用过期 Token，不能越权操作 |

**CP7: 不可变项检查（Immutability Check）**

| 项 | 说明 |
|----|------|
| 检查内容 | 是否修改了不可变项 |
| 通过条件 | 所有标记为 immutable 的项未被修改 |
| 不可变项包括 | Root Trust 核心规则、Protocol 核心规则、ABI 接口、已发布 Truth 版本的历史 |
| 失败处理 | 拒绝变更 |
| 防绕过 | 不能用"修复错误"的名义修改不可变项，不可变项修改需要特殊授权流程 |

### 4.4 Trust Transition 状态机

```
proposed（已提案）
  │
  ├─ CP1 失败 → unreproducible（不可复现）
  │
  ▼ CP1 通过
reproducible（可复现）
  │
  ├─ CP2 失败 → evidence_incomplete（证据不完整）
  │
  ▼ CP2 通过
evidence_complete（证据完整）
  │
  ├─ CP3 失败 → unverified（未验证）
  │
  ▼ CP3 通过
verified（已验证）
  │
  ├─ CP4 失败 → overclaim（过度声明）
  │
  ▼ CP4 通过
claim_matched（声明匹配）
  │
  ├─ CP5 失败 → disputed（有争议）
  │
  ▼ CP5 通过
uncontested（无争议）
  │
  ├─ CP6 失败 → unauthorized（未授权）
  │
  ▼ CP6 通过
authorized（授权合规）
  │
  ├─ CP7 失败 → immutable_violation（违反不可变项）
  │
  ▼ CP7 通过
canonical_truth（Canonical Truth）
```

**状态转换规则**:
- 任何一个检查点失败 → 进入相应的失败状态，不能继续前进
- 失败状态可以通过补充信息/修复问题后重新进入检查
- `canonical_truth` 状态是最终状态，不可修改
- 已成为 `canonical_truth` 的声明，如果后续发现矛盾证据，可以被标记为 `superseded` 或 `revoked`，但历史记录不可修改

### 4.5 Truth Version 创建规则

**什么时候创建新的 Truth Version**:
- 当一个或多个 Claim 达到 `canonical_truth` 状态时
- 定期（如每次 CI 全绿后）
- 重大变更后（如 Runtime 核心修改）

**Truth Version 包含**:
- 所有当前 `canonical_truth` 状态的 Claim
- 所有支持这些 Claim 的 Evidence
- 版本号和 parent_hash
- 创建时间和创建者
- 变更记录（相对于上一版本）

**Truth Version 不可变**:
- 一旦创建，不可修改
- 只能创建新版本
- 历史版本永久保留，可追溯
- 哈希链保证完整性

### 4.6 关键原则总结

| 原则 | 说明 |
|------|------|
| **真相不由任何人定义** | 没有任何个人或系统可以"宣布"真相 |
| **真相由检查点保证** | 通过所有 7 个检查点的声明才是 Canonical Truth |
| **可复现性是最终信任根** | 即使所有记录被销毁，真相仍可通过重新复现重建 |
| **各层只记录不定义** | Identity/Authority/Protocol 只记录、验证、授权，不定义真相 |
| **信任转换是过程不是瞬间** | 没有"某个时刻变成真相"，只有"通过所有检查点" |
| **历史不可修改** | 已成为 Canonical Truth 的声明历史不可修改，只能被新版本替代或撤销 |

---

## 五、TLL Official vs User Space

### 5.1 架构

```
                    TLL OS
                       │
               Engineering World
                       │
        ┌──────────────┴──────────────┐
        │                             │
   TLL Official                  User Space
   (官方空间)                     (用户空间)
        │                             │
        ▼                             ▼
  Official Agents               User Agents
  (官方 LLM / API)              (用户自己的 LLM)
        │                             │
        └──────────────┬──────────────┘
                       ▼
              SAME TLL PROTOCOL
              (同一套工程协议)
                       │
                       ▼
              SAME TRUTH RULES
              (同一套真相规则)
                       │
                       ▼
                SAME CI GATES
                (同一套 CI 门禁)
```

### 5.2 核心原则

> TLL 不需要规定用户必须使用 Claude、GPT、豆包、DeepSeek 还是其他模型。
> 
> 模型可以换，Agent 可以换，Agent 框架可以换。
> 
> 但是：Truth / Protocol / Identity / Authority / Evidence / Verification / World Model 不能随便换。

**这才可能形成真正的开发语言级 AI 工程生态。**

### 5.3 Official 与 User 的区别

| 维度 | TLL Official | User Space |
|------|-------------|------------|
| Agent 身份 | 官方注册，高可信度 | 用户自行注册，可信度取决于验证 |
| 权限等级 | 可达到 Level 5+（Authorized Committer） | 默认 Level 3，可通过验证升级 |
| Truth 提交 | 可以直接提交经过验证的 Truth 变更 | 需要 Official Agent 或人工审核后提交 |
| Evidence 可信度 | 高（官方验证） | 取决于验证方式，可复现的 Evidence 可信度高 |
| 协议遵守 | 必须严格遵守 | 必须遵守，违规会被检测和拒绝 |
| CI 门禁 | 同一套 | 同一套 |

**关键**: 即使是 User Space 的 Agent，只要它的 Evidence 可复现、通过所有信任转换检查点，它的 Claim 也可以成为 Canonical Truth。

> 真相不看身份，只看可复现性和验证。

这就是可复现性作为 Root of Trust 的力量。

---

## 六、v0.4 与 v0.3 的关系

### 6.1 v0.3 保留的部分

v0.3 的所有设计在 v0.4 中保留：
- 11 个核心概念（Identity/Authority/Permission/Truth/Claim/Evidence/Verification/World Model/CI-CD/History/Agent）
- 防自升权机制
- World Model 5 个子图
- Agent 操作 10 阶段流程
- 不可变核心规则

### 6.2 v0.4 新增的部分

| 概念 | v0.3 状态 | v0.4 新增 |
|------|-----------|-----------|
| **Root of Trust** | Identity Root 作为信任锚 | 可复现性作为最终信任根，Identity Root 只记录不定义 |
| **Reproducibility** | 隐含在 Evidence 中 | 独立的可复现性等级（R0-R4），作为 CP1 检查点 |
| **Engineering Cognition Layer** | World Model 查询 | 8 个核心查询 + 影响分析引擎 + 证据链验证器 + 历史追溯器 |
| **Trust Transition** | 隐含在 Truth 版本中 | 7 个检查点 + 状态机 + 明确的转换规则 |
| **Official vs User Space** | 未定义 | 官方 Agent 与用户 Agent 共享同一 Protocol/Truth/CI |

### 6.3 v0.4 修正的部分

| v0.3 的问题 | v0.4 的修正 |
|-------------|-------------|
| "Identity Root 是信任根" | "可复现性是信任根，Identity Root 只记录验证者身份" |
| "真相由各层定义" | "真相由通过所有检查点定义，各层只记录验证授权" |
| "World Model 是图数据库" | "World Model 是工程认知层，支持 8 个核心查询和工程决策" |
| "神经网络" | 修正为"Engineering Cognition Layer"，暂时不训练神经网络 |
| "CI 通过 = 能力成立" | "CI 通过只是 Evidence，需要通过 CP4 Claim-Evidence 匹配检查" |

---

## 七、实施路线

### Phase 0: v0.4 评审（当前）
- [ ] 本文档评审通过
- [ ] 确认可复现性作为 Root of Trust
- [ ] 确认 7 个信任转换检查点
- [ ] 确认 Engineering Cognition Layer 的 8 个核心查询
- [ ] 确认 Official vs User Space 分离

### Phase 1: Root of Trust 基础设施
- [ ] 建立可复现性等级定义（R0-R4）
- [ ] 建立 Identity Root（Agent 注册 + 密钥对 + 签名验证）
- [ ] 建立 Authority Root（Authorization Token 机制）
- [ ] 建立 Protocol Root（不可变核心规则）
- [ ] 实现防自升权机制
- [ ] CI 集成：身份验证 + 授权验证

### Phase 2: Trust Transition 机制
- [ ] 实现 7 个检查点的自动化检查
- [ ] 实现 Trust Transition 状态机
- [ ] 实现 Truth Version 创建和管理
- [ ] 实现不可变历史和哈希链
- [ ] CI 集成：自动运行所有检查点

### Phase 3: Engineering Cognition Layer
- [ ] 建立 World Model 数据结构（5 个子图）
- [ ] 实现 8 个核心查询接口
- [ ] 实现 Impact Analysis Engine
- [ ] 实现 Evidence Chain Verifier
- [ ] 实现 History Tracer
- [ ] CLI 工具：查询工程世界

### Phase 4: CI/CD 升级
- [ ] 升级 CI 为自动验证层
- [ ] 实现验证报告输出（验证了什么/没验证什么）
- [ ] 实现可复现性自动检测
- [ ] 实现 Claim-Evidence 匹配自动检查
- [ ] 实现矛盾证据自动检测

### Phase 5: Official vs User Space
- [ ] 建立 Official Agent 注册机制
- [ ] 建立 User Agent 注册机制
- [ ] 实现统一的 Protocol/Truth/CI 门禁
- [ ] 实现身份与权限分离
- [ ] 文档：用户如何接入自己的 Agent

### Phase 6: tllos.com Engineering World Browser
- [ ] 官网技术选型
- [ ] Engineering World Browser 实现
- [ ] 8 个核心查询的 Web 界面
- [ ] Truth Transition 状态可视化
- [ ] World Model 可视化
- [ ] 部署上线

---

## 八、待决策事项

### 8.1 Root of Trust

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 1 | 可复现性最低等级 | R1 / R2 / R3 | R2（环境可复现） |
| 2 | 可复现性验证方式 | 自动检测 / 人工确认 / 第三方复现 | 自动检测 + 多平台 CI |
| 3 | Identity Root 存储 | 独立文件 / Git 子模块 / 独立仓库 | 独立文件 + 哈希链 + 签名 |
| 4 | Agent 密钥类型 | RSA / Ed25519 / SSH 密钥 | Ed25519 |
| 5 | 不可变项修改流程 | 人工授权 / 多签 / 特殊 Protocol | 人工授权 + 特殊 Protocol 流程 |

### 8.2 Trust Transition

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 6 | 检查点是否全部强制 | 全部强制 / 部分可选 | 全部强制（CP1-CP7） |
| 7 | 检查点执行顺序 | 严格顺序 / 可并行 | 严格顺序（CP1→CP7） |
| 8 | 失败状态恢复 | 自动重试 / 人工介入 / 补充信息后重试 | 补充信息后重试 |
| 9 | Truth Version 创建频率 | 每次 Claim 通过 / 定期 / 重大变更后 | 定期 + 重大变更后 |
| 10 | 已撤销 Truth 的处理 | 保留标记 / 删除 / 归档 | 保留标记，历史不可修改 |

### 8.3 Engineering Cognition Layer

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 11 | 查询接口形式 | CLI / HTTP API / 两者都有 | CLI 优先，后续加 HTTP API |
| 12 | World Model 存储 | JSON 文件 / 图数据库 / SQLite | 初始 JSON 文件，后续可迁移 |
| 13 | 影响分析深度 | 1层 / 3层 / 全路径 | 3层（可配置） |
| 14 | 查询响应时间要求 | <1s / <5s / <10s | <5s（初始阶段） |
| 15 | 是否需要自然语言查询 | 是 / 否 / 后续 | 后续（先实现结构化查询） |

### 8.4 Official vs User Space

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 16 | Official Agent 数量 | 1个 / 多个 / 按需 | 多个（不同 LLM 提供商） |
| 17 | User Agent 默认权限 | Level 1 / Level 2 / Level 3 | Level 3（可改代码，不可改 Truth） |
| 18 | User Agent 升级流程 | 自动 / 人工审核 / 验证后自动 | 验证后自动（基于可复现 Evidence） |
| 19 | 用户 Truth 提交方式 | 直接 / Official 审核 / 人工审核 | Official 审核（可复现 Evidence 可加速） |
| 20 | 官网是否支持用户登录 | 是 / 否 / 后续 | 后续（先做只读浏览） |

---

## 九、成功标准

### 9.1 v0.4 治理层建立成功的标志

1. **Root of Trust 可解释**: 能清楚回答"TLL 最终相信什么？为什么？"——答案是"可复现性"
2. **Identity Root 不定义真相**: Identity Root 只记录验证者身份，不定义真相
3. **7 个检查点可执行**: 每个检查点有明确的通过/失败条件，可自动化检查
4. **Trust Transition 状态机完整**: 从 proposed 到 canonical_truth 的所有状态和转换明确定义
5. **Engineering Cognition Layer 可查询**: 8 个核心查询可以返回有意义的结果
6. **Claim-Evidence 匹配可检测**: 能自动检测"CI 通过 ≠ 生产就绪"这类过度声明
7. **Official vs User Space 分离**: 官方 Agent 和用户 Agent 共享同一 Protocol/Truth/CI
8. **真相不看身份**: User Agent 的可复现 Evidence 也可以成为 Canonical Truth

### 9.2 不接受的"伪成功"

- ❌ Root of Trust 仍然是某个文件/JSON/管理员账号
- ❌ Identity Root 可以被 Agent 修改
- ❌ 检查点只是文档描述，没有可执行的检查逻辑
- ❌ Trust Transition 只是"CI 通过就变成 Truth"
- ❌ Engineering Cognition Layer 只是图数据库，不能回答工程问题
- ❌ Claim 可以超出 Evidence 的证明范围
- ❌ Official Agent 的声明不需要通过检查点
- ❌ User Agent 的 Evidence 被自动拒绝（不看可复现性）
- ❌ 已发布 Truth 版本可以被修改

---

## 附录 A: 核心概念速查表

| 概念 | 一句话定义 | 最终信任来源 |
|------|-----------|-------------|
| **Root of Trust** | TLL 最终相信什么 | 可复现性 |
| **Reproducibility** | 可以被独立复现的工程事实 | 任何人重新运行得到相同结果 |
| **Identity** | 谁在做验证 | 私钥签名 + 公钥验证 |
| **Authority** | 谁授权提交记录 | Authorization Token |
| **Claim** | 事实声明（有范围） | Evidence 支持 |
| **Evidence** | 支持声明的证据（有证明范围） | 可复现的测试结果 |
| **Verification** | 谁验证了证据 | 验证者身份 + 验证记录 |
| **Trust Transition** | 从"可能正确"到"Canonical Truth"的过程 | 7 个检查点全部通过 |
| **Canonical Truth** | 在当前证据下成立的声明 | 通过所有检查点 |
| **Engineering Cognition Layer** | Agent 认识工程世界的查询层 | World Model + 查询接口 |
| **World Model** | 工程关系网络（支持工程决策） | 5 个子图 + 8 个核心查询 |

## 附录 B: 7 个信任转换检查点速查

| # | 检查点 | 检查内容 | 通过条件 |
|---|--------|----------|----------|
| CP1 | 可复现性 | 测试结果是否可复现 | R2+ 等级，有步骤有环境 |
| CP2 | Evidence 完整性 | Evidence 结构是否完整 | 所有必填字段存在，哈希正确 |
| CP3 | Verification | Evidence 是否被验证 | 验证者身份可验证，范围明确 |
| CP4 | Claim-Evidence 匹配 | Claim scope 是否在 Evidence proves 内 | Claim.scope ⊆ Evidence.proves |
| CP5 | 无矛盾证据 | 是否存在矛盾 Evidence | 无矛盾或已解决 |
| CP6 | 授权合规 | 变更是否有合法授权 | Token 有效，操作在范围内 |
| CP7 | 不可变项 | 是否修改了不可变项 | 所有 immutable 项未修改 |

## 附录 C: 8 个工程认知查询速查

| # | 查询 | 回答的问题 |
|---|------|-----------|
| Q1 | What is X? | 这个东西是什么？ |
| Q2 | Why does X exist? | 它为什么存在？ |
| Q3 | What depends on X? | 什么依赖它？ |
| Q4 | What proves X? | 什么证明它？ |
| Q5 | What constrains X? | 什么约束它？ |
| Q6 | What changed X? | 什么改变了它？ |
| Q7 | What can I safely change? | 我可以安全地修改什么？ |
| Q8 | What must I verify after changing X? | 修改后必须验证什么？ |

---

*本文档为 TLL AI Engineering Foundation v0.4 信任根与工程认知架构设计，待评审后进入 Phase 1 施工。*

*核心原则: TLL 最终相信的不是任何"东西"，而是"可以被独立复现的过程"。真相不由任何层定义，真相由通过所有信任转换检查点保证。*

*第一性原理: 不是"先建 .truth/ 再想它是什么"，而是"先定义真实和信任的本质，再设计承载它的系统"。*

*这一步做好了，TLL 才真正开始从"开发一个编程语言"，走向"建立一套 AI 可以持续建设大型软件的工程基础设施"。*
