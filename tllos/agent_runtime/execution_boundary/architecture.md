# Execution Boundary Architecture

## 定位

Execution Boundary 是 Runtime Bridge 与 Runtime Adapter 之间的**生产级执行边界控制层**。

它不执行任何实际操作，只负责：
- Runtime Target 验证
- Execution Policy 验证
- Lifecycle 状态管理
- Result 验证
- Audit 绑定

---

## 调用链

```
Execution Engine Core
       |
       v
Runtime Bridge
       |
       v
Execution Boundary          ← 本层
       |
       v
Runtime Adapter
       |
       v
TLL Runtime
```

---

## 五层组件

| 组件 | 职责 | 文件 |
|------|------|------|
| Runtime Target Registry | 管理可用 Runtime Target | target_registry.md |
| Execution Policy Gate | 执行前策略验证 | execution_policy.md |
| Execution Lifecycle | 执行生命周期管理 | lifecycle/execution_lifecycle.md |
| Result Verification | 执行结果验证 | result_verification.md |
| Audit Binding | 审计绑定 | audit_event.json |

---

## 边界规则

1. **Runtime Target 必须注册** — 未注册的 Target 必须 REJECT
2. **Policy 必须通过** — 未通过 Policy Gate 必须 REJECT
3. **Evidence 必须存在** — 无 Evidence 的结果必须 REJECT
4. **状态机必须严格** — 非法跳转必须 REJECT

---

## 状态机

```
CREATED
  ↓
VALIDATING
  ↓
AUTHORIZED
  ↓
READY
  ↓
EXECUTING
  ↓
COMPLETED
```

异常状态：REJECTED / FAILED / CANCELLED

---

*Execution Boundary Architecture — P2-04.3*
