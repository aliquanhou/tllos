# Real Execution Architecture

## 定位

Real Execution 是 Runtime Adapter 与真实执行环境之间的**接口层**。

它不实现完整执行引擎，只负责定义：
- 执行目标
- 执行驱动
- 执行适配器
- 执行结果

---

## 调用链

```
Agent
  ↓
Trust Verification
  ↓
Permission Check
  ↓
Execution Gateway
  ↓
Execution Engine Core
  ↓
Runtime Bridge
  ↓
Execution Boundary
  ↓
Execution Orchestrator
  ↓
Execution Governance
  ↓
Execution Intelligence
  ↓
Adaptive Execution
  ↓
Runtime Adapter
  ↓
Real Execution              ← P2-05.0
  ↓
Real Runtime / Driver
```

---

## 核心组件

| 组件 | 职责 |
|------|------|
| Execution Target | 定义执行目标 |
| Execution Driver | 定义执行驱动 |
| Execution Adapter | 定义执行适配器 |
| Execution Result | 定义执行结果 |

---

## Execution Driver Model

### 支持的 Driver 类型

| Driver ID | 类型 | 说明 |
|-----------|------|------|
| tll.execute | TLL Runtime | TLL 语言执行 |
| python.execute | Python Runtime | Python 脚本执行 |
| shell.execute | Shell Command | Shell 命令执行 |
| http.request | HTTP Service | HTTP 请求执行 |

### Driver 规则

- 每个 Driver 必须有 driver_id
- 每个 Driver 必须有 runtime_type
- 每个 Driver 必须有 permission
- 每个 Driver 必须有 capability
- 每个 Driver 必须有 handler
- 每个 Driver 必须有 evidence

---

## Execution Lifecycle

**Before (P2-04):**
```
REQUEST -> VALIDATE -> EXECUTE -> COMPLETE
```

**After (P2-05.0):**
```
REQUESTED
  ↓
VALIDATING
  ↓
AUTHORIZED
  ↓
DISPATCHING
  ↓
RUNNING
  ↓
OBSERVING
  ↓
COMPLETED
```

**异常状态：**
- FAILED
- ROLLBACK

---

## 边界规则

1. **只定义接口** — 不实现完整执行引擎
2. **必须经过 Permission** — 无 Permission 不执行
3. **必须经过 Identity** — 无 Identity 不执行
4. **必须绑定 Evidence** — 无 Evidence 不记录
5. **必须记录 Audit** — 所有执行必须记录到 Audit

---

*Real Execution Architecture — P2-05.0*
