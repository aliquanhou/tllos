# TLL OS Runtime Adapter Interface

## 职责

定义 Agent Runtime 与 TLL Runtime Core 之间的适配层接口。

**本阶段只定义接口，禁止调用 vm.c，禁止修改 Runtime。**

## 定位

```
Agent Runtime
  ↓
Execution Gateway
  ↓
Runtime Adapter  ← 当前层
  ↓
[Runtime Core — FUTURE]
```

## 接口方法

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| execute | runtime_request | runtime_result | 执行任务（本阶段不实现） |
| get_status | request_id | status | 查询执行状态 |
| cancel | request_id | result | 取消执行 |

## 设计原则

1. **隔离**：Agent Runtime 不直接访问 Runtime Core
2. **边界**：所有 Runtime 调用必须经过 Adapter
3. **可替换**：未来可以替换不同的 Runtime 后端
4. **可测试**：Adapter 可以 mock，不依赖真实 Runtime

## 禁止事项

- ❌ 调用 vm.c
- ❌ 修改 Runtime Core
- ❌ 直接访问 coroutine
- ❌ 直接访问 scheduler
- ❌ 直接访问 frame pool

---

*Runtime Adapter Layer — P2-03.3*

---

## Runtime Bridge Layer (P2-04.2)

**Runtime Bridge 是 Execution Engine 与 Runtime Adapter 之间的必经层。**

所有 Runtime 请求必须经过：

```
Execution Engine
       ↓
Runtime Bridge          ← 不可绕过
       ↓
Runtime Adapter
       ↓
TLL Runtime
```

**禁止：** 直接从 Execution Engine 调用 Runtime Adapter，必须经过 Runtime Bridge。

---

## Execution Engine Bridge (P2-04.1)

### 调用链

```
Execution Engine Core
        ↓
Runtime Adapter Interface
        ↓
TLL Runtime Boundary
```

### 接口定义

**输入：RuntimeRequest**

```json
{
  "execution_id": "exec-001",
  "agent_id": "doubao-a",
  "task_id": "task-001",
  "action": "some_action",
  "input": {}
}
```

**输出：RuntimeResult**

```json
{
  "execution_id": "exec-001",
  "status": "SUCCESS",
  "result": {},
  "timestamp": "2026-09-11T12:00:00Z"
}
```

### 当前状态

- ✅ Mock Adapter 可用（用于测试）
- ❌ 真实 Runtime 执行 NOT IMPLEMENTED
- ❌ 直接修改 VM 禁止

### 边界

Execution Engine → Runtime Adapter → TLL Runtime Boundary

Execution Engine 不直接调用 VM，必须通过 Runtime Adapter。

---

*Execution Engine Bridge — P2-04.1*

---

## Execution Orchestrator Integration (P2-04.4)

**Runtime Adapter 接收 Orchestration Command。**

### 调用链

```
Execution Orchestrator
       ↓
Runtime Adapter
       ↓
TLL Runtime
```

### 规则

- ❌ Runtime Adapter **不接收**未经 Orchestrator 的直接调用
- ✅ Runtime Adapter **只接收**来自 Execution Orchestrator 的命令

```
Direct Runtime Call
        |
        X
        |
 Orchestrator Required
```

### 输入：Orchestration Command

```json
{
  "orchestration_id": "orch-001",
  "step_id": "step-001",
  "action": "write_evidence",
  "target": "mock_adapter",
  "input": {},
  "evidence_ref": "ev-step-001"
}
```

---

*Execution Orchestrator Integration — P2-04.4*
