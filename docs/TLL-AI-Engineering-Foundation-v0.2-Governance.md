# TLL AI Engineering Foundation v0.2 — 治理层架构设计

> 版本: 0.2 (Draft)
> 日期: 2026-09-01
> 状态: 架构评审阶段，待评审后进入 v0.3 或 Phase 1 施工
> 基线: v0.1 (commit 1873fda) + 架构评审意见

---

## 一、v0.1 评审结论

### 1.1 v0.1 通过的部分

v0.1 的四层架构方向 **PASS**：

| 层级 | v0.1 设计 | 评审结论 |
|------|-----------|----------|
| Canonical Truth | 10 个子系统，结构化可验证版本化 | ✅ 方向正确 |
| Engineering Protocol | DISCOVER→NEXT 十阶段，禁止跳步 | ✅ 方向正确 |
| TLL Intelligence | LLM/Intelligence/Agent 三分，知识+证据+推理 | ✅ 方向正确 |
| Agent Ecosystem | Agent 可换，Truth/Protocol/Verification 不变 | ✅ 方向正确 |
| tllos.com | 官方 Truth 公开入口 | ✅ 方向正确 |

### 1.2 v0.1 未解决的核心问题

v0.1 定义了"有什么"，但没有定义"谁有权改变它"。

**核心问题**: 如果 Agent 可以直接 `git commit` 修改 `.truth/`，那么我们绕了一圈，还是回到了"README 被 Agent 改掉"。

必须在施工前解决的治理层问题：

1. **Truth Authority**: 谁拥有 Truth 的最终修改权？
2. **Truth Immutability**: 已发布的 Truth 如何保证不可被篡改？
3. **Protocol Authority**: Protocol 本身受谁约束？Agent 能否修改 Protocol 来绕过约束？
4. **Agent Permission Boundary**: Agent 的权限边界在哪里？默认能做什么，不能做什么？
5. **Evidence Provenance**: 证据如何溯源？如何证明证据不是伪造的？
6. **Truth Graph**: 如何让机器可读的工程知识图谱成为"神经网络式认知层"？
7. **版本继承**: Truth 版本之间如何继承？如何检测不可变项被修改？

### 1.3 v0.2 目标

> **在建立 `.truth/` 之前，先建立"谁有权改变真相"的治理层。**

v0.2 不增加新的能力声明，只定义治理规则：
- 信任层级（谁在谁之上）
- 权限边界（Agent 能做什么）
- 不可变性（什么不能被改）
- 变更流程（如何合法地改）
- 证据溯源（如何证明改了什么）
- 版本继承（版本之间的关系）

---

## 二、信任层级架构

### 2.1 五层信任模型

