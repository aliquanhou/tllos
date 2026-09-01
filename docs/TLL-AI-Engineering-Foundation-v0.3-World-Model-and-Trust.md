# TLL AI Engineering Foundation v0.3 — Engineering World Model & Trust Architecture

> 版本: 0.3 (Draft)
> 日期: 2026-09-01
> 状态: 架构评审阶段，待评审后进入 v0.4 或 Phase 1 施工
> 基线: v0.2 (commit f797fcf) + 架构评审意见

---

## 一、v0.2 评审结论

### 1.1 v0.2 通过的部分

v0.2 的治理方向 **PASS**：

| 设计 | 评审结论 |
|------|----------|
| 五层信任模型 (Root Trust → Constitution → Protocol → Truth → Evidence) | ✅ 方向正确 |
| Truth 版本继承 + parent_hash，历史不可修改 | ✅ 方向正确 |
| Evidence provenance chain (Code→Test→CI→Evidence→Truth) | ✅ 方向正确 |
| Truth Graph 作为机器可查询的工程关系网络 | ✅ 方向正确 |
| 禁止 Agent 修改 Protocol 核心规则绕过约束 | ✅ 方向正确 |
| 禁止为 CI 变绿降低测试标准 | ✅ 方向正确 |

### 1.2 v0.2 未解决的核心问题

v0.2 仍然有"把治理当成文件权限"的倾向。

**核心问题**: 我们真正需要回答的不是"哪个文件在上面"，而是：

> **什么机制能够证明一个主体确实有权进行这个操作？**

举个极端例子：
```
Agent 声称: 我是 agent:doubao, Level 5
Agent 操作: 修改 .truth/...
Agent 声称: 这是合法 Truth Change，这是我的 Evidence
```

问题：**谁验证"你真的是 Level 5？"**

如果答案是"读取 agent.json"，那又回来了：
```
Agent 修改 agent.json → 给自己升权 → 声称合法
```

所以真正的 Root Trust 不能只是一个 JSON 文件。

### 1.3 v0.2 的四个具体缺陷

**缺陷 1: 缺少 Identity / Authorization Root**

v0.2 定义了权限等级 Level 0-7，但没有定义：
- 谁验证 Agent 的身份？
- 谁授予 Agent 权限？
- 如何防止 Agent 自封身份或自升权限？

**缺陷 2: Level ≠ Trust**

v0.2 把权限等级和可信度混为一谈。需要区分三个概念：
- **Identity** = 你是谁（身份验证）
- **Authority** = 你被允许做什么（授权）
- **Evidence Trust** = 你的结果有多可信（证据可信度）

一个 Agent 可以暂时获得 Level 5，但这不意味着"它说的话就是真相"。

**缺陷 3: Truth Graph 只是图数据库，不是工程世界模型**

v0.2 的 Truth Graph 设计了节点和边，但验收标准只是"无孤立节点无断边"。

真正的价值是：**它必须能够回答 Agent 的工程问题，支持真实施工决策。**

例如 Agent 要修改 `cg_resolveVar()`，系统应该能回答：
- 这个函数属于哪个模块？
- 谁调用它？
- 哪些 ABI 依赖它？
- 哪些测试覆盖它？
- 哪些 Capability 依赖它？
- 最近谁修改过？
- 过去有没有因为它产生 Regression？
- 修改它会影响哪些 Truth？
- 当前有哪些 Constraint？
- 需要重新执行哪些验证？

**缺陷 4: Evidence 没有明确的证明范围**

v0.2 定义了 Evidence 类型和可信度，但没有定义：
- 这个 Evidence 具体证明了什么？
- 它不证明什么？
- CI PASS 只能证明"某个 commit 在某个环境下通过了某组验证"，不能自动证明"整个能力成立"

我们自己的 Blockchain 就是最好的例子：
```
CI 全绿
  ↓
Production Blockchain = NOT READY
```

如果 Evidence 没有明确的范围，就会出现：
```
测试通过 → 能力 COMPLETE → 生产 READY
```
这种逻辑偷换。

### 1.4 v0.3 目标

> **先定义：什么是真实？谁能声明？谁能验证？谁能授权？如何证明？如何追溯？如何自动验证？如何演化？**
> 
> **然后再设计 .truth/ → Truth Graph → Protocol → Agent。**

v0.3 不增加新的能力声明，只定义核心概念和它们之间的关系：

| 概念 | 解决的问题 |
|------|-----------|
| **Identity** | 谁是 Agent？如何验证身份？ |
| **Authority** | 谁授权它？授权证明是什么？ |
| **Permission** | 它能做什么？范围和时间限制？ |
| **Truth** | 什么叫工程事实？ |
| **Claim** | 这个事实声称了什么？范围和置信度？ |
| **Evidence** | 什么证据支持这个事实？证明什么/不证明什么？ |
| **Verification** | 谁验证了证据？验证方式和范围？ |
| **World Model** | 这些事实之间是什么关系？能否支持工程决策？ |
| **CI/CD** | 哪些关系能够自动验证？ |
| **History** | 事实为什么发生变化？完整演化链？ |

---

## 二、整体架构：TLL Engineering World

### 2.1 架构总览

```
                    TLL Engineering World
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Identity         Truth         Protocol
   (身份层)        (事实层)        (规则层)
        │              │              │
        └──────────────┼──────────────┘
                       │
                  World Model
               (工程世界模型层)
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Code           Tests            Git
   (代码世界)      (测试世界)      (历史世界)
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                    CI/CD
               (自动验证层)
                       │
                       ▼
                    Evidence
                (证据层)
                       │
                       ▼
                     Agent
                 (执行主体层)
                       │
                       ▼
                      LLM
                 (外部智能来源)
```

### 2.2 各层职责

| 层 | 职责 | 核心问题 |
|----|------|----------|
| **Identity** | 验证 Agent 身份，防止冒充 | 你是谁？如何证明？ |
| **Truth** | 定义工程事实，管理声明和证据 | 什么是真实的？ |
| **Protocol** | 定义施工规则，约束 Agent 行为 | 应该怎么做？ |
| **World Model** | 建立工程关系网络，支持决策 | 这些事实之间什么关系？ |
| **Code/Tests/Git** | 工程世界的原始数据 | 实际代码/测试/历史是什么？ |
| **CI/CD** | 自动验证工程关系 | 哪些能自动验证？ |
| **Evidence** | 记录验证结果，支持 Truth 声明 | 什么证据支持什么声明？ |
| **Agent** | 执行施工操作，遵循 Protocol | 谁在做事？ |
| **LLM** | 提供智能推理能力 | 智能从哪来？ |

### 2.3 层间关系原则

