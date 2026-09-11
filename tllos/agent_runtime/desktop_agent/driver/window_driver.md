# Window Driver Interface

## 职责

窗口管理能力接口。

---

## 能力

| 方法 | 职责 |
|------|------|
| list() | 列出窗口 |
| focus(window) | 聚焦窗口 |
| resize(window, size) | 调整窗口大小 |
| close(window) | 关闭窗口 |

---

## 规则

1. list 只读（LOW risk）
2. close 必须经过 Permission Check
3. close 必须记录到 Audit
4. 所有动作必须 Evidence Binding

---

*Window Driver — P2-06*
