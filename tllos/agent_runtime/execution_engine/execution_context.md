# Execution Context

## 定义

Execution Context 是一次执行请求的完整上下文。

## 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| execution_id | string | 执行唯一 ID |
| agent_id | string | Agent ID |
| task_id | string | 任务 ID |
| capability | string | 所需能力 |
| permission | string | 所需权限 |
| evidence_required | boolean | 是否需要证据 |
| status | string | 当前状态 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

## 状态机

```
CREATED
  ↓
AUTHORIZED
  ↓
RUNNING
  ↓
COMPLETED
```

### 异常状态

| 状态 | 说明 |
|------|------|
| REJECTED | 被拒绝（权限不足、格式错误等） |
| FAILED | 执行失败 |
| AUDIT_REQUIRED | 需要审计 |

## 状态转换规则

| 当前状态 | 允许转换到 |
|---------|-----------|
| CREATED | AUTHORIZED, REJECTED |
| AUTHORIZED | RUNNING, REJECTED |
| RUNNING | COMPLETED, FAILED, AUDIT_REQUIRED |
| COMPLETED | （终态） |
| FAILED | （终态） |
| REJECTED | （终态） |
| AUDIT_REQUIRED | COMPLETED, FAILED |

## 非法状态转换

- ❌ CREATED → RUNNING（必须先 AUTHORIZED）
- ❌ CREATED → COMPLETED（必须经过 AUTHORIZED 和 RUNNING）
- ❌ AUTHORIZED → COMPLETED（必须先 RUNNING）
- ❌ COMPLETED → 任何状态（终态）

---

*Execution Context — P2-04*
