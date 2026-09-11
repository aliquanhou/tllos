# TLL OS Runtime Adapter Interface

## 职责

定义 Agent Runtime 与 TLL Runtime Core 之间的适配层接口。

**本阶段只定义接口，禁止调用 vm.c，禁止修改 Runtime。**

## 定位

```
Agent Runtime
  ↓
Execution Gateway
  ↓
Runtime Adapter  ← 当前层
  ↓
[Runtime Core — FUTURE]
```

## 接口方法

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| execute | runtime_request | runtime_result | 执行任务（本阶段不实现） |
| get_status | request_id | status | 查询执行状态 |
| cancel | request_id | result | 取消执行 |

## 设计原则

1. **隔离**：Agent Runtime 不直接访问 Runtime Core
2. **边界**：所有 Runtime 调用必须经过 Adapter
3. **可替换**：未来可以替换不同的 Runtime 后端
4. **可测试**：Adapter 可以 mock，不依赖真实 Runtime

## 禁止事项

- ❌ 调用 vm.c
- ❌ 修改 Runtime Core
- ❌ 直接访问 coroutine
- ❌ 直接访问 scheduler
- ❌ 直接访问 frame pool

---

*Runtime Adapter Layer — P2-03.3*
