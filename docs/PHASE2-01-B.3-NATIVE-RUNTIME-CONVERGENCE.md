# PHASE 2-01-B.3 — Native Runtime Convergence & Cross-Target Contract

**施工队**: 豆包 A
**阶段**: Phase 2 / P2-01-B Native Backend Foundation
**基线**: b32dc67
**日期**: 2026-09-09
**状态**: Architecture PASS / Engineering Foundation / 不封板

---

## 一、执行摘要

本阶段核心目标：**不建立第二套长期维护的 TLL Runtime**，优先复用、抽象和收敛现有 host/c/ 资产，并建立 Bytecode/Native 双 Target 语义一致性测试框架。

### 核心结论

1. **host/c/ Runtime 是成熟资产**：包含完整的 TLLValue、引用计数、Array/Map、JSON、146+ 内置函数、VM、协程调度、SQLite/Crypto/HTTP/FFI 扩展，总计 ~250KB C 源码（不含 sqlite3）。
2. **native/runtime/ 当前是独立最小实现**：~14KB，与 host/c/value.c 有大量功能重叠，存在变成"第二套 TLL Runtime"的风险。
3. **正确架构**：Shared TLL Runtime Core + 多 Target 前端（Bytecode VM / Native C Code），而不是两套独立 Runtime。
4. **Cross-Target Conformance Test 框架已建立**：同一 TLL Source → Bytecode Target (VM) vs Native Target (CPU)，比较输出/return 值一致性。
5. **Native Target 最小执行已验证**：return 42 链路完整（TLL → Compiler → native_lower → C → MSVC → Native EXE → CPU → 42）。
6. **native_lower.tll 仍有 GAP**：函数调用参数、io.println 解析、Return 节点结构等问题需后续修复，记录为 GAP，不阻塞本阶段架构收敛。

---

## 二、host/c/ Runtime Reality Inventory

### 2.1 文件清单与规模

| 文件 | 大小 | 功能 |
|------|------|------|
| tllvm.h | 9.5 KB | 核心头文件：TLLValue/Array/Map/Closure/Program/Frame/Coroutine/VM 定义，63 操作码，函数声明 |
| value.c | 14.4 KB | 值操作：创建/引用计数/释放/toString/toJSON/truthy/equals，Array/Map 操作 |
| json.c | 11.0 KB | JSON 解析器，程序加载器 |
| vm.c | 60.1 KB | VM 解释器：63 操作码执行，调用栈，异常处理，协程调度 |
| builtin.c | 83.3 KB | 146 内置函数：math/string/array/convert/fs/process/coroutine/channel |
| main.c | 2.0 KB | tllvm.exe 入口 |
| crypto_builtin.c | 11.1 KB | 密码学内置（SHA/HMAC 等） |
| hmac_builtin.c | 10.9 KB | HMAC-SHA256 内置 |
| password_builtin.c | 27.9 KB | 密码哈希（bcrypt 等） |
| http_client_builtin.c | 42.0 KB | HTTP 客户端内置 |
| ffi_builtin.c | 9.9 KB | FFI 内置 |
| sqlite_builtin.c | 9.0 KB | SQLite 内置绑定 |
| sqlite3.c/h | 9,770 KB | SQLite  amalgamation |

**总计（不含 sqlite3）**：~293 KB C 源码
**tllvm.exe**：1,346 KB（MSVC 构建）

### 2.2 核心数据结构（tllvm.h）

```
TLLValue (tagged union, 10 types)
├── TLL_NULL
├── TLL_BOOL
├── TLL_INT (long long)
├── TLL_FLOAT (double)
├── TLL_STRING (char* + length + refcount)
├── TLL_ARRAY (TLLArray* + refcount)
├── TLL_MAP (TLLMap* + refcount)
├── TLL_FUNCTION (fnIdx + closureEnv)
├── TLL_BUILTIN (idx)
└── TLL_STRUCT (TLLMap* 复用)

TLLArray: elements[], count, capacity, refcount
TLLMap: entries[], count, capacity, refcount
TLLClosureEnv: upvalues[], upvalueCount, refcount
TLLUpvalue: value*, closed, value
```

### 2.3 值操作 API（value.c）

