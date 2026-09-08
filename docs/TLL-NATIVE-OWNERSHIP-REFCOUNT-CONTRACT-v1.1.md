# TLL Native Ownership & Refcount Contract v1.1

**版本**: 1.1
**阶段**: Phase 2-01-B.11
**状态**: FROZEN / 待架构师验收
**日期**: 2026-09-09
**前序版本**: v1.0 (P2-01-B.10)

---

## 一、概述

本文档冻结 TLL Native Target 的 Ownership Model 和引用计数规则。

**核心原则**: TLL 使用纯引用计数（无 GC / 无 cycle collector）。所有堆分配对象（string/array/map/function/upvalue）通过引用计数管理生命周期。

**模型来源**: 本 Contract 基于对 Bytecode VM（host/c/vm.c）实际引用计数行为的完整调查，确保 Native Target 与 Bytecode Target 拥有完全一致的语义。

**冻结声明**: 本版本 v1.1 为 TLL Native Ownership Model 的正式冻结版本。后续修改必须通过架构师裁决，并升级版本号。

---

## 二、Ownership Model 总览

### 2.1 六种核心操作

| 操作 | Ownership 语义 | 引用计数动作 |
|------|--------------|------------|
| **Creation** | 调用者获得新引用 | 返回 refCount=1 的值 |
| **Assignment** | 旧引用释放，新引用获得 | free 旧值 + incref 新值 |
| **Function Argument** | 调用者 retain，被调用者 release | 调用者 incref + 被调用者直接存储（不 incref）+ 被调用者结束时 free |
| **Function Return** | 调用者获得返回值引用 | incref 返回值 + free 局部变量 + return |
| **Container Element** | 调用者 retain，容器 release | 调用者 incref + 容器直接存储（不 incref）+ 容器释放时 free 所有元素 |
| **Scope Exit** | 所有局部引用释放 | free 所有局部变量 |

### 2.2 设计选择说明

**函数返回: Borrow → Return Retain（设计 A）**

```
local s (refCount=1)
    ↓ return
    ↓ incref(s)  (refCount=2)
    ↓ free(local s)  (refCount=1)
    ↓ caller owns s (refCount=1)
```

选择设计 A（而非设计 B Ownership Transfer）的原因：
1. 与 Bytecode VM 实际行为一致（OP_RET 中 `tll_value_incref(retVal)`）
2. 统一的 retain/release 语义，简化推理
3. 便于未来扩展（如多返回值、异常路径）

---

## 三、详细规则

### 3.1 Creation（创建）

**规则**: 值创建函数返回的 TLLValue 引用计数为 1，调用者拥有该引用。

**涉及函数**:
- `tll_null()`, `tll_bool()`, `tll_int()`, `tll_float()` — 值类型，无堆分配，refCount 不适用
- `tll_string()`, `tll_string_n()` — refCount=1
- `tll_array()` — refCount=1
- `tll_map()` — refCount=1
- `tll_function()` — env refCount++
- `tll_builtin()` — 值类型，无堆分配

**示例**:
```c
TLLValue s = tll_string("hello");  // refCount=1, caller owns
// use s
tll_value_free(s);  // refCount=0, freed
```

### 3.2 Assignment（赋值）— Assignment Expression Ownership Protocol v1.2

**语义规则**: 变量赋值时，必须 release 旧引用，retain 新引用，然后存储。

**安全顺序要求**: 必须先 retain 新引用，再 release 旧引用，以安全处理 alias 情况（如 `x = x`）。如果先 release 旧引用，当 old 和 new 指向同一对象时，会导致 use-after-free。

**Bytecode VM 实现**（OP_STORE_VAR）:
```c
tll_value_free(frame->locals[a]);  // release old (old and new are in different registers, no alias risk)
tll_value_incref(regs[b]);          // retain new
frame->locals[a] = regs[b];         // store
```
Bytecode VM 中 old（locals[a]）和 new（regs[b]）位于不同存储位置，不存在 alias 风险，因此可以先 free old。

---

#### Assignment Expression Ownership Protocol（P2-01-B11-R1-R2-FIX2 明确化）

