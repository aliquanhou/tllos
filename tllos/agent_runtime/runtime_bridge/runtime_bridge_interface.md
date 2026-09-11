# Runtime Bridge Interface

## 接口定义

### 输入：Execution Context（来自 Execution Engine）

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "permission_state": "APPROVED",
  "evidence_reference": "ev-001",
  "execution_request": {
    "operation": "some_action",
    "input": {}
  }
}
```

**必须包含：**
- agent_id
- task_id
- permission_state
- evidence_reference
- execution_request

---

### 输出：Runtime Execution Request（到 Runtime Adapter）

```json
{
  "runtime_target": "mock_adapter",
  "operation": "some_action",
  "context_hash": "abc123...",
  "evidence_binding": "ev-001"
}
```

**必须包含：**
- runtime_target
- operation
- context_hash
- evidence_binding

---

## 验证规则

### 输入验证

1. **agent_id 必须存在** → 否则 REJECT
2. **task_id 必须存在** → 否则 REJECT
3. **permission_state 必须为 APPROVED** → 否则 REJECT
4. **evidence_reference 必须存在** → 否则 REJECT

### 输出验证

1. **runtime_target 必须合法** → 否则 REJECT
2. **context_hash 必须存在** → 否则 REJECT
3. **evidence_binding 必须与输入 evidence_reference 一致** → 否则 REJECT

---

## 禁止

- ❌ 无 Evidence 转 Runtime
- ❌ permission_state 不是 APPROVED 时转发
- ❌ 非法 runtime_target 转发

---

## 接口方法

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| translate | ExecutionContext | RuntimeRequest | 协议转换 |
| validate_boundary | RuntimeRequest | bool | 边界验证 |
| bind_evidence | RuntimeRequest | RuntimeRequest | 绑定 Evidence |

---

*Runtime Bridge Interface — P2-04.2*
