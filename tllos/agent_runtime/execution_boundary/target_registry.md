# Runtime Target Registry

## 职责

Runtime Target Registry 管理所有可用的 Runtime 执行目标。

## 原则

- Agent **不能自定义** Runtime Target
- 所有 Runtime Target 必须在 Registry 中注册
- Registry → Validation → Execution

---

## Target 状态

| 状态 | 说明 |
|------|------|
| AVAILABLE | 可用 |
| DISABLED | 已禁用 |
| DEPRECATED | 已废弃 |
| BLOCKED | 已阻塞 |

---

## Target Schema

见 `schemas/runtime_target.json`

---

## 当前注册 Target

| Target ID | Type | Status |
|-----------|------|--------|
| mock_adapter | mock | AVAILABLE |
| tll_runtime | vm | AVAILABLE |

---

## 禁止

- ❌ Agent 自定义 Runtime Target
- ❌ 未注册的 Target 执行
- ❌ BLOCKED Target 执行

---

*Runtime Target Registry — P2-04.3*
