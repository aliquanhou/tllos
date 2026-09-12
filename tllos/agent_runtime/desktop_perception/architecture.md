# TLL OS Desktop Perception Architecture

## 定位

Perception Layer 是 Agent Runtime 的视觉感知层，让 Agent 第一次具备“看懂屏幕”的协议能力。

---

## 完整调用链

```
Desktop Agent
      ↓
Perception Layer          ← P2-07 新增
      ↓
Vision Engine
      ↓
Object Model
      ↓
Action Planning
      ↓
Execution
```

---

## Perception 职责

### 输入
- Screen Frame（屏幕帧）
- Vision Result（视觉结果）
- Object Detection（目标检测）

### 输出
- Screen Understanding（屏幕理解）
- Object List（目标列表）
- Action Suggestion（动作建议）

---

## 核心组件

| 组件 | 职责 |
|------|------|
| Screen Frame | 屏幕帧模型 |
| Vision Object | 视觉目标模型 |
| OCR | 文字识别 |
| Object Detection | 目标检测 |
| Frame Lifecycle | 帧生命周期 |

---

## Safety Boundary

**禁止：**
- Vision → Action（直接执行）

**必须：**
- Vision → Decision → Permission → Governance → Execution

---

## 当前状态

```
Protocol Layer Only
Real Implementation: NOT IMPLEMENTED
```

---

*Perception Architecture — P2-07*
