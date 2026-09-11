# Execution Engine Interface

## 接口定义

Execution Engine 是 Execution Gateway 和 Runtime Adapter 之间的中间层。

## 调用链

```
Execution Gateway
       ↓ (GatewayRequest)
Execution Engine
       ↓ (ExecutionRequest)
Runtime Adapter
       ↓ (RuntimeRequest)
TLL Runtime Boundary
```

## Input: ExecutionRequest

来自 Execution Gateway 的请求。

```json
{
  "execution_id": "exec-001",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "evidence_required": true,
  "action": "create_evidence_file",
  "input": {}
}
```

## Output: ExecutionResult

Execution Engine 返回的结果。

```json
{
  "execution_id": "exec-001",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "status": "COMPLETED",
  "result": {},
  "evidence_ref": "evidence-001",
  "timestamp": "2026-09-11T12:00:00Z"
}
```

## 执行流程

1. **接收请求** — 从 Gateway 接收 ExecutionRequest
2. **验证格式** — 检查必填字段
3. **验证 Permission** — 检查权限是否在能力范围内
4. **创建 Context** — 创建 ExecutionContext（状态 = CREATED）
5. **授权检查** — 状态从 CREATED → AUTHORIZED
6. **执行调度** — 状态从 AUTHORIZED → RUNNING
7. **调用 Adapter** — 通过 Runtime Adapter 调用底层
8. **返回结果** — 状态从 RUNNING → COMPLETED
9. **生成 Evidence** — 生成执行证据
10. **记录 Audit** — 记录到 Audit Ledger

## 错误处理

| 场景 | 状态 |
|------|------|
| 缺少必填字段 | REJECTED |
| 权限不足 | REJECTED |
| Agent 未注册 | REJECTED |
| 执行失败 | FAILED |
| 需要审计 | AUDIT_REQUIRED |

## 边界声明

- ✅ 本层只定义接口和流程
- ❌ 本层不实现真实执行
- ❌ 本层不直接调用 VM
- ❌ 本层不实现沙箱

---

*Execution Engine Interface — P2-04*
