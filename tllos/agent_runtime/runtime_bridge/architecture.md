# Runtime Bridge Architecture

## 定位

Runtime Bridge 是 Execution Engine 与 Runtime Adapter 之间的**协议转换层**。

它不执行任何实际操作，只负责：
- 格式转换
- 边界验证
- Evidence 绑定

---

## 调用链

```
Execution Engine
       |
       v
Runtime Bridge
       |
       v
Runtime Adapter
       |
       v
TLL Runtime
```

---

## 数据流

### 输入（来自 Execution Engine）

```
Execution Context
  - agent_id
  - task_id
  - permission_state
  - evidence_reference
  - execution_request
```

### 输出（到 Runtime Adapter）

```
Runtime Execution Request
  - runtime_target
  - operation
  - context_hash
  - evidence_binding
```

---

## Runtime Bridge 不负责

- ❌ VM execution
- ❌ Scheduler
- ❌ Memory management
- ❌ Bytecode execution
- ❌ Direct Runtime calls

---

## 边界规则

1. **单向连接**：Execution Engine → Bridge → Adapter，不可反向
2. **Evidence 必须存在**：无 Evidence 的请求必须 REJECT
3. **Runtime Target 验证**：非法 Runtime Target 必须 REJECT
4. **不绕过 Bridge**：所有 Runtime 请求必须经过 Bridge

---

## 状态机

```
CREATED
  ↓
VALIDATED
  ↓
FORWARDED
  ↓
COMPLETED
```

异常状态：REJECTED

---

*Runtime Bridge Architecture — P2-04.2*
