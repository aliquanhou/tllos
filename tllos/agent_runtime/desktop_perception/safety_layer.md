# Perception Safety Layer

## 定位

Perception Safety Layer 确保所有视觉感知输出都经过验证和审批，禁止 Vision → Action 直接执行。

---

## Safety Flow

```
Vision Output
      ↓
Evidence Validation
      ↓
Confidence Check
      ↓
Governance
      ↓
Decision
      ↓
Permission
      ↓
Execution
```

---

## Safety Rules

### Rule 1: Evidence Required
- 所有 Vision Output 必须有 Evidence
- 无 Evidence 的 Object 必须 REJECT

### Rule 2: Confidence Check
- confidence < 0.5 必须 REJECT
- confidence >= 0.5 进入 Governance

### Rule 3: No Direct Action
- Vision 不能直接触发 Action
- 必须经过 Decision → Permission → Governance

### Rule 4: Audit Required
- 所有 Perception 行为必须记录 Audit Ledger

---

## 禁止路径

```
Vision → Action （禁止）
```

## 允许路径

```
Vision → Decision → Permission → Governance → Execution
```

---

*Perception Safety Layer — P2-07*
