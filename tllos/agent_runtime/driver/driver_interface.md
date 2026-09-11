# Driver Interface

## 概述

Driver Interface 定义所有 Driver 必须实现的统一接口。

---

## 统一接口方法

| 方法 | 职责 |
|------|------|
| register() | 注册 Driver |
| validate() | 验证 Driver 合法性 |
| prepare() | 准备执行环境 |
| execute() | 执行任务 |
| collect_result() | 收集执行结果 |
| generate_evidence() | 生成证据 |

---

## 接口流程

```
register()
  ↓
validate()
  ↓
prepare()
  ↓
execute()
  ↓
collect_result()
  ↓
generate_evidence()
```

---

## 规则

1. 所有 Driver 必须实现以上接口
2. execute() 之前必须 validate() 通过
3. generate_evidence() 必须在 collect_result() 之后
4. 任何步骤失败必须 REJECT
5. 所有步骤必须记录到 Audit

---

*Driver Interface — P2-05.1*
