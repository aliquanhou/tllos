# TLL OS Execution Engine Test Suite

**Project:** TLL OS
**Phase:** P2-04 Execution Engine Foundation
**Date:** 2026-09-11

---

## Test 25: 合法 Execution Context

**目的：** 验证合法的 Execution Context 通过验证。

### 测试输入

```json
{
  "execution_id": "exec-001",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "evidence_required": true,
  "status": "CREATED"
}
```

### 预期结果

✅ PASS（所有必填字段存在，agent_id 已注册）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| 必填字段完整 | PASS | ✅ PASS |
| agent_id 已注册 | PASS | ✅ PASS |

**Test 25 Result: ✅ PASS**

---

## Test 26: Permission Gate

**目的：** 验证缺少 permission 的请求必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-002",
  "agent_id": "doubao-a",
  "task_id": "task-002",
  "capability": "write_evidence",
  "evidence_required": true,
  "status": "CREATED"
}
```

**注意：** 缺少 `permission` 字段

### 预期结果

❌ REJECT（缺少必填字段 permission）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| permission 缺失 | REJECT | ✅ PASS |

**Test 26 Result: ✅ PASS**

---

## Test 27: Evidence Gate

**目的：** 验证缺少 evidence_required 的请求必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-003",
  "agent_id": "doubao-a",
  "task_id": "task-003",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "status": "CREATED"
}
```

**注意：** 缺少 `evidence_required` 字段

### 预期结果

❌ REJECT（缺少必填字段 evidence_required）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| evidence_required 缺失 | REJECT | ✅ PASS |

**Test 27 Result: ✅ PASS**

---

## Test 28: State Machine

**目的：** 验证非法状态跳转必须被拒绝。

### 测试场景

**场景 A: CREATED → RUNNING（非法）**
- 当前状态：CREATED
- 请求跳转：RUNNING
- 预期：❌ REJECT

**场景 B: CREATED → AUTHORIZED（合法）**
- 当前状态：CREATED
- 请求跳转：AUTHORIZED
- 预期：✅ ALLOW

**场景 C: AUTHORIZED → RUNNING（合法）**
- 当前状态：AUTHORIZED
- 请求跳转：RUNNING
- 预期：✅ ALLOW

### 测试结果

| 场景 | 当前状态 | 目标状态 | 预期 | 结果 |
|------|---------|---------|------|------|
| A: 非法 | CREATED | RUNNING | REJECT | ✅ PASS |
| B: 合法 | CREATED | AUTHORIZED | ALLOW | ✅ PASS |
| C: 合法 | AUTHORIZED | RUNNING | ALLOW | ✅ PASS |

**Test 28 Result: ✅ PASS**

---

## Test 29: Agent Identity

**目的：** 验证未知 agent_id 的请求必须被拒绝。

### 测试输入

```json
{
  "execution_id": "exec-004",
  "agent_id": "unknown-agent",
  "task_id": "task-004",
  "capability": "write_evidence",
  "permission": "write:evidence",
  "evidence_required": true,
  "status": "CREATED"
}
```

**注意：** agent_id = "unknown-agent"（不在已注册列表中）

### 预期结果

❌ REJECT（未知 agent_id）

### 测试结果

| 检查项 | 预期 | 结果 |
|--------|------|------|
| agent_id 未注册 | REJECT | ✅ PASS |

**Test 29 Result: ✅ PASS**

---

## Test 30: Execution Event Chain

**目的：** 验证完整的 Execution 事件链记录到 Audit Ledger。

### 事件链

```
EXECUTION_CREATED
  ↓
EXECUTION_AUTHORIZED
  ↓
EXECUTION_STARTED
  ↓
EXECUTION_COMPLETED
```

### 测试结果

| 事件 | 记录 | 结果 |
|------|------|------|
| EXECUTION_CREATED | ✅ 记录 | ✅ PASS |
| EXECUTION_AUTHORIZED | ✅ 记录 | ✅ PASS |
| EXECUTION_STARTED | ✅ 记录 | ✅ PASS |
| EXECUTION_COMPLETED | ✅ 记录 | ✅ PASS |

**Test 30 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 25 | 合法 Execution Context | P2-04 | ✅ PASS |
| Test 26 | Permission Gate | P2-04 | ✅ PASS (REJECT) |
| Test 27 | Evidence Gate | P2-04 | ✅ PASS (REJECT) |
| Test 28 | State Machine | P2-04 | ✅ PASS (REJECT) |
| Test 29 | Agent Identity | P2-04 | ✅ PASS (REJECT) |
| Test 30 | Execution Event Chain | P2-04 | ✅ PASS |

**Overall: 6/6 PASS**

---

*Execution Engine Test Suite — P2-04*
