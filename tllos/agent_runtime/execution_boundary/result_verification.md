# Execution Result Verification

## 职责

Execution Result Verification 验证执行结果的完整性和可信度。

## 验证要求

Execution Result 必须绑定：

```
execution_id
agent_id
runtime_target
permission
evidence
audit_event
result_hash
status
```

---

## 禁止

**无 Evidence 的：**
- SUCCESS
- COMPLETED
- FINISHED

**声明。**

---

## Result Schema

见 `schemas/execution_result_validation.json`

---

## 验证规则

1. **execution_id 必须存在** — 否则 REJECT
2. **agent_id 必须存在** — 否则 REJECT
3. **runtime_target 必须存在** — 否则 REJECT
4. **permission 必须存在** — 否则 REJECT
5. **evidence 必须存在** — 否则 REJECT
6. **audit_event 必须存在** — 否则 REJECT
7. **result_hash 必须存在** — 否则 REJECT
8. **status 必须合法** — 否则 REJECT

---

*Execution Result Verification — P2-04.3*
