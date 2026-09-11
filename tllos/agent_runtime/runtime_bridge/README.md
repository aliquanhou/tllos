# TLL OS Runtime Bridge

## 职责

Runtime Bridge 是 Execution Engine 与 Runtime Adapter 之间的协议转换层。

**定位：Execution Protocol Translation Layer**

## 核心职责

1. **接收** Execution Engine 输出
2. **转换** Runtime Adapter 请求格式
3. **验证** Runtime Boundary
4. **绑定** Evidence
5. **返回** Execution Result

## 不负责

- ❌ VM execution
- ❌ Scheduler
- ❌ Memory management
- ❌ Bytecode execution
- ❌ Direct Runtime calls

## 架构定位

```
Execution Engine
       ↓
Runtime Bridge          ← 本层
       ↓
Runtime Adapter
       ↓
TLL Runtime Boundary
```

## 设计原则

1. **单向**：Execution Engine → Bridge → Adapter，不可反向
2. **Evidence Binding**：所有 Runtime 请求必须绑定 Evidence
3. **Boundary Check**：Bridge 验证 Runtime Boundary
4. **Translation Only**：只做协议转换，不做执行

---

*Runtime Bridge Layer — P2-04.2*
