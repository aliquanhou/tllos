# Desktop Safety Layer

## 职责

Desktop Agent 的安全控制层。

---

## Task 24: Human Approval Gate

### 高风险动作（必须人工批准）

| 动作 | Risk Level | Approval Required |
|------|-----------|-------------------|
| file.delete | HIGH | ✅ YES |
| process.kill | HIGH | ✅ YES |
| process.install | HIGH | ✅ YES |
| permission_change | CRITICAL | ✅ YES |
| file.write (system dir) | CRITICAL | ✅ YES |

### 批准流程

```
Desktop Action Request
  ↓
Risk Level Check
  ↓
HIGH/CRITICAL
  ↓
Human Approval Gate
  ↓
Approved / Rejected
```

---

## Task 25: Governance Integration

Desktop Agent 接入 Execution Governance：

```
Desktop Action
  ↓
Governance Check
  ↓
Policy Evaluation
  ↓
Approved / Rejected
```

所有 Desktop Action 必须经过 Governance。

---

## Task 26: Intelligence Integration

Desktop Agent 接入 Execution Intelligence：

```
Desktop Action
  ↓
Execution
  ↓
Observation
  ↓
Metric
  ↓
Insight
```

所有 Desktop 行为产生 Observation / Metric / Insight。

---

## Task 27: Adaptive Integration

Desktop Agent 接入 Adaptive Execution：

```
Observation
  ↓
Proposal
  ↓
Governance Review
  ↓
Approved / Rejected
```

**禁止：** Adaptive 自动升级权限。

---

*Desktop Safety Layer — P2-06*
