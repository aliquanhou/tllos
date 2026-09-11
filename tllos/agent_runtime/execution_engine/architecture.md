# Execution Engine Architecture

## 执行管道

```
┌─────────────────────────────────────────────────────────┐
│                    Execution Pipeline                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ Gateway  │ →  │ Permission│ →  │ Execution Engine │  │
│  │ Request  │    │   Check   │    │                  │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│                                          ↓              │
│                                   ┌──────────────┐      │
│                                   │  Execution   │      │
│                                   │   Context    │      │
│                                   └──────────────┘      │
│                                          ↓              │
│                                   ┌──────────────┐      │
│                                   │   Runtime    │      │
│                                   │   Adapter   │      │
│                                   └──────────────┘      │
│                                          ↓              │
│                                   ┌──────────────┐      │
│                                   │   Execution  │      │
│                                   │   Result     │      │
│                                   └──────────────┘      │
│                                          ↓              │
│                                   ┌──────────────┐      │
│                                   │   Evidence   │      │
│                                   │   Record     │      │
│                                   └──────────────┘      │
│                                          ↓              │
│                                   ┌──────────────┐      │
│                                   │     Audit    │      │
│                                   │    Ledger    │      │
│                                   └──────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 职责划分

| 组件 | 职责 |
|------|------|
| Gateway | 接收请求，验证格式 |
| Permission Check | 验证权限是否允许 |
| Execution Engine | 创建执行上下文，调度执行 |
| Execution Context | 保存执行状态和元数据 |
| Runtime Adapter | 调用底层 Runtime（边界） |
| Execution Result | 返回执行结果 |
| Evidence Record | 生成执行证据 |
| Audit Ledger | 记录执行事件 |

## 关键边界

- **Execution Engine → Runtime Adapter**：通过接口调用，不直接操作 VM
- **Execution Engine → Evidence**：必须生成 Evidence
- **Execution Engine → Audit Ledger**：必须记录事件

---

*Execution Engine Architecture — P2-04*