| 类别 | 函数 |
|------|------|
| 创建 | tll_null, tll_bool, tll_int, tll_float, tll_string, tll_string_n, tll_array, tll_map, tll_function, tll_builtin |
| 引用计数 | tll_value_incref, tll_value_free |
| 转换 | tll_to_string, tll_to_json, tll_truthy, tll_equals |
| Array | array_push, array_get, array_set |
| Map | map_set, map_get, map_has |

### 2.4 内置函数分类（builtin.c，0-149）

| 索引范围 | 类别 | 数量 | 代表函数 |
|----------|------|------|----------|
| 0-4 | 基础 IO | 5 | print, println, input |
| 5-23 | math | 19 | sqrt, abs, floor, ceil, round, min, max, pow, sin, cos, tan, log, exp, PI, E, random |
| 24-48 | string | 25 | length, toUpper, toLower, trim, split, join, contains, startsWith, endsWith, substring, replace, replaceAll, repeat, padStart, padEnd, charAt, charCodeAt, indexOf, lastIndexOf, isEmpty, reverse, lines, words |
| 49-71 | array | 23 | length, get, push, pop, shift, unshift, concat, slice, includes, indexOf, join, reverse, sort, filter, map, reduce, forEach, find, some, every, flat, fill, range |
| 72-78 | convert | 7 | toInt, toFloat, toString, toBool, toChar, charCode, typeOf |
| 79-90 | fs | 12 | readFile, writeFile, appendFile, exists, mkdir, remove, listDir, isFile, isDir, fileSize, copyFile, rename |
| 91-149 | process/coroutine/channel/其他 | ~59 | process.argv, process.exit, coroutine.spawn, coroutine.yield, coroutine.sleep, channel.make, channel.send, channel.receive |

### 2.5 扩展内置函数

| 索引范围 | 模块 | 文件 |
|----------|------|------|
| 150-159 | SQLite | sqlite_builtin.c |
| 160-179 | Crypto | crypto_builtin.c |
| 180-189 | Password Hashing | password_builtin.c |
| 190-199 | HMAC-SHA256 | hmac_builtin.c |
| 200-209 | HTTP Client | http_client_builtin.c |
| 210-219 | FFI | ffi_builtin.c |

### 2.6 VM 执行模型（vm.c）

- **寄存器机**：每帧 4096 寄存器
- **帧池**：64 → 512 动态扩容
- **调用栈**：TLLFrame 数组，动态扩容
- **异常处理**：tryStack + pending_exception + exception_pending
- **协程**：协作式，per-VM 调度器，支持 sleep/IO wait/channel wait
- **引用计数**：纯 RC，无 GC，无 cycle collector

---

## 三、native/runtime/ 当前状态

### 3.1 文件清单

| 文件 | 大小 | 功能 |
|------|------|------|
| tll_native.h | 3.9 KB | TLLValue 定义（与 host/c/ 一致）、值创建函数、Array/Map 操作、引用计数、IO、算术、比较接口 |
| tll_native.c | 10.2 KB | 最小实现：值创建、引用计数、Array/Map、IO、算术/比较运算 |

### 3.2 与 host/c/ 的功能重叠

| 功能 | host/c/ | native/runtime/ | 重叠程度 |
|------|---------|-----------------|----------|
| TLLValue 定义 | tllvm.h | tll_native.h | 100% |
| 值创建（tll_int/tll_string/...） | value.c | tll_native.c | 100% |
| 引用计数（incref/free） | value.c | tll_native.c | 100% |
| Array 操作 | value.c | tll_native.c | 100% |
| Map 操作 | value.c | tll_native.c | 100% |
| toString | value.c | tll_native.c | 部分 |
| IO（println） | builtin.c + host_println | tll_native.c | 部分 |
| 算术运算 | vm.c (OP_ADD 等) | tll_native.c | 100% |
| 比较运算 | vm.c (OP_EQ 等) | tll_native.c | 100% |
| JSON 解析 | json.c | ❌ 无 | 0% |
| VM 执行 | vm.c | ❌ 无（Native 不需要） | N/A |
| 内置函数 | builtin.c + 扩展 | ❌ 无 | 0% |
| 协程调度 | vm.c | ❌ 无 | 0% |

### 3.3 风险评估

**当前 native/runtime/ 存在变成"第二套 TLL Runtime"的风险**：
- 如果继续在 tll_native.c 中实现 JSON、内置函数、协程等，将与 host/c/ 形成两套独立维护的 Runtime
- 两套 Runtime 必然产生语义漂移（Bytecode: map行为A，Native: map行为B）
- 维护成本翻倍，且无法保证语义一致性