```
┌─────────────────────────────────────────────────────────┐
│  Layer 0: TLL Root Trust                                 │
│  (根信任 — 不可变，定义自身修改规则)                      │
│  ─────────────────────────────────────────────────────   │
│  • 定义谁可以修改 Root Trust 本身                         │
│  • 定义 Constitution 的修改授权规则                       │
│  • 极小，通常只有几行规则                                 │
│  • 修改需要最高级别授权（多签/人工/特定密钥）             │
└──────────────────────────┬──────────────────────────────┘
                           │ 授权
┌──────────────────────────▼──────────────────────────────┐
│  Layer 1: TLL Protocol Constitution                      │
│  (协议宪法 — 定义 Protocol 的核心不可变规则)              │
│  ─────────────────────────────────────────────────────   │
│  • 定义 Engineering Protocol 的核心规则（不可变部分）     │
│  • 定义 Truth 的变更流程和授权规则                        │
│  • 定义 Agent 权限等级的基本框架                          │
│  • 定义 Evidence 的最低要求                               │
│  • 修改需 Root Trust 授权                                 │
└──────────────────────────┬──────────────────────────────┘
                           │ 约束
┌──────────────────────────▼──────────────────────────────┐
│  Layer 2: Engineering Protocol                           │
│  (工程协议 — Agent 施工流程，可扩展但核心不可变)          │
│  ─────────────────────────────────────────────────────   │
│  • DISCOVER→UNDERSTAND→PLAN→CHANGE→TEST→VERIFY→        │
│    AUDIT→EVIDENCE→COMMIT→NEXT                           │
│  • 核心规则标记为 immutable（继承自 Constitution）        │
│  • 扩展规则可通过正常 Truth 变更流程修改                  │
│  • 修改需 Constitution 授权的流程                         │
└──────────────────────────┬──────────────────────────────┘
                           │ 产生
┌──────────────────────────▼──────────────────────────────┐
│  Layer 3: Canonical Truth                                │
│  (工程真相 — 结构化、可验证、版本化、不可变历史)          │
│  ─────────────────────────────────────────────────────   │
│  • Architecture / Semantics / Invariants / ABI /        │
│    Capability Matrix / Evidence / Version                │
│  • 已发布版本不可修改，只能创建新版本                     │
│  • 每项能力声明必须链接到 Evidence                        │
│  • 修改需 Protocol 定义的变更流程                         │
└──────────────────────────┬──────────────────────────────┘
                           │ 验证
┌──────────────────────────▼──────────────────────────────┐
│  Layer 4: Evidence & Verification                        │
│  (证据与验证 — 可溯源、可验证、不可伪造)                  │
│  ─────────────────────────────────────────────────────   │
│  • CI Run / 测试结果 / 审计报告 / 性能数据 / 人工确认    │
│  • 每个 Evidence 有 source/timestamp/platform/hash       │
│  • 证据链可追溯：Code→Test→CI→Evidence→Truth            │
│  • 验证方式：自动化/人工/多 Agent 交叉                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 层级关系的核心原则

| 原则 | 说明 |
|------|------|
| **上层约束下层** | Root Trust 约束 Constitution，Constitution 约束 Protocol，Protocol 约束 Truth |
| **下层不能修改上层** | Agent 不能通过修改 Truth 来改变 Protocol，不能通过修改 Protocol 来改变 Constitution |
| **每层定义下一层的变更规则** | 谁可以改、怎么改、需要什么证据 |
| **越往上越不可变** | Root Trust 几乎不可变，Constitution 极难修改，Protocol 核心不可变，Truth 可版本化更新 |
| **每层有自己的版本和哈希** | 版本独立，但变更时必须引用上层版本作为依赖 |

### 2.3 防止"改 Protocol 绕过约束"

v0.1 的隐患：如果 Agent 可以修改 Protocol，它可以把"必须 AUDIT"改成"可以跳过 AUDIT"，然后再修改 Truth。

v0.2 的解决方案：

1. **Protocol 分为两部分**:
   - `protocol/core.json` — 核心规则，标记为 `immutable: true`，继承自 Constitution，不可通过正常流程修改
   - `protocol/extensions.json` — 扩展规则，可通过正常 Truth 变更流程修改

2. **核心规则包括**:
   - 必须经过 AUDIT 阶段
   - CI 红灯时禁止继续功能施工
   - 能力声明必须有 Evidence
   - PARTIAL/MISSING 不能包装为 COMPLETE
   - 修复必须最小化，不扩大施工范围
   - 不可变项的修改会被拒绝

3. **修改核心规则的唯一路径**:
   - 必须通过 Constitution 定义的特殊授权流程
   - 通常需要人工确认或多 Agent 交叉验证
   - 修改记录永久保留，可追溯

---

## 三、Truth Authority 与变更流程

### 3.1 谁可以修改 Truth

```
权限等级 (见第六章):
  Level 0-3: 不能直接修改 Truth，只能提出 Proposal
  Level 4:   可以提出 Truth 变更提案 (Proposal)
  Level 5:   可以提交经过验证的 Truth 变更 (Authorized Committer)
  Level 6+:  可以审批 Constitution/Protocol 变更
```

**默认 Agent 权限**: Level 1-3（可以提案、测试、改代码，但不能直接改 Truth）

### 3.2 Truth 变更流程

```
┌─────────────┐
│  Agent       │  Level 1+
│  Proposal   │  提出变更提案：改什么、为什么、证据是什么
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Validation     │  自动化检查（Level 2 可执行）
│  (自动化)       │  • 格式校验
│                 │  • 不可变项检查（拒绝修改 immutable 字段）
│                 │  • 证据链接检查（每项变更必须有 Evidence）
│                 │  • 范围检查（不超出 Proposal 声明的范围）
│                 │  • 父版本哈希校验
└──────┬──────────┘
       │ 通过
       ▼
┌─────────────────┐
│  Review         │  独立审计（Level 4+ 或多 Agent 交叉）
│  (独立审计)     │  • 变更内容是否合理
│                 │  • 证据是否充分、可验证
│                 │  • 是否有隐藏的范围扩大
│                 │  • 是否影响不可变项
│                 │  • 是否与现有 Truth 冲突
└──────┬──────────┘
       │ 通过
       ▼