| 原则 | 说明 |
|------|------|
| **下层为上层提供数据** | Code/Tests/Git → World Model → Truth → Agent |
| **上层约束下层行为** | Protocol → Agent → Code/Tests/Git |
| **Identity 独立于 Truth** | 身份验证不依赖 Truth 文件（防止自升权） |
| **Evidence 连接 Truth 和 CI/CD** | Truth 声明必须有 Evidence，Evidence 来自 CI/CD 或验证 |
| **World Model 是中间层** | 不直接存储事实，而是建立事实之间的关系 |
| **LLM 可替换** | 换 LLM 不换 Identity/Truth/Protocol/World Model |

---

## 三、Identity（身份层）

### 3.1 什么是 Identity

Identity 回答"你是谁"的问题。

**关键原则**:
- 身份不可自封：Agent 不能自己声明自己是谁
- 身份必须验证：每个操作都必须验证操作者身份
- 身份不可篡改：身份记录不可被 Agent 修改
- 身份与权限分离：身份验证通过后，才检查权限

### 3.2 Identity Root（身份根）

Identity Root 不是一个 JSON 文件，而是一个**注册和验证机制**。

```
Identity Root
├── 注册机制
│   ├── 人工注册 Agent（初始阶段）
│   ├── 每个 Agent 分配唯一 Agent ID
│   ├── 每个 Agent 生成密钥对（公钥注册，私钥保留）
│   └── 注册记录不可修改，只能追加
│
├── 验证机制
│   ├── Agent 操作时用私钥签名
│   ├── 系统用注册的公钥验证签名
│   ├── 验证失败 → 拒绝操作
│   └── 验证记录永久保留
│
└── 身份生命周期
    ├── active（正常）
    ├── suspended（暂停，违规或安全事件）
    ├── revoked（撤销，永久禁用）
    └── 状态变更需人工授权
```

### 3.3 Agent 身份记录

```json
{
  "agent_id": "agent:doubao",
  "identity": {
    "type": "registered_agent",
    "registered_at": "2026-09-01T10:00:00Z",
    "registered_by": "admin:user",
    "public_key": "ssh-rsa AAAAB3...",
    "key_fingerprint": "SHA256:abc123..."
  },
  "status": "active",
  "status_history": [
    {
      "status": "active",
      "changed_at": "2026-09-01T10:00:00Z",
      "changed_by": "admin:user",
      "reason": "initial registration"
    }
  ],
  "identity_root_hash": "sha256:def456..."
}
```

### 3.4 身份验证流程

```
Agent 发起操作
    │
    ▼
携带操作签名（私钥签名）
    │
    ▼
系统验证签名（用注册的公钥）
    │
    ├─ 验证失败 → 拒绝操作，记录违规
    │
    └─ 验证成功 → 确认 Agent ID
         │
         ▼
    检查 Agent 状态（active/suspended/revoked）
         │
         ├─ 非 active → 拒绝操作
         │
         └─ active → 进入 Authority 检查
```

### 3.5 防止自升权

| 攻击路径 | 防御机制 |
|----------|----------|
| Agent 修改 agent.json 给自己升权 | Identity Root 不在 .truth/ 内，Agent 无权限修改 |
| Agent 冒充其他 Agent | 每个操作需要私钥签名，公钥在 Identity Root 注册 |
| Agent 修改 Identity Root | Identity Root 修改需人工授权 + 多签 |
| Agent 篡改历史验证记录 | 记录只追加，不可修改，有哈希链 |
| Agent 用已撤销身份操作 | 身份状态检查，revoked 身份拒绝所有操作 |

---

## 四、Authority（授权层）

### 4.1 什么是 Authority

Authority 回答"谁授权你做这个"的问题。

**关键原则**:
- 授权不可自授：Agent 不能自己给自己授权
- 授权有范围：不是"Level 5 就能做所有事"，而是"在这个 scope 内能做这些事"
- 授权有时间：临时授权到期自动失效
- 授权有证明：每个操作必须有授权证明（Authorization Token）

### 4.2 授权来源

| 来源 | 说明 | 可信度 |
|------|------|--------|
| **人工授权** | 人工管理员明确授权 | 最高 |
| **施工令授权** | 用户/管理员下发的施工令，有明确范围和时间 | 高 |
| **Protocol 自动授权** | 符合 Protocol 规则的操作自动获得授权（如运行测试） | 中 |
| **继承授权** | 父任务授权范围内的子操作 | 中（需验证范围） |

### 4.3 Authorization Token（授权证明）

每个 Agent 操作必须携带有效的 Authorization Token：

```json
{
  "token_id": "auth-2026-09-01-001",
  "agent_id": "agent:doubao",
  "identity_verified": true,
  "identity_verification": {
    "method": "signature",
    "public_key_fingerprint": "SHA256:abc123...",
    "verified_at": "2026-09-01T11:00:00Z"
  },
  "permission_level": 3,
  "scope": {
    "operations": ["code_change", "test_run", "ci_submit"],
    "paths": {
      "includes": ["src/*", "tests/*", "docs/*"],
      "excludes": [".truth/*", "protocol/core.json", "identity/*"]
    }
  },
  "time_limit": {
    "issued_at": "2026-09-01T10:00:00Z",
    "expires_at": "2026-09-01T18:00:00Z",
    "max_duration_hours": 8
  },
  "authorized_by": {
    "type": "human",
    "id": "admin:user",
    "authorization_proof": {
      "type": "signature",
      "signature": "abc123...",
      "verified_at": "2026-09-01T10:00:00Z"
    }
  },
  "task_context": {
    "task_id": "P0-15.18.5",
    "description": "Long-Run Stability test",
    "parent_token": null
  },
  "hash": "sha256:def456...",
  "token_status": "active"
}
```

### 4.4 授权验证流程

```
Agent 操作（携带 Authorization Token）
    │
    ▼
验证 Token 完整性（哈希校验）
    │
    ├─ 哈希不匹配 → 拒绝，记录违规
    │
    └─ 哈希匹配 → 验证 Token 状态
         │
         ├─ expired/revoked → 拒绝
         │
         └─ active → 验证身份一致性
              │
              ├─ Token.agent_id ≠ 操作签名身份 → 拒绝（冒用 Token）
              │
              └─ 身份一致 → 验证操作范围
                   │
                   ├─ 操作不在 scope.operations 内 → 拒绝
                   ├─ 路径在 scope.excludes 内 → 拒绝
                   ├─ 路径不在 scope.includes 内 → 拒绝
                   │
                   └─ 范围合法 → 验证时间
                        │
                        ├─ 当前时间 > expires_at → 拒绝
                        │
                        └─ 时间有效 → 授权通过
```

### 4.5 Identity ≠ Authority ≠ Evidence Trust

