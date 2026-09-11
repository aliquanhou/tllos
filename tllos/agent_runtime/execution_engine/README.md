# TLL OS Execution Engine

## 职责

Execution Engine 负责连接 Execution Gateway 和 Runtime Adapter，形成完整的执行管道。

## 定位

```
Agent
  ↓
Trust Verification
  ↓
Permission Check
  ↓
Execution Gateway
  ↓
Execution Engine          ← 本层
  ↓
Runtime Adapter
  ↓
TLL Runtime Boundary
```

## 核心原则

1. **不直接调用 VM** — Execution Engine 不直接操作 vm.c
2. **不实现真实执行** — 本阶段只建立 Pipeline 结构
3. **Permission 前置** — 所有执行必须先通过 Permission 验证
4. **Evidence 绑定** — 所有执行结果必须绑定 Evidence
5. **Audit 记录** — 所有执行事件必须记录到 Audit Ledger

## 不是什么

- ❌ 不是完整 AI Agent
- ❌ 不是自主智能
- ❌ 不是沙箱
- ❌ 不是网络执行
- ❌ 不是数据库执行

---

*Execution Engine — P2-04*
