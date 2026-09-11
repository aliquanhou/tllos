# TLL OS Audit Event

## 事件模型

Audit Event 是 Agent 行为的最小记录单元。

## 事件类型

| 事件类型 | 说明 | 触发时机 |
|---------|------|---------|
| AgentRegistered | Agent 注册 | Agent 首次接入 |
| CapabilityDeclared | 能力声明 | Agent 声明自己的能力 |
| PermissionRequested | 权限申请 | Agent 申请权限 |
| PermissionGranted | 权限批准 | Owner 批准权限 |
| PermissionDenied | 权限拒绝 | Owner 拒绝权限 |
| TaskCreated | 任务创建 | 新任务被创建 |
| ExecutionRequested | 执行请求 | Agent 通过 Gateway 请求执行 |
| ExecutionCompleted | 执行完成 | 任务执行完成 |
| ExecutionFailed | 执行失败 | 任务执行失败 |
| EvidenceGenerated | 证据生成 | 产生新证据 |
| TaskRejected | 任务拒绝 | 任务被拒绝 |
| AuditReviewed | 审计完成 | 审计者完成审计 |

## 事件字段

| 字段 | 类型 | 说明 |
|------|------|------|
| event_id | string | 事件唯一 ID |
| event_type | string | 事件类型（见上表） |
| agent_id | string | Agent ID |
| task_id | string | 任务 ID |
| capability | string | 使用的能力 |
| permission | string | 使用的权限 |
| action | string | 执行的动作 |
| evidence_ref | string | 证据引用 |
| status | string | 事件状态 |
| timestamp | string | 事件时间 |

## 关键规则

1. **ExecutionCompleted 必须有 evidence_ref**
2. **ExecutionRequested 必须有 permission**
3. **TaskCreated 必须有 scope**

---

*Audit Event Model — P2-03.4*