---

## 四、Runtime Convergence 架构设计

### 4.1 核心原则

**不建立第二套长期维护的 TLL Runtime。优先复用、抽象和收敛现有 host/c/ 资产。**

### 4.2 目标架构

```
                    TLL Language Semantics
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       Bytecode Target           Native Target
              ↓                         ↓
       TLL VM (vm.c)          C Code (native_lower.tll)
              ↓                         ↓
              └───────────┬─────────────┘
                          ↓
              ┌───────────────────────┐
              │  Shared TLL Runtime   │
              │  Core (可复用层)       │
              │                       │
              │  ┌─────────────────┐  │
              │  │ value.c         │  │  ← TLLValue, 引用计数, Array/Map
              │  │ json.c          │  │  ← JSON 解析
              │  │ tll_runtime.h   │  │  ← 统一头文件
              │  └─────────────────┘  │
              │                       │
              │  ┌─────────────────┐  │
              │  │ builtin_core.c  │  │  ← 与 Target 无关的内置函数
              │  │ (math/string/   │  │     (math, string, array, convert)
              │  │  array/convert) │  │
              │  └─────────────────┘  │
              └───────────────────────┘
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
       Bytecode-specific       Native-specific
       (vm.c, 63 opcodes)      (C main, MSVC/GCC)
```

### 4.3 分层复用策略

| 层级 | 模块 | 复用策略 | 说明 |
|------|------|----------|------|
| L0 核心数据 | TLLValue, TLLArray, TLLMap | **直接复用** | 从 tllvm.h 提取到 tll_runtime.h，两个 Target 共用 |
| L1 值操作 | value.c | **直接复用** | 值创建、引用计数、Array/Map 操作、toString、truthy、equals |
| L2 JSON | json.c | **直接复用** | JSON 解析、程序加载 |
| L3 内置函数（纯计算） | math, string, array, convert | **抽象复用** | 提取为 builtin_core.c，不依赖 VM 状态 |
| L4 内置函数（IO/系统） | fs, process, network | **Target 适配** | Bytecode 用 host_*，Native 用系统调用/C 标准库 |
| L5 VM 执行 | vm.c | **Bytecode 专用** | Native 不需要 VM 解释器 |
| L6 协程调度 | vm.c (scheduler) | **后续统一** | High-Frame Runtime 阶段统一处理 |
| L7 扩展内置 | crypto, http, sqlite, ffi | **按需复用** | Native Target 可直接链接相同的 .c 文件 |

### 4.4 具体收敛步骤（建议，不在本阶段执行）

**Step 1**: 创建 `runtime/tll_runtime.h`（从 tllvm.h 提取核心数据结构和值操作声明）
**Step 2**: 创建 `runtime/value.c`（从 host/c/value.c 复制，移除 VM 依赖）
**Step 3**: 创建 `runtime/json.c`（从 host/c/json.c 复制）
**Step 4**: 修改 `native/runtime/tll_native.h` 包含 `runtime/tll_runtime.h`
**Step 5**: 修改 `native/runtime/tll_native.c` 调用 runtime/value.c 的函数，删除重复实现
**Step 6**: 修改 `host/c/tllvm.h` 包含 `runtime/tll_runtime.h`
**Step 7**: 验证 Bytecode Target 和 Native Target 都能正常工作

---

## 五、TLL Native Runtime ABI 定义

### 5.1 ABI 原则

1. **与 Bytecode Target 语义一致**：TLLValue 表示、引用计数、Array/Map 行为必须完全相同
2. **C 友好**：使用标准 C 类型，便于 MSVC/GCC/Clang 编译
3. **可扩展**：预留 Future/Closure/Exception 等高级类型的接口
4. **平台无关**：核心 ABI 不依赖特定 OS，平台相关部分隔离

### 5.2 核心 ABI（当前已定义在 tll_native.h）

