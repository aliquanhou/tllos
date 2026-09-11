# Process Driver Interface

## 职责

进程管理能力接口。

---

## 能力

| 方法 | 职责 |
|------|------|
| list() | 列出进程 |
| start(command) | 启动进程 |
| stop(pid) | 终止进程 |
| inspect(pid) | 检查进程 |

---

## 规则

1. list / inspect 只读（LOW risk）
2. start / stop 必须经过 Permission Check
3. stop 必须 Approval（HIGH risk）
4. 所有动作必须 Evidence Binding

---

*Process Driver — P2-06*
