# TLL OS Execution Engine Core

## 职责

Execution Engine Core 是 Execution Engine 的核心调度层，负责接收请求、验证、调度和返回结果。

## 定位

```
Execution Gateway
       ↓
Execution Engine Core          ← 本层
       ↓
Runtime Adapter
       ↓
TLL Runtime Boundary
```

## 输入

**Execution Request** 包含：
- agent_id
- task_id
- capability
- permission
- evidence_requirement
- execution_context

## 输出

**Execution Result** 包含：
- status
- result
- evidence
- audit_event

## 核心原则

1. **不绕过 Trust Verification** — 所有请求必须先通过身份验证
2. **不绕过 Permission Model** — 所有执行必须先通过权限检查
3. **不绕过 Evidence Gate** — 所有完成必须生成证据
4. **不直接调用 Runtime** — 通过 Runtime Adapter 调用

## 禁止

- ❌ 绕过 Trust Verification
- ❌ 绕过 Permission Model
- ❌ 绕过 Evidence Gate
- ❌ 直接调用 VM

---

*Execution Engine Core — P2-04.1*
