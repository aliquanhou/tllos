# File Driver Interface

## 职责

文件系统访问能力接口。

---

## 能力

| 方法 | 职责 |
|------|------|
| read(path) | 读取文件 |
| write(path, content) | 写入文件 |
| move(src, dst) | 移动文件 |
| delete(path) | 删除文件 |

---

## 规则

1. read 只读（LOW risk）
2. write / move 必须经过 Permission Check
3. delete 必须 Approval（HIGH risk）
4. 敏感路径（如系统目录）必须 CRITICAL
5. 所有动作必须 Evidence Binding

---

*File Driver — P2-06*
