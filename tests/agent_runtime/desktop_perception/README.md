# TLL OS Desktop Perception Test Suite

**Project:** TLL OS
**Phase:** P2-07 Desktop Perception Foundation
**Date:** 2026-09-12

---

## Test 91: Invalid Frame Reject

**目的：** 验证非法 Screen Frame 必须被拒绝。

### 测试输入

```json
{
  "frame_id": "",
  "timestamp": "",
  "source": "",
  "resolution": "",
  "evidence_ref": ""
}
```

**注意：** frame_id 为空，缺少必填字段

### 预期结果

❌ REJECT（非法 Frame）

**Test 91 Result: ✅ PASS (REJECT)**

---

## Test 92: Missing Evidence Reject

**目的：** 验证无 Evidence 的 Vision Output 必须被拒绝。

### 测试输入

```json
{
  "object_id": "obj-001",
  "type": "BUTTON",
  "position": {"x": 100, "y": 200, "width": 80, "height": 30},
  "confidence": 0.95,
  "evidence_ref": ""
}
```

**注意：** evidence_ref 为空

### 预期结果

❌ REJECT（缺 Evidence）

**Test 92 Result: ✅ PASS (REJECT)**

---

## Test 93: Fake Object Reject

**目的：** 验证伪造的 Vision Object 必须被拒绝。

### 测试输入

```json
{
  "object_id": "fake-obj",
  "type": "UNKNOWN_TYPE",
  "position": {"x": 0, "y": 0, "width": 0, "height": 0},
  "confidence": 1.5,
  "evidence_ref": "ev-fake"
}
```

**注意：** type 未知，confidence 超出范围 (1.5 > 1.0)

### 预期结果

❌ REJECT（伪造 Object）

**Test 93 Result: ✅ PASS (REJECT)**

---

## Test 94: Invalid Lifecycle Reject

**目的：** 验证非法的 Lifecycle 跳转必须被拒绝。

### 测试输入

```
REQUESTED → USED
```

**注意：** 非法跳转（跳过 CAPTURED, ANALYZING, MATCHED）

### 预期结果

❌ REJECT（非法 Lifecycle）

**Test 94 Result: ✅ PASS (REJECT)**

---

## Test 95: Confidence Too Low Reject

**目的：** 验证置信度过低的 Vision Output 必须被拒绝。

### 测试输入

```json
{
  "object_id": "obj-low-conf",
  "type": "BUTTON",
  "position": {"x": 100, "y": 200, "width": 80, "height": 30},
  "confidence": 0.3,
  "evidence_ref": "ev-low"
}
```

**注意：** confidence = 0.3 < 0.5（低于阈值）

### 预期结果

❌ REJECT（置信度过低）

**Test 95 Result: ✅ PASS (REJECT)**

---

## Test 96: Complete Perception Chain PASS

**目的：** 验证完整的 Perception Chain 通过验证。

### 测试输入

```
REQUESTED
  ↓
CAPTURED
  ↓
ANALYZING
  ↓
MATCHED
  ↓
USED
  ↓
ARCHIVED
```

### 预期结果

✅ PASS（完整 Perception Chain）

**Test 96 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | Phase | 结果 |
|------|------|-------|------|
| Test 91 | Invalid Frame Reject | P2-07 | ✅ PASS (REJECT) |
| Test 92 | Missing Evidence Reject | P2-07 | ✅ PASS (REJECT) |
| Test 93 | Fake Object Reject | P2-07 | ✅ PASS (REJECT) |
| Test 94 | Invalid Lifecycle Reject | P2-07 | ✅ PASS (REJECT) |
| Test 95 | Confidence Too Low Reject | P2-07 | ✅ PASS (REJECT) |
| Test 96 | Complete Perception Chain PASS | P2-07 | ✅ PASS |

**Overall: 6/6 PASS**

---

*Desktop Perception Test Suite — P2-07*
