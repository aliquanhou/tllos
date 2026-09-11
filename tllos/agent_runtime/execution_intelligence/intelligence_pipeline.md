# Execution Intelligence Pipeline

## 概述

Execution Intelligence Pipeline 定义从 Audit Ledger 到 Insight Output 的分析流程。

---

## Pipeline 流程

```
Audit Ledger
       |
       v
Execution Observation
       |
       v
Metrics Extraction
       |
       v
Pattern Analysis
       |
       v
Insight Output
```

---

## 各阶段说明

### 1. Audit Ledger

**输入来源：** 完整的审计事件链

### 2. Execution Observation

**职责：** 从 Audit Ledger 中提取执行过程的观察记录

**输出：** Execution Observation 列表

### 3. Metrics Extraction

**职责：** 从 Observation 中提取量化指标

**输出：** Execution Metrics

### 4. Pattern Analysis

**职责：** 分析执行过程中的模式和趋势

**输出：** Execution Pattern

### 5. Insight Output

**职责：** 生成执行洞察和优化建议

**输出：** Execution Insight

---

## Insight 规则

Insight **必须**满足：

1. **有 Evidence** — 每个 Insight 必须绑定 evidence_ref
2. **有 Audit Reference** — 每个 Insight 必须有 audit reference
3. **不改变执行结果** — Insight 不修改、不绕过、不提升
4. **只是建议** — Insight 只是分析建议，不自动执行

---

## 禁止

- ❌ 自动修改 Execution Plan
- ❌ 自动提升 Permission
- ❌ 自动绕过 Governance
- ❌ 自动改变 Trust State
- ❌ 自动决策执行
- ❌ 自动优化执行

---

## 示例

```json
{
  "execution_id": "exec-int-001",
  "insights": [
    {
      "type": "performance",
      "description": "执行时长 12.5 秒，低于平均水平",
      "evidence_ref": "ev-int-001"
    },
    {
      "type": "reliability",
      "description": "验证通过率 100%，无失败",
      "evidence_ref": "ev-int-002"
    }
  ]
}
```

---

*Execution Intelligence Pipeline — P2-04.6*
