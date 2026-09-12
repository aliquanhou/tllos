# TLL OS Action Recovery Model

## Purpose

Failed step recovery.
Agent doesn't stop on failure.

---

## Recovery Levels

### Level 1: Retry
- Same action, retry up to 2 times
- Use for: temporary failures (slow response)

### Level 2: Reobserve
- Re-capture screen
- Re-identify target
- Re-plan step
- Use for: wrong target, state changed

### Level 3: Replan
- Re-plan entire remaining sequence
- Use for: step failure cascading

### Level 4: Abort
- Stop entire plan
- Report failure
- Use for: critical failure, max retries

---

## Recovery Rules

```
FAILED
  ↓
Retry (max 2)
  ↓
  ├─ Success → Continue
  └─ Fail → Reobserve
              ↓
              ├─ Success → Continue
              └─ Fail → Replan
                          ↓
                          ├─ Success → Continue
                          └─ Fail → Abort + Report
```

---

*P2-10 Action Recovery Model v1.0*
