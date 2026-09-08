# P0-TLL-LANGUAGE-COMPLETE Phase 5
## FFI / Native Interop Foundation (FFI v0)

**Status:** IMPLEMENTED + VERIFIED (Windows)
**Branch:** p0-language-phase5-ffi
**Baseline:** main @ b08a7af

---

## 一、实现目标

建立 TLL 的第一条 Native Interop 最小闭环：

```
TLL Program
    ↓
ffi.load(real shared library)
    ↓
ffi.symbol(real C function)
    ↓
ffi.call(explicit ABI signature)
    ↓
REAL native result
```

本阶段只建立最小 Native Interop Primitive，不提前建设完整工业级 FFI。

---

## 二、TLL Native ABI v0 定义

| TLL 类型常量 | TLL 类型名 | Native ABI | 说明 |
|------------|----------|-----------|------|
| 0 | void | void | 无返回值 |
| 1 | int32 | C int32_t | 32位有符号整数 |
| 2 | int64 | C int64_t | 64位有符号整数 |
| 3 | uint32 | C uint32_t | 32位无符号整数 |
| 4 | uint64 | C uint64_t | 64位无符号整数 |
| 5 | float64 | C double | **GAP: 暂不支持**（需要 XMM 寄存器处理） |
| 6 | pointer | void* | 通用指针 |
| 7 | cstring | const char* | NUL 终止的 C 字符串 |

**注意：** 不使用 C 的 `int`、`long` 等平台相关类型，全部使用固定宽度类型。

---

## 三、API 设计

### ffi.load(path) -> handle (int64)

加载动态链接库。

- **Windows:** `LoadLibraryA(path)`
- **Linux/macOS:** `dlopen(path, RTLD_NOW | RTLD_LOCAL)`
- **成功:** 返回非零 handle
- **失败:** 返回 0，错误信息输出到 stderr

### ffi.symbol(handle, name) -> pointer (int64)

解析动态库中的函数符号。

- **Windows:** `GetProcAddress(handle, name)`
- **Linux/macOS:** `dlsym(handle, name)`
- **成功:** 返回非零函数指针
- **失败:** 返回 0，错误信息输出到 stderr

### ffi.call(pointer, returnType, argTypes[], args[]) -> result

调用 C 函数，必须显式指定 ABI 签名。

- **returnType:** 上述类型常量（0-7）
- **argTypes:** 参数类型常量数组
- **args:** 参数值数组
- **最大参数数:** 4（v0 限制）
- **支持的参数类型:** int32, int64, uint32, uint64, pointer, cstring
- **支持的返回类型:** void, int32, int64, uint32, uint64, pointer, cstring

### ffi.cstring(tll_string) -> pointer (int64)

将 TLL 字符串转换为 C 字符串指针。

- **警告:** 返回的指针指向 TLL 内部管理的内存，C 代码不应释放，且在 TLL 字符串被回收后失效。

### ffi.string(pointer) -> tll_string

将 C 字符串（NUL 终止）复制为 TLL 字符串。

- 安全复制，不持有 C 内存指针。

---

## 四、架构实现

### 文件修改清单

| 文件 | 修改类型 | 说明 |
|-----|---------|------|
| `host/c/ffi_builtin.c` | 新建 | FFI 完整实现（~280行） |
| `host/c/tllvm.h` | 修改 | 添加 `ffi_builtin_invoke` 声明 |
| `host/c/builtin.c` | 修改 | 添加 FFI builtin 范围分发（210-219） |
| `compiler/codegen.tll` | 修改 | 添加 `ffi` 模块 builtin 映射（210-214） |
| `compiler/typechecker.tll` | 修改 | 在 builtin 模块列表中添加 `ffi` |
| `tests/ffi/probe_ffi.tll` | 新建 | FFI 测试套件（12个测试，真断言） |

### Builtin 索引分配

| 索引 | 函数 |
|-----|------|
| 210 | ffi.load |
| 211 | ffi.symbol |
| 212 | ffi.call |
| 213 | ffi.cstring |
| 214 | ffi.string |

### 平台抽象层

```c
#ifdef _WIN32
typedef HMODULE native_lib_t;
typedef FARPROC native_sym_t;
#else
typedef void* native_lib_t;
typedef void* native_sym_t;
#endif
```

所有平台 API 调用封装在 `ffi_platform_load()` 和 `ffi_platform_symbol()` 中，不直接泄漏到 TLL 层。

### 函数调用 Thunk

由于 C 语言不支持动态调用任意签名的函数，v0 使用预定义的函数指针类型：