```c
// 值类型
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
    TLL_STRUCT = 9
} TLLType;

// TLLValue (与 host/c/ 完全一致)
typedef struct {
    TLLType type;
    union {
        int boolean;
        long long integer;
        double floating;
        struct { char* data; int length; int refcount; } *string;
        struct { TLLValue* elements; int count; int capacity; int refcount; } *array;
        struct { ... } *map;
        struct { int fnIdx; void* closureEnv; } function;
        int builtin;
    } as;
} TLLValue;

// 值创建
TLLValue tll_null(void);
TLLValue tll_bool(int b);
TLLValue tll_int(long long v);
TLLValue tll_float(double v);
TLLValue tll_string(const char* s);

// 引用计数
void tll_value_incref(TLLValue v);
void tll_value_free(TLLValue v);

// 真值判断
int tll_truthy(TLLValue v);

// 算术运算
TLLValue tll_add(TLLValue a, TLLValue b);
TLLValue tll_sub(TLLValue a, TLLValue b);
TLLValue tll_mul(TLLValue a, TLLValue b);
TLLValue tll_div(TLLValue a, TLLValue b);
TLLValue tll_mod(TLLValue a, TLLValue b);

// 比较运算
TLLValue tll_eq(TLLValue a, TLLValue b);
TLLValue tll_neq(TLLValue a, TLLValue b);
TLLValue tll_lt(TLLValue a, TLLValue b);
TLLValue tll_gt(TLLValue a, TLLValue b);
TLLValue tll_le(TLLValue a, TLLValue b);
TLLValue tll_ge(TLLValue a, TLLValue b);

// IO
void tll_io_println(TLLValue v);
void tll_io_print(TLLValue v);

// 生命周期
void tll_native_init(void);
void tll_native_cleanup(void);
```

### 5.3 待扩展 ABI（后续阶段）

| 类别 | 待扩展接口 | 优先级 |
|------|-----------|--------|
| String | tll_string_concat, tll_string_substring, tll_string_length | P1 |
| Array | tll_array_push, tll_array_get, tll_array_set, tll_array_length | P1 |
| Map | tll_map_set, tll_map_get, tll_map_has, tll_map_length | P1 |
| Function | tll_function_call, tll_closure_create | P2 |
| Exception | tll_throw, tll_catch, tll_finally | P2 |
| JSON | tll_json_parse, tll_json_stringify | P1 |
| Conversion | tll_to_int, tll_to_float, tll_to_string, tll_typeof | P1 |

---

## 六、Cross-Target Conformance Test 框架

### 6.1 框架目标

验证同一 TLL Source 在 Bytecode Target 和 Native Target 上产生**完全一致**的可观测结果（输出 + return 值）。

### 6.2 测试流程

```
TLL Source (.tll)
    │
    ├──→ Bytecode Target
    │       ├── tllc.tllbc compile → .tllbc
    │       └── tllvm.exe → output + exit_code
    │
    └──→ Native Target
            ├── TLL Compiler (compileNative) → .c
            ├── MSVC/GCC compile + link tll_native.c → .exe
            └── .exe → output + exit_code
    │
    └──→ 比较: output 一致 && exit_code 一致 → PASS
```

### 6.3 测试目录结构

```
native/conformance/
├── framework/
│   ├── run_bytecode.sh      # Bytecode Target 运行脚本
│   ├── run_native.sh        # Native Target 运行脚本
│   └── compare.sh           # 结果比较脚本
├── tests/
│   ├── batch1_basic.tll     # 第一批：int/bool/string/arithmetic/comparison/function/return/io
│   ├── simple_return.tll    # 简化版：通过 return 值验证
│   └── ...
└── expected/
    ├── batch1_basic.txt     # Bytecode Target 预期输出（作为基准）
    └── ...
```

### 6.4 第一批测试覆盖范围

| 测试项 | 覆盖能力 | Bytecode | Native | 状态 |
|--------|----------|----------|--------|------|
| simple_return | int, arithmetic, function call, return, comparison, if | ✅ | ⚠️ 部分 | Native 有函数调用参数 GAP |
| batch1_basic | int, bool, string, arithmetic, comparison, function call, return, io.println | ✅ | ⚠️ 部分 | Native 有 io.println 解析 GAP |

---

## 七、Native Target 当前能力边界

### 7.1 native_lower.tll 已支持

