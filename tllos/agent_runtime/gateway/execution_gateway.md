# TLL OS Execution Gateway

## 职责

建立 Agent Runtime 与执行系统之间的安全入口。

**本阶段只建立 Gateway，不实现 Runtime 执行。**

## 流程

```
Agent
  ↓
Task Contract
  ↓
Capability Check
  ↓
Permission Check
  ↓
Execution Gateway
  ↓
Runtime Adapter
  ↓
[Runtime — FUTURE]
  ↓
Evidence Record
  ↓
Audit
```

## Gateway 职责

| 职责 | 说明 |
|------|------|
| 入口检查 | 验证 task_id, permission_id, capability 完整性 |
| 权限校验 | 确认 permission state == approved |
| Scope 校验 | 确认 action 在 task scope 内 |
| 证据要求 | 确认 evidence_required == true |
| 转发请求 | 将请求转发给 Runtime Adapter |
| 收集结果 | 收集 Execution Result |
| 生成 Evidence | 生成 Evidence Record |

## Gateway 规则

1. **所有执行请求必须经过 Gateway**
2. **无 permission_id 的请求直接 REJECT**
3. **无 evidence_required 的请求直接 REJECT**
4. **permission state != approved 的请求直接 REJECT**
5. **action 超出 task scope 的请求直接 REJECT**

## Gateway 错误码

| 错误码 | 说明 |
|--------|------|
| MISSING_TASK_ID | 缺少 task_id |
| MISSING_PERMISSION | 缺少 permission_id |
| MISSING_CAPABILITY | 缺少 capability 声明 |
| PERMISSION_NOT_APPROVED | 权限未批准 |
| SCOPE_VIOLATION | 超出任务范围 |
| EVIDENCE_REQUIRED | 必须提供证据 |

---

*Execution Gateway Layer — P2-03.3*

---

## Execution Orchestrator Integration (P2-04.4)

**Gateway 不直接执行。**

### 调用链

```
Gateway
  ↓
Execution Boundary
  ↓
Execution Orchestrator          ← P2-04.4 新增
  ↓
Runtime Adapter
```

### Gateway Response（增加 Orchestrator 字段）

```json
{
  "orchestration_id": "orch-001",
  "execution_plan_id": "plan-001",
  "next_stage": "orchestrator"
}
```

### 规则

- Gateway 不直接调用 Runtime Adapter
- Gateway 将请求转发给 Execution Orchestrator
- 多步骤任务必须经过 Orchestrator

---

*Execution Gateway Orchestrator Integration — P2-04.4*
