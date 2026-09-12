# TLL OS Desktop Agent Cockpit Architecture

## Purpose

Desktop Robot Cockpit.
Real-time GUI monitor for TLL Agent.

---

## Architecture

```
Desktop Cockpit
  ├── Main Window
  ├── State Controller
  ├── Widgets
  │     ├── Status Widget
  │     ├── Vision Widget
  │     ├── Reasoning Widget
  │     ├── Plan Widget
  │     ├── Action Widget
  │     └── Evidence Widget
  ├── Timeline
  └── Replay
```

---

## Safety Boundary

- GUI is READ-ONLY monitor + control buttons
- GUI cannot directly call pyautogui
- GUI → State Bus → Permission Gate → Action Runtime
- Buttons: START / PAUSE / STOP / APPROVE / DENY

---

## Multi-Monitor Support

- --monitor 1: Primary screen
- --monitor 2: Secondary screen (default)

---

*P2-12.1 Desktop Cockpit Architecture v1.0*
