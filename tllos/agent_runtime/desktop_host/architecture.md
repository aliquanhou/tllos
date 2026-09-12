# TLL OS Desktop Agent Host Architecture

## Purpose

Desktop Agent Cockpit.
Real-time monitor for Vision / Reasoning / Plan / Action / Evidence.

---

## Architecture

```
TLL Agent
  ↓
Desktop Host
  ├── Event Bus
  ├── State Manager
  ├── Debug Console
  │     ├── Vision Panel
  │     ├── Reasoning Panel
  │     ├── Plan Panel
  │     ├── Action Panel
  │     └── Evidence Panel
  └── Safety Control
```

---

## Safety Boundary

- Debug Console is READ-ONLY monitor
- Console cannot directly call pyautogui
- Console → Permission Gate → Action Runtime
- Pause / Approval controls only

---

*P2-12 Desktop Host Architecture v1.0*
