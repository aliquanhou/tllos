# TLL OS Desktop Agent Test Suite

**Project:** TLL OS
**Phase:** P2-06 Desktop Agent Foundation
**Date:** 2026-09-12

---

## Test 85: 合法 Screen Observe PASS

**目的：** 验证合法的屏幕观察动作通过验证。

### 测试输入

```json
{
  "action_id": "act-screen-001",
  "capability": "screen.observe",
  "target": "screen.main",
  "parameters": { "type": "capture" },
  "permission": "desktop.screen.observe",
  "evidence": "ev-screen-001"
}
```

### 预期结果

✅ PASS（合法 Screen Observe）

**Test 85 Result: ✅ PASS**

---

## Test 86: 无权限 Action REJECT

**目的：** 验证无 Permission 的动作必须被拒绝。

### 测试输入

```json
{
  "action_id": "act-mouse-001",
  "capability": "mouse.click",
  "target": "button.ok",
  "parameters": { "button": "left" },
  "permission": "",
  "evidence": "ev-mouse-001"
}
```

**注意：** permission = ""（空）

### 预期结果

❌ REJECT（无 Permission）

**Test 86 Result: ✅ PASS (REJECT)**

---

## Test 87: 绕过 Approval REJECT

**目的：** 验证高风险动作绕过 Approval 必须被拒绝。

### 测试输入

```json
{
  "action_id": "act-process-001",
  "capability": "process.kill",
  "target": "pid-1234",
  "parameters": { "signal": "kill" },
  "permission": "desktop.process.manage",
  "evidence": "ev-process-001",
  "human_approval": false
}
```

**注意：** human_approval = false（高风险动作未批准）

### 预期结果

❌ REJECT（绕过 Approval）

**Test 87 Result: ✅ PASS (REJECT)**

---

## Test 88: 非法 Lifecycle REJECT

**目的：** 验证非法的 Lifecycle 跳转必须被拒绝。

### 测试输入

```
REQUESTED -> EXECUTING
```

**注意：** 非法跳转（跳过 VALIDATING, AUTHORIZED, PREPARING）

### 预期结果

❌ REJECT（非法 Lifecycle）

**Test 88 Result: ✅ PASS (REJECT)**

---

## Test 89: 缺 Evidence REJECT

**目的：** 验证无 Evidence 的动作必须被拒绝。

### 测试输入

```json
{
  "action_id": "act-file-001",
  "capability": "file.read",
  "target": "/tmp/test.txt",
  "parameters": { "mode": "read" },
  "permission": "desktop.file.access",
  "evidence": ""
}
```

**注意：** evidence = ""（空）

### 预期结果

❌ REJECT（缺 Evidence）

**Test 89 Result: ✅ PASS (REJECT)**

---

## Test 90: 完整 Desktop Chain PASS

**目的：** 验证完整的 Desktop Chain 通过验证。

### 测试输入

```
REQUESTED
  ↓
VALIDATING
  ↓
AUTHORIZED
  ↓
PREPARING
  ↓
EXECUTING
  ↓
OBSERVING
  ↓
COMPLETED
```

### 预期结果

✅ PASS（完整 Desktop Chain）

**Test 90 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 85 | 合法 Screen Observe | P2-06 | ✅ PASS |
| Test 86 | 无权限 Action Reject | P2-06 | ✅ PASS (REJECT) |
| Test 87 | 绕过 Approval Reject | P2-06 | ✅ PASS (REJECT) |
| Test 88 | 非法 Lifecycle Reject | P2-06 | ✅ PASS (REJECT) |
| Test 89 | 缺 Evidence Reject | P2-06 | ✅ PASS (REJECT) |
| Test 90 | 完整 Desktop Chain PASS | P2-06 | ✅ PASS |

**Overall: 6/6 PASS**

---

*Desktop Agent Test Suite — P2-06*