| 概念 | 回答的问题 | 验证方式 | 示例 |
|------|-----------|----------|------|
| **Identity** | 你是谁？ | 私钥签名 + 公钥验证 | "这是 agent:doubao，身份已验证" |
| **Authority** | 你被允许做什么？ | Authorization Token 验证 | "agent:doubao 被授权在 8 小时内修改 src/ 和 tests/" |
| **Evidence Trust** | 你的结果有多可信？ | Evidence 类型 + 验证方式 + 可复现性 | "CI 生成的证据可信度高；Agent 自报可信度低" |

**关键区分**:
- 一个 Agent 可以有高 Authority（Level 5），但它的自报证据仍然是低可信度
- 一个 Agent 可以有低 Authority（Level 2），但它运行的 CI 测试结果仍然是高可信度
- Authority 决定"能做什么"，Evidence Trust 决定"说的话有多可信"

---

## 五、Truth（事实层）

### 5.1 什么是 Truth

Truth 回答"什么叫工程事实"的问题。

**关键原则**:
- Truth 不是"文档里写的"，而是"有证据支持的声明"
- 每个 Truth 项本质上是一个 Claim（声明）
- Claim 必须有 Evidence 支持
- Claim 有明确的 Scope（范围）和 Validity（有效性条件）
- Truth 不是绝对的，而是"在当前证据下成立"

### 5.2 Truth as Claim（事实即声明）

每个 Truth 项是一个结构化的 Claim：

```json
{
  "claim_id": "truth-001",
  "claim": "TLL Runtime supports 100K concurrent coroutines without crash",
  "claim_type": "capability_claim",
  "scope": {
    "platforms": ["ubuntu", "windows", "macos"],
    "versions": ["tll-v0.15.18+"],
    "conditions": ["standard_ci_environment", "immediate_return_coroutines"],
    "proves": "100K coroutines can be created and completed without crash in CI",
    "does_not_prove": [
      "production readiness",
      "memory safety under all conditions",
      "long-term stability (>10 minutes)",
      "100K concurrent active coroutines"
    ]
  },
  "validity": {
    "status": "valid",
    "valid_since": "2026-09-01",
    "valid_until": null,
    "superseded_by": null,
    "revoked_reason": null
  },
  "confidence": "high",
  "confidence_reason": "3-platform CI, reproducible, automated verification",
  "evidence": ["ev-001", "ev-002", "ev-003"],
  "verification": {
    "method": "ci+multi_agent_review",
    "verifiers": ["ci-bot", "agent:claude", "agent:doubao"],
    "verified_at": "2026-09-01T12:00:00Z",
    "verification_scope": "claim.scope.proves only"
  },
  "constraints": ["constraint-001", "constraint-002"],
  "history": [
    {
      "version": "1.0",
      "timestamp": "2026-09-01T12:00:00Z",
      "change_type": "initial_claim",
      "changed_by": "agent:doubao",
      "authorization_token": "auth-2026-09-01-001",
      "evidence": ["ev-001"],
      "change_description": "Initial claim based on CI Run #123"
    }
  ]
}
```

### 5.3 Claim 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `capability_claim` | 能力声明 | "TLL 支持 X 能力" |
| `performance_claim` | 性能声明 | "TLL 的 X 操作性能为 Y" |
| `bug_claim` | Bug 声明 | "TLL 在 X 条件下存在 Bug Y" |
| `fix_claim` | 修复声明 | "Bug Y 已在 commit Z 修复" |
| `constraint_claim` | 约束声明 | "TLL 受约束 X 限制" |
| `compatibility_claim` | 兼容性声明 | "TLL 与 X 兼容" |
| `security_claim` | 安全声明 | "TLL 在 X 方面是安全的" |
| `readiness_claim` | 就绪声明 | "TLL 的 X 模块已生产就绪" |

### 5.4 Confidence（置信度）

| 等级 | 说明 | 条件 |
|------|------|------|
| `high` | 高置信度 | 多平台 CI + 可复现 + 多 Agent 或人工验证 |
| `medium` | 中置信度 | 单平台 CI 或本地测试 + 可复现 |
| `low` | 低置信度 | Agent 自报 + 无独立验证 |
| `disputed` | 有争议 | 存在矛盾证据，待解决 |
| `invalid` | 已失效 | 证据被推翻或声明被撤销 |

### 5.5 Truth 状态流转

```
draft (提案中)
  │
  ▼ 验证通过
proposed (已提案，待审核)
  │
  ▼ 审核通过
valid (有效，当前成立)
  │
  ├─ 新证据出现 → updated (更新版本，旧版本标记 superseded)
  ├─ 证据被推翻 → disputed (有争议，待解决)
  ├─ 声明错误 → revoked (已撤销，记录原因)
  └─ 被新声明替代 → superseded (已替代)
```

---

## 六、Evidence（证据层）

### 6.1 什么是 Evidence

Evidence 回答"什么证据支持这个事实"的问题。

**关键原则**:
- Evidence 有明确的证明范围（证明什么，不证明什么）
- CI 不是天然真相，只是"在某个环境下通过了某组验证"
- Evidence 可以被挑战和推翻
- Evidence 有可信度等级（基于类型和验证方式）
- Evidence 必须可溯源

### 6.2 Evidence 结构

```json
{
  "evidence_id": "ev-001",
  "type": "ci_run",
  "supports_claim": "truth-001",
  "claim_scope": {
    "proves": "100K coroutines complete without crash in CI environment",
    "does_not_prove": [
      "production readiness",
      "memory safety",
      "long-term stability"
    ],
    "scope_boundary": "CI environment only, not production"
  },
  "confidence": "high",
  "confidence_reason": "automated CI, 3 platforms, reproducible",
  "source": {
    "kind": "github_actions",
    "repository": "aliquanhou/tllos",
    "run_id": 123,
    "run_number": 123,
    "job": "native-build-test (ubuntu-latest)",
    "step": "Run all tests",
    "url": "https://github.com/aliquanhou/tllos/actions/runs/123",
    "commit": "157d198"
  },
  "timestamp": "2026-09-01T12:00:00Z",
  "platform": "ubuntu",
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
    "verified_at": "2026-09-01T12:05:00Z",
    "verification_notes": "CI log hash verified, test count matches summary"
  },
  "provenance_chain": [
    "code:157d198",
    "test:coroutine_stress_test.tll",
    "ci:run123",
    "evidence:ev-001"
  ],
  "challenges": [],
  "status": "valid"
}
```

### 6.3 Evidence 类型与可信度

