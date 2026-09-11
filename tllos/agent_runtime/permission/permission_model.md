# TLL OS Agent Permission Model

**Layer 2.5: Permission Model**

## 职责

定义 Agent 的权限状态机和边界。

## 核心原则

- **Capability ≠ Permission**
  - Capability 是 Agent 声明的能力
  - Permission 是系统授予的权限
  - 有 Capability 不等于有 Permission
- **最小权限原则**
  - 默认无权限
  - 显式申请，显式批准
- **状态不可自行提升**
  - Agent 不能自己把 requested 变成 approved

## 权限状态机

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ requested │ ──→ │ approved  │ ──→ │ executed │
└──────────┘     └──────────┘     └──────────┘
     │                │                │
     │ rejected       │ revoked       │
     ▼                ▼                ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│ rejected │     │ revoked  │     │ expired  │
└──────────┘     └──────────┘     └──────────┘
```

## 状态定义

| 状态 | 说明 | 谁可以设置 |
|------|------|-----------|
| requested | Agent 申请了权限 | Agent |
| approved | 系统批准了权限 | 裁决方 / Owner |
| executed | 权限已被使用 | System |
| rejected | 权限被拒绝 | 裁决方 / Owner |
| revoked | 权限被撤销 | 裁决方 / Owner |
| expired | 权限已过期 | System |

## 禁止行为

- ❌ Agent 自行将 requested → approved
- ❌ Agent 自行将 approved → executed
- ❌ 无 approved 状态下执行任务
- ❌ 权限超出 Capability 范围

## 权限粒度

| 级别 | 说明 | 示例 |
|------|------|------|
| read:canonical | 读取 Canonical Layer | genesis.json |
| write:evidence | 写 Evidence 文档 | docs/evidence/*.md |
| write:code | 修改代码 | host/c/*.c |
| execute:test | 运行测试 | python test_*.py |
| execute:build | 运行构建 | build_all.bat |

---

*Permission Model Layer*
