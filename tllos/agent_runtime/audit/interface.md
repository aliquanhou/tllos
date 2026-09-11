# Audit Interface

**Layer 5: Audit Interface**

## 职责

为独立审计方提供接口。

## 工作流程

1. **Read State** — 审计方读取 Agent Runtime 状态
2. **Verify Evidence** — 审计方验证 Evidence Record
3. **Give Verdict** — 审计方给出 PASS / REQUEST CHANGES
4. **Record Result** — 结果记录到 Evidence Index

## 核心原则

- ✅ 施工方不自行宣布 SEALED
- ✅ 审计独立于施工
- ✅ 审计结果由裁决方确认
- ❌ 禁止施工方代替审计

## 审计输出格式

```
PASS
  Evidence: ...
  Blocking GAP: ...
  Non-blocking GAP: ...
  Decision: Seal / Return
```

或

```
REQUEST CHANGES
  Issues: ...
  Required Fixes: ...
  Decision: Return for correction
```

## 输出

Audit Result

---

*Audit Interface Layer*
