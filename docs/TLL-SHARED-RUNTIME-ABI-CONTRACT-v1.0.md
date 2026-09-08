# TLL Shared Runtime ABI Contract v1.0

**版本**: 1.0
**阶段**: Phase 2-01-B.9
**状态**: DRAFT / 待架构师验收
**日期**: 2026-09-09

---

## 一、ABI 概述

TLL Shared Runtime ABI 是 TLL Bytecode VM 和 Native Target 共享的运行时核心接口契约。所有语言基础语义（值表示、引用计数、真值判断、算术、比较、IO）必须在此处统一定义，确保 Bytecode 和 Native 行为完全一致。

**核心原则**: 不建立第二套 Runtime。Shared Runtime Core 是唯一的语义地基。

**ABI 稳定性等级**（B.9 架构师裁决修正）:
- **数据结构布局 (ABI Layout)**: STABLE（二进制兼容，修改需同时更新 host/c/tllvm.h）
- **函数签名 (Function Signature)**: STABLE（新增函数不破坏兼容性，修改签名需版本升级）
- **调用约定 (Calling Convention)**: STABLE（cdecl）
- **语义契约 (Semantic Contract)**: PROVISIONAL（基本语义已验证，但完整语义覆盖待后续阶段）
- **内存所有权 / 引用计数 (Ownership / Refcount)**: OPEN（Native Target 当前不主动管理引用计数，完整所有权规则待 B.10 定义）

---

## 二、数据结构布局

### 2.1 TLLType (enum)

```c
typedef enum {
    TLL_NULL = 0,
    TLL_BOOL = 1,
    TLL_INT = 2,
    TLL_FLOAT = 3,
    TLL_STRING = 4,
    TLL_ARRAY = 5,
    TLL_MAP = 6,
    TLL_FUNCTION = 7,
    TLL_BUILTIN = 8,
    TLL_UPVALUE = 9
} TLLType;
```

**大小**: 4 bytes (int)
**对齐**: 4 bytes

### 2.2 TLLValue (tagged union)

```c
struct TLLValue {
    TLLType type;          // 4 bytes
    union {
        int boolean;        // 4 bytes
        long long integer;  // 8 bytes
        double floating;    // 8 bytes
        char *string;       // 8 bytes (pointer)
        TLLArray *array;    // 8 bytes (pointer)
        TLLMap *map;        // 8 bytes (pointer)
        struct { int fnIdx; TLLClosureEnv *env; } func;  // 16 bytes
        struct { int idx; } builtin;  // 4 bytes
        TLLUpvalue *upvalue;  // 8 bytes (pointer)
    } as;
};
```

**大小**: 24 bytes (type 4 + padding 4 + union 16)
**对齐**: 8 bytes
**二进制兼容**: ✅ 与 host/c/tllvm.h 完全一致

**字符串内存布局**:
```
[int refCount][char data...]
            ↑
         string 指针指向这里
```
通过 `(int*)(s - sizeof(int))` 访问 refcount。

### 2.3 TLLArray

```c
struct TLLArray {
    TLLValue *items;    // 8 bytes (pointer to TLLValue array)
    int length;          // 4 bytes
    int capacity;        // 4 bytes
    int refCount;        // 4 bytes
};
```

**大小**: 24 bytes
**对齐**: 8 bytes

### 2.4 TLLMap (hash table with chaining)

```c
struct TLLMapEntry {
    char *key;           // 8 bytes
    TLLValue value;      // 24 bytes
    TLLMapEntry *next;   // 8 bytes
};

struct TLLMap {
    TLLMapEntry **buckets;  // 8 bytes
    int bucketCount;         // 4 bytes
    int size;                // 4 bytes
    int refCount;            // 4 bytes
};
```

**TLLMapEntry 大小**: 40 bytes (8 + 24 + 8)
**TLLMap 大小**: 24 bytes

### 2.5 TLLUpvalue

```c
struct TLLUpvalue {
    TLLValue value;    // 24 bytes
    int refCount;      // 4 bytes
};
```

