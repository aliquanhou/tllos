# Execution Lifecycle

## 状态机

```
CREATED
  ↓
VALIDATING
  ↓
AUTHORIZED
  ↓
READY
  ↓
EXECUTING
  ↓
COMPLETED
```

异常状态：REJECTED / FAILED / CANCELLED

---

## 状态说明

| 状态 | 说明 |
|------|------|
| CREATED | 执行已创建 |
| VALIDATING | 正在验证 |
| AUTHORIZED | 已授权 |
| READY | 准备就绪 |
| EXECUTING | 正在执行 |
| COMPLETED | 已完成 |
| REJECTED | 已拒绝（异常终态） |
| FAILED | 执行失败（异常终态） |
| CANCELLED | 已取消（异常终态） |

---

## 状态转换规则

| 当前状态 | 允许转换到 |
|---------|-----------|
| CREATED | VALIDATING, REJECTED |
| VALIDATING | AUTHORIZED, REJECTED |
| AUTHORIZED | READY, REJECTED |
| READY | EXECUTING, CANCELLED |
| EXECUTING | COMPLETED, FAILED |
| COMPLETED | （终态） |
| REJECTED | （终态） |
| FAILED | （终态） |
| CANCELLED | （终态） |

---

## 非法状态转换

- ❌ CREATED → COMPLETED
- ❌ VALIDATING → EXECUTING
- ❌ AUTHORIZED → COMPLETED
- ❌ READY → COMPLETED
- ❌ EXECUTING → （除 COMPLETED / FAILED 外）

---

*Execution Lifecycle — P2-04.3*
