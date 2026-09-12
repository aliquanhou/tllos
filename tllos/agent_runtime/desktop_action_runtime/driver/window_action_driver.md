# TLL OS Window Action Driver

## Interface

### list_windows()
- Input: none
- Output: { windows: [...], action_id, timestamp, evidence }
- Risk: LOW

### focus_window(window_id)
- Input: window identifier
- Output: { success, action_id, timestamp, evidence }
- Risk: LOW

### close_window(window_id)
- Input: window identifier
- Output: { success, action_id, timestamp, evidence }
- Risk: HIGH

### resize_window(window_id, width, height)
- Input: window id, dimensions
- Output: { success, action_id, timestamp, evidence }
- Risk: LOW

---

## Safety Rules

- close_window requires Approval
- All actions return Evidence

---

*P2-09 Window Action Driver Interface*