**大小**: 32 bytes (24 + 4 + padding 4)

### 2.6 TLLClosureEnv

```c
struct TLLClosureEnv {
    TLLUpvalue **upvalues;  // 8 bytes
    int count;               // 4 bytes
    int capacity;            // 4 bytes
    int refCount;            // 4 bytes
};
```

**大小**: 24 bytes

---

## 三、函数签名与语义

### 3.1 值创建 (Value Creation)

| 函数 | 签名 | 语义 |
|------|------|------|
| `tll_null` | `TLLValue tll_null(void)` | 创建 null 值 |
| `tll_bool` | `TLLValue tll_bool(int b)` | 创建 bool 值（非0=true） |
| `tll_int` | `TLLValue tll_int(long long v)` | 创建 int 值 |
| `tll_float` | `TLLValue tll_float(double v)` | 创建 float 值 |
| `tll_string` | `TLLValue tll_string(const char *s)` | 创建 string 值（复制字符串） |
| `tll_string_n` | `TLLValue tll_string_n(const char *s, int len)` | 创建指定长度的 string 值 |
| `tll_array` | `TLLValue tll_array(void)` | 创建空数组（capacity=8） |
| `tll_array_from` | `TLLValue tll_array_from(TLLValue *items, int count)` | 从 C 数组创建数组（B.9 新增，**当前暂无消费者**，B.10 评估保留或删除） |
| `tll_map` | `TLLValue tll_map(void)` | 创建空 map（bucketCount=16） |
| `tll_function` | `TLLValue tll_function(int fnIdx, TLLClosureEnv *env)` | 创建 function 值 |
| `tll_builtin` | `TLLValue tll_builtin(int idx)` | 创建 builtin 值 |

### 3.2 引用计数 (Reference Counting)

| 函数 | 签名 | 语义 |
|------|------|------|
| `tll_value_incref` | `void tll_value_incref(TLLValue v)` | 增加引用计数（string/array/map/function/upvalue） |
| `tll_value_free` | `void tll_value_free(TLLValue v)` | 减少引用计数，归零时释放内存 |

**所有权规则**:
- 值创建函数返回的 TLLValue 引用计数为 1（调用者拥有）
- 赋值给变量/数组元素/map 值时，应调用 incref
- 变量/数组元素/map 值被覆盖或释放时，应调用 free
- Native Target 当前简化处理：不主动管理引用计数（依赖进程退出时释放）

### 3.3 真值与相等 (Truth & Equality)

| 函数 | 签名 | 语义 |
|------|------|------|
| `tll_truthy` | `int tll_truthy(TLLValue v)` | 判断真值（null/false/0/0.0/空字符串=false，其他=true） |
| `tll_equals` | `int tll_equals(TLLValue a, TLLValue b)` | 判断相等（值相等，非引用相等） |

### 3.4 字符串转换 (String Conversion)

| 函数 | 签名 | 语义 |
|------|------|------|
| `tll_to_string` | `char *tll_to_string(TLLValue v)` | 转换为字符串表示（调用者负责释放） |
| `tll_to_json` | `char *tll_to_json(TLLValue v)` | 转换为 JSON 表示（调用者负责释放） |

### 3.5 算术运算 (Arithmetic Operations)

**语义规则**（与 TLL Bytecode VM 操作码行为一致）:
- int + int = int
- 任一操作数为 float = float
- 字符串 + 字符串 = 字符串拼接
- 除法始终返回 float
- 取模仅支持 int
- 类型错误返回 tll_null()

| 函数 | 签名 |
|------|------|
| `tll_add` | `TLLValue tll_add(TLLValue a, TLLValue b)` |
| `tll_sub` | `TLLValue tll_sub(TLLValue a, TLLValue b)` |
| `tll_mul` | `TLLValue tll_mul(TLLValue a, TLLValue b)` |
| `tll_div` | `TLLValue tll_div(TLLValue a, TLLValue b)` |
| `tll_mod` | `TLLValue tll_mod(TLLValue a, TLLValue b)` |

