# Adaptive Execution Model

## 模型概述

Adaptive Execution Model 定义如何收集执行反馈、分析适配需求和生成优化建议。

---

## 核心概念

### Execution Feedback

一个 Feedback 记录执行后的反馈信息：
- execution_id：执行唯一标识符
- observation_ref：观察引用
- metrics_ref：指标引用
- insight_ref：洞察引用
- feedback_type：反馈类型
- feedback_value：反馈值
- evidence_ref：证据引用
- audit_ref：审计引用

### Adaptation Proposal

一个 Proposal 是对执行的优化建议：
- proposal_id：建议唯一标识符
- execution_id：执行 ID
- proposal_type：建议类型
- reason：建议原因
- evidence_ref：证据引用
- confidence：置信度
- status：状态

---

## Feedback 类型

| 类型 | 说明 |
|------|------|
| performance | 性能反馈 |
| reliability | 可靠性反馈 |
| trust | 信任反馈 |
| pattern | 模式反馈 |
| risk | 风险反馈 |

---

## Proposal 类型

### 允许的类型

| 类型 | 说明 |
|------|------|
| performance_hint | 性能优化提示 |
| reliability_hint | 可靠性优化提示 |
| risk_warning | 风险警告 |

### 禁止的类型

| 类型 | 说明 |
|------|------|
| permission_upgrade | 权限提升（禁止） |
| policy_change | 策略修改（禁止） |
| execution_override | 执行覆盖（禁止） |

---

## Proposal 状态

| 状态 | 说明 |
|------|------|
| CREATED | 建议已创建 |
| SUBMITTED | 已提交 |
| REVIEWING | 正在审核 |
| APPROVED | 已批准 |
| REJECTED | 已拒绝 |

---

## 规则

1. **Feedback 必须绑定 Observation + Metrics + Insight + Evidence + Audit**
2. **Proposal 只能是 performance_hint / reliability_hint / risk_warning**
3. **Proposal 必须经过 Governance Review**
4. **Proposal 不能直接执行**
5. **Proposal 不能改变 Permission / Policy / Execution**

---

*Adaptive Execution Model — P2-04.7*
