# Execution Metrics Model

## 概述

Execution Metrics 是从执行过程中提取的量化指标，用于分析执行质量和性能。

---

## Metrics 分类

### 1. Performance（性能指标）

| 指标 | 类型 | 说明 |
|------|------|------|
| execution_duration | number | 执行时长（秒） |
| step_count | number | 步骤数量 |
| retry_count | number | 重试次数 |

### 2. Reliability（可靠性指标）

| 指标 | 类型 | 说明 |
|------|------|------|
| failure_count | number | 失败次数 |
| rollback_count | number | 回滚次数 |
| validation_pass_rate | number | 验证通过率（0-100） |

### 3. Trust（信任指标）

| 指标 | 类型 | 说明 |
|------|------|------|
| evidence_quality | number | 证据质量评分（0-100） |
| governance_compliance | number | 治理合规性评分（0-100） |
| audit_integrity | number | 审计完整性评分（0-100） |

---

## 禁止生成的指标

以下指标**禁止**在 P2-04.6 生成：

- ❌ agent_score
- ❌ agent_rank
- ❌ trust_upgrade

**原因：P2-04.6 只观察，不治理。**

---

## 指标来源

所有指标**必须**来自真实的 Execution Observation 和 Audit Ledger，**禁止**伪造或估计。

---

## 示例

```json
{
  "execution_id": "exec-int-001",
  "performance": {
    "execution_duration": 12.5,
    "step_count": 5,
    "retry_count": 0
  },
  "reliability": {
    "failure_count": 0,
    "rollback_count": 0,
    "validation_pass_rate": 100
  },
  "trust": {
    "evidence_quality": 95,
    "governance_compliance": 100,
    "audit_integrity": 100
  }
}
```

---

## 禁止

- ❌ 伪造 Metrics
- ❌ 估计 Metrics
- ❌ 无 Evidence 的 Metrics
- ❌ 用于自动决策的 Metrics

---

*Execution Metrics Model — P2-04.6*