### 3.6 比较运算 (Comparison Operations)

**返回 TLLValue(TLL_BOOL 类型)**，而非 int。

**语义规则**:
- int/float 可跨类型比较
- 字符串按字典序比较
- 其他类型仅支持 ==/!=（引用相等）
- 不支持的比较返回 false

| 函数 | 签名 |
|------|------|
| `tll_eq` | `TLLValue tll_eq(TLLValue a, TLLValue b)` |
| `tll_neq` | `TLLValue tll_neq(TLLValue a, TLLValue b)` |
| `tll_lt` | `TLLValue tll_lt(TLLValue a, TLLValue b)` |
| `tll_gt` | `TLLValue tll_gt(TLLValue a, TLLValue b)` |
| `tll_le` | `TLLValue tll_le(TLLValue a, TLLValue b)` |
| `tll_ge` | `TLLValue tll_ge(TLLValue a, TLLValue b)` |

### 3.7 Array/Map 操作 (Array/Map Operations)

| 函数 | 签名 | 语义 |
|------|------|------|
| `array_push` | `void array_push(TLLArray *arr, TLLValue v)` | 向数组末尾添加元素 |
| `array_get` | `TLLValue array_get(TLLArray *arr, int idx)` | 获取数组元素（越界返回 null） |
| `array_set` | `void array_set(TLLArray *arr, int idx, TLLValue v)` | 设置数组元素（越界自动扩展） |
| `map_set` | `void map_set(TLLMap *map, const char *key, TLLValue value)` | 设置 map 键值 |
| `map_get` | `TLLValue map_get(TLLMap *map, const char *key)` | 获取 map 值（不存在返回 null） |
| `map_has` | `int map_has(TLLMap *map, const char *key)` | 检查 map 键是否存在 |

**注意**: 这些函数接受 `TLLArray*` / `TLLMap*`，而非 `TLLValue`。调用者需通过 `value.as.array` / `value.as.map` 获取指针。

### 3.8 基础 IO (Basic IO)

| 函数 | 签名 | 语义 |
|------|------|------|
| `tll_io_print` | `void tll_io_print(TLLValue v)` | 打印值（不换行） |
| `tll_io_println` | `void tll_io_println(TLLValue v)` | 打印值（换行） |

### 3.9 运行时生命周期 (Runtime Lifecycle)

| 函数 | 签名 | 语义 |
|------|------|------|
| `tll_runtime_init` | `void tll_runtime_init(void)` | 初始化运行时 |
| `tll_runtime_cleanup` | `void tll_runtime_cleanup(void)` | 清理运行时 |

---

## 四、调用约定

- **调用约定**: cdecl（C 默认调用约定）
- **参数传递**: 栈传递（x86-64 平台前 4 个整数/指针参数用寄存器，浮点参数用 XMM 寄存器）
- **返回值**: TLLValue 通过 RAX 返回（24 bytes，x86-64 平台通过隐藏指针返回）
- **名称修饰**: 无（C 函数名不修饰）
- **异常**: 不使用 C++ 异常，错误通过返回 null 值表示

---

## 五、内存管理规则

### 5.1 引用计数

- 引用计数存储在对象头部（string/array/map/function/upvalue）
- 创建时引用计数为 1
- `tll_value_incref` 增加引用计数
- `tll_value_free` 减少引用计数，归零时释放内存

### 5.2 所有权转移

- 值创建函数返回的 TLLValue 所有权归调用者
- 数组/map 存储元素时，应 incref
- 数组/map 释放时，应 free 所有元素
- Native Target 当前简化处理：不主动管理引用计数

### 5.3 字符串内存

- 字符串使用 `alloc_string_rc` 分配，包含 refCount 头部
- `tll_string` / `tll_string_n` 复制输入字符串
- 字符串释放时，同时释放 refCount 头部和数据

---

