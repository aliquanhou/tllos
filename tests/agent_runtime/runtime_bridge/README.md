# TLL OS Runtime Bridge Test Suite

**Project:** TLL OS
**Phase:** P2-04.2 Runtime Bridge Foundation
**Date:** 2026-09-11

---

## Test 37: 合法 Bridge Flow

**目的：** 验证完整的合法 Bridge 流程通过。

### 测试流程

```
Execution Engine
       ↓
Runtime Bridge
       ↓
Runtime Adapter
```

### 测试输入

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-bridge-001",
  "execution_id": "exec-bridge-001",
  "permission": {
    "state": "APPROVED",
    "name": "write:evidence"
  },
  "evidence": {
    "reference": "ev-bridge-001",
    "hash": "sha256:abc123..."
  },
  "runtime_target": {
    "type": "mock",
    "name": "mock_adapter"
  }
}
```

### 预期结果

✅ PASS（Execution Engine → Bridge → Adapter 完整流程）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| Engine → Bridge | PASS | ✅ PASS |
| Bridge → Adapter | PASS | ✅ PASS |
| Evidence 绑定 | PASS | ✅ PASS |

**Test 37 Result: ✅ PASS**

---

## Test 38: 绕过 Runtime Bridge

**目的：** 验证绕过 Bridge 直接调用 Adapter 必须被拒绝。

### 测试场景

**场景：** 直接从 Execution Engine 调用 Runtime Adapter，不经过 Runtime Bridge

### 预期结果

❌ REJECT（必须经过 Bridge）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| 绕过 Bridge | REJECT | ✅ PASS |

**Test 38 Result: ✅ PASS**

---

## Test 39: 无 Evidence Forward

**目的：** 验证缺少 Evidence 的转发请求必须被拒绝。

### 测试输入

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-bridge-002",
  "execution_id": "exec-bridge-002",
  "permission": {
    "state": "APPROVED",
    "name": "write:evidence"
  },
  "runtime_target": {
    "type": "mock",
    "name": "mock_adapter"
  }
}
```

**注意：** 缺少 `evidence` 字段

### 预期结果

❌ REJECT（缺少 evidence）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| evidence 缺失 | REJECT | ✅ PASS |

**Test 39 Result: ✅ PASS**

---

## Test 40: 非法 Runtime Target

**目的：** 验证非法 Runtime Target 必须被拒绝。

### 测试输入

```json
{
  "agent_id": "doubao-a",
  "task_id": "task-bridge-003",
  "execution_id": "exec-bridge-003",
  "permission": {
    "state": "APPROVED",
    "name": "write:evidence"
  },
  "evidence": {
    "reference": "ev-bridge-003",
    "hash": "sha256:def456..."
  },
  "runtime_target": {
    "type": "invalid_type",
    "name": "unknown_target"
  }
}
```

**注意：** runtime_target.type = "invalid_type"（非法）

### 预期结果

❌ REJECT（非法 runtime_target）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| 非法 runtime_target | REJECT | ✅ PASS |

**Test 40 Result: ✅ PASS**

---

## Test 41: 完整 Runtime Bridge Chain

**目的：** 验证完整的 Runtime Bridge 调用链通过。

### 调用链

```
CREATED
  ↓
VALIDATED
  ↓
FORWARDED
  ↓
COMPLETED
```

### 预期结果

✅ PASS（完整调用链，每一步都验证通过）

### 测试结果

| 步骤 | 状态 | 预期 | 结果 |
|------|------|------|------|
| 1. 创建 | CREATED | PASS | ✅ PASS |
| 2. 验证 | VALIDATED | PASS | ✅ PASS |
| 3. 转发 | FORWARDED | PASS | ✅ PASS |
| 4. 完成 | COMPLETED | PASS | ✅ PASS |

**Test 41 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 37 | 合法 Bridge Flow | P2-04.2 | ✅ PASS |
| Test 38 | 绕过 Runtime Bridge | P2-04.2 | ✅ PASS (REJECT) |
| Test 39 | 无 Evidence Forward | P2-04.2 | ✅ PASS (REJECT) |
| Test 40 | 非法 Runtime Target | P2-04.2 | ✅ PASS (REJECT) |
| Test 41 | 完整 Runtime Bridge Chain | P2-04.2 | ✅ PASS |

**Overall: 5/5 PASS**

---

*Runtime Bridge Test Suite — P2-04.2*
