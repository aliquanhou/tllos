# TLL OS Evidence Binding Protocol

## 证据绑定协议

定义 Task → Action → Evidence → Ledger 的完整闭环。

## 完整闭环

```
Task Contract
  ↓
Execution Request
  ↓
Action
  ↓
Evidence
  ↓
Ledger Record
  ↓
Audit
```

## 核心规则

### 1. 无 Evidence → Task Completed 禁止

```
❌ 错误：
Task → Action → "完成了"

✅ 正确：
Task → Action → Evidence → Ledger → Audit
```

### 2. 无 Task → Action Recorded 禁止

```
❌ 错误：
Action → Ledger Record（没有 Task ID）

✅ 正确：
Task → Action → Ledger Record（必须有 Task ID）
```

### 3. ExecutionCompleted 必须有 evidence_ref

```
❌ 错误：
event_type: ExecutionCompleted
evidence_ref: empty

✅ 正确：
event_type: ExecutionCompleted
evidence_ref: evidence-xxx
```

### 4. ExecutionRequested 必须有 permission

```
❌ 错误：
event_type: ExecutionRequested
permission: empty

✅ 正确：
event_type: ExecutionRequested
permission: perm-xxx
```

## Evidence 类型

| 类型 | 说明 |
|------|------|
| commit_sha | Git Commit SHA |
| test_result | 测试结果 |
| build_log | 构建日志 |
| file_hash | 文件哈希 |
| manual_verify | 人工验证 |

## 绑定关系

```
Task Contract ──→ Execution Request ──→ Action
                                         ↓
Evidence Record ←──────────────────────┘
         ↓
Ledger Record
         ↓
Audit Review
```

## 禁止模式

1. ❌ Task Completed but no Evidence
2. ❌ Action Recorded but no Task
3. ❌ ExecutionCompleted but no evidence_ref
4. ❌ ExecutionRequested but no permission
5. ❌ Ledger Record but no Event

---

*Evidence Binding Protocol — P2-03.4*