| 类型 | 说明 | 默认可信度 | 备注 |
|------|------|-----------|------|
| `ci_run` | CI 运行结果 | high | 自动化，可复现，但范围有限 |
| `test_result` | 测试运行结果 | medium-high | 取决于运行环境 |
| `audit_report` | 独立审计报告 | high | 人工或多 Agent 交叉 |
| `performance_data` | 性能基准数据 | medium | 需注明运行环境 |
| `code_review` | 代码审查记录 | medium-high | 取决于审查者 |
| `human_confirmation` | 人工确认 | highest | 但需记录确认人 |
| `agent_self_report` | Agent 自报结果 | low | 必须有其他证据佐证 |
| `reproducible_test` | 可复现测试 | high | 其他人可重新运行 |

### 6.4 CI 不是天然真相

**重要原则**: CI PASS 只能证明：
> "某个 commit 在某个环境下通过了某组验证。"

它**不能**自动证明：
- 整个能力成立
- 生产就绪
- 所有场景下都正确
- 没有隐藏 Bug

**示例**:
```
CI Run #123: 34 tests pass, 95 assertions pass
  ↓
Evidence ev-001 proves:
  "在 CI 环境下，34 个测试全部通过"
  ↓
Does NOT prove:
  "TLL 生产就绪"
  "所有场景下无 Bug"
  "Blockchain 可用于生产"
```

**防止逻辑偷换**:
```
❌ 错误: 测试通过 → 能力 COMPLETE → 生产 READY
✅ 正确: 测试通过 → Evidence(范围:CI环境) → Claim(范围:CI环境下成立) → Confidence(high, but scope-limited)
```

### 6.5 Evidence 挑战机制

Evidence 可以被挑战：

```json
{
  "challenge_id": "ch-001",
  "evidence_id": "ev-001",
  "challenged_by": "agent:claude",
  "challenge_reason": "CI environment differs from production",
  "challenge_evidence": ["ev-005"],
  "timestamp": "2026-09-02T10:00:00Z",
  "status": "pending",
  "resolution": null
}
```

挑战处理：
1. 挑战提交后，Evidence 状态变为 `disputed`
2. 相关 Claim 的 confidence 降为 `disputed`
3. 需要新的 Evidence 或人工裁决来解决
4. 解决后记录 resolution，Evidence 状态恢复或标记 `invalid`

---

## 七、Verification（验证层）

### 7.1 什么是 Verification

Verification 回答"谁验证了证据"的问题。

**关键原则**:
- 验证不是"证据存在"，而是"证据被验证过"
- 验证者身份必须可验证
- 验证有明确的范围（验证了什么，没验证什么）
- 验证有时间戳和方法记录

### 7.2 验证方式

| 方式 | 说明 | 可信度 |
|------|------|--------|
| `automated` | 自动化验证（CI 脚本/校验工具） | high（可复现） |
| `human` | 人工验证 | highest（但需记录确认人） |
| `multi_agent` | 多 Agent 交叉验证 | high（独立验证） |
| `reproducible` | 可复现验证（其他人可重新运行） | high |
| `formal` | 形式化验证 | highest（但适用范围有限） |

### 7.3 验证者身份验证

验证者本身也需要身份验证：

```
验证者声称: 我是 ci-bot，我验证了 Evidence ev-001
  ↓
系统验证:
  - ci-bot 的身份是否在 Identity Root 注册？
  - 验证操作是否有 ci-bot 的签名？
  - 签名是否匹配注册的公钥？
  ↓
验证通过 → 记录验证者和验证方式
验证失败 → 拒绝验证记录
```

### 7.4 验证范围

每个验证必须明确范围：

```json
{
  "verification_id": "ver-001",
  "evidence_id": "ev-001",
  "verifier": "ci-bot",
  "verifier_identity_verified": true,
  "method": "automated",
  "verified_at": "2026-09-01T12:05:00Z",
  "scope": {
    "verified": [
      "CI log hash matches artifact hash",
      "test count (34) matches summary",
      "assertion count (95) matches summary",
      "exit code is 0"
    ],
    "not_verified": [
      "test logic correctness",
      "production environment compatibility",
      "memory safety",
      "long-term stability"
    ]
  },
  "result": "pass",
  "notes": "Automated verification of CI metadata only"
}
```

---

## 八、World Model（工程世界模型层）

### 8.1 什么是 World Model

World Model 回答"这些事实之间是什么关系"的问题。

**关键原则**:
- World Model 不只是图数据库，而是工程世界模型
- 验收标准不只是"无孤立节点无断边"，而是"能支持真实施工决策"
- World Model 必须能回答 Agent 的工程问题
- World Model 连接 Code/Tests/Git 和 Truth/Evidence/Protocol

### 8.2 World Model 的组成

```
World Model
├── Code Graph        (代码结构)
│   ├── 模块/函数/类
│   ├── 调用关系
│   ├── 依赖关系
│   └── ABI 接口
│
├── Test Graph        (测试覆盖)
│   ├── 测试用例
│   ├── 覆盖的代码
│   ├── 产生的 Evidence
│   └── 验证的 Claim
│
├── Truth Graph       (事实关系)
│   ├── Capability
│   ├── Constraint
│   ├── Claim
│   ├── Evidence
│   └── 关系(verified_by / constrains / depends_on)
│
├── History Graph     (历史演化)
│   ├── Git commits
│   ├── 变更记录
│   ├── Regression 记录
│   ├── Bug 修复记录
│   └── Truth 版本演化
│
└── Agent Graph       (Agent 活动)
    ├── Agent 身份
    ├── 操作记录
    ├── 授权记录
    ├── 验证记录
    └── 违规记录
```

### 8.3 节点类型

| 类型 | 说明 | 属性 |
|------|------|------|
| `module` | 模块 | name, path, version |
| `function` | 函数 | name, signature, module, line |
| `test` | 测试 | name, file, covers, produces_evidence |
| `capability` | 能力 | id, name, status, confidence |
| `claim` | 声明 | id, type, scope, confidence |
| `evidence` | 证据 | id, type, source, confidence |
| `constraint` | 约束 | id, rule, scope, immutable |
| `commit` | Git 提交 | hash, author, timestamp, changes |
| `bug` | Bug | id, description, status, introduced_in, fixed_in |
| `regression` | 回归 | id, description, commit, test |
| `agent` | Agent | id, identity, status, permission_level |
| `abi` | ABI 接口 | name, signature, stability |

