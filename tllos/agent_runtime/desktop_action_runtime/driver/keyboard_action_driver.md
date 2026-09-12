# TLL OS Keyboard Action Driver

## Interface

### type_text(text)
- Input: text string
- Output: { success, action_id, timestamp, evidence }
- Risk: MEDIUM

### press(key)
- Input: key name (e.g. 'enter', 'tab', 'esc')
- Output: { success, action_id, timestamp, evidence }
- Risk: MEDIUM

### hotkey(keys)
- Input: key combination (e.g. ['ctrl', 'c'])
- Output: { success, action_id, timestamp, evidence }
- Risk: HIGH

---

## Safety Rules

- All keyboard actions require Permission
- Hotkeys that modify system state require Approval
- Password input requires special approval

---

*P2-09 Keyboard Action Driver Interface*
