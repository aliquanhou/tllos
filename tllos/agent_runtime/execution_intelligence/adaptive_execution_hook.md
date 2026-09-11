# Adaptive Execution Hook

## 概述

Adaptive Execution Hook 定义 Execution Intelligence 与 Adaptive Execution 之间的集成点。

---

## 流程升级

**Before (P2-04.6):**

```
Observation
  ↓
Metrics
  ↓
Insight
```

**After (P2-04.7):**

```
Observation
  ↓
Metrics
  ↓
Insight
  ↓
Adaptive Feedback
  ↓
Proposal
```

---

## Hook 职责

Adaptive Execution Hook 在 Insight 之后执行，负责：

1. **接收 Insight** — 接收 Execution Intelligence 输出的洞察
2. **生成 Feedback** — 生成执行反馈
3. **生成 Proposal** — 生成优化建议
4. **提交 Governance** — 提交 Governance Review

---

## 规则

- Adaptive Hook 在 Insight 之后执行
- Adaptive Hook 只生成 Feedback 和 Proposal
- Adaptive Hook 不修改 Execution Result
- Adaptive Hook 不直接执行
- Adaptive Hook 必须提交 Governance Review

---

## 禁止

- ❌ Adaptive Hook 直接执行 Proposal
- ❌ Adaptive Hook 绕过 Governance
- ❌ Adaptive Hook 修改 Execution Result
- ❌ Adaptive Hook 自动提升权限

---

*Adaptive Execution Hook — P2-04.7*