### 8.4 边类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `contains` | 包含 | module contains function |
| `calls` | 调用 | function calls function |
| `depends_on` | 依赖 | module depends_on module |
| `implements` | 实现 | function implements abi |
| `covers` | 覆盖 | test covers function |
| `verified_by` | 被验证 | capability verified_by test |
| `produces` | 产生 | test produces evidence |
| `supports` | 支持 | evidence supports claim |
| `constrains` | 约束 | constraint constrains module |
| `conflicts_with` | 冲突 | constraint conflicts_with constraint |
| `introduced_in` | 引入于 | bug introduced_in commit |
| `fixed_in` | 修复于 | bug fixed_in commit |
| `caused_regression` | 导致回归 | commit caused_regression regression |
| `supersedes` | 替代 | claim supersedes claim |
| `inherited_from` | 继承自 | truth_version inherited_from truth_version |
| `authorized_by` | 授权于 | agent_operation authorized_by authorization_token |
| `performed_by` | 执行于 | commit performed_by agent |
| `verified_by_agent` | 被验证 | evidence verified_by_agent agent |

### 8.5 World Model 必须能回答的工程问题

**问题类型 1: 代码变更影响分析**
```
Agent 要修改 cg_resolveVar()
World Model 应该回答:
  ✓ 这个函数属于哪个模块？
  ✓ 谁调用它？（调用链）
  ✓ 哪些 ABI 依赖它？
  ✓ 哪些测试覆盖它？
  ✓ 哪些 Capability 依赖它？
  ✓ 最近谁修改过？（Git 历史）
  ✓ 过去有没有因为它产生 Regression？
  ✓ 修改它会影响哪些 Truth/Claim？
  ✓ 当前有哪些 Constraint 作用于它？
  ✓ 需要重新执行哪些验证？
```

**问题类型 2: 能力声明证据链验证**
```
Auditor 要验证 "TLL 支持 100K Coroutine" 这个声明
World Model 应该回答:
  ✓ 这个 Claim 的 scope 是什么？
  ✓ 有哪些 Evidence 支持它？
  ✓ 每个 Evidence 的证明范围是什么？
  ✓ Evidence 是否在 Claim 的 scope 内？
  ✓ Evidence 的可信度是多少？
  ✓ 谁验证了 Evidence？
  ✓ 验证范围是否覆盖 Claim 的 scope？
  ✓ 有没有矛盾的 Evidence？
  ✓ 这个 Claim 的 confidence 是否合理？
```

**问题类型 3: 约束冲突检测**
```
System 要检测约束冲突
World Model 应该回答:
  ✓ 有哪些 Constraint 作用于同一个模块/函数？
  ✓ 这些 Constraint 之间是否冲突？
  ✓ 有没有不可变 Constraint 被修改？
  ✓ 新的代码变更是否违反现有 Constraint？
```

**问题类型 4: Agent 操作合规检查**
```
System 要检查 Agent 操作是否合规
World Model 应该回答:
  ✓ Agent 的身份是否已验证？
  ✓ Agent 的 Authorization Token 是否有效？
  ✓ 操作是否在 Token 的 scope 内？
  ✓ 操作是否在 Token 的时间限制内？
  ✓ Agent 是否修改了不可变文件？
  ✓ Agent 的操作记录是否完整？
  ✓ 有没有违规记录？
```

**问题类型 5: 历史追溯**
```
Investigator 要追溯 "为什么这个能力声明变化了"
World Model 应该回答:
  ✓ 这个 Claim 的完整版本历史是什么？
  ✓ 每次变化的原因是什么？
  ✓ 是因为新 Evidence？Bug 修复？能力增强？
  ✓ 谁提出的变更？谁授权的？谁验证的？
  ✓ 变更前后的 Evidence 有什么不同？
  ✓ 有没有被撤销或替代的版本？
```

### 8.6 World Model 验收标准

**不只是**:
- ❌ 无孤立节点
- ❌ 无断边
- ❌ 节点数量达标

**而是**:
- ✅ 给定一个代码变更，能输出完整的影响分析报告
- ✅ 给定一个能力声明，能输出完整的证据链完整性报告
- ✅ 给定一个 Agent 操作，能输出权限和授权验证报告
- ✅ 能检测约束冲突
- ✅ 能追溯历史变更原因
- ✅ 查询响应时间在可接受范围内
- ✅ 数据与实际代码/测试/Git 一致

---

## 九、CI/CD（自动验证层）

### 9.1 什么是 CI/CD

CI/CD 回答"哪些关系能够自动验证"的问题。

**关键原则**:
- CI 不是"测试通过就完事"，而是"自动验证 World Model 中的关系"
- CI 输出的不只是 PASS/FAIL，而是验证报告（验证了什么，没验证什么）
- CI 证据有明确的范围（证明什么，不证明什么）
- CI 是 Evidence 的主要来源，但不是唯一来源

### 9.2 CI 验证的内容

| 验证类别 | 验证内容 | 输出 |
|----------|----------|------|
| **代码验证** | 编译通过、lint、类型检查 | build_report |
| **测试验证** | 测试通过、断言数量、覆盖率 | test_report |
| **Truth 验证** | Truth 哈希链完整、不可变项未修改、版本继承正确 | truth_report |
| **Evidence 验证** | Evidence 溯源链完整、哈希匹配、证明范围明确 | evidence_report |
| **权限验证** | Agent 身份验证、Authorization Token 验证、操作范围检查 | permission_report |
| **World Model 验证** | 图一致性、无孤立节点、能力有证据、约束无冲突 | world_model_report |
| **Protocol 验证** | 施工流程符合 Protocol、审计阶段未跳过、CI 红灯未继续 | protocol_report |

### 9.3 CI 验证报告格式

CI 不只是输出 PASS/FAIL，而是输出结构化的验证报告：

```json
{
  "ci_run_id": 123,
  "commit": "157d198",
  "overall_result": "pass",
  "verification_reports": [
    {
      "category": "code",
      "result": "pass",
      "verified": ["compilation", "lint", "type_check"],
      "not_verified": ["formal_verification", "security_audit"],
      "evidence": ["ev-build-001"]
    },
    {
      "category": "test",
      "result": "pass",
      "verified": ["34 tests", "95 assertions", "exit_code_0"],
      "not_verified": ["production_environment", "long_term_stability", "memory_safety"],
      "evidence": ["ev-test-001"]
    },
    {
      "category": "truth",
      "result": "pass",
      "verified": ["hash_chain_complete", "immutable_items_unchanged", "version_inheritance_valid"],
      "not_verified": ["claim_accuracy", "evidence_sufficiency"],
      "evidence": ["ev-truth-001"]
    },
    {
      "category": "world_model",
      "result": "pass",
      "verified": ["graph_consistency", "no_isolated_nodes", "capabilities_have_evidence"],
      "not_verified": ["query_performance", "decision_support_quality"],
      "evidence": ["ev-wm-001"]
    }
  ],
  "summary": {
    "total_checks": 28,
    "passed": 28,
    "failed": 0,
    "not_verified": 12
  },
  "scope_boundary": "CI environment only, does not prove production readiness"
}
```