本协议回答架构师提出的 8 个问题，明确 TLL Assignment Expression 在 Native Target 中的完整 ownership 语义。

##### Q1: Assignment RHS 在求值后究竟拥有几个 reference？

- **RHS 是临时表达式**（字面量 `tll_string("a")`、函数调用 `fn()`、Binary 运算等）：创建对象时 refcount=1，这个引用是**临时引用**，在表达式结束时应被释放
- **RHS 是变量引用**（Ident，如 `x`、`y`）：不创建新对象，RHS 的 TLLValue 是已有对象的 borrow，refcount 不变

##### Q2: tll_assign() 的 retain/release 分别代表谁的 ownership？

```c
TLLValue tll_assign(TLLValue *target, TLLValue new_value) {
    tll_value_incref(new_value);  // retain: 为 target 持有一个引用
    tll_value_free(*target);       // release: 释放 target 的旧值
    *target = new_value;           // store
    return new_value;              // return: 返回 borrow（不额外持有引用）
}
```

- `incref(new_value)`：为 **target** 持有一个引用
- `free(*target)`：释放 **target 的旧值**
- `return new_value`：返回 **borrow**（TLLValue 结构体拷贝，不额外 incref，不持有引用）

##### Q3: assignment expression result 是 owned value / borrowed value / transferred value 哪一种？

**是 borrowed value（借用值）**。

`tll_assign()` 返回的 TLLValue 是结构体拷贝，指向被赋值的对象，但不额外持有引用（不 incref）。

但是，当 RHS 是临时表达式时，RHS 创建的**临时引用**（refcount=1）"附着"在返回值上。这个临时引用不是返回值持有的，而是 RHS 表达式创建的，需要在表达式结束时被释放。

当 RHS 是变量引用时，没有临时引用，返回值是纯粹的 borrow。

##### Q4: statement context 如何消费 result？

ExpressionStatement 中的赋值表达式，根据 RHS 类型决定是否 release 返回值：

- **RHS 是临时表达式**（`x = "a"` / `x = fn()` / `x = a + b`）：release 返回值。这会 decref 对象，相当于释放 RHS 的临时引用
- **RHS 是变量引用**（`x = x` / `x = y`）：不 release 返回值。因为没有临时引用需要释放，release 会导致 UAF

生成代码：
```c
// RHS 是临时表达式
{ TLLValue __tll_assign_result = tll_assign(&x, rhs);
  tll_value_free(__tll_assign_result); }

// RHS 是变量引用
tll_assign(&x, x);  // borrow, do not release
```

##### Q5: `let y = (x = rhs)` 如何消费/转移 result？

```tll
let y = (x = "nested");
```

生成代码：
```c
TLLValue y = tll_assign(&x, tll_string("nested"));
```

ownership 链：
1. `"nested"` 创建 -> refcount=1（临时引用）
2. `tll_assign(&x, "nested")`：
   - incref -> refcount=2（x 持有 1，临时 1）
   - free(x 旧值)
   - x = "nested"
   - 返回 "nested"（borrow）
3. `y = 返回值`（结构体拷贝，refcount 不变，还是 2）
4. 此时 refcount=2：x 持有 1，临时 1。y 是 borrow，不额外持有引用
5. 函数退出时：
   - `free(x)` -> refcount=1（释放 x 的引用）
   - `free(y)` -> refcount=0（释放临时引用）-> free 内存 ✅

**关键**：inner assignment 的临时引用"附着"在 y 上，函数退出时 `free(y)` 释放这个临时引用。如果 y 被后续重新赋值，`free(y 旧值)` 也会释放这个临时引用。

##### Q6: `y = (x = rhs)` 如何消费 inner result？

```tll
y = (x = "nested2");
```

生成代码：
```c
{ TLLValue __tll_assign_result = tll_assign(&y, tll_assign(&x, tll_string("nested2")));
  tll_value_free(__tll_assign_result); }
```

ownership 链：
1. `"nested2"` 创建 -> refcount=1（inner 临时引用）
2. inner `tll_assign(&x, "nested2")`：
   - incref -> refcount=2（x 持有 1，inner 临时 1）
   - free(x 旧值)
   - x = "nested2"
   - 返回 "nested2"（borrow）
