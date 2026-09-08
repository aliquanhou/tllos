# P0-TLL-LANGUAGE-COMPLETE Phase 5 — FFI / Native Interop Reality Audit

**日期**: 2026-09-08
**分支**: p0-language-phase5-ffi
**基线**: main @ b08a7af (Phase 4 merged)
**审计阶段**: Reality Audit (Audit First, 未修改代码)

---

## 一、审计目标

盘点当前 TLL 在 FFI / Native Interop 领域的真实能力状态，分析实现路径和风险，为 Phase 5 施工提供决策依据。

---

## 二、当前能力矩阵

### 2.1 FFI / Native Interop 能力

| 能力 | 状态 | 说明 |
|------|------|------|
| FFI 关键字/语法 | ❌ MISSING | 无 ffi/native/extern/dlopen 等关键字 |
| 动态库加载 | ❌ MISSING | 无 dlopen/LoadLibrary 能力（sqlite3.c 内部的不暴露） |
| 符号解析 | ❌ MISSING | 无 dlsym/GetProcAddress |
| C ABI 类型映射 | ❌ MISSING | 无 TLL↔C 类型转换机制 |
| 外部函数调用 | ❌ MISSING | 无法调用动态库中的 C 函数 |
| 回调函数 | ❌ MISSING | 无法将 TLL 函数作为 C 回调传递 |
| 结构体/联合体 | ❌ MISSING | 无 C 结构体映射 |
| 指针操作 | ❌ MISSING | 无原始指针操作 |
| 内存管理 | ❌ MISSING | 无 C 内存分配/释放接口 |
| 语言规范定义 | ❌ MISSING | docs/language/ 中无 FFI 定义 |
| stdlib FFI 模块 | ❌ MISSING | 无 stdlib 目录，所有标准库都是静态 builtin |

### 2.2 现有 Native 能力（静态 Builtin）

| 能力 | 状态 | 说明 |
|------|------|------|
| 静态 Builtin 注册 | ✅ COMPLETE | 145+ 个静态注册的 builtin 函数（idx 0-145+） |
| Builtin 名称映射 | ✅ COMPLETE | `cg_getBuiltinIndex(modName, fnName)` 硬编码 if-else 链 |
| Builtin 加载 | ✅ COMPLETE | `OP_LOAD_BUILTIN [reg, idx]` 操作码 |
| Builtin 调用 | ✅ COMPLETE | `OP_CALL` 调用 builtin 函数 |
| Builtin 模块 | ✅ COMPLETE | io, json, math, strings, arrays, convert, process, fs, coroutine, crypto, http, sqlite 等 |
| 模块.函数语法 | ✅ COMPLETE | `io.println("hello")`、`math.sqrt(2.0)` |

### 2.3 关键发现

**TLL 当前没有任何形式的动态 FFI 能力。**

所有 native 功能都是通过**静态编译进 VM 的 builtin 函数**提供的：
- builtin 函数在 C 代码中静态实现
- 通过 `idx` 编号注册（0-145+）
- 编译器通过 `cg_getBuiltinIndex()` 将 `module.function` 映射到 idx
- VM 通过 `tll_call_builtin(vm, idx, args, argCount)` 分发调用

这意味着：
- ❌ 无法在运行时加载新的 native 库
- ❌ 无法调用未静态注册的 C 函数
- ❌ 无法与第三方 C 库交互
- ❌ 无法扩展 native 功能而不重新编译 VM

---

## 三、FFI 实现路径分析

### 3.1 完整 FFI 需要的组件

