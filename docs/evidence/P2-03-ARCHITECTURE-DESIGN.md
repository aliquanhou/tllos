# P2-03 Agent Runtime Foundation — Architecture Design

**Project:** TLL OS
**Phase:** P2-03 Agent Runtime Foundation
**Date:** 2026-09-11
**Architect:** 于秋鸿博士
**Implementer:** 豆包A（施工方）

---

## 1. 设计目标

让外部 AI Agent 不只是"读取文件"，而是能够：

```
发现 TLL OS
    ↓
验证身份
    ↓
理解规则
    ↓
声明能力
    ↓
申请任务
    ↓
执行任务
    ↓
提交 Evidence
```

**形成第一个 Agent 工作闭环。**

---

## 2. Agent Runtime 分层

```
┌─────────────────────────────────────────┐
│           Layer 5: Audit Interface      │  ← 审计接口
├─────────────────────────────────────────┤
│           Layer 4: Evidence Collector    │  ← 证据收集
├─────────────────────────────────────────┤
│           Layer 3: Task Dispatcher      │  ← 任务分发
├─────────────────────────────────────────┤
│           Layer 2: Capability Manager    │  ← 能力管理
├─────────────────────────────────────────┤
│           Layer 1: Identity Adapter     │  ← 身份适配器
└─────────────────────────────────────────┘
```

---

## 3. 各层职责

### Layer 1: Identity Adapter

**职责：** Agent 接入 TLL OS 的身份验证层。

**工作流程：**
1. 读取 Genesis（确认这是 TLL OS）
2. 验证 Manifest（确认 Canonical Layer 完整性）
3. 读取 Agent Contract（理解权利义务）
4. 完成身份绑定

**输出：** 已验证的 Agent Identity Token

---

### Layer 2: Capability Manager

**职责：** 管理 Agent 能力声明和权限边界。

**工作流程：**
1. Agent 提交 Capability Declaration
2. 验证声明是否符合 Agent Contract
3. 分配 permission_scope
4. 记录 risk_level

**核心原则：**
- 默认无权限
- 显式声明能力
- 最小权限原则
- 禁止 root 默认

**输出：** 已授权的 Capability Profile

---

### Layer 3: Task Dispatcher

**职责：** 任务分发和执行调度。

**工作流程：**
1. 接收 Task Contract
2. 验证任务 Scope 是否在 Agent 权限内
3. 分发任务给 Agent
4. 监控执行状态
5. 收集执行结果

**核心原则：**
- 任务必须有明确 Scope
- 任务必须有 evidence_requirement
- 越权任务必须拒绝

**输出：** Task Execution Result

---

### Layer 4: Evidence Collector

**职责：** 收集和验证 Agent 提交的 Evidence。

**工作流程：**
1. 接收 Agent 提交的 Evidence Record
2. 验证 Claim 是否有对应 Evidence
3. 验证 Evidence 是否符合 evidence_rules
4. 记录 Evidence 到 Evidence Index

**核心原则：**
- 没有 Evidence，不生成 Claim
- Evidence 必须可追溯
- Evidence 必须分级（OBSERVED / PROVEN / UNVERIFIED）

**输出：** Validated Evidence Record

---

### Layer 5: Audit Interface

**职责：** 为独立审计方提供接口。

**工作流程：**
1. 审计方读取 Agent Runtime 状态
2. 审计方验证 Evidence Record
3. 审计方给出 PASS / REQUEST CHANGES
4. 结果记录到 Evidence Index

**核心原则：**
- 施工方不自行宣布 SEALED
- 审计独立于施工
- 审计结果由裁决方确认

**输出：** Audit Result

---

## 4. Agent 工作闭环

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Boot    │ ──→ │ Declare  │ ──→ │  Task    │
│ Identity │     │Capability│     │  Receive │
└──────────┘     └──────────┘     └────┬─────┘
     ↑                                  │
     │                                  ↓
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Audit   │ ←── │  Verify  │ ←── │  Execute │
│  Result  │     │ Evidence │     │  Task    │
└──────────┘     └──────────┘     └──────────┘
```

---

## 5. 第一阶段范围

**本阶段只建立协议骨架，不实现复杂执行。**

| 阶段 | 内容 |
|------|------|
| Phase 1 | 架构设计文档 |
| Phase 2 | 目录结构建立 |
| Phase 3 | Boot Protocol v1 |
| Phase 4 | Capability Declaration v1 |
| Phase 5 | Task Contract v1 |
| Phase 6 | Evidence Record v1 |
| Phase 7 | 基础测试 |
| Phase 8 | Evidence 文档 |

**后续阶段：**
- Phase 2: 实际执行引擎
- Phase 3: 多 Agent 协作
- Phase 4: 与 Runtime Core 集成

---

## 6. 边界确认

### 本阶段允许

- ✅ 新增 `tllos/agent_runtime/` 目录
- ✅ 新增协议文件（JSON / Markdown）
- ✅ 新增测试
- ✅ 新增 Evidence 文档

### 本阶段禁止

- ❌ 修改 Runtime Core
- ❌ 修改 vm.c / tllvm.h
- ❌ 修改 Scheduler / Coroutine
- ❌ 修改 Canonical Layer 已封板文件
- ❌ 修改 Genesis / Manifest
- ❌ 修改历史 Evidence
- ❌ 引入密码学身份系统

---

## 7. 设计原则

1. **Audit first.** — 先审计，再施工
2. **Architecture second.** — 先架构，再实现
3. **Construction third.** — 先骨架，再功能
4. **Evidence fourth.** — 每个阶段必须有 Evidence
5. **Independent Audit fifth.** — 独立审计后才封板
6. **Seal last.** — 最后才是 SEALED

---

*文档生成时间：2026-09-11 (Asia/Shanghai)*
*P2-03 Agent Runtime Foundation Architecture Design*