| 能力 | 状态 | 说明 |
|------|------|------|
| 函数声明/定义 | ✅ | 支持参数、返回类型（统一为 TLLValue） |
| let/const 变量 | ✅ | TLLValue 类型 |
| return | ⚠️ 部分 | Return 节点参数结构需确认 |
| if/else | ✅ | 支持 Block 节点体 |
| while | ✅ | 支持 Block 节点体 |
| 整数常量 | ✅ | tll_int() 包装 |
| 浮点常量 | ✅ | tll_float() 包装 |
| 字符串常量 | ✅ | tll_string("...") 包装，已修复引号 |
| 布尔常量 | ✅ | tll_bool() 包装 |
| null | ✅ | tll_null() 包装 |
| 变量引用 | ✅ | Ident 节点 |
| 二元运算（算术） | ✅ | + - * / % → tll_add 等 |
| 二元运算（比较） | ✅ | == != < > <= >= → tll_eq 等 |
| 二元运算（逻辑） | ✅ | && \|\| → tll_bool(tll_truthy() && ...)，本次新增 |
| 一元运算 | ✅ | ! → tll_bool(!tll_truthy())，- → tll_int(-...)，本次新增 |
| 函数调用 | ⚠️ 部分 | 参数丢失（Call 节点 arguments 结构问题） |
| 成员访问 | ⚠️ 部分 | io.println 解析问题（Member 节点 name 为空） |
| io.println | ⚠️ 部分 | 依赖成员访问 |
| 前向声明 | ✅ | 已修复参数和返回类型 |

### 7.2 native_lower.tll 已知 GAP

| GAP | 分类 | 影响 | 优先级 |
|-----|------|------|--------|
| 函数调用参数丢失 | IMPLEMENTATION GAP | 无法调用带参数的函数 | P1 |
| io.println Member 解析 | IMPLEMENTATION GAP | 无法使用 io.println 输出 | P1 |
| Return 节点参数结构 | IMPLEMENTATION GAP | return 表达式可能不正确 | P1 |
| Array/Map 字面量 | MISSING | 无法创建数组/Map | P2 |
| Struct/Closure/Exception | MISSING | 高级语言特性不支持 | P2 |
| Module/Import | MISSING | 无法编译多模块程序 | P2 |
| 字符串转义处理 | IMPLEMENTATION GAP | 含特殊字符的字符串可能出错 | P2 |

---

## 八、Evidence

### 8.1 Bytecode Target 基准输出（batch1_basic.tll）

```
=== TLL Cross-Target Conformance Test Batch 1 ===
--- Int Arithmetic ---
5
6
42
5.0
2
--- Bool Logic ---
true
false
false
true
false
--- String ---
Hello World
Hello World
Hello, TLL!
--- Comparison ---
true
false
true
false
true
true
--- Function Calls ---
42
42
true
false
20
30
--- Nested Expressions ---
42
4
=== Conformance Test Batch 1 Complete ===
Exit: 0
```

### 8.2 Native Target 最小执行验证（return 42）

```
TLL Source (fn main() -> int { let x = 40; let y = 2; return x + y; })
    ↓ TLL Compiler (Native Target: Lexer→Parser→TypeChecker→native_lower)
C Source (517 bytes)
    ↓ MSVC (cl /O2 /utf-8, linking tll_native.c)
Native Executable (test_integration.exe, x86-64)
    ↓
CPU → return 42 ✅
```

### 8.3 Native Target 编译流程验证（simple_return.tll）

```
[Phase 1] Lexer... done, tokens=N
[Phase 2] Parser... done, statements=4
[Phase 3] TypeChecker... done, errors=0
[Phase 4] Native Lowering (C code generation)... done, C code length=1554
C code written successfully
```

生成的 C 代码包含：
- 正确的前向声明（带参数和 TLLValue 返回类型）
- 正确的函数定义（带参数）
- 正确的 if 语句体（Block 节点处理）
- 正确的逻辑运算和一元运算处理
- 正确的 C main 入口（调用 tll_main，返回 int）

---

## 九、GAP Ledger

### 9.1 本阶段新发现 GAP

| ID | 分类 | 描述 | 状态 |
|----|------|------|------|
| B3-GAP-01 | IMPLEMENTATION GAP | native_lower.tll 函数调用参数丢失（Call 节点 arguments 结构与预期不符） | 开放 |
| B3-GAP-02 | IMPLEMENTATION GAP | native_lower.tll io.println Member 节点 name 为空（parser 对内置模块特殊处理） | 开放 |
| B3-GAP-03 | IMPLEMENTATION GAP | native_lower.tll Return 节点参数结构需确认 | 开放 |
| B3-GAP-04 | ARCHITECTURE GAP | native/runtime/ 与 host/c/ 存在功能重叠，需收敛为 Shared Runtime Core | 开放（架构设计已完成，实施待后续） |
| B3-GAP-05 | TEST/EVIDENCE GAP | Cross-Target Conformance Test 框架已建立，但第一批测试因 Native GAP 未完全通过 | 开放 |
| B3-GAP-06 | EVIDENCE GAP | Linux Native 平台尚未验证（需 GCC/Clang + ELF） | 开放 |

