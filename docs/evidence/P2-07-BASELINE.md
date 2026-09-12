# P2-07 Desktop Perception Foundation — Baseline

**Status:** Baseline Freeze
**Parent Commit:** 0af792630b2d6059178f7e8e4e4666f79609ec49
**Branch:** feature/P2-02-canonical-layer-genesis
**Date:** 2026-09-12
**Architect:** 于秋鸿博士
**Implementer:** 豆包A（施工方）

---

## 1. Baseline State

```
HEAD: 0af792630b2d6059178f7e8e4e4666f79609ec49
Parent: ed1020a42cb6c80df9c9ddb3ec334d3760a8a73e
Branch: feature/P2-02-canonical-layer-genesis
Remote: in sync
```

---

## 2. Allowed Files

```
tllos/agent_runtime/desktop_perception/**
tools/agent_runtime_validator/validate_desktop_perception.py
tests/agent_runtime/desktop_perception/README.md
docs/evidence/P2-07-*.md
tllos/agent_runtime/audit_ledger/audit_event.json
tools/agent_runtime_validator/validate_audit_ledger.py
```

---

## 3. Forbidden Files

```
host/c/vm.c
host/c/tllvm.h
host/c/main.c
runtime/
compiler/
canonical_layer/
crypto/
```

---

## 4. Previous Stage

```
P2-06 Desktop Agent Foundation
Status: SEALED
Commit: 0af7926
Validators: 17/17 PASS
Tests: 6/6 PASS
```

---

## 5. Goal

建立 Agent 视觉感知层，让 Agent 第一次具备“看懂屏幕”的协议能力。

```
Desktop Agent
      ↓
Perception Layer
      ↓
Vision Engine
      ↓
Object Model
      ↓
Action Planning
```

---

*Baseline Freeze — P2-07*
