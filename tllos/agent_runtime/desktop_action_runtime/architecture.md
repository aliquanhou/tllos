# TLL OS Desktop Action Runtime Architecture

## Purpose

First real Desktop Action execution layer.
Transitions from "see" to "act" safely.

---

## Architecture Flow

```
Vision Runtime
  ↓
Object Model
  ↓
Action Intent
  ↓
Permission Gate
  ↓
Human Approval (if needed)
  ↓
Action Runtime
  ↓
Desktop Driver
  ↓
OS Adapter
  ↓
Hardware
  ↓
Verification (before/after frame)
  ↓
Evidence
  ↓
Audit Ledger
```

---

## Core Principle

```
Vision → Decision → Permission → Approval → Action → Verification → Evidence
```

**Forbidden:**
```
AI → Mouse Click (direct)
```

---

## Safety Boundary

- All actions require Permission
- High-risk actions require Human Approval
- Every action has Evidence (before/after frame hash)
- Every action is recorded in Audit Ledger
- No direct OS API calls

---

*P2-09 Action Runtime Architecture v1.0*
