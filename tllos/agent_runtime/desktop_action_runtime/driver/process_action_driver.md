# TLL OS Process Action Driver

## Interface

### list_processes()
- Input: none
- Output: { processes: [...], action_id, timestamp, evidence }
- Risk: LOW

### start_process(name, args)
- Input: process name, arguments
- Output: { success, pid, action_id, timestamp, evidence }
- Risk: MEDIUM

### stop_process(pid)
- Input: process ID
- Output: { success, action_id, timestamp, evidence }
- Risk: HIGH

### query_process(pid)
- Input: process ID
- Output: { status, action_id, timestamp, evidence }
- Risk: LOW

---

## Safety Rules

- stop_process requires Approval
- start_process of unknown binaries requires Approval
- All actions return Evidence

---

*P2-09 Process Action Driver Interface*