```
TLL FFI System
    │
    ├── 1. 动态库加载
    │   ├── Linux/macOS: dlopen()
    │   ├── Windows: LoadLibrary()
    │   └── 跨平台抽象层
    │
    ├── 2. 符号解析
    │   ├── Linux/macOS: dlsym()
    │   ├── Windows: GetProcAddress()
    │   └── 函数指针存储
    │
    ├── 3. C ABI 类型映射
    │   ├── 基本类型: int, float, double, char, bool
    │   ├── 字符串: char* ↔ TLL string
    │   ├── 指针: void* ↔ TLL opaque pointer
    │   ├── 结构体: struct ↔ TLL struct/map
    │   └── 数组: C array ↔ TLL array
    │
    ├── 4. 函数调用机制
    │   ├── 方案 A: libffi (跨平台调用约定)
    │   ├── 方案 B: 手写汇编 (各平台)
    │   └── 方案 C: 固定签名 thunk (限制功能)
    │
    ├── 5. 内存管理
    │   ├── C malloc/free 接口
    │   ├── TLL 对象 ↔ C 数据转换
    │   ├── GC 与 C 内存的交互
    │   └── 生命周期管理
    │
    └── 6. 语言语法
        ├── ffi.load("lib.so") → library handle
        ├── ffi.cdef("int printf(char*, ...);")
        ├── lib.function(args) → call C function
        └── ffi.new("type", value) → C data
```

### 3.2 三种实现方案对比

| 方案 | 描述 | 优点 | 缺点 | 工作量 |
|------|------|------|------|--------|
| **A: libffi** | 集成 libffi 库，支持完整 C ABI | 功能完整，跨平台，支持任意签名 | 依赖外部库，构建复杂，内存安全挑战 | 大 |
| **B: 手写 thunk** | 为固定数量的函数签名手写汇编 thunk | 无外部依赖，性能好 | 仅支持固定签名，跨平台工作量大 | 中 |
| **C: Builtin 扩展** | 通过新增 builtin 支持常见 C 库调用 | 实现简单，复用现有机制 | 不是真正的 FFI，无法动态加载 | 小 |

### 3.3 推荐的 Phase 5 最小实现路径

**建议采用渐进式实现，Phase 5 只做最小可用 FFI 基础：**

#### Stage 1: 动态库加载 + 符号解析（基础）
- 新增 builtin 模块 `ffi`
- `ffi.load(path: string) -> handle`：加载动态库
- `ffi.symbol(handle, name: string) -> pointer`：解析符号
- 跨平台实现：dlopen/dlsym (Linux/macOS) + LoadLibrary/GetProcAddress (Windows)

#### Stage 2: 基本类型 C 函数调用（核心）
- 支持固定签名的 C 函数调用：
  - `int fn()` 
  - `int fn(int)`
  - `int fn(int, int)`
  - `const char* fn()`
  - `void fn(int)`
  - 等常见签名
- 通过手写 thunk 或 libffi 实现
- `ffi.call(pointer, returnType, argTypes, args...) -> value`

#### Stage 3: 字符串和指针支持
- `ffi.string(pointer) -> string`：C 字符串转 TLL 字符串
- `ffi.cstring(string) -> pointer`：TLL 字符串转 C 字符串
- `ffi.malloc(size) -> pointer` / `ffi.free(pointer)`
- 基本指针操作

#### Stage 4: 语言语法糖（可选）
- `ffi.load("libc.so").printf("hello")` 简化语法
- `ffi.cdef` 类型声明
- 更友好的 API

### 3.4 Phase 5 范围控制建议

**本阶段（Phase 5）建议只做 Stage 1 + Stage 2：**
- ✅ 动态库加载（ffi.load）
- ✅ 符号解析（ffi.symbol）
- ✅ 基本类型 C 函数调用（固定签名）
- ✅ 跨平台支持（Windows/Linux/macOS）

**暂不做（后续阶段）：**
- ❌ 结构体/联合体映射
- ❌ 回调函数（TLL 函数作为 C 回调）
- ❌ 完整 libffi 集成
- ❌ 复杂类型系统
- ❌ ffi.cdef 声明语法
- ❌ 自动内存管理

---

## 四、风险和挑战

### 4.1 技术风险

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|----------|
| 跨平台差异 | 🔴 高 | Windows/Linux/macOS 的动态库加载和调用约定不同 | 建立跨平台抽象层，分别实现 |
| C ABI 复杂性 | 🟡 中 | 结构体、联合体、浮点传递规则复杂 | Phase 5 只支持基本类型和固定签名 |
| 内存安全 | 🔴 高 | C 内存错误可能导致 VM 崩溃 | 文档明确风险，添加基本边界检查 |
| 类型安全 | 🟡 中 | TLL 动态类型与 C 静态类型不匹配 | 运行时类型检查，错误时抛异常 |
| GC 交互 | 🟡 中 | TLL GC 可能回收 C 仍在使用的对象 | 明确生命周期规则，文档说明 |

