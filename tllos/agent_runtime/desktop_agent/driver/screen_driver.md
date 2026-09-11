# Screen Driver Interface

## 职责

屏幕观察能力接口。

---

## 能力

| 方法 | 职责 |
|------|------|
| capture() | 捕获屏幕截图 |
| observe() | 观察屏幕内容 |
| locate() | 定位 UI 元素 |

---

## 规则

1. 只读操作（LOW risk）
2. 不修改屏幕内容
3. 所有观察必须记录到 Audit
4. 截图必须绑定 Evidence

---

*Screen Driver — P2-06*
