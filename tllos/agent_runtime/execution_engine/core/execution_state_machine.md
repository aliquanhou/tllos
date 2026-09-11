# Execution Engine Core State Machine

## 状态定义（P2-04.2 扩展）

```
CREATED
  ↓
VALIDATED
  ↓
AUTHORIZED
  ↓
ENGINE_VALIDATED          ← 新增（P2-04.2）
  ↓
BRIDGE_VALIDATED          ← 新增（P2-04.2）
  ↓
RUNTIME_READY             ← 新增（P2-04.2）
  ↓
EXECUTING
  ↓
COMPLETED
  ↓
RECORDED
```

## 状态说明

| 状态 | 说明 | Phase |
|------|------|-------|
| CREATED | 执行上下文已创建 | P2-04 |
| VALIDATED | 身份和能力已验证 | P2-04.1 |
| AUTHORIZED | 权限已批准 | P2-04.1 |
| ENGINE_VALIDATED | Execution Engine 内部验证完成 | P2-04.2 |
| BRIDGE_VALIDATED | Runtime Bridge 验证完成 | P2-04.2 |
| RUNTIME_READY | Runtime 调用准备就绪 | P2-04.2 |
| EXECUTING | 正在执行 | P2-04 |
| COMPLETED | 执行完成 | P2-04 |
| RECORDED | 已记录到 Audit Ledger | P2-04.1 |

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
| AUTHORIZED | ENGINE_VALIDATED, REJECTED |
| ENGINE_VALIDATED | BRIDGE_VALIDATED, REJECTED |
| BRIDGE_VALIDATED | RUNTIME_READY, REJECTED |
| RUNTIME_READY | EXECUTING, REJECTED |
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
- ❌ ENGINE_VALIDATED → EXECUTING（必须先 BRIDGE_VALIDATED 和 RUNTIME_READY）
- ❌ BRIDGE_VALIDATED → EXECUTING（必须先 RUNTIME_READY）
- ❌ EXECUTING → RECORDED（必须先 COMPLETED）
- ❌ COMPLETED → 任何状态（终态之前还有 RECORDED）

---

*Execution State Machine — P2-04.2*
