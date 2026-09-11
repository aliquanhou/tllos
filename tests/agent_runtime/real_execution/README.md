# TLL OS Real Execution Test Suite

**Project:** TLL OS
**Phase:** P2-05.0 Runtime Execution Activation Foundation
**Date:** 2026-09-12

---

## Test 67: 合法 Runtime 调用

**目的：** 验证合法的 Runtime 调用通过验证。

### 测试输入

```json
{
  "execution_id": "exec-real-001",
  "agent_id": "doubao-a",
  "target_id": "target-python-001",
  "driver_id": "python.execute",
  "permission": "python/execute",
  "capability": "python_execution",
  "evidence_ref": "ev-real-001",
  "audit_ref": "evt-real-001"
}
```

### 预期结果

✅ PASS（合法 Runtime 调用）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| execution_id 存在 | PASS | ✅ PASS |
| agent_id 存在 | PASS | ✅ PASS |
| target_id 存在 | PASS | ✅ PASS |
| driver_id 存在 | PASS | ✅ PASS |
| permission 存在 | PASS | ✅ PASS |
| evidence_ref 存在 | PASS | ✅ PASS |
| audit_ref 存在 | PASS | ✅ PASS |

**Test 67 Result: ✅ PASS**

---

## Test 68: 未知 Driver 拒绝

**目的：** 验证未知 Driver 必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-real-002",
  "agent_id": "doubao-a",
  "driver_id": "unknown.driver",
  "permission": "unknown/execute",
  "evidence_ref": "ev-real-002",
  "audit_ref": "evt-real-002"
}
```

**注意：** driver_id = unknown.driver（未知 Driver）

### 预期结果

❌ REJECT（未知 Driver）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| driver_id = unknown.driver | REJECT | ✅ PASS |

**Test 68 Result: ✅ PASS**

---

## Test 69: 无权限执行拒绝

**目的：** 验证无 Permission 的执行必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-real-003",
  "agent_id": "doubao-a",
  "driver_id": "python.execute",
  "permission": "",
  "evidence_ref": "ev-real-003",
  "audit_ref": "evt-real-003"
}
```

**注意：** permission = ""（空）

### 预期结果

❌ REJECT（无权限执行）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| permission 为空 | REJECT | ✅ PASS |

**Test 69 Result: ✅ PASS**

---

## Test 70: 执行结果缺 Evidence 拒绝

**目的：** 验证无 Evidence 的执行结果必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-real-004",
  "agent_id": "doubao-a",
  "driver_id": "python.execute",
  "permission": "python/execute",
  "evidence_ref": "",
  "audit_ref": "evt-real-004"
}
```

**注意：** evidence_ref = ""（空）

### 预期结果

❌ REJECT（执行结果缺 Evidence）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| evidence_ref 为空 | REJECT | ✅ PASS |

**Test 70 Result: ✅ PASS**

---

## Test 71: 失败状态记录

**目的：** 验证执行失败状态必须被正确记录。

### 测试输入

```json
{
  "execution_id": "exec-real-005",
  "agent_id": "doubao-a",
  "driver_id": "python.execute",
  "permission": "python/execute",
  "status": "FAILED",
  "evidence_ref": "ev-real-005",
  "audit_ref": "evt-real-005"
}
```

**注意：** status = FAILED

### 预期结果

✅ PASS（失败状态正确记录）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| status = FAILED | PASS | ✅ PASS |
| evidence_ref 存在 | PASS | ✅ PASS |
| audit_ref 存在 | PASS | ✅ PASS |

**Test 71 Result: ✅ PASS**

---

## Test 72: 完整 Execution Chain

**目的：** 验证完整的 Execution Chain 通过验证。

### 测试输入

```
REQUESTED
  ↓
VALIDATING
  ↓
AUTHORIZED
  ↓
DISPATCHING
  ↓
RUNNING
  ↓
OBSERVING
  ↓
COMPLETED
```

### 预期结果

✅ PASS（完整 Execution Chain）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| REQUESTED 存在 | PASS | ✅ PASS |
| VALIDATING 存在 | PASS | ✅ PASS |
| AUTHORIZED 存在 | PASS | ✅ PASS |
| DISPATCHING 存在 | PASS | ✅ PASS |
| RUNNING 存在 | PASS | ✅ PASS |
| OBSERVING 存在 | PASS | ✅ PASS |
| COMPLETED 存在 | PASS | ✅ PASS |
| 无非法跳转 | PASS | ✅ PASS |

**Test 72 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 67 | 合法 Runtime 调用 | P2-05.0 | ✅ PASS |
| Test 68 | 未知 Driver 拒绝 | P2-05.0 | ✅ PASS (REJECT) |
| Test 69 | 无权限执行拒绝 | P2-05.0 | ✅ PASS (REJECT) |
| Test 70 | 执行结果缺 Evidence 拒绝 | P2-05.0 | ✅ PASS (REJECT) |
| Test 71 | 失败状态记录 | P2-05.0 | ✅ PASS |
| Test 72 | 完整 Execution Chain | P2-05.0 | ✅ PASS |

**Overall: 6/6 PASS**

---

*Real Execution Test Suite — P2-05.0*
