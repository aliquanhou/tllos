# Adaptive Adaptation Policy

## 概述

Adaptation Policy 定义 Adaptive Execution 层的策略规则，确保自适应建议在安全边界内运行。

---

## 策略规则

### Rule 1: Read-Only

Adaptive Layer **只能建议，不能执行**。

```
Adaptive:
  只能: Recommend
  不能: Execute
```

---

### Rule 2: Governance Required

所有 Proposal **必须经过 Governance Review**。

```
Proposal
  ↓
Governance Review
  ↓
Approved / Rejected
```

禁止：
- Proposal 直接进入 Execution Engine
- Proposal 绕过 Governance

---

### Rule 3: Evidence Required

所有 Feedback 和 Proposal **必须绑定 Evidence**。

```
Feedback:
  evidence_ref != null

Proposal:
  evidence_ref != null
```

---

### Rule 4: Boundary Types

Proposal 类型**只能**是：

```
performance_hint
reliability_hint
risk_warning
```

禁止：
```
permission_upgrade
policy_change
execution_override
```

---

### Rule 5: Audit Required

所有 Feedback 和 Proposal **必须记录到 Audit Ledger**。

---

## 决策边界

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

## 禁止行为

- ❌ 自动修改 Execution Plan
- ❌ 自动提升 Permission
- ❌ 自动改变 Governance Decision
- ❌ 自动修改 Trust State
- ❌ 直接执行 Proposal
- ❌ 绕过 Governance

---

*Adaptive Adaptation Policy — P2-04.7*
