# Driver Adapter

## 职责

Driver Adapter 负责 Driver Registry ↔ Driver Runtime 的转换。

---

## 转换流程

```
Driver Registry
  ↓
Driver Adapter
  ↓
Driver Runtime
```

---

## 转换规则

### Registry → Runtime

| Registry 字段 | Runtime 字段 |
|--------------|-------------|
| driver_id | execution_id |
| capability | capability |
| permission | permission |
| handler | runtime_target |

### Runtime → Result

| Runtime 字段 | Result 字段 |
|-------------|------------|
| status | status |
| output | output |
| error | error |
| execution_time | execution_time |

---

## 规则

1. 转换必须保持数据一致性
2. 缺失字段必须 REJECT
3. 不修改原始数据

---

*Driver Adapter — P2-05.2*
