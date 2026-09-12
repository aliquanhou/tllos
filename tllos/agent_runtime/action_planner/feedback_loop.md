# TLL OS Action Feedback Loop

## Purpose

Verify action results.
Compare expected vs actual state.

---

## Feedback Flow

```
Action Executed
  ↓
Capture After Frame
  ↓
Compare Expected Change
  ↓
  ├─ Expected Matched → SUCCESS
  └─ Expected Not Matched → FAILED → Recovery
```

---

## Verification Methods

### 1. Hash Comparison
- before_frame_hash vs after_frame_hash
- Different = state changed

### 2. Visual Verification
- Object presence check
- Expected UI element visible

### 3. State Verification
- Window focus check
- Application running check

---

## Recovery Triggers

| Trigger | Recovery Action |
|---------|----------------|
| Hash not changed | Retry (1x) |
| Wrong window | Reobserve → Refocus |
| Object not found | Replan step |
| Max retries | Abort + Report |

---

*P2-10 Action Feedback Loop v1.0*
