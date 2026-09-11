# TLL OS Agent Runtime

**Agent Runtime Foundation** — 让 AI Agent 在 TLL OS 上安全、可信、可审计地工作。

## 分层架构

```
Layer 5: Audit Interface      ← 审计接口
Layer 4: Evidence Collector   ← 证据收集
Layer 3: Task Dispatcher      ← 任务分发
Layer 2: Capability Manager   ← 能力管理
Layer 1: Identity Adapter      ← 身份适配器
```

## 目录结构

```
tllos/agent_runtime/
├── README.md                 ← 本文件
├── identity/
│   └── adapter.md            ← Identity Adapter 说明
├── capability/
│   └── manager.md            ← Capability Manager 说明
├── task/
│   └── dispatcher.md         ← Task Dispatcher 说明
├── evidence/
│   └── collector.md         ← Evidence Collector 说明
└── audit/
    └── interface.md          ← Audit Interface 说明
```

## 协议文件

| 文件 | 说明 |
|------|------|
| `boot_protocol.json` | Agent 启动协议 |
| `capability_declaration.schema.json` | Agent 能力声明 Schema |
| `task_contract.json` | 任务契约 |
| `evidence_record.json` | 证据记录格式 |

## 当前状态

- **阶段：** P2-03 Phase 1
- **状态：** 协议骨架建立中
- **不提供：** 实际执行引擎、权限沙箱、密码学身份

## 核心原则

1. 默认无权限
2. 显式声明能力
3. 最小权限原则
4. 没有 Evidence，不生成 Claim
5. 施工方不自行宣布 SEALED

---

*TLL OS Agent Runtime Foundation*
