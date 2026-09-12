# TLL OS Vision Runtime Test Suite

**Project:** TLL OS
**Phase:** P2-08 Computer Vision Runtime
**Date:** 2026-09-12

---

## Test 97: Real Screenshot PASS

**目的：** 验证真实屏幕截图成功。

### 测试输入
```
python screen_capture_runtime.py
```

### 预期结果
✅ PASS（输出 PNG + Frame Metadata）

**Test 97 Result: ✅ PASS**

---

## Test 98: Invalid Frame Reject

**目的：** 验证无效 Frame 必须被拒绝。

### 测试输入
```json
{
  "frame_id": "",
  "timestamp": "",
  "width": 0,
  "height": 0,
  "format": "INVALID",
  "hash": "",
  "evidence_ref": ""
}
```

**注意：** 所有必填字段为空/无效

### 预期结果
❌ REJECT（无效 Frame）

**Test 98 Result: ✅ PASS (REJECT)**

---

## Test 99: Missing Hash Reject

**目的：** 验证无 Hash 的 Frame 必须被拒绝。

### 测试输入
```json
{
  "frame_id": "frame-test-001",
  "timestamp": "2026-09-12T10:00:00",
  "width": 1920,
  "height": 1080,
  "format": "PNG",
  "hash": "",
  "evidence_ref": "ev-test"
}
```

**注意：** hash 为空

### 预期结果
❌ REJECT（缺 Hash）

**Test 99 Result: ✅ PASS (REJECT)**

---

## Test 100: OCR Evidence PASS

**目的：** 验证 OCR 结果产生 Evidence。

### 测试输入
```
python ocr_runtime.py
```

**注意：** 需要 Tesseract 引擎

### 预期结果
✅ PASS（产生 Text Regions + Evidence）
⚠️ Note: 当前 Tesseract 未安装，标记为 GAP

**Test 100 Result: ⚠️ GAP (Tesseract not installed)**

---

## Test 101: Fake Object Reject

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

**注意：** type 未知，confidence 超出范围

### 预期结果
❌ REJECT（伪造 Object）

**Test 101 Result: ✅ PASS (REJECT)**

---

## Test 102: Complete Vision Chain PASS

**目的：** 验证完整 Vision Chain 通过验证。

### 测试流程
```
Screen Capture
  ↓
Frame Buffer
  ↓
Object Detection
  ↓
Evidence Generation
  ↓
Audit Ledger
```

### 预期结果
✅ PASS（完整 Vision Chain）

**Test 102 Result: ✅ PASS**

---

## 测试总结

| Test | 名称 | 结果 |
|------|------|------|
| Test 97 | Real Screenshot PASS | ✅ PASS |
| Test 98 | Invalid Frame Reject | ✅ PASS (REJECT) |
| Test 99 | Missing Hash Reject | ✅ PASS (REJECT) |
| Test 100 | OCR Evidence PASS | ⚠️ GAP (Tesseract) |
| Test 101 | Fake Object Reject | ✅ PASS (REJECT) |
| Test 102 | Complete Vision Chain PASS | ✅ PASS |

**Overall: 5/6 PASS, 1 GAP**

---

*Vision Runtime Test Suite — P2-08*
