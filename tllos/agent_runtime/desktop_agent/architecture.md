# TLL OS Desktop Agent Architecture

## 定位

Desktop Agent Layer 是 Agent Runtime 与现实计算环境之间的控制层。

---

## 完整调用链

```
Agent
  ↓
Trust Verification
  ↓
Permission Model
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
Real Execution
  ↓
Driver Registry
  ↓
Driver Runtime
  ↓
Desktop Agent          ← P2-06 新增
  ↓
OS Adapter
  ↓
Windows / Linux / macOS
  ↓
Computer Hardware
```

---

## 核心原则

1. **不能直接调用 OS API** — 必须经过 Desktop Agent Layer
2. **所有动作必须 Permission** — 无 Permission 不执行
3. **所有动作必须 Governance** — 高风险必须审批
4. **所有结果必须 Evidence** — 无 Evidence 不记录
5. **所有行为必须 Audit** — 全部进入 Audit Ledger

---

## 组件

| 组件 | 职责 |
|------|------|
| Desktop Architecture | 架构定义 |
| Capability Model | 能力定义 |
| Desktop Context | 上下文模型 |
| Desktop Action | 动作模型 |
| Lifecycle | 状态机 |
| Screen Driver | 屏幕能力 |
| Mouse Driver | 鼠标能力 |
| Keyboard Driver | 键盘能力 |
| Window Driver | 窗口能力 |
| Process Driver | 进程能力 |
| File Driver | 文件能力 |

---

## 不负责

- ❌ 不修改 Runtime Core
- ❌ 不修改 Canonical Layer
- ❌ 不绕过 Permission
- ❌ 不绕过 Governance
- ❌ 不直接调用 OS API

---

*Desktop Agent Architecture — P2-06*
