# Evidence Collector

**Layer 4: Evidence Collector**

## 职责

收集和验证 Agent 提交的 Evidence。

## 工作流程

1. **Receive Record** — 接收 Agent 提交的 Evidence Record
2. **Validate Claim** — 验证 Claim 是否有对应 Evidence
3. **Validate Format** — 验证 Evidence 是否符合 evidence_rules
4. **Record Index** — 记录 Evidence 到 Evidence Index

## 核心原则

- ✅ 没有 Evidence，不生成 Claim
- ✅ Evidence 必须可追溯
- ✅ Evidence 必须分级
- ❌ 禁止只有结果，没有证据

## Evidence 分级

| 等级 | 说明 |
|------|------|
| OBSERVED | 观察到的现象 |
| INFERRED | 推断的结论 |
| UNVERIFIED | 未验证的声明 |
| PROVEN | 已证明的结论 |
| RULED OUT | 已排除的假设 |

## 输出

Validated Evidence Record

---

*Evidence Collector Layer*
