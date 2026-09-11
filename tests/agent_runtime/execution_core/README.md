# TLL OS Execution Core Test Suite

**Project:** TLL OS
**Phase:** P2-04.1 Execution Engine Core Integration
**Date:** 2026-09-11

---

## Test 31: 合法 Execution Flow

**目的：** 验证完整的合法执行流程通过。

### 测试输入

```json
{
  "execution_id": "exec-core-001",
  "agent_identity": {
    "agent_id": "doubao-a",
    "agent_type": "construction_agent",
    "registered": true
  },
  "capability_id": "write_evidence",
  "permission_set": ["write:evidence"],
  "runtime_target": {
    "type": "adapter",
    "target": "mock_adapter"
  },
  "audit_reference": "led-core-001",
  "evidence_reference": "ev-core-001",
  "created_at": "2026-09-11T12:00:00Z"
}
```

### 预期结果

✅ PASS（Identity + Capability + Permission + Evidence 全部存在）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| Identity 存在 | PASS | ✅ PASS |
| Capability 存在 | PASS | ✅ PASS |
| Permission 存在 | PASS | ✅ PASS |
| Evidence 存在 | PASS | ✅ PASS |

**Test 31 Result: ✅ PASS**

---

## Test 32: 无 Permission 执行

**目的：** 验证缺少 permission 的执行请求必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-core-002",
  "agent_identity": {
    "agent_id": "doubao-a",
    "agent_type": "construction_agent",
    "registered": true
  },
  "capability_id": "write_evidence",
  "runtime_target": {
    "type": "adapter",
    "target": "mock_adapter"
  },
  "audit_reference": "led-core-002",
  "evidence_reference": "ev-core-002",
  "created_at": "2026-09-11T12:00:00Z"
}
```

**注意：** 缺少 `permission_set` 字段

### 预期结果

❌ REJECT（缺少 permission_set）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| permission_set 缺失 | REJECT | ✅ PASS |

**Test 32 Result: ✅ PASS**

---

## Test 33: 绕过 Gateway

**目的：** 验证绕过 Gateway 直接调用 Core 必须被拒绝。

### 测试场景

**场景：** 直接调用 Execution Engine Core，不经过 Execution Gateway

### 预期结果

❌ REJECT（必须经过 Gateway）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| 绕过 Gateway | REJECT | ✅ PASS |

**Test 33 Result: ✅ PASS**

---

## Test 34: 非法状态跳转

**目的：** 验证非法状态跳转必须被拒绝。

### 测试场景

**场景 A: CREATED → COMPLETED（非法）**
- 当前状态：CREATED
- 请求跳转：COMPLETED
- 预期：❌ REJECT

**场景 B: CREATED → VALIDATED（合法）**
- 当前状态：CREATED
- 请求跳转：VALIDATED
- 预期：✅ ALLOW

**场景 C: VALIDATED → AUTHORIZED（合法）**
- 当前状态：VALIDATED
- 请求跳转：AUTHORIZED
- 预期：✅ ALLOW

### 测试结果

| 场景 | 当前状态 | 目标状态 | 预期 | 结果 |
|------|---------|---------|------|------|
| A: 非法 | CREATED | COMPLETED | REJECT | ✅ PASS |
| B: 合法 | CREATED | VALIDATED | ALLOW | ✅ PASS |
| C: 合法 | VALIDATED | AUTHORIZED | ALLOW | ✅ PASS |

**Test 34 Result: ✅ PASS**

---

## Test 35: Audit Event 缺失

**目的：** 验证缺少 Audit Event 的执行必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-core-003",
  "agent_identity": {
    "agent_id": "doubao-a",
    "agent_type": "construction_agent",
    "registered": true
  },
  "capability_id": "write_evidence",
  "permission_set": ["write:evidence"],
  "runtime_target": {
    "type": "adapter",
    "target": "mock_adapter"
  },
  "evidence_reference": "ev-core-003",
  "created_at": "2026-09-11T12:00:00Z"
}
```

**注意：** 缺少 `audit_reference` 字段

### 预期结果

❌ REJECT（缺少 audit_reference）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| audit_reference 缺失 | REJECT | ✅ PASS |

**Test 35 Result: ✅ PASS**

---

## Test 36: 完整执行链

**目的：** 验证完整的执行链从创建到记录全部通过。

### 执行链

```
CREATED
  ↓
VALIDATED
  ↓
AUTHORIZED
  ↓
EXECUTING
  ↓
COMPLETED
  ↓
RECORDED
```

### 预期结果

✅ PASS（完整执行链，每一步都验证通过）

### 测试结果

| 步骤 | 状态 | 预期 | 结果 |
|------|------|------|------|
| 1. 创建 | CREATED | PASS | ✅ PASS |
| 2. 验证 | VALIDATED | PASS | ✅ PASS |
| 3. 授权 | AUTHORIZED | PASS | ✅ PASS |
| 4. 执行 | EXECUTING | PASS | ✅ PASS |
| 5. 完成 | COMPLETED | PASS | ✅ PASS |
| 6. 记录 | RECORDED | PASS | ✅ PASS |

**Test 36 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 31 | 合法 Execution Flow | P2-04.1 | ✅ PASS |
| Test 32 | 无 Permission 执行 | P2-04.1 | ✅ PASS (REJECT) |
| Test 33 | 绕过 Gateway | P2-04.1 | ✅ PASS (REJECT) |
| Test 34 | 非法状态跳转 | P2-04.1 | ✅ PASS (REJECT) |
| Test 35 | Audit Event 缺失 | P2-04.1 | ✅ PASS (REJECT) |
| Test 36 | 完整执行链 | P2-04.1 | ✅ PASS |

**Overall: 6/6 PASS**

---

*Execution Core Test Suite — P2-04.1*
