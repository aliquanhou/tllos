# OCR Interface

## 定位

OCR Interface 负责从 Screen Frame 中识别文本。

---

## Interface Definition

### recognize_text(frame) → TextRegions

**输入：**
- frame: Screen Frame

**输出：**
- regions: Text Region 列表

---

## Text Region 结构

```json
{
  "region_id": "",
  "text": "",
  "position": {"x": 0, "y": 0, "width": 0, "height": 0},
  "confidence": 0.0,
  "evidence_ref": ""
}
```

---

## 支持的文本类型

- 标题文本 (Title)
- 按钮文本 (Button)
- 菜单文本 (Menu)
- 标签文本 (Label)
- 输入框文本 (Input)

---

## 安全边界

**禁止：**
- OCR → Action（直接执行）

**必须：**
- OCR Result → Decision → Permission → Execution

---

## 实现状态

```
INTERFACE ONLY
Real Implementation: NOT IMPLEMENTED
```

---

*OCR Interface — P2-07*
