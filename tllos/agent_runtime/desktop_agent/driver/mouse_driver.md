# Mouse Driver Interface

## 职责

鼠标控制能力接口。

---

## 能力

| 方法 | 职责 |
|------|------|
| move(x, y) | 移动鼠标 |
| click(button) | 点击 |
| scroll(direction) | 滚动 |

---

## 规则

1. click 必须经过 Permission Check
2. click 必须记录到 Audit
3. 高风险点击（如关闭按钮）必须 Approval
4. 所有动作必须 Evidence Binding

---

*Mouse Driver — P2-06*
