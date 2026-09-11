# TLL OS Execution Orchestrator

## 职责

Execution Orchestrator 是多执行步骤的编排层，负责任务分解、顺序控制、生命周期管理和 Evidence 连续绑定。

**定位：Execution Orchestration Layer**

## 核心职责

1. **Execution Plan** — 将任务分解为多个步骤
2. **顺序控制** — 按预定顺序执行步骤
3. **生命周期管理** — 管理整体执行生命周期
4. **失败恢复定义** — 定义失败时的恢复策略
5. **Evidence 连续绑定** — 每步都绑定 Evidence
6. **Audit Ledger 完整记录** — 每步都记录到 Audit Ledger

## 不负责

- ❌ VM execution
- ❌ Scheduler
- ❌ Memory management
- ❌ Bytecode execution
- ❌ Direct Runtime calls

## 架构定位

```
Execution Boundary
       ↓
Execution Orchestrator          ← 本层
       ↓
Runtime Adapter
       ↓
TLL Runtime Boundary
```

## 设计原则

1. **编排优先** — 所有多步骤执行必须先有 Plan
2. **顺序严格** — 步骤必须按预定顺序执行
3. **Evidence 连续** — 每步都必须绑定 Evidence
4. **审计完整** — 每步都必须记录到 Audit Ledger
5. **不直接调用 Runtime** — 必须通过 Runtime Adapter

---

*Execution Orchestrator Layer — P2-04.4*
