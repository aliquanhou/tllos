# TLL OS Desktop Vision Runtime Architecture

## 定位

Vision Runtime 是 Perception Layer 的真实实现层，让 Agent 第一次产生真实视觉能力。

---

## 完整调用链

```
Screen Source (Windows GDI / MSS)
  ↓
Frame Buffer (PNG / Raw)
  ↓
Image Processor (Preprocessing)
  ↓
Vision Engine (OCR + Object Detection)
  ↓
Object Model (Vision Object List)
  ↓
Evidence (Hash + Metadata)
  ↓
Audit Ledger
```

---

## 核心组件

| 组件 | 职责 | 实现 |
|------|------|------|
| Screen Capture | 获取屏幕帧 | Pillow.ImageGrab / MSS |
| Frame Buffer | 帧存储 | PNG / Raw Buffer |
| Image Processor | 预处理 | OpenCV / Pillow |
| OCR Engine | 文字识别 | pytesseract |
| Object Detection | 目标检测 | Rule-based (v1) |
| Vision Evidence | 证据生成 | SHA256 Hash |

---

## Safety Boundary

**禁止：**
- Vision → Action（直接执行）
- 低置信度输出进入 Decision

**必须：**
- Vision → Decision → Permission → Governance → Execution

---

## 当前状态

```
PROTOCOL + CODE
Real Implementation: IN PROGRESS
```

---

*Vision Runtime Architecture — P2-08*
