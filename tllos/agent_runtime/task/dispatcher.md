# Task Dispatcher

**Layer 3: Task Dispatcher**

## 职责

任务分发和执行调度。

## 工作流程

1. **Receive Task** — 接收 Task Contract
2. **Validate Scope** — 验证任务 Scope 是否在 Agent 权限内
3. **Dispatch** — 分发任务给 Agent
4. **Monitor** — 监控执行状态
5. **Collect Result** — 收集执行结果

## 核心原则

- ✅ 任务必须有明确 Scope
- ✅ 任务必须有 evidence_requirement
- ✅ 越权任务必须拒绝
- ❌ 不允许无 Scope 的任务

## 拒绝条件

Task Dispatcher 必须拒绝以下任务：

1. 超出 Agent permission_scope
2. 没有 evidence_requirement
3. 要求修改已 SEALED 层级
4. 风险等级未声明

## 输出

Task Execution Result

---

*Task Dispatcher Layer*