### 9.2 历史 GAP（保留）

| ID | 分类 | 描述 | 状态 |
|----|------|------|------|
| D20-GAP-01 | ARCHITECTURE GAP | Compiler Bootstrap Convergence 尚未完全闭合（Compiler₃→Compiler₄ 问题） | 开放（P2-01-A 已修复 Stage-2 可运行，完整收敛待后续） |
| D20-GAP-02 | ARCHITECTURE GAP | 完全无 Native Code Generation（本阶段已建立 TLL→C→MSVC 路径，但非直接机器码后端） | 部分缓解 |
| B2-GAP-01 | IMPLEMENTATION GAP | Qualified Symbol Resolution（json.parse vs 全局 parse 冲突） | 已用 parseTokens 重命名规避，根本修复后置 |

---

## 十、对后续阶段的建议

### 10.1 P2-01-B.4 建议（Native Lowering 修复与扩展）

**目标**：修复 native_lower.tll 的 P1 GAP，使第一批 Conformance Tests 全部通过。

**优先级排序**：
1. 修复函数调用参数丢失（B3-GAP-01）— 调查 Call 节点 arguments 真实结构
2. 修复 io.println Member 解析（B3-GAP-02）— 调查 parser 对内置模块的特殊处理
3. 修复 Return 节点参数结构（B3-GAP-03）
4. 验证第一批 Conformance Tests 双 Target 一致通过
5. 扩展 native_lower.tll 支持 Array/Map 字面量（需先确认 Runtime Convergence）

**禁止**：
- 不实现完整 Native Backend（寄存器分配/优化器/linker）
- 不重新实现 host/c/ 已有功能
- 不扩大到 Closure/Exception/Coroutine（待 Runtime Convergence 实施后）

### 10.2 P2-01-B.5 建议（Runtime Convergence 实施）

**目标**：实施 Shared TLL Runtime Core，消除两套 Runtime 风险。

**步骤**：
1. 创建 `runtime/tll_runtime.h`（核心数据结构）
2. 创建 `runtime/value.c`（从 host/c/ 提取）
3. 创建 `runtime/json.c`（从 host/c/ 提取）
4. 修改 native/runtime/ 引用 Shared Runtime
5. 修改 host/c/ 引用 Shared Runtime
6. 验证 Bytecode 和 Native 双 Target 回归通过

### 10.3 P2-01-C 建议（High-Frame Runtime Foundation）

**前置条件**：
- P2-01-B 全部封板（Native Target 稳定 + Runtime Convergence 实施）
- Cross-Target Conformance Tests 全部通过

**核心方向**（按架构师已确定的路线）：
- ExecutionContext 作为核心 Runtime 对象
- Worker ↓ ExecutionContext ↓ Task 模型
- Scheduler ↓ Runnable Queue ↓ Worker
- 禁止全局 VM Lock
- 第一阶段证明多 Worker 真正并发执行多 Task

---

## 十一、状态总结

| 项目 | 状态 |
|------|------|
| host/c/ Runtime Inventory | ✅ 完成 |
| native/runtime/ 功能对比 | ✅ 完成 |
| Runtime Convergence 架构设计 | ✅ 完成 |
| TLL Native Runtime ABI 定义 | ✅ 完成（基础层） |
| Cross-Target Conformance Test 框架 | ✅ 建立 |
| 第一批 Conformance Tests | ⚠️ 部分（Native 有 P1 GAP） |
| Native Target 最小执行 | ✅ 验证（return 42） |
| 不建立第二套 Runtime | ✅ 架构原则已确立 |
| BLOCKER | 0 |
| 本阶段新开发功能 | native_lower.tll 增强（逻辑运算/一元运算/Block 体/前向声明参数/字符串引号/统一 TLLValue 类型） |
| Git Push | ❌ 禁止 |

---

**报告结束。停止施工，等待架构裁决。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
**日期**: 2026-09-09
