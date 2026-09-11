# TLL OS Audit Ledger

## 职责

记录 Agent 的所有行为，形成可信的行为历史。

## 核心原则

1. **Record Everything** — Agent 的所有关键行为都必须记录
2. **Bind Evidence** — 每个执行事件必须绑定证据
3. **Chain Records** — 记录之间形成逻辑链
4. **Audit Friendly** — 记录格式必须便于审计和回放

## 当前定位

**Local Protocol Layer** — 只定义协议和格式

**未来：** Database / Distributed Storage

## 不是什么

- ❌ 不是数据库系统
- ❌ 不是区块链
- ❌ 不是分布式账本
- ❌ 不是密码签名系统
- ❌ 不是 Runtime 执行实现

## 工作流

```
Task Contract
  ↓
Execution Request
  ↓
Action
  ↓
Evidence
  ↓
Ledger Record
  ↓
Audit
```

## 价值

没有 Audit Ledger：
- Agent 每次执行都是"无状态行为"
- 无法回溯历史
- 无法评估信任度
- 无法发现异常模式

有了 Audit Ledger：
- 完整的行为历史
- 可审计的执行链
- 可评估的信任轨迹
- 可回放的事件序列

---

*Audit Ledger Layer — P2-03.4*
