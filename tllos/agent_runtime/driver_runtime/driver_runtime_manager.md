# Driver Runtime Manager

## 职责

Driver Runtime Manager 是 Driver 执行的核心管理器。

---

## 核心职责

1. **load driver** — 加载 Driver
2. **validate driver** — 验证 Driver 合法性
3. **dispatch driver** — 分发执行
4. **collect result** — 收集结果

---

## 管理流程

```
load_driver()
  ↓
validate_driver()
  ↓
dispatch_driver()
  ↓
collect_result()
```

---

## 规则

1. load 之前必须存在于 Registry
2. validate 必须通过后才能 dispatch
3. dispatch 之前必须经过 Governance
4. collect 之前必须 dispatch 完成
5. 任何步骤失败必须 REJECT

---

*Driver Runtime Manager — P2-05.2*