```c
typedef int64_t (*ffi_fn_0)(void);
typedef int64_t (*ffi_fn_1)(int64_t);
typedef int64_t (*ffi_fn_2)(int64_t, int64_t);
typedef int64_t (*ffi_fn_3)(int64_t, int64_t, int64_t);
typedef int64_t (*ffi_fn_4)(int64_t, int64_t, int64_t, int64_t);
```

所有整数类类型（int32, int64, uint32, uint64, pointer, cstring）在 x64 上都通过通用寄存器传递，因此可以用 int64_t 作为通用载体。

---

## 五、测试结果

### FFI 测试套件：12/12 PASS

| 测试 | 结果 | 说明 |
|-----|------|------|
| FFI-01 load msvcrt.dll | PASS | 返回非零 handle |
| FFI-02 resolve strlen | PASS | 返回非零指针 |
| FFI-03 strlen("hello world") | PASS | 返回 11 |
| FFI-04 atoi("42") | PASS | 返回 42 |
| FFI-05 strcmp("abc","abc") | PASS | 返回 0 |
| FFI-05 strcmp("abc","abd") | PASS | 返回 -1 |
| FFI-06 ffi.cstring | PASS | 返回非零指针 |
| FFI-06 ffi.string roundtrip | PASS | 恢复原字符串 |
| FFI-N01 invalid library | PASS | 返回 0，不崩溃 |
| FFI-N02 invalid symbol | PASS | 返回 0，不崩溃 |

### 回归测试：15/15 acceptance tests PASS

所有现有 acceptance tests（01_hello 到 15_for_loop）编译和运行正常。

---

## 六、验证的真实 C 函数

使用 Windows 系统库 `msvcrt.dll` 中的真实 C 函数：

- `strlen(const char*) -> size_t` — 字符串长度
- `atoi(const char*) -> int` — 字符串转整数
- `strcmp(const char*, const char*) -> int` — 字符串比较

这些都是真实的、跨平台存在的 C ABI 函数，不是 mock 或自洽函数。

---

## 七、已知 GAP（非阻塞）

| GAP | 说明 | 优先级 |
|-----|------|-------|
| float64 参数/返回值 | x64 浮点参数需要 XMM 寄存器，当前 thunk 只支持整数类参数 | 高 |
| 超过 4 个参数 | v0 限制最多 4 个参数 | 中 |
| struct/union 参数 | 复杂 ABI aggregate 未实现 | 中 |
| 回调函数指针 | C 回调 TLL 函数未实现 | 中 |
| 可变参数函数 | printf 等 variadic 函数未实现 | 低 |
| malloc/free 原生内存管理 | FFI 调用和通用 native memory ownership 是两个问题 | 中 |
| Linux/macOS 验证 | 当前仅在 Windows 验证，代码已跨平台设计 | 高（CI 验证） |
| 错误处理机制 | 当前错误信息输出到 stderr，未来应返回 TLL Error 对象 | 中 |

---

## 八、架构概念分离

**builtin 是 TLL 内部能力**（io, json, math 等，静态编译进 VM）。

**FFI 是 TLL 对外部世界的 Native Boundary**（动态加载任意 .dll/.so/.dylib，调用任意 C 函数）。

两者虽然当前都通过 builtin 索引机制访问，但架构概念必须分开。未来 FFI 应拥有独立的类型系统和编译器支持。

---

## 九、最终 Gate 验证

```
TLL Program
   │
   ▼
ffi.load("msvcrt.dll")  →  140721899044864 (non-zero)
   │
   ▼
ffi.symbol(handle, "strlen")  →  140721899426496 (non-zero)
   │
   ▼
ffi.call(ptr, int64, [cstring], ["hello"])  →  5 (REAL native result)
   │
   ▼
✅ Phase 5 Stage 1 FFI Foundation 成功
```

---

## 十、提交信息

```
feat(runtime): add FFI native interop foundation (FFI v0)

- Add ffi.load/ffi.symbol/ffi.call/ffi.cstring/ffi.string builtins
- Platform abstraction: LoadLibrary/dlopen, GetProcAddress/dlsym
- TLL Native ABI v0: int32/int64/uint32/uint64/pointer/cstring/void
- Explicit ABI signature required for ffi.call
- Max 4 args, integer-class types only (float64 = GAP)
- 12/12 FFI tests pass (positive + negative, real assertions)
- 15/15 acceptance regression pass
- Verified with real msvcrt.dll: strlen, atoi, strcmp
```

---

**本阶段最多称：TLL Native Interop Foundation / FFI v0**
**不是完整工业级 FFI。**
