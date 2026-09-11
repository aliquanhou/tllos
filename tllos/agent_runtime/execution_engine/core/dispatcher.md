# Execution Engine Dispatcher

## 职责

Dispatcher 是 Execution Engine Core 的调度器，负责按照固定流程处理每个执行请求。

## 调度流程

```
Receive Request
    ↓
Validate Identity
    ↓
Validate Capability
    ↓
Validate Permission
    ↓
Create Execution Context
    ↓
Call Runtime Adapter
    ↓
Collect Result
    ↓
Create Audit Event
    ↓
Return Result
```

## 每一步说明

### 1. Receive Request
- 接收 ExecutionRequest
- 检查基本格式

### 2. Validate Identity
- 验证 agent_id 是否存在
- 验证 agent 是否注册
- 失败 → REJECTED

### 3. Validate Capability
- 验证 capability 是否存在
- 验证 capability 是否声明
- 失败 → REJECTED

### 4. Validate Permission
- 验证 permission 是否在 capability 范围内
- 验证 permission 是否已批准
- 失败 → REJECTED

### 5. Create Execution Context
- 创建 ExecutionContext
- 状态 = CREATED
- 分配 execution_id

### 6. Call Runtime Adapter
- 通过 Runtime Adapter 调用底层
- 状态 = EXECUTING
- 注意：不直接调用 Runtime

### 7. Collect Result
- 收集执行结果
- 状态 = COMPLETED

### 8. Create Audit Event
- 创建 Audit Event
- 绑定 Evidence
- 状态 = RECORDED

### 9. Return Result
- 返回 ExecutionResult
- 包含 evidence_ref

## 禁止

- ❌ Dispatcher 直接调用 Runtime
- ❌ Dispatcher 绕过 Identity 验证
- ❌ Dispatcher 绕过 Permission 验证
- ❌ Dispatcher 不生成 Audit Event

---

*Execution Engine Dispatcher — P2-04.1*
