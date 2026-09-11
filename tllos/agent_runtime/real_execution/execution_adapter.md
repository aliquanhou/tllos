# Execution Adapter

## 概述

Execution Adapter 是 Real Execution 与 Runtime Adapter 之间的适配器。

---

## 定位

```
Runtime Adapter
       ↓
Execution Adapter           ← 本组件
       ↓
Real Execution
       ↓
Real Runtime / Driver
```

---

## Adapter 职责

1. **接收 Runtime Request** — 从 Runtime Adapter 接收请求
2. **转换为 Execution Request** — 转换为 Real Execution 请求
3. **调用 Driver** — 调用对应的 Driver
4. **返回 Result** — 返回执行结果

---

## Adapter Schema

```json
{
  "adapter_id": "",
  "runtime_target": "",
  "driver_id": "",
  "input": "",
  "output": ""
}
```

---

## 规则

1. Adapter 不直接执行 Runtime
2. Adapter 必须经过 Driver
3. Adapter 必须绑定 Evidence
4. Adapter 必须记录 Audit

---

*Execution Adapter — P2-05.0*
