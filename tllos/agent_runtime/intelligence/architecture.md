# TLL OS Intelligent Agent Brain Architecture

## Purpose

Agent Reasoning Layer.
Transitions from "execute fixed plans" to "reason and decide dynamically".

---

## Architecture Flow

```
Human Goal
  ↓
Agent Reasoning
  ↓
Context Injection (Vision + Memory + History)
  ↓
Option Generation
  ↓
Decision (with confidence)
  ↓
Permission Gate
  ↓
Action Execution
  ↓
Reflection
  ↓
Retry / Improve
```

---

## Core Principle

```
Observe → Think → Plan → Act → Verify → Reflect
```

**Forbidden:**
```
Brain → OS (direct)
```

---

## Safety Boundary

- All decisions require Permission
- Low confidence decisions require verification
- Failed actions trigger Reflection + Recovery
- Every decision has Evidence

---

*P2-11 Agent Brain Architecture v1.0*
