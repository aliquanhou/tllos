# Vision Safety Gate

## 定位

Vision Safety Gate 确保所有视觉输出都经过安全检查。

---

## Safety Rules

### Rule 1: Evidence Required
- 所有 Frame 必须有 SHA256 hash
- 所有 Result 必须绑定 Evidence
- 无 Evidence 的输出必须 REJECT

### Rule 2: Confidence Gate
- confidence < 0.5 必须 REJECT
- confidence >= 0.5 进入 Decision Layer

### Rule 3: No Direct Action
- Vision Output 不能直接触发 Action
- 必须经过 Decision → Permission → Governance → Execution

### Rule 4: Size Limits
- 帧宽度: 1 - 7680 pixels
- 帧高度: 1 - 4320 pixels
- 超出范围必须 REJECT

### Rule 5: Audit Required
- 所有视觉行为必须记录 Audit Ledger
- 无 Audit 的输出无效

---

## Safety Flow

```
Vision Output
  ↓
Evidence Validation
  ↓
Confidence Check
  ↓
Size Check
  ↓
Decision Layer
  ↓
Permission
  ↓
Governance
  ↓
Execution
```

---

*Vision Safety Gate — P2-08*
