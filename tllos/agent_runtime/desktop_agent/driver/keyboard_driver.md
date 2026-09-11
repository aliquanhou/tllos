# Keyboard Driver Interface

## 职责

键盘输入能力接口。

---

## 能力

| 方法 | 职责 |
|------|------|
| type(text) | 输入文本 |
| press(key) | 按键 |
| shortcut(keys) | 快捷键 |

---

## 规则

1. type 必须经过 Permission Check
2. shortcut 必须记录到 Audit
3. 敏感输入（如密码）必须 Approval
4. 所有动作必须 Evidence Binding

---

*Keyboard Driver — P2-06*
