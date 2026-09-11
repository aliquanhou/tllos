# Identity Adapter

**Layer 1: Identity Adapter**

## 职责

Agent 接入 TLL OS 的身份验证层。

## 工作流程

1. **Load Genesis** — 读取 `tllos/identity/genesis.json`
   - 确认这是 TLL OS
   - 读取 OS 身份信息

2. **Verify Manifest** — 读取 `tllos/identity/canonical_manifest.json`
   - 验证 Canonical Layer 完整性
   - 确认文件 hash 一致

3. **Read Agent Contract** — 读取 `tllos/agents/agent_contract.md`
   - 理解 Agent 权利和义务
   - 理解 Agent 拒绝权

4. **Declare Identity** — 提交 Agent 身份信息
   - agent_id
   - agent_type
   - 接入目的

## 输出

已验证的 Agent Identity Token

## 核心要求

- ✅ 必须先验证 Genesis，再继续
- ✅ 必须验证 Manifest 完整性
- ✅ 必须阅读 Agent Contract
- ❌ 不允许跳过任何步骤

---

*Identity Adapter Layer*
