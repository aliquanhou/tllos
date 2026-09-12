# TLL OS Intelligent Action Planner Architecture

## Purpose

Task Reasoning Layer.
Transitions from "execute actions" to "plan and complete goals".

---

## Architecture Flow

```
User Goal
  ↓
Task Planner
  ↓
Vision Query
  ↓
Object Selection
  ↓
Action Plan
  ↓
Permission Gate
  ↓
Action Runtime
  ↓
Verification
  ↓
Memory Update
```

---

## Core Principle

```
Goal → Plan → Action → Verify → Memory
```

**Forbidden:**
```
Direct Action without Plan
```

---

## Safety Boundary

- All plans require Permission check
- High-risk plans require Approval
- Every step has Evidence
- Failed steps trigger Recovery

---

*P2-10 Action Planner Architecture v1.0*
