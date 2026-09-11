# TLL OS Audit Ledger Test Suite

**Project:** TLL OS
**Phase:** P2-03.4 Audit Ledger Foundation
**Date:** 2026-09-11

---

## Test 11: Valid Audit Event

**目的：** 验证合法的 Audit Event 通过验证。

### 测试输入

```json
{
  "event_id": "evt-001",
  "event_type": "ExecutionCompleted",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "action": "write_file",
  "evidence_ref": "evidence-001",
  "status": "SUCCESS",
  "timestamp": "2026-09-11T10:00:00Z"
}
```

### 预期结果

✅ PASS（所有必填字段存在，event_type 有效，status 有效，evidence_ref 存在）

### 测试结果

| 检查项 | 结果 |
|--------|------|
| event_id 存在 | ✅ PASS |
| event_type 有效 | ✅ PASS |
| agent_id 存在 | ✅ PASS |
| task_id 存在 | ✅ PASS |
| status 有效 | ✅ PASS |
| evidence_ref 存在（ExecutionCompleted） | ✅ PASS |

**Test 11 Result: ✅ PASS**

---

## Test 12: Missing Evidence Reject

**目的：** 验证 ExecutionCompleted 缺少 evidence_ref 时必须拒绝。

### 测试输入

```json
{
  "event_id": "evt-002",
  "event_type": "ExecutionCompleted",
  "agent_id": "doubao-a",
  "task_id": "task-002",
  "status": "SUCCESS",
  "timestamp": "2026-09-11T10:01:00Z"
}
```

**注意：** 缺少 `evidence_ref`

### 预期结果

❌ REJECT（ExecutionCompleted 必须有 evidence_ref）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| evidence_ref 缺失 | REJECT | ✅ PASS |

**Test 12 Result: ✅ PASS**

---

## Test 13: Unknown Agent Reject

**目的：** 验证使用不存在的 agent_id 时必须拒绝。

### 测试输入

```json
{
  "event_id": "evt-003",
  "event_type": "ExecutionRequested",
  "agent_id": "unknown-agent-999",
  "task_id": "task-003",
  "permission": "write:code",
  "status": "PENDING",
  "timestamp": "2026-09-11T10:02:00Z"
}
```

**注意：** agent_id = "unknown-agent-999" 不存在

### 预期结果

❌ REJECT（agent_id 不存在）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| agent_id 不存在 | REJECT | ✅ PASS |

**Test 13 Result: ✅ PASS**

---

## Test 14: Permission History Reject

**目的：** 验证没有 PermissionGranted 记录直接执行时必须拒绝。

### 测试场景

**场景：** Agent 直接执行，没有先申请和批准权限

```
事件序列：
1. TaskCreated（task-004）
2. ExecutionRequested（task-004）
   - 没有 PermissionGranted 记录
```

### 预期结果

❌ REJECT（执行事件前必须有 PermissionGranted）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| 无 PermissionGranted 直接执行 | REJECT | ✅ PASS |

**Test 14 Result: ✅ PASS**

---

## Test 15: Ledger Chain Validation

**目的：** 验证 Ledger Record 的 previous_record 链正确。

### 测试输入

**Record 1:**
```json
{
  "ledger_id": "led-001",
  "event_id": "evt-001",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "previous_record": "null",
  "integrity": "logical_chain_v1",
  "status": "ACTIVE"
}
```

**Record 2:**
```json
{
  "ledger_id": "led-002",
  "event_id": "evt-002",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "previous_record": "led-001",
  "integrity": "logical_chain_v1",
  "status": "ACTIVE"
}
```

### 预期结果

✅ PASS（Record 2 的 previous_record == Record 1 的 ledger_id）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| previous_record 链正确 | PASS | ✅ PASS |

**Test 15 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 11 | Valid Audit Event | P2-03.4 | ✅ PASS |
| Test 12 | Missing Evidence Reject | P2-03.4 | ✅ PASS |
| Test 13 | Unknown Agent Reject | P2-03.4 | ✅ PASS |
| Test 14 | Permission History Reject | P2-03.4 | ✅ PASS |
| Test 15 | Ledger Chain Validation | P2-03.4 | ✅ PASS |

**Overall: 5/5 PASS**

---

*Audit Ledger Test Suite — P2-03.4*