### 9.4 CI 红灯处理

```
CI 红灯
  ↓
禁止继续功能施工（Protocol R002）
  ↓
分类失败原因:
  ├─ 代码 Bug → 修复代码
  ├─ 测试问题 → 修复测试
  ├─ Truth 违规 → 修复 Truth 或回滚变更
  ├─ 权限违规 → 调查 Agent 操作
  ├─ World Model 不一致 → 修复数据
  └─ 环境问题 → 修复 CI 环境
  ↓
修复后重新运行 CI
  ↓
CI 全绿 → 才能继续
```

---

## 十、History（历史演化层）

### 10.1 什么是 History

History 回答"事实为什么发生变化"的问题。

**关键原则**:
- 每个 Truth 项有完整的变更历史
- 历史不可修改，只能追加
- 每次变更记录原因、证据、授权者、验证者
- 可以追溯任何一个 Truth 项从创建到当前的完整演化
- 可以检测"事实为什么变化"

### 10.2 变更记录格式

```json
{
  "change_id": "change-001",
  "claim_id": "truth-001",
  "version": "1.1",
  "parent_version": "1.0",
  "timestamp": "2026-09-02T10:00:00Z",
  "change_type": "update",
  "change_reason": "new_evidence_from_ci_run_124",
  "changed_by": {
    "agent_id": "agent:doubao",
    "identity_verified": true,
    "authorization_token": "auth-2026-09-02-001"
  },
  "changes": {
    "confidence": {
      "old": "medium",
      "new": "high",
      "reason": "Added 2 more platform CI evidence"
    },
    "evidence": {
      "old": ["ev-001"],
      "new": ["ev-001", "ev-004", "ev-005"],
      "added": ["ev-004", "ev-005"]
    }
  },
  "verification": {
    "method": "multi_agent",
    "verifiers": ["agent:claude", "agent:doubao"],
    "verified_at": "2026-09-02T11:00:00Z"
  },
  "hash": "sha256:abc123...",
  "parent_hash": "sha256:def456..."
}
```

### 10.3 变更类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `initial_claim` | 初始声明 | 首次提出能力声明 |
| `update` | 更新 | 新证据导致 confidence 提升 |
| `scope_change` | 范围变更 | 扩大或缩小声明范围 |
| `correction` | 修正 | 发现之前声明有误，修正 |
| `supersede` | 替代 | 被新的声明替代 |
| `revoke` | 撤销 | 声明被推翻，标记为无效 |
| `constraint_add` | 新增约束 | 发现新的限制条件 |
| `constraint_remove` | 移除约束 | 约束不再适用 |

### 10.4 历史追溯能力

```
给定一个 Claim，能追溯:
  ✓ 完整的版本历史（从创建到当前）
  ✓ 每次变更的原因
  ✓ 每次变更的 Evidence
  ✓ 谁提出的变更
  ✓ 谁授权的变更
  ✓ 谁验证的变更
  ✓ 变更前后的差异
  ✓ 有没有被撤销或替代的版本
  ✓ 变更的哈希链是否完整

给定一个时间点，能重建:
  ✓ 当时的 Truth 状态
  ✓ 当时的 World Model 状态
  ✓ 当时的 Agent 权限状态
  ✓ 当时的 Evidence 状态
```

---

## 十一、Agent 操作完整流程

### 11.1 端到端流程

