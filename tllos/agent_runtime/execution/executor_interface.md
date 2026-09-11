# TLL OS Agent Execution Interface

## 职责

定义 Agent 执行任务的边界接口。

**注意：本阶段只定义 Boundary，不实现真正执行。**

## 执行流程

```
Agent
  ↓
Task Contract
  ↓
Permission Check
  ↓
Execution Request
  ↓
[Execution Engine — FUTURE]
  ↓
Execution Result
  ↓
Evidence
```

## 边界定义

| 边界 | 说明 |
|------|------|
| 输入 | Task Contract（包含 scope + permission） |
| 前置条件 | Permission state == approved |
| 输出 | Execution Result（包含 status + evidence） |
| 禁止 | 无 approved permission 时执行 |

## 接口方法

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| check_permission | task_id, agent_id, permission_type | ALLOW / REJECT | 检查权限 |
| execute | execution_request | execution_result | 执行任务（本阶段不实现） |
| collect_evidence | task_id, result | evidence_record | 收集证据 |

## 错误处理

| 错误码 | 说明 |
|--------|------|
| PERMISSION_DENIED | 权限不足 |
| TASK_NOT_FOUND | 任务不存在 |
| SCOPE_VIOLATION | 超出任务范围 |
| EVIDENCE_REQUIRED | 必须提供证据 |

---

*Execution Boundary Layer — P2-03.2*
