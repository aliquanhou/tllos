# Execution Observation Model

## 概述

Execution Observation 记录执行过程中的一个时间点状态，用于后续分析。

---

## 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| execution_id | string | ✅ | 执行唯一标识符 |
| agent_id | string | ✅ | 执行 Agent |
| task_id | string | ✅ | 任务 ID |
| execution_stage | string | ✅ | 执行阶段 |
| timestamp | string | ✅ | 时间戳 |
| input_state | string | ✅ | 输入状态 |
| output_state | string | ✅ | 输出状态 |
| evidence_ref | string | ✅ | 证据引用 |
| audit_ref | string | ✅ | 审计引用 |

---

## 执行阶段

Observation 可以记录在以下阶段：

| 阶段 | 说明 |
|------|------|
| CREATED | 执行已创建 |
| VALIDATED | 已验证 |
| AUTHORIZED | 已授权 |
| EXECUTING | 正在执行 |
| COMPLETED | 已完成 |
| FAILED | 执行失败 |

---

## 绑定规则

Observation **必须**绑定：

1. **Execution** — execution_id 必须存在
2. **Evidence** — evidence_ref 必须非空
3. **Audit** — audit_ref 必须非空

---

## 示例

```json
{
  "execution_id": "exec-int-001",
  "agent_id": "doubao-a",
  "task_id": "task-int-001",
  "execution_stage": "COMPLETED",
  "timestamp": "2026-09-12T12:00:00Z",
  "input_state": "CREATED",
  "output_state": "COMPLETED",
  "evidence_ref": "ev-int-001",
  "audit_ref": "evt-int-001"
}
```

---

## 禁止

- ❌ 无 Evidence 的 Observation
- ❌ 无 Audit Reference 的 Observation
- ❌ 伪造的 Observation

---

*Execution Observation Model — P2-04.6*