```
┌─────────────────────────────────────────────────────────────┐
│  1. Identity Verification（身份验证）                          │
│     ├─ Agent 用私钥签名操作                                    │
│     ├─ 系统用 Identity Root 注册的公钥验证签名                 │
│     └─ 验证失败 → 拒绝，记录违规                               │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Authority Verification（授权验证）                          │
│     ├─ 检查 Authorization Token                                │
│     ├─ 验证 Token 哈希、状态、身份一致性                        │
│     ├─ 验证操作范围（operations/paths）                        │
│     ├─ 验证时间限制                                            │
│     └─ 验证失败 → 拒绝，记录违规                               │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Protocol Compliance（协议合规）                            │
│     ├─ 检查操作是否符合 Engineering Protocol                   │
│     ├─ 检查是否跳过了必要阶段（如 AUDIT）                      │
│     ├─ 检查 CI 是否红灯（红灯禁止功能施工）                    │
│     └─ 不合规 → 拒绝，要求补流程                               │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  4. World Model Impact Analysis（影响分析）                    │
│     ├─ 查询 World Model，分析操作影响范围                      │
│     ├─ 识别受影响的模块/函数/测试/Capability/Constraint       │
│     ├─ 检测是否违反不可变 Constraint                            │
│     ├─ 推荐需要重新执行的验证                                   │
│     └─ 输出影响分析报告                                         │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Execution（执行操作）                                      │
│     ├─ 执行代码修改/测试运行/Truth 提案等                      │
│     ├─ 记录操作日志（谁、什么时间、做了什么）                  │
│     └─ 操作过程不可修改历史记录                                │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Evidence Generation（证据生成）                            │
│     ├─ 运行测试，产生测试结果                                  │
│     ├─ 运行 CI，产生 CI 报告                                  │
│     ├─ 每个 Evidence 有明确的证明范围                          │
│     ├─ Evidence 有哈希和溯源链                                 │
│     └─ Evidence 可信度基于类型和验证方式                       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Verification（验证）                                      │
│     ├─ 自动化验证（CI 脚本/校验工具）                          │
│     ├─ 独立审计（多 Agent 交叉或人工）                         │
│     ├─ 验证 Evidence 完整性和准确性                            │
│     ├─ 验证 Claim 与 Evidence 的范围匹配                       │
│     └─ 输出验证报告（验证了什么，没验证什么）                  │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  8. Truth Update（Truth 更新）                                │
│     ├─ 基于新 Evidence 提出 Claim 变更提案                    │
│     ├─ 经过 Validation（格式/不可变项/证据链接）              │
│     ├─ 经过 Review（独立审计）                                │
│     ├─ Authorized Committer 提交新版本                        │
│     ├─ 新版本有 parent_hash 和变更记录                        │
│     └─ 旧版本标记为 superseded，不可修改                      │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  9. World Model Update（世界模型更新）                        │
│     ├─ 更新 Code Graph（代码变更）                            │
│     ├─ 更新 Test Graph（测试变更）                            │
│     ├─ 更新 Truth Graph（Truth 变更）                         │
│     ├─ 更新 History Graph（历史记录）                         │
│     ├─ 更新 Agent Graph（Agent 操作记录）                     │
│     └─ 验证 World Model 一致性（无孤立/无冲突/能力有证据）    │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  10. CI/CD Verification（CI 验证）                            │
│     ├─ 自动验证所有层的关系                                    │
│     ├─ 输出验证报告（验证了什么，没验证什么）                  │
│     ├─ CI 全绿 → 操作完成                                     │
│     └─ CI 红灯 → 回滚或修复，重新开始流程                     │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 违规检测点

| 阶段 | 检测内容 | 违规处理 |
|------|----------|----------|
| Identity | 身份伪造、签名无效 | 拒绝操作，记录违规，可能暂停身份 |
| Authority | 无 Token、Token 过期、越权操作 | 拒绝操作，记录违规 |
| Protocol | 跳过审计、CI 红灯继续施工 | 拒绝操作，要求补流程 |
| World Model | 违反不可变约束、影响范围未评估 | 拒绝操作，要求补评估 |
| Evidence | 伪造证据、证据范围不匹配 | 拒绝 Truth 更新，标记 Evidence invalid |
| Verification | 验证者身份无效、验证范围不足 | 拒绝 Truth 更新，要求补验证 |
| Truth | 修改已发布版本、不可变项变更 | 拒绝操作，记录违规 |
| History | 篡改历史记录 | 拒绝操作，严重违规 |

---

## 十二、v0.3 与 v0.2 的关系

### 12.1 v0.2 保留的部分

v0.2 的所有治理设计在 v0.3 中保留：
- 五层信任模型（作为 v0.3 架构的子集）
- Truth 版本继承 + parent_hash
- Evidence provenance chain
- 不可变核心规则 R001-R010
- Agent 权限等级 Level 0-7（作为 Permission 的一部分）
- Truth Graph 节点和边类型（作为 World Model 的一部分）

### 12.2 v0.3 新增的部分

v0.3 新增核心概念层：

| 概念 | v0.2 状态 | v0.3 新增 |
|------|-----------|-----------|
| **Identity** | 隐含在权限等级中 | 独立身份层，Identity Root 注册验证机制，防自升权 |
| **Authority** | 隐含在"授权流程"中 | 独立授权层，Authorization Token，范围和时间限制 |
| **Claim** | 隐含在 Truth 项中 | 独立声明概念，有明确的 Scope/Validity/Confidence |
| **Evidence Scope** | 有类型和可信度 | 新增明确的证明范围（proves/does_not_prove） |
| **Verification** | 隐含在 Evidence 中 | 独立验证层，验证者身份验证，验证范围明确 |
| **World Model** | Truth Graph（图数据库） | 升级为工程世界模型，支持施工决策，5 个子图 |
| **CI/CD** | 测试运行 | 升级为自动验证层，验证 World Model 关系，输出验证报告 |
| **History** | 版本变更记录 | 升级为完整历史演化层，可追溯变更原因，可重建历史状态 |

### 12.3 v0.3 修正的部分

| v0.2 的问题 | v0.3 的修正 |
|-------------|-------------|
| "把治理当成文件权限" | 建立 Identity/Authority 独立验证机制，不依赖文件 |
| "Root Trust 只是一个 JSON 文件" | Identity Root 是注册和验证机制，Agent 无法修改 |
| "Level ≠ Trust 混为一谈" | 明确区分 Identity/Authority/Evidence Trust 三个概念 |
| "Truth Graph 只是图数据库" | 升级为 World Model，验收标准是支持施工决策 |
| "Evidence 没有证明范围" | 每个 Evidence 有明确的 proves/does_not_prove |
| "CI 是天然真相" | CI 只是自动验证层，证据有明确范围，不证明生产就绪 |
| "Agent 可以自封身份" | Identity Root 注册 + 私钥签名验证，防冒充和自升权 |

---

## 十三、实施路线

### Phase 0: v0.3 评审（当前）
- [ ] 本文档评审通过
- [ ] 确认 Identity/Authority/Claim/Evidence/World Model 核心概念
- [ ] 确认防自升权机制
- [ ] 确认 World Model 验收标准

### Phase 1: Identity & Authorization Root
- [ ] 建立 Identity Root（Agent 注册 + 密钥对 + 身份验证）
- [ ] 实现 Authorization Token 机制
- [ ] 实现身份验证流程（签名验证）
- [ ] 实现授权验证流程（Token 验证 + 范围检查）
- [ ] 防自升权机制（Identity Root 不可被 Agent 修改）
- [ ] CI 集成：自动验证 Agent 身份和授权

### Phase 2: Truth as Claim + Evidence with Scope
- [ ] 建立 Claim 数据结构（scope/validity/confidence）
- [ ] 建立 Evidence 证明范围（proves/does_not_prove）
- [ ] 实现 Truth 版本化和变更记录
- [ ] 实现 Evidence 挑战机制
- [ ] 实现 Verification 层（验证者身份 + 验证范围）
- [ ] 迁移现有能力声明到 Claim 格式

### Phase 3: World Model
- [ ] 建立 5 个子图（Code/Test/Truth/History/Agent）
- [ ] 实现图查询接口（CLI 或 API）
- [ ] 实现影响分析查询（代码变更 → 影响范围）
- [ ] 实现证据链验证查询（Claim → Evidence 完整性）
- [ ] 实现约束冲突检测
- [ ] 实现历史追溯查询
- [ ] CI 集成：World Model 一致性验证

### Phase 4: CI/CD as Automatic Verification
- [ ] 升级 CI 为自动验证层
- [ ] 实现验证报告输出（验证了什么，没验证什么）
- [ ] 实现 Truth 哈希链验证
- [ ] 实现权限合规验证
- [ ] 实现 World Model 一致性验证
- [ ] 实现 Protocol 合规验证

### Phase 5: History & Evolution
- [ ] 建立完整历史记录机制
- [ ] 实现历史状态重建
- [ ] 实现变更原因追溯
- [ ] 实现历史哈希链验证

### Phase 6: tllos.com Truth Browser
- [ ] 官网技术选型
- [ ] Truth Browser 实现（浏览 Claim/Evidence/World Model）
- [ ] World Model 可视化
- [ ] Agent 接入指南
- [ ] 部署上线

---

## 十四、待决策事项

### 14.1 身份与授权

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 1 | Identity Root 初始权威 | 人工管理员 / 多签 / DAO | 初始阶段人工管理员 |
| 2 | Agent 密钥类型 | RSA / Ed25519 / SSH 密钥 | Ed25519（更短更安全） |
| 3 | 授权 Token 有效期 | 8小时 / 24小时 / 任务结束自动失效 | 任务结束自动失效，最长 24 小时 |
| 4 | 默认 Agent 权限 | Level 1 / Level 2 / Level 3 | Level 3（可改代码，不可改 Truth） |
| 5 | 身份暂停/撤销流程 | 人工决定 / 自动检测违规 | 自动检测 + 人工确认 |

### 14.2 Truth 与 Evidence

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 6 | Claim 范围粒度 | 粗粒度（平台/版本） / 细粒度（具体条件） | 细粒度（明确 proves/does_not_prove） |
| 7 | Confidence 计算方式 | 人工评定 / 自动计算（基于证据类型） | 自动计算 + 人工调整 |
| 8 | Evidence 保留期限 | 永久 / 与 Truth 版本绑定 / 1年 | 与 Truth 版本绑定（永久） |
| 9 | CI 证据范围声明 | 自动生成 / 人工填写 | 自动生成模板 + 人工确认 |
| 10 | Evidence 挑战处理 | 自动解决 / 人工裁决 / 多 Agent 投票 | 人工裁决（高风险项） |

### 14.3 World Model

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 11 | World Model 存储 | JSON 文件 / 图数据库（Neo4j） / SQLite | 初始 JSON 文件，后续可迁移 |
| 12 | 查询接口 | CLI / HTTP API / GraphQL | 初始 CLI，后续加 HTTP API |
| 13 | 图更新时机 | 每次提交 / 定时同步 / CI 触发 | CI 触发（保证与代码一致） |
| 14 | 影响分析深度 | 1层 / 3层 / 全路径 | 3层（可配置） |
| 15 | World Model 验收 | 仅一致性 / 一致性 + 决策支持质量 | 一致性 + 决策支持质量（用真实问题测试） |

### 14.4 流程与治理

| # | 事项 | 选项 | 建议 |
|---|------|------|------|
| 16 | v0.3 评审方式 | 人工评审 / 多 Agent 交叉 / 直接通过 | 人工评审（治理层必须人工确认） |
| 17 | Phase 1 启动时间 | 立即 / v0.3 评审后 / 等待 | v0.3 评审通过后立即启动 |
| 18 | Blockchain P0-15.19+ 优先级 | 高于 Foundation / 低于 Foundation / 并行 | 低于 Foundation（Foundation 是基础设施） |
| 19 | 现有文档迁移 | 全部迁移到 Truth / 保留为参考 / 逐步迁移 | 逐步迁移（优先迁移能力声明） |
| 20 | 第一个外部 Agent 接入时间 | Foundation 完成后 / Phase 3 后 / 立即 | Phase 3（World Model）后 |

---

## 十五、成功标准

### 15.1 v0.3 治理层建立成功的标志

1. **Identity 可验证**: 每个 Agent 操作都有身份验证，冒充被检测和拒绝
2. **Authority 可证明**: 每个操作都有 Authorization Token，越权被检测和拒绝
3. **防自升权有效**: Agent 无法修改 Identity Root 或给自己升权
4. **Claim 有范围**: 每个 Truth 声明有明确的 proves/does_not_prove
5. **Evidence 有边界**: CI 证据不被包装成"生产就绪"
6. **World Model 支持决策**: 给定代码变更，能输出影响分析报告
7. **CI 输出验证报告**: 不只是 PASS/FAIL，而是验证了什么/没验证什么
8. **历史可追溯**: 任何 Truth 变更可追溯原因和完整演化链
9. **Identity ≠ Authority ≠ Evidence Trust**: 三个概念明确区分，不混淆

### 15.2 不接受的"伪成功"

- ❌ 建了 Identity Root 但 Agent 可以修改
- ❌ 有 Authorization Token 但不验证范围和时间
- ❌ 有 Claim 格式但 scope 写得模糊（"支持 X" 而不写范围）
- ❌ 有 Evidence 但 proves/does_not_prove 为空
- ❌ CI 还是只输出 PASS/FAIL，没有验证范围
- ❌ World Model 只有节点和边，不能回答工程问题
- ❌ 历史记录可以被修改
- ❌ Agent 自报证据被当作高可信度

---

## 附录 A: 核心概念速查表

| 概念 | 一句话定义 | 验证方式 |
|------|-----------|----------|
| **Identity** | 你是谁 | 私钥签名 + 公钥验证 |
| **Authority** | 谁授权你做什么 | Authorization Token 验证 |
| **Permission** | 你能做什么（范围/时间） | Token scope + 时间检查 |
| **Truth** | 有证据支持的工程事实 | Claim + Evidence + Verification |
| **Claim** | 事实声明（有范围/置信度） | Scope 明确 + Evidence 支持 |
| **Evidence** | 支持声明的证据（有证明范围） | 哈希 + 溯源链 + 验证 |
| **Verification** | 谁验证了证据（有验证范围） | 验证者身份 + 验证记录 |
| **World Model** | 工程关系网络（支持决策） | 能回答工程问题 |
| **CI/CD** | 自动验证层（输出验证报告） | 验证报告 + 范围声明 |
| **History** | 事实演化历史（可追溯） | 哈希链 + 只追加 |
| **Agent** | 执行主体（遵循 Protocol） | 身份 + 授权 + 操作记录 |
| **LLM** | 外部智能来源（可替换） | 不直接信任，需经过验证 |

## 附录 B: 防自升权机制速查

| 攻击 | 防御 |
|------|------|
| 修改 agent.json 升权 | Identity Root 不在 .truth/，Agent 无权限 |
| 冒充其他 Agent | 私钥签名 + 公钥验证 |
| 修改 Identity Root | 需人工授权 + 多签 |
| 篡改验证记录 | 只追加，不可修改，哈希链 |
| 用已撤销身份 | 身份状态检查 |
| 越权操作 | Authorization Token 范围检查 |
| 伪造 Evidence | Evidence 哈希 + 溯源链验证 |
| 修改已发布 Truth | 版本不可变，只能创建新版本 |

## 附录 C: CI 验证范围速查

| CI 验证了 | CI 没验证 |
|-----------|-----------|
| 代码编译通过 | 代码逻辑正确性 |
| 测试通过 | 生产环境兼容性 |
| 断言数量匹配 | 测试覆盖充分性 |
| Truth 哈希链完整 | Claim 准确性 |
| 不可变项未修改 | Evidence 充分性 |
| World Model 一致性 | 决策支持质量 |
| Agent 身份格式 | Agent 身份真实性（需签名验证） |
| 操作记录完整 | 操作意图合理性 |

---

*本文档为 TLL AI Engineering Foundation v0.3 工程世界模型与信任架构设计，待评审后进入 Phase 1 施工。*

*核心原则: 先定义"什么是真实、谁能声明、谁能验证、谁能授权、如何证明、如何追溯"，再设计 .truth/ → Truth Graph → Protocol → Agent。*

*第一性原理: 不是"先建 .truth/ 再想它是什么"，而是"先定义真实和信任的本质，再设计承载它的系统"。*
