# TLL OS Trust Chain

## 可信链模型

定义一次 Agent 行为的完整可信链。

## 完整链

```
┌──────────┐    ┌────────────┐    ┌────────────┐
│ Identity  │ → │ Capability │ → │ Permission │
│ (agent)   │    │ (skill)    │    │ (granted)  │
└──────────┘    └────────────┘    └────────────┘
                                       ↓
┌──────────┐    ┌────────────┐    ┌────────────┐
│ Audit     │ ← │ Evidence   │ ← │ Execution  │
│ (ledger)  │    │ (proof)    │    │ (action)   │
└──────────┘    └────────────┘    └────────────┘
```

## 每一环的要求

### 1. Identity
- 必须有 agent_id
- 必须已注册（AgentRegistered 事件存在）

### 2. Capability
- 必须有 capability 声明
- 必须已声明（CapabilityDeclared 事件存在）

### 3. Permission
- 必须有 permission_id
- 必须已批准（PermissionGranted 事件存在）
- 必须在 Capability 范围内

### 4. Execution
- 必须有 execution_request_id
- 必须通过 Gateway

### 5. Evidence
- 必须有 evidence_ref
- 必须包含 commit_sha 或 test_result

### 6. Audit Ledger
- 必须有 ledger_record_id
- 必须在 Audit Ledger 中存在

## 缺失检测

| 缺失环节 | 结果 |
|---------|------|
| 无 Identity | REJECT |
| 无 Capability | REJECT |
| 无 Permission | REJECT |
| 无 Execution | REJECT |
| 无 Evidence | REJECT |
| 无 Audit Ledger | REJECT |

---

*Trust Chain Model — P2-03.5*
