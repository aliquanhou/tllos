# TLL Native Ownership & Refcount Rules v1.0

**版本**: 1.0 (DRAFT)
**阶段**: Phase 2-01-B.10
**状态**: PROVISIONAL / 待架构师验收
**日期**: 2026-09-09

---

## 一、概述

本文档定义 TLL Native Target 的内存所有权和引用计数规则。

**核心原则**: TLL 使用纯引用计数（无 GC / 无 cycle collector）。所有堆分配对象（string/array/map/function/upvalue）通过引用计数管理生命周期。

**当前状态**: 
- Bytecode VM: 完整的引用计数管理（已验证）
- Native Target: 基本框架已建立，完整实现待后续阶段
- Shared Runtime: 引用计数函数已实现（tll_value_incref / tll_value_free）

---

## 二、对象类型与引用计数

### 2.1 需要引用计数的类型

| 类型 | 存储位置 | refCount 位置 |
|------|---------|--------------|
| TLL_STRING | 堆 | 字符串数据前的 int header |
| TLL_ARRAY | 堆 | TLLArray.refCount |
| TLL_MAP | 堆 | TLLMap.refCount |
| TLL_FUNCTION | 堆（env） | TLLClosureEnv.refCount |
| TLL_UPVALUE | 堆 | TLLUpvalue.refCount |

### 2.2 不需要引用计数的类型

| 类型 | 存储位置 | 说明 |
|------|---------|------|
| TLL_NULL | 值类型 | 无堆分配 |
| TLL_BOOL | 值类型 | 无堆分配 |
| TLL_INT | 值类型 | 无堆分配 |
| TLL_FLOAT | 值类型 | 无堆分配 |
| TLL_BUILTIN | 值类型 | 无堆分配 |

---

## 三、所有权规则

### 3.1 创建（Creation）

- 值创建函数（tll_string, tll_array, tll_map, etc.）返回的 TLLValue 引用计数为 1
- 调用者拥有该引用
- 示例: `TLLValue s = tll_string("hello"); // refCount = 1, caller owns`

### 3.2 赋值（Assignment）

- 变量赋值时，应先 free 旧值，再 incref 新值
- 示例:
  ```c
  // Before: x owns old_value
  tll_value_free(x);      // release old value
  x = new_value;
  tll_value_incref(x);    // acquire new value
  // After: x owns new_value
  ```

### 3.3 函数参数传递（Function Argument Passing）

- 调用者传递参数时，应 incref 参数（被调用者获得引用）
- 被调用者在函数结束时应 free 参数
- 示例:
  ```c
  // Caller
  tll_value_incref(arg);
  callee(arg);
  
  // Callee
  fn callee(TLLValue arg) {
      // use arg
      tll_value_free(arg); // release at end
  }
  ```

### 3.4 函数返回值（Function Return Value）

- 函数返回值时，应 incref 返回值（调用者获得引用）
- 调用者负责 free 返回值
- 示例:
  ```c
  TLLValue callee() {
      TLLValue result = tll_string("hello");
      tll_value_incref(result); // caller will own
      return result;
  }
  
  // Caller
  TLLValue r = callee();
  // use r
  tll_value_free(r); // release
  ```

### 3.5 容器元素（Container Elements）

- Array/Map 存储元素时，应 incref 元素（容器拥有引用）
- Array/Map 释放时，应 free 所有元素
- 示例:
  ```c
  // array_push (caller should incref before calling)
  tll_value_incref(elem);
  array_push(arr.as.array, elem);
  
  // array_get (caller should incref after receiving)
  TLLValue v = array_get(arr.as.array, 0);
  tll_value_incref(v); // caller owns
  
  // array_set (container frees old, caller should incref new)
  tll_value_incref(new_elem);
  array_set(arr.as.array, 0, new_elem); // array_set internally frees old
  ```

### 3.6 作用域结束（Scope End）

- 变量作用域结束时，应 free 所有局部变量
- 示例:
  ```c
  fn example() {
      TLLValue s = tll_string("hello");
      TLLValue a = tll_array();
      // use s and a
      tll_value_free(s); // release at end
      tll_value_free(a);
  }
  ```

---

## 四、Shared Runtime 引用计数函数

### 4.1 tll_value_incref

```c
void tll_value_incref(TLLValue v);
```

- 增加值的引用计数（如果是需要引用计数的类型）
- 对于值类型（null/bool/int/float/builtin），是 no-op

### 4.2 tll_value_free

```c
void tll_value_free(TLLValue v);
```

- 减少值的引用计数（如果是需要引用计数的类型）
- 引用计数归零时释放内存
- 对于值类型，是 no-op
- 释放 Array/Map 时，递归 free 所有元素

---

## 五、Bytecode VM vs Native Target 对比

### 5.1 Bytecode VM（已实现）

- 变量赋值: free 旧值 + incref 新值 ✅
- 函数参数: incref 参数 ✅
- 函数返回: incref 返回值 ✅
- 容器元素: incref 元素 ✅
- 帧销毁: free 所有寄存器/局部变量/参数 ✅

### 5.2 Native Target（当前状态）

- 变量赋值: ❌ 未实现（直接覆盖，旧值泄漏）
- 函数参数: ❌ 未实现
- 函数返回: ❌ 未实现
- 容器元素: ⚠️ 部分（array_set/map_set 内部 free 旧值，但未 incref 新值）
- 函数结束: ❌ 未实现（依赖进程退出释放）

### 5.3 影响

- 短期运行的程序: 内存泄漏不明显（进程退出时释放）
- 长期运行的程序: 内存泄漏会累积
- Native Target 当前不适合长期运行的服务端程序

---

## 六、实现路线图

### Phase 2-01-B.10（当前阶段）

- ✅ 建立所有权规则文档
- ✅ 验证 Shared Runtime 引用计数函数工作正常
- ⏳ 实现变量赋值时的 free 旧值
- ⏳ 实现函数结束时的 free 局部变量

### Phase 2-01-B.11（后续阶段）

- 实现函数参数的 incref/free
- 实现函数返回值的 incref
- 实现容器元素的完整引用计数
- 建立引用计数测试套件
- 内存泄漏检测

### Phase 2-01-C（High-Frame Runtime）

- 多线程环境下的引用计数线程安全
- 弱引用 / 循环引用处理
- 增量式引用计数优化

---

## 七、已知限制

1. **循环引用**: 纯引用计数无法处理循环引用（A→B→A）。当前 TLL 没有 cycle collector，循环引用会导致内存泄漏。
2. **线程安全**: 当前引用计数不是原子操作，不适合多线程环境。High-Frame Runtime 阶段需要处理。
3. **Native Target 不完整**: Native Target 当前没有完整的引用计数管理，长期运行会内存泄漏。

---

## 八、版本历史

| 版本 | 日期 | 阶段 | 变更 |
|------|------|------|------|
| 1.0 | 2026-09-09 | P2-01-B.10 | 初始版本。定义所有权规则、引用计数函数、Bytecode VM vs Native Target 对比、实现路线图。 |

---

**文档结束。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
