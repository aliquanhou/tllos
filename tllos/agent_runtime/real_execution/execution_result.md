# Execution Result

## 概述

Execution Result 定义真实执行的结果格式。

---

## Result Schema

```json
{
  "execution_id": "",
  "agent_id": "",
  "target_id": "",
  "driver_id": "",
  "status": "",
  "result": "",
  "evidence_ref": "",
  "audit_ref": "",
  "timestamp": ""
}
```

---

## Result 状态

| Status | 说明 |
|--------|------|
| COMPLETED | 执行完成 |
| FAILED | 执行失败 |
| CANCELLED | 执行取消 |
| TIMEOUT | 执行超时 |
| REJECTED | 执行拒绝 |

---

## Result 规则

1. 每个 Result 必须有 execution_id
2. 每个 Result 必须有 agent_id
3. 每个 Result 必须有 target_id
4. 每个 Result 必须有 driver_id
5. 每个 Result 必须有 status
6. 每个 Result 必须有 evidence_ref
7. 每个 Result 必须有 audit_ref
8. 无 Evidence 的 Result 必须 REJECT

---

## Result 验证

```
Execution Result
  ↓
evidence_ref 存在？
  ↓
audit_ref 存在？
  ↓
status 合法？
  ↓
PASS / FAIL
```

---

*Execution Result — P2-05.0*
