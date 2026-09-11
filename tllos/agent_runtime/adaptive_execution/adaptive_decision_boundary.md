# Adaptive Decision Boundary

## 概述

Adaptive Decision Boundary 定义 Adaptive Execution 层与 Governance 层之间的决策边界。

**核心规则：Adaptive 只能 Recommend，不能 Execute。**

---

## 决策流程

```
Execution Result
       |
       v
Observation
       |
       v
Intelligence
       |
       v
Adaptive Analysis
       |
       v
Proposal
       |
       v
Governance Review
       |
       +---- Approved
       |
       +---- Rejected
```

---

## 关键边界

### Adaptive Layer 只能做：

✅ Recommend
- 生成优化建议
- 输出风险警告
- 提供性能提示

### Adaptive Layer 不能做：

❌ Execute
- 不能直接修改执行计划
- 不能直接提升权限
- 不能直接改变 Governance Decision
- 不能直接修改 Trust State
- 不能直接执行 Proposal

---

## Governance Review

所有 Proposal **必须经过 Governance Review**：

```
Adaptive Proposal
       ↓
Governance Decision
       ↓
Approved / Rejected
```

### 禁止

- ❌ Adaptive Proposal 直接进入 Execution Engine
- ❌ Adaptive Proposal 绕过 Governance
- ❌ Adaptive Proposal 自动执行

---

## 决策原则

1. **建议不执行** — Adaptive 只提供建议，不执行
2. **治理必审** — 所有建议必须经过治理审核
3. **证据绑定** — 所有建议必须绑定证据
4. **审计完整** — 所有建议必须记录到审计

---

## 禁止行为

- ❌ 自动修改 Execution Plan
- ❌ 自动提升 Permission
- ❌ 自动改变 Governance Decision
- ❌ 自动修改 Trust State
- ❌ 直接执行 Proposal
- ❌ 绕过 Governance

---

*Adaptive Decision Boundary — P2-04.7*
