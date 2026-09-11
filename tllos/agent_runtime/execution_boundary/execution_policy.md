# Execution Policy Gate

## 职责

Execution Policy Gate 是执行前的最终策略验证层。

## 验证项

Execution 前必须全部通过：

```
Identity
  ↓
Capability
  ↓
Permission
  ↓
Evidence
  ↓
Runtime Target
  ↓
Policy
  ↓
Execution Allowed
```

否则：**Execution Rejected**

---

## 关键原则

### Permission ≠ Execution Permission

```
Capability
    ↓
Permission
    ↓
Policy
    ↓
Execution
```

**禁止：** Permission = Execution Permission

---

## Policy Schema

见 `schemas/execution_policy.json`

---

## Policy 规则

1. **Identity 必须已验证** — 未验证身份 REJECT
2. **Capability 必须已声明** — 未声明能力 REJECT
3. **Permission 必须已批准** — 未批准权限 REJECT
4. **Evidence 必须存在** — 无证据 REJECT
5. **Runtime Target 必须注册** — 未注册 Target REJECT
6. **Policy 必须全部通过** — 未通过 Policy REJECT

---

*Execution Policy Gate — P2-04.3*
