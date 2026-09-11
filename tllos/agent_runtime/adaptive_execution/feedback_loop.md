# Adaptive Feedback Loop

## 概述

Adaptive Feedback Loop 定义从 Execution Result 到 Optimization Proposal 的反馈闭环。

---

## 反馈闭环流程

```
Execution Result
       ↓
Observation
       ↓
Metrics Extraction
       ↓
Insight Generation
       ↓
Feedback Collection
       ↓
Adaptation Analysis
       ↓
Proposal Generation
       ↓
Governance Review
       ↓
Approved / Rejected
```

---

## 各阶段说明

### 1. Execution Result

执行完成后的结果

### 2. Observation

记录执行过程

### 3. Metrics Extraction

提取执行指标

### 4. Insight Generation

生成执行洞察

### 5. Feedback Collection

收集执行反馈

### 6. Adaptation Analysis

分析适配需求

### 7. Proposal Generation

生成优化建议

### 8. Governance Review

治理审核

---

## 关键规则

1. **Feedback 必须绑定 Evidence** — 无 Evidence 的 Feedback 无效
2. **Proposal 必须经过 Governance Review** — 未经审批的 Proposal 无效
3. **Proposal 不能直接执行** — 只能建议，不能执行
4. **Proposal 不能改变 Permission / Policy** — 只能优化，不能提权
5. **所有 Feedback 和 Proposal 必须记录到 Audit** — 审计完整

---

## 示例

```
Execution: 执行完成
Observation: 记录执行过程
Metrics: 提取指标 (duration=12.5s, step_count=5)
Insight: 执行时长低于平均水平
Feedback: performance feedback
Proposal: performance_hint - 建议优化步骤顺序
Governance: APPROVED
```

---

*Adaptive Feedback Loop — P2-04.7*
