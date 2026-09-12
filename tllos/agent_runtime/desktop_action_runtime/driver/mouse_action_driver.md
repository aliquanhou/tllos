# TLL OS Mouse Action Driver

## Interface

### move(x, y)
- Input: x, y coordinates
- Output: { success, action_id, timestamp, evidence }
- Risk: LOW

### click(button='left', clicks=1)
- Input: button, click count
- Output: { success, action_id, timestamp, evidence }
- Risk: MEDIUM

### scroll(amount)
- Input: scroll amount
- Output: { success, action_id, timestamp, evidence }
- Risk: LOW

---

## Safety Rules

- All mouse actions require Permission
- Click on CRITICAL targets requires Approval
- Every action returns Evidence

---

*P2-09 Mouse Action Driver Interface*