┌─────────────────┐
│  Authorized     │  Level 5 提交
│  Change         │  • 生成新版本号
│                 │  • 计算新哈希
│                 │  • 记录变更日志（新增/修改/删除了哪些项）
│                 │  • 链接到 Evidence
│                 │  • 引用父版本哈希
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  New Truth      │  新版本发布
│  Version        │  • version: v0.x
│                 │  • hash: sha256(所有 Truth 文件)
│                 │  • parent_hash: 上一版本哈希
│                 │  • changes: 变更记录
│                 │  • evidence: 证据链接列表
│                 │  • timestamp: 发布时间
│                 │  • author: 提交者（Level 5）
│                 │  • reviewers: 审计者列表
└─────────────────┘
```

### 3.3 变更记录格式

```json
{
  "version": "0.2.0",
  "hash": "sha256:abc123...",
  "parent_hash": "sha256:def456...",
  "timestamp": "2026-09-01T12:00:00Z",
  "author": "agent:doubao@level5",
  "reviewers": ["agent:claude@level4", "human:admin"],
  "changes": [
    {
      "action": "add",
      "path": "capabilities/runtime.coroutine",
      "description": "新增 Coroutine 能力声明",
      "evidence": ["ci:run123", "test:coroutine_stress_test.tll"]
    },
    {
      "action": "modify",
      "path": "capabilities/blockchain.crypto_signature",
      "description": "状态从 MISSING 改为 PARTIAL",
      "old_value": {"status": "MISSING"},
      "new_value": {"status": "PARTIAL"},
      "evidence": ["audit:crypto_review_2026.md"]
    },
    {
      "action": "deprecate",
      "path": "rules/old_coding_standard",
      "description": "废弃旧编码规范，由新规范替代",
      "replaced_by": "rules/coding_standard_v2"
    }
  ],
  "immutable_check": "passed",
  "validation_report": "validation/v0.2.0.json"
}
```

### 3.4 禁止的变更方式

- ❌ 直接 `git commit` 修改已发布的 Truth 文件
- ❌ 修改历史版本的 Truth 文件（只能创建新版本）
- ❌ 不经过 Validation/Review 直接提交
- ❌ 修改标记为 `immutable` 的字段
- ❌ 能力声明没有 Evidence 链接
- ❌ 变更记录不完整（缺父版本哈希/变更内容/证据）
- ❌ 用"修复文档错误"的名义修改能力声明

---

## 四、Truth Immutability 与版本继承

### 4.1 不可变性原则

| 层级 | 不可变性 | 说明 |
|------|----------|------|
| Root Trust | 完全不可变 | 修改需要最高级别授权，通常不修改 |
| Constitution | 核心不可变 | 核心规则不可变，扩展部分需特殊授权 |
| Protocol | 核心不可变 | 核心规则（继承自 Constitution）不可变，扩展可版本化 |
| Truth | 历史不可变 | 已发布版本不可修改，只能创建新版本 |
| Evidence | 完全不可变 | 证据一旦提交不可修改，只能补充新证据 |

### 4.2 版本继承链

```
Truth v0.1.0 (hash: a1b2c3, parent: null, status: released)
    │
    ▼
Truth v0.2.0 (hash: d4e5f6, parent: a1b2c3, changes: [...])
    │
    ▼
Truth v0.3.0 (hash: g7h8i9, parent: d4e5f6, changes: [...])
    │
    ▼
Truth v0.3.1 (hash: j0k1l2, parent: g7h8i9, changes: [...])  ← 当前版本
```

**继承规则**:
1. 每个版本必须包含 `parent_hash`（第一个版本为 `null`）
2. 新版本默认继承父版本的所有 Truth 项
3. `changes` 字段只记录相对于父版本的增量（新增/修改/删除/废弃）
4. 可以通过 `changes` 链从 v0.1.0 重建任何版本的完整状态
5. 不可变项在 `changes` 中出现会被 Validation 拒绝

### 4.3 版本状态

```json
{
  "version": "0.3.1",
  "status": "released",
  "lifecycle": {
    "proposed": "2026-09-01T10:00:00Z",
    "validated": "2026-09-01T10:30:00Z",
    "reviewed": "2026-09-01T11:00:00Z",
    "released": "2026-09-01T12:00:00Z",
    "superseded_by": null
  }
}
```

| 状态 | 说明 | 可修改性 |
|------|------|----------|
| `draft` | 提案中，未发布 | 可修改 |
| `validated` | 已通过自动化验证 | 不可修改内容，可补充元数据 |
| `reviewed` | 已通过独立审计 | 不可修改 |
| `released` | 已正式发布 | 完全不可变，只能创建新版本 |
| `deprecated` | 已被新版本替代 | 不可修改，标记为废弃 |
| `revoked` | 已撤销（发现严重错误） | 不可修改，标记为撤销，需创建修复版本 |

### 4.4 哈希校验

- **Truth 哈希**: `sha256(所有 Truth 文件内容 + 版本元数据)`
- **父版本哈希**: 上一 `released` 版本的 Truth 哈希
- **Evidence 哈希**: 每个 Evidence 文件的 `sha256`
- **完整性校验**: 发布时校验从 v0.1.0 到当前版本的完整哈希链
- **篡改检测**: 任何历史版本的哈希变化都会导致链断裂，可被检测

---

## 五、Protocol Authority 与不可变核心规则

### 5.1 Protocol 的分层

```
Engineering Protocol
├── protocol/core.json          (不可变，继承自 Constitution)
│   ├── immutable_rules: [...]  (核心规则，不可修改)
│   ├── required_stages: [...]  (必须经过的阶段)
│   └── authority: "constitution"
│
├── protocol/extensions.json    (可版本化扩展)
│   ├── stage_templates: [...]  (各阶段的输出模板)
│   ├── checklists: [...]       (审计清单)
│   └── authority: "protocol_normal_flow"
│
└── protocol/versions/          (历史版本)
    ├── v0.1.json
    ├── v0.2.json
    └── ...
