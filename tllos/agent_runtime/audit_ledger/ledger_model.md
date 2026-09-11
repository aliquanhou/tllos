# TLL OS Ledger Model

## 账本模型

Ledger Record 是 Audit Ledger 中的一条完整记录。

## 核心概念

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Record 001 │ ──→ │ Record 002 │ ──→ │ Record 003 │
└─────────────┘     └─────────────┘     └─────────────┘
  previous: null     previous: 001     previous: 002
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| ledger_id | string | 账本记录唯一 ID |
| event_id | string | 对应的 Audit Event ID |
| agent_id | string | Agent ID |
| task_id | string | 任务 ID |
| previous_record | string | 上一条记录的 ID |
| evidence_ref | string | 证据引用 |
| integrity | string | 完整性校验值 |
| status | string | 记录状态 |

## previous_record 的含义

**当前：** 只是逻辑链（不是区块链）

- 每条记录指向上一条记录
- 形成单向链
- 可以验证记录顺序

**不是：**
- ❌ 不是区块链
- ❌ 不是分布式账本
- ❌ 不是密码学哈希链

## 完整性校验

**当前：** 逻辑引用

- previous_record 指向
- 顺序可验证

**未来：** 密码学完整性

- Hash Chain
- Merkle Tree
- Digital Signature

---

*Ledger Model — P2-03.4*
