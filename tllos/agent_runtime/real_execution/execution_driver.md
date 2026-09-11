# Execution Driver

## 概述

Execution Driver 定义真实执行的驱动程序。

---

## Driver 类型

| Driver ID | Runtime Type | 说明 |
|-----------|--------------|------|
| tll.execute | tll_runtime | TLL 语言执行 |
| python.execute | python_runtime | Python 脚本执行 |
| shell.execute | shell_command | Shell 命令执行 |
| http.request | http_service | HTTP 请求执行 |

---

## Driver Schema

```json
{
  "driver_id": "",
  "runtime_type": "",
  "permission": "",
  "capability": "",
  "handler": "",
  "evidence": ""
}
```

---

## Driver 规则

1. 每个 Driver 必须有 driver_id
2. 每个 Driver 必须有 runtime_type
3. 每个 Driver 必须有 permission
4. 每个 Driver 必须有 capability
5. 每个 Driver 必须有 handler
6. 每个 Driver 必须有 evidence
7. 未知 Driver 必须 REJECT
8. 无 Permission 的 Driver 必须 REJECT

---

## Driver 调用流程

```
Agent Request
  ↓
Permission Check
  ↓
Capability Check
  ↓
Driver Selection
  ↓
Driver Execution
  ↓
Result Return
```

---

*Execution Driver — P2-05.0*
