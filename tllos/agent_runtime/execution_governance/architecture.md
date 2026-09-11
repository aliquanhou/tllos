# Execution Governance Architecture

## 定位

Execution Governance 是 Execution Orchestrator 与 Runtime Adapter 之间的**执行治理层**。

它不执行任何实际操作，只负责：
- 策略检查
- 风险评估
- 合规验证
- 审批决策

---

## 调用链

```
Execution Orchestrator
       |
       v
Execution Governance          ← 本层
       |
       v
Runtime Adapter
       |
       v
TLL Runtime
```

---

## 治理流程

```
Execution Request
        |
        v
Governance Evaluation
        |
        +---- Policy Check
        |
        +---- Risk Check
        |
        +---- Compliance Check
        |
        +---- Approval State
        |
        v
Execution Decision
```

---

## 输入

**Execution Request + Orchestration Result + Runtime Target + Permission Approval**

---

## 输出

**Governance Decision + Reason + Risk Level + Policy Checks + Evidence Binding**

---

## 核心组件

| 组件 | 职责 |
|------|------|
| Policy Engine | 执行策略检查 |
| Risk Evaluator | 评估风险等级 |
| Compliance Checker | 验证合规性 |
| Approval Manager | 管理审批状态 |
| Decision Maker | 做出最终决策 |

---

## 边界规则

1. **Governance 不直接调用 Runtime** — 必须通过 Runtime Adapter
2. **所有执行必须先经过 Governance** — 不能绕过
3. **所有决策必须有 Reason** — 不能无理由批准
4. **所有批准必须有 Evidence** — 无 Evidence 批准 REJECT
5. **所有决策必须记录 Audit** — 审计完整

---

## 状态机

```
CREATED
  ↓
EVALUATING
  ↓
APPROVED
  ↓
REJECTED
  ↓
EXECUTED
  ↓
VERIFIED
  ↓
SEALED
```

异常状态：REJECTED

---

*Execution Governance Architecture — P2-04.5*