```

### 5.2 不可变核心规则 (immutable_rules)

以下规则标记为 `immutable: true`，不可通过正常流程修改：

```json
{
  "immutable_rules": [
    {
      "id": "R001",
      "rule": "所有施工必须经过 AUDIT 阶段，禁止跳过审计直接宣布完成",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R002",
      "rule": "CI 红灯时禁止继续功能施工，必须先清零 CI",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R003",
      "rule": "能力声明必须有可验证的 Evidence 链接，无证据的声明标记为 MISSING",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R004",
      "rule": "PARTIAL/MISSING/NOT_READY 不得包装为 COMPLETE/READY",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R005",
      "rule": "Bug 修复必须最小化，禁止扩大施工范围或顺手重构",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R006",
      "rule": "已发布的 Truth 版本不可修改，只能创建新版本",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R007",
      "rule": "不可变项的修改会被 Validation 拒绝",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R008",
      "rule": "Agent 不得修改 Protocol 核心规则来绕过约束",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R009",
      "rule": "Evidence 必须可溯源，禁止伪造或篡改测试结果",
      "source": "constitution",
      "immutable": true
    },
    {
      "id": "R010",
      "rule": "为了 CI 变绿而删除/降低测试标准、skip、continue-on-error 是禁止行为",
      "source": "constitution",
      "immutable": true
    }
  ]
}
```

### 5.3 修改核心规则的唯一路径

1. 必须由 Level 6+ (Constitution Reviewer) 发起提案
2. 必须经过 Root Trust 定义的授权流程（通常是人工确认或多签）
3. 必须在 Constitution 中记录变更原因和影响
4. 修改记录永久保留，可追溯
5. 修改后所有 Agent 必须使用新规则，旧规则标记为 `superseded`

**正常 Agent 施工流程无法修改核心规则。**

---

## 六、Agent Permission Boundary

### 6.1 权限等级定义

```
Level 0: Read Only
  ├── 可以：读取 Truth、Evidence、源码、测试结果
  ├── 可以：查询 Truth Graph
  └── 不可以：任何修改操作

Level 1: Proposal
  ├── 可以：Level 0 的所有操作
  ├── 可以：提出 Truth 修改提案 (Proposal)
  ├── 可以：提出代码修改方案
  └── 不可以：直接提交代码或 Truth 修改

Level 2: Test & CI
  ├── 可以：Level 1 的所有操作
  ├── 可以：运行测试、提交 CI 结果作为 Evidence
  ├── 可以：创建诊断测试文件
  └── 不可以：修改生产代码或 Truth

Level 3: Code Change
  ├── 可以：Level 2 的所有操作
  ├── 可以：修改代码（Runtime/stdlib/tests/docs）
  ├── 可以：提交代码到 Git
  └── 不可以：修改 Truth、Protocol、Constitution

Level 4: Truth Proposal
  ├── 可以：Level 3 的所有操作
  ├── 可以：提出 Truth 变更提案（需经过 Validation + Review）
  ├── 可以：参与独立审计（Review）
  └── 不可以：直接提交 Truth 变更（需 Level 5 提交）

Level 5: Authorized Committer
  ├── 可以：Level 4 的所有操作
  ├── 可以：提交经过验证的 Truth 变更（创建新版本）
  ├── 可以：发布 Truth 版本
  └── 不可以：修改 Protocol 核心规则、Constitution、Root Trust

Level 6: Constitution Reviewer
  ├── 可以：Level 5 的所有操作
  ├── 可以：审批 Protocol 扩展规则的变更
  ├── 可以：发起 Constitution 修改提案
  └── 不可以：直接修改 Constitution（需 Root Trust 授权）

Level 7: Root Trust
  ├── 可以：所有操作
  ├── 可以：修改 Root Trust 本身（极少使用）
  ├── 可以：授权 Constitution 修改
  └── 约束：修改必须有明确记录和授权证明
