# TLL OS Trust Chain Test Suite

**Project:** TLL OS
**Phase:** P2-03.5 Trust Verification Layer
**Date:** 2026-09-11

---

## Test 16: 完整 Trust Chain

**目的：** 验证六层完整的 Trust Chain 通过验证。

### 测试输入

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "execution": "exec-001",
  "evidence": "evidence-001",
  "audit_record": "led-001"
}
```

### 检查项

| 层 | 字段 | 预期 |
|---|------|------|
| Identity | agent_id | ✅ 存在 |
| Capability | capability | ✅ 存在 |
| Permission | permission | ✅ 存在 |
| Execution | execution | ✅ 存在 |
| Evidence | evidence | ✅ 存在 |
| Audit Ledger | audit_record | ✅ 存在 |

### 预期结果

✅ PASS（六层完整，权限在能力范围内）

### 测试结果

| 检查项 | 结果 |
|--------|------|
| 六层完整 | ✅ PASS |
| 权限在能力范围内 | ✅ PASS |

**Test 16 Result: ✅ PASS**

---

## Test 17: 无 Evidence

**目的：** 验证缺少 Evidence 的 Trust Chain 必须被 REJECT。

### 测试输入

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-002",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "execution": "exec-002"
}
```

**注意：** 缺少 `evidence` 和 `audit_record`

### 预期结果

❌ REJECT（缺少 Evidence 和 Audit Ledger）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| 缺少 evidence | REJECT | ✅ PASS |
| 缺少 audit_record | REJECT | ✅ PASS |

**Test 17 Result: ✅ PASS**

---

## Test 18: 权限越界

**目的：** 验证 Permission 超出 Capability 范围时必须被 REJECT。

### 测试输入

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-003",
  "capability": "read_code",
  "permission": "write:code",
  "execution": "exec-003",
  "evidence": "evidence-003",
  "audit_record": "led-003"
}
```

**注意：** capability = read_code, permission = write:code（越界）

### 预期结果

❌ REJECT（permission 不在 capability 范围内）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| permission_in_capability == false | REJECT | ✅ PASS |

**Test 18 Result: ✅ PASS**

---

## Test 19: 非法状态跳转

**目的：** 验证 Agent 状态非法跳转时必须被 REJECT。

### 测试场景

**场景 A: UNKNOWN → EXECUTED**
- 当前状态：UNKNOWN
- 请求跳转：EXECUTED
- 预期：❌ REJECT（非法跳转）

**场景 B: CAPABILITY_DECLARED → VERIFIED**
- 当前状态：CAPABILITY_DECLARED
- 请求跳转：VERIFIED
- 预期：❌ REJECT（非法跳转）

**场景 C: 合法跳转**
- 当前状态：PERMISSION_GRANTED
- 请求跳转：EXECUTED
- 预期：✅ ALLOW（合法跳转）

### 测试结果

| 场景 | 当前状态 | 目标状态 | 预期 | 结果 |
|------|---------|---------|------|------|
| A: 非法 | UNKNOWN | EXECUTED | REJECT | ✅ PASS |
| B: 非法 | CAPABILITY_DECLARED | VERIFIED | REJECT | ✅ PASS |
| C: 合法 | PERMISSION_GRANTED | EXECUTED | ALLOW | ✅ PASS |

**Test 19 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 16 | 完整 Trust Chain | P2-03.5 | ✅ PASS |
| Test 17 | 无 Evidence | P2-03.5 | ✅ PASS (REJECT) |
| Test 18 | 权限越界 | P2-03.5 | ✅ PASS (REJECT) |
| Test 19 | 非法状态跳转 | P2-03.5 | ✅ PASS (REJECT) |

**Overall: 4/4 PASS**

---

*Trust Chain Test Suite — P2-03.5*
