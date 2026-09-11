# Driver Runtime Interface

## 概述

Driver Runtime Interface 定义所有 Driver 必须实现的统一运行时接口。

---

## 统一接口方法

| 方法 | 职责 |
|------|------|
| initialize() | 初始化 Driver Runtime |
| validate() | 验证 Driver 合法性 |
| prepare() | 准备执行环境 |
| run() | 执行任务 |
| collect() | 收集执行结果 |
| finalize() | 清理执行环境 |

---

## 接口流程

```
initialize()
  ↓
validate()
  ↓
prepare()
  ↓
run()
  ↓
collect()
  ↓
finalize()
```

---

## 规则

1. 所有 Driver Runtime 必须实现以上接口
2. run() 之前必须 validate() 通过
3. collect() 必须在 run() 之后
4. finalize() 必须在 collect() 之后
5. 任何步骤失败必须 REJECT
6. 所有步骤必须记录到 Audit

---

*Driver Runtime Interface — P2-05.2*