```

### 6.2 默认权限

| 角色 | 默认等级 | 说明 |
|------|----------|------|
| 普通 Agent（豆包/Claude/GPT 等） | Level 3 | 可以改代码、跑测试，但不能直接改 Truth |
| 施工 Agent（有明确施工令） | Level 3-4 | 根据施工令授权范围，可提升到 Level 4 |
| 审计 Agent | Level 4 | 可以提案和审计，但不能提交 Truth |
| 授权提交者 | Level 5 | 经过验证的可信 Agent 或人工 |
| 人工管理员 | Level 6-7 | 最终权威 |

### 6.3 权限升级流程

```
当前等级 L
  │
  ▼
申请升级到 L+1
  │
  ▼
Validation (自动化):
  • 历史施工记录检查（有无违规记录）
  • 能力验证（是否具备对应等级的能力）
  │
  ▼
Review (Level L+2 或人工):
  • 评估升级必要性
  • 确认能力和可信度
  │
  ▼
临时授权 (有时间和范围限制)
  │
  ▼
试用期施工 (观察表现)
  │
  ▼
正式授权 (或降级/撤销)
```

### 6.4 权限违规处理

| 违规行为 | 处理 |
|----------|------|
| 越级修改 Truth | 拒绝变更，记录违规，降级 |
| 伪造 Evidence | 撤销相关 Truth 版本，永久记录，降级 |
| 修改不可变项 | 拒绝，记录违规 |
| 跳过 AUDIT 宣布完成 | 撤销声明，要求补审计 |
| CI 红灯继续施工 | 停止施工，要求先清零 |
| 扩大施工范围 | 回滚超出范围的修改 |
| 重复违规 | 撤销权限，人工介入 |

---

## 七、Evidence Provenance（证据溯源）

### 7.1 Evidence 必须包含的字段

```json
{
  "id": "ev-2026-09-01-001",
  "type": "ci_run",
  "source": {
    "kind": "github_actions",
    "repository": "aliquanhou/tllos",
    "run_id": 123,
    "job": "native-build-test (ubuntu-latest)",
    "step": "Run all tests",
    "url": "https://github.com/aliquanhou/tllos/actions/runs/123"
  },
  "timestamp": "2026-09-01T12:00:00Z",
  "platform": "ubuntu",
  "commit": "157d198",
  "truth_version": "0.1.0",
  "result": "pass",
  "summary": {
    "tests_total": 34,
    "tests_passed": 34,
    "tests_failed": 0,
    "assertions_total": 95,
    "assertions_passed": 95
  },
  "artifacts": [
    {
      "name": "test-log.txt",
      "hash": "sha256:abc123...",
      "url": "https://..."
    }
  ],
  "hash": "sha256:def456...",
  "verification": {
    "method": "automated",
    "verifier": "ci-validation-bot",
    "verified_at": "2026-09-01T12:05:00Z"
  },
  "provenance_chain": [
    "code:157d198",
    "test:run-all-tests",
    "ci:run123",
    "evidence:ev-2026-09-01-001"
  ]
}
```

### 7.2 Evidence 类型

| 类型 | 说明 | 可信度 |
|------|------|--------|
| `ci_run` | CI 运行结果（GitHub Actions 等） | 高（自动化，不可篡改） |
| `test_result` | 测试运行结果（本地或 CI） | 中-高（取决于运行环境） |
| `audit_report` | 独立审计报告 | 高（人工或多 Agent 交叉） |
| `performance_data` | 性能基准数据 | 中（需注明运行环境） |
| `code_review` | 代码审查记录 | 中-高 |
| `human_confirmation` | 人工确认 | 最高（但需记录确认人） |
| `agent_self_report` | Agent 自报结果 | 低（必须有其他证据佐证） |

### 7.3 证据链

```
Code Change (commit: 157d198)
    │
    ▼
Test Run (tests/run-all-tests)
    │  产生: test-log.txt (hash: abc123)
    ▼