### 4.2 工程风险

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|----------|
| 构建系统复杂度 | 🟡 中 | 需要处理 libffi 或手写汇编的构建 | Phase 5 用手写 thunk，无外部依赖 |
| 测试覆盖 | 🟡 中 | FFI 测试需要真实的 C 测试库 | 编写简单的 C 测试库，跨平台编译 |
| 文档不足 | 🟢 低 | FFI API 需要详细文档 | 随实现同步编写文档和示例 |

### 4.3 已知限制（TLL Runtime）

- **try/catch + complex function → heap corruption**（Phase 4 发现的 Runtime bug）
  - 影响：FFI 实现中可能需要 try/catch 来处理 C 错误
  - 缓解：FFI 错误通过返回值/异常码处理，不依赖 try/catch

---

## 五、与现有架构的兼容性

### 5.1 Builtin 机制复用

FFI 可以复用现有的 builtin 机制：
- 新增 `ffi` 模块到 `cg_getBuiltinIndex()`
- `ffi.load`、`ffi.symbol`、`ffi.call` 等作为新的 builtin 函数
- 不需要新的操作码或编译器改动（Stage 1+2）

### 5.2 VM 扩展

需要在 VM 层新增：
- 动态库句柄类型（TLLValue 扩展或 opaque pointer）
- C 函数指针存储
- 函数调用 thunk（手写汇编或 libffi）
- C 内存管理接口

### 5.3 编译器改动

Stage 1+2 最小实现**不需要编译器改动**：
- FFI 功能通过 builtin 函数提供
- TLL 程序通过 `ffi.load(...)`、`ffi.call(...)` 调用
- 复用现有的 `module.function` 语法和 builtin 映射机制

---

## 六、审计结论

### 6.1 当前状态

**FFI / Native Interop = 完全 MISSING**

TLL 当前没有任何形式的动态 FFI 能力，所有 native 功能都是通过静态编译进 VM 的 builtin 函数提供的。

### 6.2 实现可行性

**技术上可行，工程上可控。**

- 可以复用现有的 builtin 机制
- Stage 1+2 最小实现不需要编译器改动
- 跨平台动态库加载有成熟的 API（dlopen/LoadLibrary）
- 基本类型函数调用可以通过手写 thunk 实现（无外部依赖）

### 6.3 推荐的 Phase 5 目标

**FFI / Native Interop 最小可用闭环：**

1. `ffi.load(path)` — 加载动态库
2. `ffi.symbol(handle, name)` — 解析函数符号
3. `ffi.call(pointer, returnType, argTypes, args...)` — 调用 C 函数（基本类型，固定签名）
4. `ffi.string(pointer)` / `ffi.cstring(string)` — 字符串转换
5. `ffi.malloc(size)` / `ffi.free(pointer)` — 基本内存管理
6. 跨平台支持（Windows/Linux/macOS）
7. 持久化测试（使用简单的 C 测试库）
8. 文档和示例

### 6.4 不阻塞项

以下问题记录为 GAP，不阻塞 Phase 5：
- 结构体/联合体映射
- 回调函数
- 完整 libffi 集成
- ffi.cdef 声明语法
- 自动内存管理
- try/catch heap corruption（Runtime bug，后续专门处理）

---

## 七、下一步

**Phase 5 Reality Audit 完成，可以进入施工阶段。**

建议施工令：
- 目标：FFI / Native Interop 最小可用闭环
- 范围：Stage 1（动态库加载）+ Stage 2（基本类型函数调用）+ 字符串/指针基础支持
- 禁止：结构体、回调、libffi、复杂类型系统
- 验证：使用简单的 C 测试库，跨平台测试
- 交付：builtin 实现 + 测试 + 文档 + 示例

等待架构师审核 Reality Audit 后，下发正式施工令。