## 六、二进制兼容性验证

### 6.1 数据结构布局验证

| 结构 | 预期大小 | 验证状态 |
|------|---------|---------|
| TLLValue | 24 bytes | ✅ 已验证（与 host/c/tllvm.h 一致） |
| TLLArray | 24 bytes | ✅ 已验证 |
| TLLMap | 24 bytes | ✅ 已验证 |
| TLLMapEntry | 40 bytes | ✅ 已验证 |
| TLLUpvalue | 32 bytes | ✅ 已验证 |
| TLLClosureEnv | 24 bytes | ✅ 已验证 |

### 6.2 函数签名验证

| 类别 | 函数数量 | 验证状态 |
|------|---------|---------|
| 值创建 | 11 | ✅ 全部声明 |
| 引用计数 | 2 | ✅ 全部声明 |
| 真值与相等 | 2 | ✅ 全部声明 |
| 字符串转换 | 2 | ✅ 全部声明 |
| 算术运算 | 5 | ✅ 全部声明 |
| 比较运算 | 6 | ✅ 全部声明 |
| Array/Map 操作 | 6 | ✅ 全部声明 |
| 基础 IO | 2 | ✅ 全部声明 |
| 生命周期 | 2 | ✅ 全部声明 |
| **总计** | **38** | ✅ **全部声明** |

### 6.3 语义一致性验证

通过 Cross-Target Conformance Tests 验证 Bytecode 和 Native 语义一致：

| 测试用例 | 覆盖能力 | 状态 |
|---------|---------|------|
| cross_target_minimal | function/let/arithmetic/return/io/string | ✅ PASS |
| 01_basic | arithmetic/comparison/bool | ✅ PASS |
| 02_function | function/params/nested call | ✅ PASS |
| 03_io | string/concat/mixed output | ✅ PASS |
| 04_control_flow | reassignment/while/if-else/nested | ✅ PASS |
| 05_array | array literal/index read/index assign/length/iteration | ✅ PASS |

**总计**: 6/6 PASS ✅

---

## 七、已知限制与未来工作

### 7.1 当前限制

1. **Native Target 引用计数**: 当前 Native Target 不主动管理引用计数，依赖进程退出时释放内存。长期运行的 Native 程序可能存在内存泄漏。
2. **Array/Map 函数接受指针**: `array_push`/`array_get`/`array_set` 等函数接受 `TLLArray*` 而非 `TLLValue`，调用者需手动访问 `value.as.array`。未来可增加接受 `TLLValue` 的包装函数。
3. **异常处理**: Shared Runtime Core 暂不包含异常处理（throw/try/catch/finally）。
4. **协程**: Shared Runtime Core 暂不包含协程支持。
5. **模块系统**: Shared Runtime Core 暂不包含模块加载/链接。

### 7.2 未来工作

1. **Native Target 引用计数管理**: 在 native_lower 生成的代码中插入 incref/free 调用。
2. **TLLValue 包装函数**: 增加接受 `TLLValue` 的 array/map 操作函数。
3. **异常处理收敛**: 将异常处理从 host/c/builtin.c 收敛到 Shared Runtime Core。
4. **协程收敛**: 将协程调度从 host/c/vm.c 收敛到 Shared Runtime Core。
5. **完整 ABI 测试套件**: 建立自动化 ABI 兼容性测试，每次修改后自动验证数据结构大小和函数签名。

---

## 八、版本历史

| 版本 | 日期 | 阶段 | 变更 |
|------|------|------|------|
| 1.0 | 2026-09-09 | P2-01-B.9 | 初始版本。定义 38 个函数、7 个数据结构。6 个 Conformance Tests 全部 PASS。 |
| 1.0.1 | 2026-09-09 | P2-01-B.9 架构师裁决 | 修正 ABI 稳定性等级：Ownership/Refcount = OPEN，Semantic Contract = PROVISIONAL。记录 tll_array_from 暂无消费者，B.10 评估。 |

---

**文档结束。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
