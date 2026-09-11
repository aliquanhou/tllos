# Execution Target

## 概述

Execution Target 定义真实执行的目标对象。

---

## Target 类型

| Target Type | 说明 |
|-------------|------|
| tll_runtime | TLL Runtime 执行 |
| python_runtime | Python 脚本执行 |
| shell_command | Shell 命令执行 |
| http_service | HTTP 服务执行 |

---

## Target Schema

```json
{
  "target_id": "",
  "target_type": "",
  "runtime_type": "",
  "capabilities": [],
  "status": "AVAILABLE",
  "security_level": ""
}
```

---

## Target 状态

| Status | 说明 |
|--------|------|
| AVAILABLE | 可用 |
| DISABLED | 已禁用 |
| DEPRECATED | 已废弃 |
| BLOCKED | 已阻止 |

---

## 规则

1. Agent 不能自定义 Target
2. Target 必须经过 Registry
3. Target 必须经过 Validation
4. Target 必须经过 Execution
5. 未知 Target 必须 REJECT

---

*Execution Target — P2-05.0*
