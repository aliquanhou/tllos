# Execution Engine Core State Machine

## 状态定义

```
CREATED
  ↓
VALIDATED
  ↓
AUTHORIZED
  ↓
EXECUTING
  ↓
COMPLETED
  ↓
RECORDED
```

## 状态说明

| 状态 | 说明 |
|------|------|
| CREATED | 执行上下文已创建 |
| VALIDATED | 身份和能力已验证 |
| AUTHORIZED | 权限已批准 |
| EXECUTING | 正在执行 |
| COMPLETED | 执行完成 |
| RECORDED | 已记录到 Audit Ledger |

## 异常状态

| 状态 | 说明 |
|------|------|
| REJECTED | 被拒绝（验证失败） |
| FAILED | 执行失败 |

## 状态转换规则

| 当前状态 | 允许转换到 |
|---------|-----------|
| CREATED | VALIDATED, REJECTED |
| VALIDATED | AUTHORIZED, REJECTED |
| AUTHORIZED | EXECUTING, REJECTED |
| EXECUTING | COMPLETED, FAILED |
| COMPLETED | RECORDED |
| RECORDED | （终态） |
| REJECTED | （终态） |
| FAILED | （终态） |

## 非法状态转换

- ❌ CREATED → EXECUTING（必须先 VALIDATED 和 AUTHORIZED）
- ❌ CREATED → COMPLETED
- ❌ VALIDATED → COMPLETED
- ❌ AUTHORIZED → RECORDED
- ❌ EXECUTING → RECORDED（必须先 COMPLETED）
- ❌ COMPLETED → 任何状态（终态之前还有 RECORDED）

---

*Execution State Machine — P2-04.1*