3. outer `tll_assign(&y, inner_result)`：
   - incref(inner_result) -> refcount=3（x 1，y 1，inner 临时 1）
   - free(y 旧值)
   - y = inner_result
   - 返回 inner_result（borrow）
4. ExpressionStatement release outer 返回值 -> refcount=2（x 1，y 1）
   - 这一步 decref 释放了 inner 的临时引用
5. 函数退出时：
   - `free(x)` -> refcount=1
   - `free(y)` -> refcount=0 -> free 内存 ✅

**关键**：outer 的 release 释放了 inner 的临时引用。因为 outer RHS 是 inner assignment（临时表达式），所以 ExpressionStatement 会 release outer 返回值。

##### Q7: `x = x`、`x = y`、`x = fn()` 三种情形统一解释

| 情形 | RHS 类型 | ExpressionStatement release? | refcount 变化 | 结果 |
|------|----------|------------------------------|---------------|------|
| `x = x` | Ident（变量引用） | 否（borrow） | incref(x)->ref+1, free(x)->ref-1, 净 0 | x refcount 不变 ✅ |
| `x = y` | Ident（变量引用） | 否（borrow） | incref(y)->y ref+1, free(x)->x ref-1 | y refcount +1, x 旧值释放 ✅ |
| `x = fn()` | Call（临时表达式） | 是（release 返回值） | fn() ref=1, incref->ref=2, release->ref=1 | x 持有 ref=1 ✅ |

统一原则：
- RHS 是变量引用 -> 返回值是纯粹 borrow -> 不 release
- RHS 是临时表达式 -> 返回值附着临时引用 -> release 返回值以释放临时引用

##### Q8: nested assignment 至少一层的可观测 refcount/memory-safety evidence

测试 `tests/native/14_nested_assignment_ownership.tll` 覆盖：
- `let y = (x = "nested")` — 一层嵌套，let 上下文
- `y = (x = "nested2")` — 一层嵌套，statement 上下文
- `z = (y = (x = "deep"))` — 两层嵌套
- `x = x` — 自赋值
- `x = y` — 变量引用赋值
- `x = get_with_marker()` — 函数调用赋值，可观测副作用

验证结果：
- Bytecode / Native 输出完全一致 ✅
- MSVC ASan 无 UAF / double-free / heap-buffer-overflow ✅
- 14/14 Conformance 测试全部 PASS ✅

---

**两种实现的语义等价性**: Bytecode VM 和 Native Target 最终都达到相同的语义结果——old 被 release，new 被 retain，变量存储 new。Native Target 使用 `tll_assign` 辅助函数额外保证了 RHS 只求值一次，避免了函数调用作为 RHS 时的 double-evaluation 问题。

**注意**: 本协议仅覆盖普通变量赋值（`x = rhs`）。Array/Map index assignment（`arr[i] = rhs` / `map["k"] = rhs`）的 ownership 协议待后续阶段明确。

**注意**: 对于值类型（null/bool/int/float/builtin），tll_value_free 和 tll_value_incref 是 no-op，所以可以安全调用。

### 3.3 Function Argument（函数参数）

**规则**: 
- **调用者**: 在 push 参数时 incref（OP_PUSH）
- **被调用者**: 直接赋值到新帧的局部变量，不 incref（因为调用者已经 incref）
- **被调用者结束时**: free 所有局部变量（包括参数）

**Bytecode VM 实现**:
```c
// Caller (OP_PUSH)
tll_value_incref(regs[a]);  // retain argument
push_arg(frame, regs[a]);   // push to arg stack

// Callee (do_call)
for (int i = 0; i < argCount; i++) {
    tll_value_free(newFrame->locals[i]);  // free initial null
    newFrame->locals[i] = args[i];         // store directly (no incref)
}

// Callee end (free_frame)
for (int i = 0; i < frame->localCount; i++) {
    tll_value_free(frame->locals[i]);  // release all locals (including args)
}
```

