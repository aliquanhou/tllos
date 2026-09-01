# TLL AI Engineering Foundation — 总体设计 v0.1

> 版本: 0.1 (Draft)
> 日期: 2026-09-01
> 状态: 设计阶段，待评审后进入施工
> 基线: P0-15.18.7 (commit 157d198, CI Run #123 三平台全绿)

---

## 一、战略定位

### 1.1 为什么需要 AI Engineering Foundation

TLL 已经完成了从"自制语言"到"可承载复杂系统的工程语言原型"的跨越：

```
TLL Compiler → TLL VM → Coroutine → TCP → P2P → Blockchain
→ 4 Node 真实网络 → 故障注入 → 长稳运行 → 性能基准
→ 三平台 CI 强制验证 → Assertion Hard Gate
```

P0-15.18.x 证明了一件核心事实：**TLL Runtime 可以承载复杂系统**。

但这只是第一层。TLL 的终极目标不是"又一个编程语言"，而是：

> **让 AI Agent 能够真正使用 TLL 开发、维护、演进复杂软件系统。**

这需要的不只是 Runtime 能力，而是一整套 **AI 软件工程基础设施**：
- Agent 应该相信什么？(Canonical Truth)
- Agent 应该怎么施工？(Engineering Protocol)
- TLL 如何认知自身？(TLL Intelligence)
- 外部 Agent 如何接入？(Agent Ecosystem)

### 1.2 核心原则

| 原则 | 说明 |
|------|------|
| **Agent 可以换，工程真相不能换** | LLM/Agent 可以不同，Truth/Protocol/Contract/Verification 保持一致 |
| **证据优先于声明** | 任何能力声明必须有可验证的证据（测试/CI/审计） |
| **最小修复，不扩大施工范围** | 发现 Bug 只修根因，不顺手重构 |
| **先审计，再施工，再独立审计** | 不接受"施工报告=已完成"，必须以仓库真实代码和 CI 结果为准 |
| **无法证明的能力必须标记** | PARTIAL / MISSING / NOT READY，不得包装为已完成 |

---

## 二、四层架构

```
                    TLL OS
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    TLL Runtime              AI Engineering Foundation
    (已开始成熟)              (下一战略核心)
          │                         │
          ▼                         ▼
   Blockchain 验证            ┌─────────────────┐
   Runtime 能力               │  1. Canonical   │
                              │     Truth        │
                              │  2. Engineering  │
                              │     Protocol     │
                              │  3. TLL          │
                              │     Intelligence │
                              │  4. Agent        │
                              │     Ecosystem    │
                              └────────┬────────┘
                                       │
                                       ▼
                                 tllos.com
                          (TLL 官方 Truth 公开入口)
```

### 2.1 第一层：Canonical Truth（工程真相层）

**解决的问题**: Agent 到底应该相信什么？

不是 README.md，不是施工报告，而是结构化的、可验证的、版本化的工程真相。

```
TLL Truth
├── Architecture          (系统架构图 + 模块边界 + 依赖关系)
├── Language Semantics    (语言语义规范：作用域/类型/函数/闭包/模块)
├── Runtime Invariants    (运行时不变量：内存安全/引用计数/帧生命周期)
├── ABI Contracts         (ABI 契约：C↔TLL 调用约定/数据结构布局)
├── Capability Matrix     (能力矩阵：每项能力的状态/证据/版本)
├── Dependency Graph      (依赖图：模块间依赖/版本约束)
├── Engineering Rules     (工程规则：编码规范/提交规范/测试要求)
├── Test Requirements     (测试要求：每层必须通过的测试集)
├── Evidence              (证据链：CI Run ID/审计报告/性能数据)
└── Version / Hash        (版本/哈希：Truth 本身的版本化与完整性校验)
```

**关键设计**:
- Truth 本身必须版本化，每次变更有哈希校验
- 每项能力声明必须链接到具体证据（测试文件/CI Run/审计报告）
- Truth 是只读的，只能通过 Engineering Protocol 变更
- Agent 施工前必须读取当前 Truth，施工后必须更新 Truth

### 2.2 第二层：Engineering Protocol（工程协议）

**解决的问题**: Agent 下一步应该怎么施工？

这不是"豆包自己的工作习惯"，而是 TLL 官方规定的 Agent 工程协议。

```
DISCOVER      ← 探查：读取源码/文档/测试/CI，建立当前状态认知
   │
UNDERSTAND    ← 理解：分析问题根因，区分 Bug/能力缺口/测试问题
   │
PLAN          ← 计划：制定最小修复方案，明确施工范围和验收标准
   │
CHANGE        ← 变更：执行代码修改，保持最小范围，不扩大施工
   │
TEST          ← 测试：运行相关测试，验证修复有效，无回归
   │
VERIFY        ← 验证：通过不同于生成路径的方式回读验证
   │
AUDIT         ← 审计：独立审计（或自审计清单），核对证据链
   │
EVIDENCE      ← 证据：记录 CI Run ID/测试结果/性能数据
   │
COMMIT        ← 提交：Git commit + push，更新 Truth
   │
NEXT          ← 下一步：基于新状态决定下一阶段
```

**协议规则**:
- 每一步必须有可验证的输出，不能跳过
- 发现真实 Bug 才允许修改 Runtime/stdlib，否则只改测试/文档
- 修复必须最小化，不顺手重构
- 测试失败必须分类：代码 Bug / 测试问题 / 环境差异 / flaky
- CI 红灯时禁止继续堆功能，先清零
- 任何能力声明必须有证据，否则标记 PARTIAL/MISSING

### 2.3 第三层：TLL Intelligence（结构化认知）

**解决的问题**: TLL 如何认知自身？

**关键概念区分**:

| 概念 | 定义 | 来源 |
|------|------|------|
| **LLM** | 外部智能来源 | Claude / GPT / 豆包 / DeepSeek / 本地模型 |
| **TLL Intelligence** | TLL 对自身的结构化认知 | Canonical Truth + Engineering Protocol + Runtime Knowledge + Verified Evidence |
| **TLL Agent** | 利用 LLM + TLL Truth + Protocol 执行工作的 Agent | 外部 LLM + TLL 工程基础设施 |

**TLL Intelligence 的组成**:

```
TLL Intelligence
├── Self-Knowledge      (自我认知：架构/能力/限制/已知 Bug)
├── Runtime Knowledge   (运行时知识：VM/Coroutine/TCP/P2P/Blockchain 内部机制)
├── Evidence Base       (证据库：所有测试结果/CI Run/审计报告/性能数据)
├── Pattern Library     (模式库：常见问题/修复模式/最佳实践)
├── Decision History    (决策历史：为什么这样做，为什么不那样做)
└── Inference Engine    (推理引擎：基于 Truth + Evidence 进行工程决策)
```

**设计原则**:
- 不需要一开始就训练巨大的 TLL 大模型
- 先把 Truth + Protocol + Knowledge + Evidence 建立起来
- LLM 是"大脑"，TLL Intelligence 是"记忆和知识"，Agent 是"执行体"
- 换 LLM 不换 Truth，换 Agent 不换 Protocol

### 2.4 第四层：Agent Ecosystem（外部 Agent 接入）

**解决的问题**: 外部 Agent 如何接入 TLL 工程体系？

```
外部 Agent / LLM
├── Claude
├── Codex
├── 豆包
├── OpenClaw
├── DeepSeek
├── 本地模型
└── ...

接入标准:
├── 读取 Canonical Truth (必须)
├── 遵循 Engineering Protocol (必须)
├── 提交可验证证据 (必须)
├── 更新 Truth (必须)
├── 不允许：跳过审计/伪造证据/扩大施工范围
└── 不允许：把 PARTIAL 包装为 COMPLETE
```

**核心契约**:
- Agent 可以不同，LLM 可以不同
- **Truth / Protocol / Contract / Verification 保持一致**
- 任何 Agent 接入后，其施工成果必须通过同一套验证体系
- Agent 的身份不影响验收标准，只看证据

---

## 三、Canonical Truth 详细规范

### 3.1 Truth 文件结构

```
.truth/
├── manifest.json              (Truth 清单 + 版本 + 哈希)
├── architecture/
│   ├── overview.md            (系统架构总览)
│   ├── modules.md             (模块边界)
│   └── dependencies.md        (依赖关系图)
├── semantics/
│   ├── scope.md               (作用域语义)
│   ├── types.md               (类型系统)
│   ├── functions.md           (函数/闭包)
│   └── modules.md             (模块/包/导入)
├── invariants/
│   ├── memory.md              (内存安全不变量)
│   ├── refcount.md            (引用计数规则)
│   └── frame.md               (调用帧生命周期)
├── abi/
│   ├── c-tll.md               (C↔TLL 调用约定)
│   └── data-layout.md         (数据结构布局)
├── capabilities/
│   └── matrix.json            (能力矩阵)
├── rules/
│   ├── coding.md              (编码规范)
│   ├── commit.md              (提交规范)
│   └── testing.md             (测试要求)
├── evidence/
│   ├── ci-runs.json           (CI Run 记录)
│   ├── audits/                (审计报告)
│   └── benchmarks/            (性能数据)
└── versions/
    └── changelog.md           (Truth 变更日志)
```

### 3.2 能力矩阵格式

```json
{
  "version": "0.1",
  "updated": "2026-09-01",
  "baseline_commit": "157d198",
  "capabilities": [
    {
      "id": "runtime.coroutine",
      "name": "Coroutine 创建/调度",
      "status": "READY",
      "evidence": {
        "test": "tests/coroutine_stress_test.tll",
        "ci_run": 123,
        "platforms": ["ubuntu", "windows", "macos"]
      },
      "notes": "100K coroutine 压力测试通过"
    },
    {
      "id": "blockchain.crypto_signature",
      "name": "密码学签名",
      "status": "MISSING",
      "evidence": null,
      "notes": "当前使用 HMAC-SHA256 模拟，非真实非对称加密"
    }
  ]
}
```

**状态定义**:
- `READY`: 已验证，有 CI 证据
- `PARTIAL`: 部分实现，有证据但不完整
- `MISSING`: 未实现
- `NOT_READY`: 实现存在但未达到生产标准
- `DEPRECATED`: 已废弃

### 3.3 Truth 版本化

- Truth 每次变更必须更新 `manifest.json` 中的版本号和哈希
- 哈希覆盖所有 Truth 文件内容，防止篡改
- Agent 施工前必须验证当前 Truth 哈希
- 施工后必须更新 Truth 并生成新哈希

---

## 四、Engineering Protocol 详细规范

### 4.1 阶段定义与输出

| 阶段 | 必须输出 | 验证方式 |
|------|----------|----------|
| DISCOVER | 当前状态清单 + 源码/文档/测试摘要 | 文件存在性 + 内容读取 |
| UNDERSTAND | 问题分类 + 根因分析 + 影响范围 | 逻辑自洽 + 证据支持 |
| PLAN | 施工方案 + 范围边界 + 验收标准 | 最小化原则 + 不扩大范围 |
| CHANGE | 代码 diff + 修改文件清单 | git diff + 编译通过 |
| TEST | 测试结果 + 覆盖率 + 无回归 | 测试 exit code + CI |
| VERIFY | 回读验证 + 不同于生成路径的检查 | 独立验证 |
| AUDIT | 审计清单 + 证据链核对 | 逐项核对 |
| EVIDENCE | CI Run ID + 测试日志 + 性能数据 | 可追溯 |
| COMMIT | Git commit + push + Truth 更新 | git log + 远程验证 |
| NEXT | 下一阶段计划 + 风险提示 | 基于新状态 |

### 4.2 禁止行为

- ❌ 跳过审计直接宣布完成
- ❌ 伪造测试结果或 CI 证据
- ❌ 为了 CI 变绿而删除/降低测试标准
- ❌ skip / continue-on-error 掩盖错误
- ❌ 把测试基础设施问题写成 Runtime Bug
- ❌ 把 PARTIAL/MISSING 包装为 COMPLETE
- ❌ 扩大施工范围（修 Bug 顺手重构）
- ❌ CI 红灯时继续堆功能

### 4.3 Bug 分类与处理

| 分类 | 处理方式 |
|------|----------|
| 真实代码 Bug | 最小修复 + 回归测试 + CI |
| 测试脚本问题 | 修复测试基础设施，不改生产代码 |
| CI 环境差异 | 修复 CI 配置或增加平台兼容层 |
| 能力缺口 | 记录为 MISSING/PARTIAL，不强行开发 |
| flaky / 非确定性 | 定位根因，是阈值问题修测试，是真实 Bug 修代码 |

---

## 五、tllos.com 定位

### 5.1 不是什么

- ❌ 不是单纯的宣传页
- ❌ 不是文档站（文档是 Truth 的一部分，但官网不止于文档）
- ❌ 不是博客

### 5.2 是什么

> **TLL 官方 Truth 的公开入口**

```
tllos.com
├── Truth Browser       (浏览 Canonical Truth：架构/语义/能力矩阵/证据)
├── Protocol Spec       (Engineering Protocol 规范)
├── Capability Matrix   (实时能力矩阵：每项能力的状态/证据/CI)
├── Evidence Hub        (证据中心：CI Run/审计报告/性能数据)
├── Agent Guide         (Agent 接入指南：如何成为 TLL Developer Agent)
├── Runtime Docs        (Runtime 文档：VM/Coroutine/TCP/P2P/Blockchain)
├── Language Spec       (语言规范)
├── Download            (下载/安装)
└── GitHub              (仓库链接)
```

### 5.3 核心价值

- 全球开发者 / Agent / LLM 的统一入口
- Truth 的公开可验证入口（任何人都可以核对能力声明的证据）
- Agent 接入的标准文档
- TLL 工程成熟度的实时展示

---

## 六、实施路线图

### 阶段 0: 设计评审 (当前)
- [ ] 本文档评审通过
- [ ] 确定 Truth 存储格式和版本化机制
- [ ] 确定 Engineering Protocol 的工具化方式

### 阶段 1: Canonical Truth 建立
- [ ] 建立 `.truth/` 目录结构
- [ ] 编写 Architecture 文档（基于当前仓库实际代码）
- [ ] 编写 Language Semantics 文档（重点：作用域/类型/函数/模块）
- [ ] 编写 Runtime Invariants 文档
- [ ] 建立 Capability Matrix（基于 P0-15.18.7 的 20+ 项能力评估）
- [ ] 建立 Evidence 索引（CI Run/审计报告/性能数据）
- [ ] Truth 版本化 + 哈希校验

### 阶段 2: Engineering Protocol 工具化
- [ ] 编写 Protocol 规范文档
- [ ] 建立 Agent 施工模板（DISCOVER→NEXT 每阶段的输出模板）
- [ ] 建立审计清单模板
- [ ] 建立 Truth 更新流程
- [ ] CI 集成：施工后自动验证 Truth 哈希

### 阶段 3: TLL Intelligence 基础
- [ ] 建立 Self-Knowledge 文档
- [ ] 建立 Runtime Knowledge 库
- [ ] 建立 Pattern Library（常见问题/修复模式）
- [ ] 建立 Decision History（关键决策记录）
- [ ] Agent 接入指南

### 阶段 4: tllos.com 启动
- [ ] 官网技术选型
- [ ] Truth Browser 实现
- [ ] Capability Matrix 实时展示
- [ ] Evidence Hub
- [ ] Agent Guide
- [ ] 部署上线

### 阶段 5: Agent Ecosystem
- [ ] 第一个外部 Agent 接入验证
- [ ] 多 Agent 协作测试
- [ ] Agent 施工成果对比验证

---

## 七、与现有工作的关系

### 7.1 不丢弃 Blockchain

Blockchain 是 TLL Runtime 能力的**验证探针**，不是 TLL 的全部。

- P0-15.18.x 已经证明了 Blockchain 可以验证 Runtime 能力
- 未来的 Blockchain 功能增强（密码学/共识/持久化）仍然在路线图中
- 但优先级由整体战略决定，不由 Blockchain 自己带偏

### 7.2 不丢弃 Runtime

TLL Runtime 是基础，AI Engineering Foundation 是上层建筑。

- Runtime 继续维护和优化
- 新的 Runtime 能力必须通过 Truth 记录和 Protocol 验证
- Runtime Bug 修复遵循最小化原则

### 7.3 P0-15.19+ 的重新定位

原计划：
- P0-15.19: 密码学增强
- P0-15.20: 共识
- P0-15.21: 持久化
- P0-15.22: 生产网络

新定位：
- 这些仍然是 Blockchain 能力增强的路线
- 但优先级低于 AI Engineering Foundation 的建立
- 可以作为 Foundation 建立后的验证用例
- 具体启动时间由战略评审决定

---

## 八、成功标准

### 8.1 Foundation 建立成功的标志

1. **Truth 可验证**: 任何人都可以读取 Truth，核对每项能力声明的证据
2. **Protocol 可执行**: Agent 可以按照 Protocol 完成施工，每阶段有明确输出
3. **Intelligence 可积累**: 施工成果和决策历史被结构化记录，可被后续 Agent 复用
4. **Agent 可接入**: 外部 Agent 可以按照标准接入，施工成果通过同一套验证
5. **官网可访问**: tllos.com 作为 Truth 公开入口上线

### 8.2 不接受的"伪成功"

- ❌ 写了一堆文档但没有和实际代码/测试对应
- ❌ Protocol 只是口号，没有工具化和强制执行
- ❌ Capability Matrix 全是 READY 但没有证据链接
- ❌ 官网只是宣传页，没有 Truth Browser
- ❌ Agent 接入只是文档，没有实际验证

---

## 九、待决策事项

1. **Truth 存储格式**: JSON + Markdown 混合？还是纯 JSON？
2. **Truth 存储位置**: 仓库内 `.truth/`？还是独立仓库？
3. **Protocol 工具化**: CLI 工具？CI 集成？还是纯文档规范？
4. **官网技术栈**: 静态站点？Next.js？还是 TLL 自己写？
5. **第一个外部 Agent**: 选哪个 Agent 做接入验证？
6. **Blockchain 后续优先级**: P0-15.19 何时启动？

---

## 附录 A: 当前能力基线 (P0-15.18.7)

### READY (有 CI 证据)
- TLL Compiler 自举编译 + ABI 一致性
- TLL VM 执行 (28/28 基础测试)
- 变量作用域正确性 (10/10 测试, 95 断言硬门禁)
- Coroutine (100K 压力测试)
- TCP (65+ real fd 边界测试)
- P2P (4 Node 真实网络)
- Blockchain (5 Block 同步/Auto Sync/Reconnect/Invalid Block/Fork Detection)
- 高消息压力 (120 tx + mempool capacity=50)
- 故障注入 (重复 tx/block/乱序/kill-9/多节点连续故障)
- 长稳运行 (20 区块, ~130 秒)
- 性能基准 (Coroutine/JSON/Blockchain)

### NOT READY / MISSING
- 🔴 真实密码学签名 (当前 HMAC 模拟)
- 🔴 完整共识机制 (缺 Chain Reorg/Orphan Pool)
- 🟡 账户状态/Nonce/双花检测
- 🟡 持久化
- 🟡 TCP 并发升级 (epoll/kqueue)
- 🟡 自动重连
- ⚪ Windows TCC 构建 (UNVERIFIED)
- ⚪ 消息协议版本化

### Production Readiness: NOT READY

---

*本文档为 TLL AI Engineering Foundation 的初始设计，待评审后进入施工阶段。*
