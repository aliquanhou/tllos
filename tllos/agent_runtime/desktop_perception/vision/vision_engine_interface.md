# Vision Engine Interface

## 定位

Vision Engine 是 Perception Layer 的分析引擎，负责对 Screen Frame 进行视觉分析。

---

## Interface Definition

### analyze(frame) → VisionResult

**输入：**
- frame: Screen Frame

**输出：**
- result: Vision Result（包含 OCR + Object Detection）

---

## Vision Result 结构

```json
{
  "frame_id": "",
  "objects": [],
  "text_regions": [],
  "confidence": 0.0,
  "evidence_ref": ""
}
```

---

## 安全边界

**禁止：**
- Vision → Action（直接执行）
- 绑定具体 AI 模型

**必须：**
- Vision → Decision → Permission → Governance → Execution

---

## 实现状态

```
INTERFACE ONLY
Real Implementation: NOT IMPLEMENTED
```

---

*Vision Engine Interface — P2-07*