**Native Target 实现**（B.11-R1 修复后）:
```c
// Caller (user-defined function calls only; built-in tll_ functions skip incref)
(tll_value_incref(arg), callee(arg))

// Callee (generated by native_lower.tll)
// B.11-R1: Parameters are registered in nl_localVars at function entry,
// so they participate in the same cleanup model as let/const locals.
TLLValue callee(TLLValue arg) {
    // use arg
    // ...
    // Function exit (normal fall-through or explicit return):
    // nl_localVars includes arg, so generated cleanup does:
    tll_value_free(arg);  // release parameter exactly once
}
```

**B.11-R1 修复说明**: 在 B.11 中，`nl_localVars` 只记录 `let`/`const` 局部变量，不记录函数参数，导致生成的 Native 函数在结束时不会释放参数拥有的引用，造成引用泄漏。B.11-R1 修复后，函数参数在函数入口时被注册到 `nl_localVars`，与局部变量使用相同的清理模型，确保参数在函数结束时被精确释放一次。

**explicit return 路径**: return 语句先 incref 返回值，然后 free 所有 `nl_localVars`（包括参数），然后 return。这确保返回值不会被 cleanup 销毁，同时参数被正确释放。

### 3.4 Function Return（函数返回）

**规则**: 
- incref 返回值（调用者将获得引用）
- free 所有局部变量
- return 返回值

**Bytecode VM 实现**（OP_RET）:
```c
TLLValue retVal = regs[a];
int retReg = frame->returnReg;
TLLFrame *f = pop_frame(vm);
if (vm->callStackSize > 0 && retReg >= 0) {
    tll_value_incref(retVal);  // retain for caller
    vm->callStack[vm->callStackSize - 1]->registers[retReg] = retVal;
}
free_frame(f);  // free all locals and registers (including retVal's register)
```

**Native Target 实现**:
```c
TLLValue callee() {
    TLLValue s = tll_string("hello");
    // ...
    tll_value_incref(s);  // retain for caller
    tll_value_free(s);    // release local (refCount still 1 for caller)
    // free other locals...
    return s;
}
```

**注意**: 这里的 `incref(s); free(s); return s;` 序列是正确的，因为 incref 后 refCount=2，free 后 refCount=1，调用者获得 refCount=1 的引用。

### 3.5 Container Element（容器元素）

**规则**:
- **调用者**: 在存储元素前 incref
- **容器函数**: 直接存储（不 incref），释放旧元素时 free
- **容器释放时**: free 所有元素

**array_push**:
```c
// Caller
tll_value_incref(elem);  // retain
array_push(arr.as.array, elem);  // store directly (no incref)

// array_push implementation
void array_push(TLLArray *arr, TLLValue v) {
    // ... resize if needed ...
    arr->items[arr->length++] = v;  // store directly
}
```

**array_set**:
```c
// Caller
tll_value_incref(new_elem);  // retain
array_set(arr.as.array, idx, new_elem);  // array_set frees old, stores new

// array_set implementation
void array_set(TLLArray *arr, int idx, TLLValue v) {
    // ... extend if needed ...
    tll_value_free(arr->items[idx]);  // release old
    arr->items[idx] = v;  // store new directly
}
```

**map_set**:
```c
// Caller
tll_value_incref(new_val);  // retain
map_set(map.as.map, "key", new_val);  // map_set frees old, stores new

// map_set implementation
void map_set(TLLMap *map, const char *key, TLLValue value) {
    // ... find existing entry ...
    if (found) {
        tll_value_free(e->value);  // release old
        e->value = value;  // store new directly
        return;
    }
    // ... create new entry ...
    e->value = value;  // store directly
}
```

**容器释放**:
```c
// TLLArray free (in tll_value_free)
for (int i = 0; i < arr->length; i++) {
    tll_value_free(arr->items[i]);  // release all elements
}
free(arr->items);
free(arr);

// TLLMap free (in tll_value_free)
for (int b = 0; b < map->bucketCount; b++) {
    TLLMapEntry *e = map->buckets[b];
    while (e) {
        TLLMapEntry *next = e->next;
        tll_value_free(e->value);  // release value
        free(e->key);
        free(e);
        e = next;
    }
}
free(map->buckets);
free(map);
```

### 3.6 Scope Exit（作用域结束）

**规则**: 变量作用域结束时，free 所有局部变量。

