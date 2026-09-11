# Execution Orchestrator Architecture

## 定位

Execution Orchestrator 是 Execution Boundary 与 Runtime Adapter 之间的**执行编排层**。

它不执行任何实际操作，只负责：
- 任务分解
- 步骤编排
- 顺序控制
- 生命周期管理
- Evidence 连续绑定

---

## 调用链

```
Execution Boundary
       |
       v
Execution Orchestrator          ← 本层
       |
       v
Runtime Adapter
       |
       v
TLL Runtime
```

---

## 输入

**Execution Request + Boundary Result + Runtime Target + Permission Approval**

---

## 输出

**Execution Plan + Execution Steps + Execution Result + Audit Events + Evidence Chain**

---

## 核心组件

| 组件 | 职责 |
|------|------|
| Execution Plan Model | 任务分解为步骤 |
| Orchestration State Machine | 生命周期状态管理 |
| Step Executor | 单步骤执行（通过 Adapter） |
| Evidence Chain | 连续证据绑定 |
| Audit Recorder | 完整审计记录 |

---

## 边界规则

1. **Orchestrator 不直接调用 Runtime** — 必须通过 Runtime Adapter
2. **所有步骤必须有 Plan** — 不能无序执行
3. **所有步骤必须有 Evidence** — 无 Evidence 步骤 REJECT
4. **所有步骤必须有 Audit Event** — 无审计事件 REJECT

---

## 状态机

```
CREATED
  ↓
VALIDATING
  ↓
APPROVED
  ↓
SCHEDULED
  ↓
EXECUTING
  ↓
COLLECTING_EVIDENCE
  ↓
AUDITING
  ↓
COMPLETED
```

异常状态：REJECTED / FAILED

---

*Execution Orchestrator Architecture — P2-04.4*

---

## Execution Governance Integration (P2-04.5)

**Orchestrator 不直接执行，必须先经过 Governance。**

### 调用链

**Before:**
```
Plan
  ↓
Orchestrator
  ↓
Runtime Adapter
```

**After:**
```
Plan
  ↓
Orchestrator
  ↓
Governance                ← P2-04.5 新增
  ↓
Execution Boundary
  ↓
Runtime Adapter
```

### 规则

- ❌ Plan → Runtime（直接调用禁止）
- ✅ Plan → Orchestrator → Governance → Boundary → Adapter

---

*Execution Governance Integration — P2-04.5*

---

## Execution Intelligence Integration (P2-04.6)

**Orchestrator 不直接分析，必须经过 Intelligence Hook。**

### 流程升级

**Before:**
```
Plan
  ↓
Execute
  ↓
Audit
```

**After:**
```
Plan
  ↓
Execute
  ↓
Observe
  ↓
Audit
  ↓
Analyze
  ↓
Insight
```

### Intelligence Hook

- Intelligence Hook 在 Audit 之后执行
- Intelligence 只观察、分析，不修改执行结果
- Insight 只是建议，不自动执行

---

*Execution Intelligence Integration — P2-04.6*
