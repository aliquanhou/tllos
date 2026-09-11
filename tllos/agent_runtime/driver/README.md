# TLL OS Driver Registry

## 职责

Driver Registry 是 Driver 的注册中心，负责任务管理 Driver 的生命周期、元数据和能力映射。

**定位：Driver Registry Layer**

---

## 核心职责

1. **register driver** — 注册新 Driver
2. **query driver** — 查询 Driver 元数据
3. **disable driver** — 禁用 Driver
4. **validate driver** — 验证 Driver 合法性

---

## Registry 结构

```
Driver Registry
  ├── Driver A (tll.execute)
  ├── Driver B (python.execute)
  ├── Driver C (shell.execute)
  └── Driver D (http.request)
```

---

## 注册规则

1. 每个 Driver 必须有 driver_id
2. 每个 Driver 必须有 runtime_type
3. 每个 Driver 必须有 capability
4. 每个 Driver 必须有 permission
5. 重复 driver_id 必须 REJECT
6. 未知 driver_id 必须 REJECT

---

## 不负责

- ❌ 不执行 Driver
- ❌ 不管理 Execution
- ❌ 不处理 Permission Approval

---

*Driver Registry — P2-05.1*