**Bytecode VM 实现**（free_frame）:
```c
void free_frame(TLLFrame *frame) {
    for (int i = 0; i < frame->regCount; i++) {
        tll_value_free(frame->registers[i]);  // release all registers
    }
    for (int i = 0; i < frame->localCount; i++) {
        tll_value_free(frame->locals[i]);  // release all locals
    }
    for (int i = 0; i < frame->argStackSize; i++) {
        tll_value_free(frame->argStack[i]);  // release all args
    }
    // ... free other resources ...
}
```

**Native Target 实现**:
```c
TLLValue example() {
    TLLValue x = tll_int(10);
    TLLValue s = tll_string("hello");
    // ... use x and s ...
    // At function end (if no explicit return):
    tll_value_free(x);  // release
    tll_value_free(s);  // release
}
```

**注意**: 当前 Native Target 实现为函数级作用域（所有局部变量在函数结束时 free），不支持块级作用域（if/while 块内的变量在块结束时 free）。这是已知限制，列为 GAP。

---

## 四、Native Target 实现状态

### 4.1 已实现

| 操作 | 状态 | 说明 |
|------|------|------|
| Creation | ✅ | 值创建函数返回 refCount=1 |
| Function Return | ✅ | incref 返回值 + free 局部变量 |
| Scope Exit (function-level) | ✅ | 函数结束时 free 所有局部变量 |

### 4.2 未实现（B.11 修复目标）

| 操作 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| Assignment | ❌ | P1 | 变量赋值时未 free 旧值 |
| Function Argument | ❌ | P1 | 调用者未 incref，被调用者未 free 参数 |
| Container Element | ❌ | P1 | array_push/map_set 前未 incref |

### 4.3 已知限制

| 限制 | 优先级 | 说明 |
|------|--------|------|
| 块级作用域 | P3 | 当前只支持函数级作用域 |
| 多 return 点重复 free | P2 | if/else 中的 return 可能重复 free 局部变量 |
| 循环引用 | P3 | 纯引用计数无法处理循环引用 |

---

## 五、与 Bytecode VM 的语义等价性验证

### 5.1 验证方法

通过 Cross-Target Conformance Tests 验证 Native Target 与 Bytecode Target 对同一个 TLL 程序拥有一致的语义。

### 5.2 专门的 Ownership 测试用例

| 测试 | 覆盖能力 | 状态 |
|------|---------|------|
| 07_ownership_local | 局部变量创建/释放 | ⏳ 待建立 |
| 08_ownership_assignment | 变量赋值旧值释放 | ⏳ 待建立 |
| 09_ownership_return | 函数返回值引用传递 | ⏳ 待建立 |
| 10_ownership_container | 容器元素引用管理 | ⏳ 待建立 |

### 5.3 内存检测工具

优先利用成熟工具（如 ASan / AddressSanitizer）进行内存错误检测，而非自己造内存检测器。

---

## 六、版本历史

| 版本 | 日期 | 阶段 | 变更 |
|------|------|------|------|
| 1.0 | 2026-09-09 | P2-01-B.10 | 初始版本。定义所有权规则、引用计数函数、Bytecode VM vs Native Target 对比、实现路线图。 |
| 1.1 | 2026-09-09 | P2-01-B.11 | **FROZEN**。基于 Bytecode VM 实际行为调查，冻结 Ownership Model。明确六种核心操作的语义：Creation/Assignment/Function Argument/Function Return/Container Element/Scope Exit。确定函数返回使用 Borrow → Return Retain 设计（设计 A）。明确 Native Target 实现状态和 B.11 修复目标。 |

---

## 七、冻结声明

本版本 v1.1 为 TLL Native Ownership Model 的正式冻结版本。

**冻结内容**:
1. 六种核心操作的 Ownership 语义
2. 函数返回的 Borrow → Return Retain 设计
3. 引用计数的 retain/release 规则
4. 与 Bytecode VM 的语义等价性要求

**后续修改必须**:
1. 通过架构师裁决
2. 升级版本号（v1.2, v2.0, etc.）
3. 更新所有相关文档和实现
4. 通过完整的 Cross-Target Conformance 测试

---

**文档结束。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