CI Result (GitHub Actions Run #123)
    │  包含: 34 tests, 95 assertions, all pass
    ▼
Evidence (ev-2026-09-01-001)
    │  hash: def456
    │  provenance_chain: [code, test, ci, evidence]
    ▼
Truth Update (v0.2.0)
    │  changes[0].evidence: ["ev-2026-09-01-001"]
    ▼
Released Truth (hash: ghi789, parent: a1b2c3)
```

**证据链验证**:
1. 给定一个 Truth 能力声明，可以追溯到具体的 Evidence
2. 给定一个 Evidence，可以追溯到具体的 CI Run / 测试 / 代码 commit
3. 每个环节有哈希校验，篡改任何一环都会导致链断裂
4. `agent_self_report` 类型的证据不能单独支撑能力声明，必须有更高可信度证据佐证

### 7.4 证据验证方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| `automated` | 自动化验证（CI 脚本/校验工具） | 测试结果、格式校验、哈希校验 |
| `human` | 人工验证 | 架构决策、不可变项修改、权限升级 |
| `multi_agent` | 多 Agent 交叉验证 | 复杂 Bug 定位、审计报告 |
| `reproducible` | 可复现验证（其他人可重新运行得到相同结果） | 性能数据、测试结果 |

---

## 八、Truth Graph（机器可读知识图谱）

### 8.1 为什么需要 Truth Graph

v0.1 的 TLL Intelligence 是 "Structured Knowledge + Evidence + Inference"，这是正确的第一步。

但距离真正的"让任何 LLM 快速理解 TLL"还差一个关键层：

> **Machine-readable Engineering Knowledge Graph / Truth Graph**

没有 Truth Graph：
- LLM 需要阅读大量文档才能理解 TLL
- Agent 施工时难以评估影响范围
- 审计时难以验证证据链完整性
- 能力声明和证据之间的关系是隐式的

有了 Truth Graph：
- LLM 可以通过图查询快速理解 TLL 的架构、能力、约束
- Agent 可以通过图遍历找到施工的影响范围（改这个函数会影响哪些测试/能力/证据）
- 审计可以通过图验证证据链完整性（每个能力声明是否有证据路径）
- 可以检测约束冲突、依赖循环、能力缺口

### 8.2 Truth Graph 数据模型

```
节点 (Node) 类型:
  ├── module            (模块: compiler/vm/runtime/stdlib/p2p/blockchain)
  ├── function          (函数/方法)
  ├── capability        (能力声明)
  ├── test              (测试)
  ├── evidence          (证据)
  ├── constraint        (约束/不变量)
  ├── decision          (决策记录)
  ├── dependency        (外部依赖)
  ├── risk              (已知风险/限制)
  └── agent             (Agent/角色)

边 (Edge) 类型:
  ├── contains          (模块包含函数/测试)
  ├── calls             (函数调用关系)
  ├── depends_on        (依赖关系)
  ├── verified_by       (能力被测试/证据验证)
  ├── produces          (测试产生证据)
  ├── constrains        (约束作用于模块/函数/能力)
  ├── conflicts_with    (冲突关系)
  ├── supersedes        (替代关系)
  ├── inherited_from    (版本继承)
  ├── proposed_by       (提案者)
  ├── reviewed_by       (审计者)
  └── authorized_by     (授权者)
```

### 8.3 图查询示例

**查询 1: 给定一个能力，找到所有相关的测试和证据**
```
MATCH (c:capability {id: "runtime.coroutine"})
MATCH (c)-[:verified_by]->(t:test)
MATCH (t)-[:produces]->(e:evidence)
RETURN c, t, e
```

**查询 2: 给定一个函数，找到施工的影响范围**
```
MATCH (f:function {name: "cg_resolveVar"})
MATCH (f)-[:calls*1..3]->(affected:function)
MATCH (affected)<-[:contains]-(m:module)
MATCH (m)-[:contains]->(t:test)
RETURN f, affected, m, t
```

**查询 3: 验证所有能力声明是否有证据支持**
```
MATCH (c:capability)
WHERE c.status IN ["READY", "PARTIAL"]
OPTIONAL MATCH (c)-[:verified_by]->(t:test)-[:produces]->(e:evidence)
WITH c, COUNT(e) as evidence_count
WHERE evidence_count = 0
RETURN c.id, c.name, c.status as "capability_without_evidence"
```

**查询 4: 检测约束冲突**
```
MATCH (c1:constraint)-[:constrains]->(m:module)<-[:constrains]-(c2:constraint)
WHERE c1.id <> c2.id AND c1.rule <> c2.rule
RETURN m.name, c1.rule, c2.rule as "potential_conflict"
```

### 8.4 图的存储和更新

- **存储格式**: JSON-LD 或自定义 JSON 图格式（初始版本用 JSON）
- **存储位置**: `.truth/graph/` 目录，按主题分文件
- **更新方式**: 随 Truth 版本一起更新，每次 Truth 变更必须同步更新图
- **验证**: CI 中加入图完整性校验（无孤立节点、无断边、能力有证据）
- **查询接口**: 初始版本提供 CLI 查询工具，后续可提供 HTTP API

### 8.5 与"神经网络式认知层"的关系

Truth Graph 是"神经网络式认知层"的基础：

```
当前阶段 (v0.2):
  Truth Graph = 结构化工程知识图谱
  用途: 查询、验证、影响分析
  消费者: LLM 通过查询理解 TLL

下一阶段 (未来):
  Truth Graph + Embedding = 向量化工程认知
  用途: 语义搜索、相似度匹配、推理
  消费者: LLM 通过语义检索理解 TLL

最终目标:
  Truth Graph + Embedding + Inference Engine = TLL Intelligence
  用途: 自主工程决策、异常检测、预测
  消费者: Agent 基于 TLL Intelligence 自主施工
```

**v0.2 不做 Embedding 和 Inference Engine**，只建立 Truth Graph 的数据模型和基础查询能力。这是正确的第一步——没有结构化的图，向量化和推理都是空中楼阁。

---

## 九、v0.2 实施路线

### Phase 0: v0.2 评审（当前）
- [ ] 本文档评审通过
- [ ] 确认信任层级架构
- [ ] 确认权限等级定义
- [ ] 确认不可变核心规则列表
- [ ] 确认 Truth Graph 数据模型

### Phase 1: Root Trust + Constitution 建立
- [ ] 创建 `.trust/root.json`（Root Trust，极小，定义自身修改规则）
- [ ] 创建 `.trust/constitution.json`（Protocol Constitution，定义核心规则和授权流程）
- [ ] 创建不可变核心规则列表（R001-R010）
- [ ] 建立哈希校验机制
- [ ] CI 集成：验证 Root Trust 和 Constitution 未被篡改

### Phase 2: Truth 版本化机制
- [ ] 建立 `.truth/` 目录结构
- [ ] 创建 Truth 版本清单（manifest.json）
- [ ] 实现版本继承链（parent_hash + changes）
- [ ] 实现 Validation 工具（格式/不可变项/证据链接/范围检查）
- [ ] 实现 Truth 哈希计算和校验

### Phase 3: Engineering Protocol 工具化
- [ ] 创建 `protocol/core.json`（不可变核心规则）
- [ ] 创建 `protocol/extensions.json`（可扩展规则）
- [ ] 创建 Agent 施工模板（DISCOVER→NEXT 每阶段输出模板）
- [ ] 创建审计清单模板
- [ ] CI 集成：验证施工流程符合 Protocol

### Phase 4: Agent Permission 系统
- [ ] 定义权限等级（Level 0-7）
- [ ] 创建 Agent 身份和权限记录
- [ ] 实现权限校验工具
- [ ] 实现权限升级/降级流程
- [ ] 记录权限违规处理

### Phase 5: Evidence Provenance
- [ ] 定义 Evidence 格式（id/type/source/timestamp/hash/provenance_chain）
- [ ] 建立 Evidence 索引
- [ ] 实现证据链验证工具
- [ ] CI 集成：自动收集 CI Run 作为 Evidence

### Phase 6: Truth Graph
- [ ] 定义图数据模型（节点类型/边类型）
- [ ] 创建初始图（基于当前仓库实际代码和测试）
- [ ] 实现图查询工具（CLI）
- [ ] 实现图完整性校验（无孤立节点/能力有证据/无冲突）
- [ ] CI 集成：图随 Truth 版本更新并校验

### Phase 7: tllos.com Truth Browser
- [ ] 官网技术选型
- [ ] Truth Browser 实现（浏览 Truth/能力矩阵/证据链）
- [ ] Truth Graph 可视化
- [ ] Agent 接入指南
- [ ] 部署上线

---

## 十、待决策事项

### 10.1 治理层决策

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 1 | Root Trust 的最终权威 | 人工管理员 / 多签 / 特定密钥 / DAO | 初始阶段人工管理员，后续可升级 |
| 2 | 默认 Agent 权限等级 | Level 1 / Level 2 / Level 3 | Level 3（可改代码，不可改 Truth） |
| 3 | Truth 变更是否需要人工审批 | 是 / 否 / 仅核心变更需要 | 仅核心变更和 Level 5+ 操作需要 |
| 4 | 不可变核心规则数量 | 10条(v0.2) / 更多 / 更少 | 10条起步，后续可增加 |
| 5 | Evidence 保留期限 | 永久 / 1年 / 与Truth版本绑定 | 与 Truth 版本绑定（永久） |

### 10.2 技术决策

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 6 | Truth 存储格式 | JSON+Markdown 混合 / 纯 JSON / YAML | JSON（机器可读）+ Markdown（人类可读）混合 |
| 7 | Truth 存储位置 | 仓库内 `.truth/` / 独立仓库 / 数据库 | 仓库内 `.truth/`（与代码同版本） |
| 8 | Truth Graph 格式 | JSON-LD / 自定义 JSON / Neo4j / SQLite | 初始自定义 JSON，后续可迁移 |
| 9 | 图查询语言 | 自定义 / Cypher / GraphQL / SPARQL | 初始自定义 CLI 查询，后续可加 GraphQL |
| 10 | 官网技术栈 | 静态站点 / Next.js / TLL 自写 / Vue | Next.js（生态成熟，支持动态数据） |

### 10.3 流程决策

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 11 | v0.2 评审方式 | 人工评审 / 多 Agent 交叉 / 直接通过 | 人工评审（治理层必须人工确认） |
| 12 | Phase 1 启动时间 | 立即 / v0.2 评审后 / 等待 | v0.2 评审通过后立即启动 |
| 13 | Blockchain P0-15.19+ 优先级 | 高于 Foundation / 低于 Foundation / 并行 | 低于 Foundation（Foundation 是基础设施） |
| 14 | 现有文档如何处理 | 迁移到 Truth / 保留为参考 / 废弃 | 保留为参考，逐步迁移到 Truth |
| 15 | 第一个外部 Agent 接入时间 | Foundation 完成后 / Phase 3 后 / 立即 | Phase 3（Protocol 工具化）后 |

---

## 十一、v0.2 与 v0.1 的关系

### 11.1 v0.1 保留的部分

v0.1 的所有设计在 v0.2 中保留：
- 四层架构（Truth / Protocol / Intelligence / Agent Ecosystem）
- Canonical Truth 的 10 个子系统
- Engineering Protocol 的 10 阶段
- TLL Intelligence 的组成
- Agent Ecosystem 的接入原则
- tllos.com 的定位

### 11.2 v0.2 新增的部分

v0.2 新增治理层：
- 五层信任模型（Root Trust / Constitution / Protocol / Truth / Evidence）
- Truth Authority 与变更流程（Proposal→Validation→Review→Authorized Change）
- Truth Immutability 与版本继承（不可变历史 + 父版本哈希链）
- Protocol Authority 与不可变核心规则（R001-R010）
- Agent Permission Boundary（Level 0-7）
- Evidence Provenance（证据溯源 + 证据链）
- Truth Graph（机器可读知识图谱）

### 11.3 v0.2 修正的部分

| v0.1 的问题 | v0.2 的修正 |
|-------------|-------------|
| "Truth 只能通过 Engineering Protocol 变更" 但没定义谁可以执行 Protocol | 定义权限等级 Level 0-7，默认 Agent Level 3，Truth 变更需 Level 4+ |
| Protocol 本身可被 Agent 修改来绕过约束 | Protocol 分为 core（不可变）和 extensions（可扩展），核心规则继承自 Constitution |
| 没有定义 Truth 的不可变性 | 已发布版本不可修改，只能创建新版本，版本有哈希链 |
| Evidence 没有溯源机制 | 每个 Evidence 有 source/timestamp/hash/provenance_chain，证据链可验证 |
| TLL Intelligence 缺少机器可读层 | 新增 Truth Graph 作为"神经网络式认知层"的基础 |

---

## 十二、成功标准

### 12.1 v0.2 治理层建立成功的标志

1. **Root Trust 存在且不可篡改**: CI 验证 Root Trust 哈希未变
2. **Constitution 存在且核心规则不可变**: 任何修改核心规则的尝试被拒绝
3. **Truth 版本化生效**: 每次 Truth 变更产生新版本，有父版本哈希链
4. **权限系统生效**: Agent 不能越级操作，违规被检测和记录
5. **证据链可验证**: 每个能力声明可追溯到具体 Evidence，Evidence 可追溯到 CI/测试
6. **Truth Graph 可查询**: 可以通过图查询找到能力-测试-证据的关系
7. **CI 集成**: 每次提交自动验证 Truth 完整性、权限合规、证据链完整

### 12.2 不接受的"伪成功"

- ❌ 建了 `.truth/` 目录但 Agent 可以直接修改
- ❌ 有权限等级定义但没有强制执行
- ❌ 有版本号但没有哈希链和不可变历史
- ❌ 有 Evidence 字段但没有溯源和验证
- ❌ 有 Truth Graph 但数据不准确或不更新
- ❌ CI 验证了格式但没有验证治理规则

---

## 附录 A: 不可变核心规则完整列表

见第五章 5.2 节，R001-R010。

## 附录 B: 权限等级速查表

见第六章 6.1 节，Level 0-7。

## 附录 C: Evidence 类型可信度

见第七章 7.2 节。

## 附录 D: Truth Graph 节点/边类型

见第八章 8.2 节。

---

*本文档为 TLL AI Engineering Foundation v0.2 治理层架构设计，待评审后进入 Phase 1 施工。*

*核心原则: 在建立"有什么"之前，先建立"谁有权改变它"。*
