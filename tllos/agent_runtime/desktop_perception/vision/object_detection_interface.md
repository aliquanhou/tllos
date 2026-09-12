# Object Detection Interface

## 定位

Object Detection Interface 负责从 Screen Frame 中检测 UI 控件。

---

## Interface Definition

### detect_objects(frame) → ObjectList

**输入：**
- frame: Screen Frame

**输出：**
- objects: Vision Object 列表

---

## 支持的目标类型

- BUTTON: 按钮
- WINDOW: 窗口
- ICON: 图标
- TEXT: 文本区域
- CONTROL: 通用控件 (Checkbox / Radio / Dropdown)
- IMAGE: 图片
- PANEL: 面板

---

## Object 结构

```json
{
  "object_id": "",
  "type": "BUTTON",
  "position": {"x": 0, "y": 0, "width": 0, "height": 0},
  "confidence": 0.0,
  "text": "",
  "evidence_ref": ""
}
```

---

## 安全边界

**禁止：**
- Detection → Action（直接执行）

**必须：**
- Detection Result → Decision → Permission → Governance → Execution

---

## 实现状态

```
INTERFACE ONLY
Real Implementation: NOT IMPLEMENTED
```

---

*Object Detection Interface — P2-07*
