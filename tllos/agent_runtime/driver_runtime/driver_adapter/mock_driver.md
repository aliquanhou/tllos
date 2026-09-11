# Mock Driver

## 职责

Mock Driver 用于测试，不执行真实操作。

---

## 能力

| 场景 | 模拟结果 |
|------|---------|
| success | 返回 SUCCESS |
| failed | 返回 FAILED |
| timeout | 返回 TIMEOUT |

---

## 使用场景

- 测试 Driver Runtime
- 测试 Driver Adapter
- 测试 Execution Chain
- 测试 Audit Ledger

---

## 禁止

❌ 不执行真实操作
❌ 不调用系统命令
❌ 不访问网络
❌ 不访问文件系统

---

*Mock Driver — P2-05.2*
