# Capability Manager

**Layer 2: Capability Manager**

## 职责

管理 Agent 能力声明和权限边界。

## 工作流程

1. **Receive Declaration** — 接收 Agent 提交的 Capability Declaration
2. **Validate Declaration** — 验证声明是否符合 Agent Contract
3. **Assign Permission** — 分配 permission_scope
4. **Record Risk Level** — 记录 risk_level

## 核心原则

- ✅ 默认无权限
- ✅ 显式声明能力
- ✅ 最小权限原则
- ❌ 禁止默认 root 权限

## 权限层级

| 级别 | 说明 |
|------|------|
| READ_ONLY | 只读 Canonical Layer |
| WRITE_DOC | 只写 Evidence 文档 |
| WRITE_CODE | 可以修改代码 |
| FULL | 完整权限（需要特殊授权） |

## 输出

已授权的 Capability Profile

---

*Capability Manager Layer*
