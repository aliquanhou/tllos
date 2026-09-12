# TLL OS Action Safety Gate

## Purpose

Safety rules for Desktop Action Runtime.
Ensures only authorized, approved, evidenced actions execute.

---

## Safety Rules

### Rule 1: Permission Required

- No Permission → REJECT
- Permission must be validated before action

### Rule 2: Human Approval Gate

- HIGH risk → WAIT_APPROVAL
- CRITICAL risk → REJECT by default
- High-risk actions: DELETE, PAYMENT, SEND, INSTALL

### Rule 3: Evidence Binding

- Every action must have before_frame_hash
- Every action must have after_frame_hash
- No evidence → REJECT

### Rule 4: Lifecycle Validation

- Invalid state transitions → REJECT
- CREATED → EXECUTING (skip permission) → REJECT

### Rule 5: Replay Protection

- Same action_id twice → REJECT
- Duplicate actions prevented

---

## Action Risk Levels

| Level | Examples | Approval Required |
|-------|----------|-------------------|
| LOW | mouse.move, screen.capture | No |
| MEDIUM | mouse.click, keyboard.type | No |
| HIGH | file.delete, process.kill | Yes |
| CRITICAL | payment.send, system.install | By default REJECT |

---

## Rejection Rules

| Condition | Action |
|-----------|--------|
| No Permission | REJECT |
| HIGH risk no approval | REJECT |
| Missing evidence | REJECT |
| Invalid lifecycle | REJECT |
| Duplicate action | REJECT |

---

*P2-09 Action Safety Gate v1.0*
