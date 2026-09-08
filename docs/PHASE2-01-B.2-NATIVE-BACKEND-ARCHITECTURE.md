# PHASE 2-01-B.2 — Native Backend Integration Architecture

**施工队**: 豆包 A
**阶段**: Phase 2 / P2-01-B.2
**基线**: b32dc67 + P2-01-A Bootstrap Closure + P2-01-B.1 Reality Assessment
**日期**: 2026-09-09
**Git 状态**: 本地架构设计 + 最小集成实现，未 Push

---

## 一、执行摘要

**结论：TLL Compiler 正式 Native Target 架构已设计并通过最小集成验证。**

TLL Compiler 现在正式支持两个 Target：
- **Bytecode Target**（现有）：AST → codegen.tll → 字节码 → VM
- **Native Target**（新建）：AST → native_lower.tll → C 代码 → MSVC/GCC → Native Executable

两个 Target 共享相同的前端（Lexer → Parser → TypeChecker → AST），只在后端分叉。

**最小集成验证成功**：
```
TLL Source (fn main() -> int { let x = 40; let y = 2; return x + y; })
    ↓ TLL Compiler (Native Target: Lexer→Parser→TypeChecker→native_lower)
C Source (with TLL Native Runtime calls)
    ↓ MSVC (cl /O2 /utf-8, linking tll_native.c)
Native Executable (test_integration.exe, x86-64)
    ↓
CPU → return 42 ✅
```

---

## 二、TLL Compiler Native Target 架构

### 2.1 整体架构

```
                        TLL Source
                            │
                            ▼
┌─────────────────────────────────────────────────┐
│              Shared Frontend (共享前端)            │
│  Lexer (lexer.tll) → Parser (parser.tll)        │
│  → TypeChecker (typechecker.tll) → AST           │
└───────────────────────┬─────────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│  Bytecode Target     │   │  Native Target (新建) │
│  (现有)              │   │                      │
│  codegen.tll         │   │  native_lower.tll    │
│    ↓                 │   │    ↓                 │
│  字节码 (.tllbc)     │   │  C Source (.c)       │
│    ↓                 │   │    ↓                 │
│  TLL VM (tllvm.exe)  │   │  MSVC / GCC / Clang  │
│    ↓                 │   │    ↓                 │
│  解释执行             │   │  Native Executable    │
└─────────────────────┘   └──────────┬──────────┘
                                       │
                                       ▼
                          ┌─────────────────────┐
                          │  TLL Native Runtime   │
                          │  (native/runtime/)    │
                          │  - TLLValue           │
                          │  - Array/Map          │
                          │  - 引用计数            │
                          │  - IO/算术/比较        │
                          └─────────────────────┘
```

### 2.2 共同语义边界

Bytecode Target 和 Native Target 共享以下语义：
- **AST 结构**：相同的 Parser 输出
- **类型系统**：相同的 TypeChecker（动态类型 + 部分静态检查）
- **TLLValue 表示**：相同的 tagged union 定义（与 host/c/value.c 一致）
- **引用计数内存管理**：相同的 refCount 机制
- **内置函数语义**：io.println、算术运算、比较运算等语义一致

### 2.3 Native Target 模块

| 模块 | 文件 | 功能 |
|------|------|------|
| Native Lowering | `compiler/native_lower.tll` | AST → C 代码生成 |
| Compiler Integration | `compiler/compiler.tll` | 增加 `compileNative(source)` 函数 |
| Native Runtime ABI | `native/runtime/tll_native.h` | TLLValue、Array、Map、IO、算术、比较等接口定义 |
| Native Runtime 实现 | `native/runtime/tll_native.c` | TLL Native Runtime 最小实现 |

### 2.4 compileNative 函数

在 `compiler/compiler.tll` 中新增：
```tll
export fn compileNative(source: string) -> string {
    // Phase 1: Lexer (shared with Bytecode Target)
    let tokens = tokenize(source)
    // Phase 2: Parser (shared)
    let ast = parseTokens(tokens)
    // Phase 3: TypeChecker (shared)
    let errors = check(ast)
    // Phase 4: Native Lowering (Native Target specific)
    let cSource = lowerToC(ast)
    return cSource
}
```

---

## 三、TLL Native Runtime ABI 设计

### 3.1 TLLValue 表示

与 host/c/value.c 完全一致的 tagged union：
```c
typedef enum {
    TLL_NULL, TLL_BOOL, TLL_INT, TLL_FLOAT, TLL_STRING,
    TLL_ARRAY, TLL_MAP, TLL_FUNCTION, TLL_BUILTIN, TLL_UPVALUE
} TLLType;

struct TLLValue {
    TLLType type;
    union {
        int boolean;
        long long integer;
        double floating;
        char *string;
        TLLArray *array;
        TLLMap *map;
        struct { int fnIdx; TLLClosureEnv *env; } func;
        struct { int idx; } builtin;
        TLLUpvalue *upvalue;
    } as;
};
```

### 3.2 值创建函数

| 函数 | 说明 |
|------|------|
| `tll_null()` | 创建 null 值 |
| `tll_bool(int b)` | 创建布尔值 |
| `tll_int(long long val)` | 创建整数值 |
| `tll_float(double val)` | 创建浮点数值 |
| `tll_string(const char *s)` | 创建字符串值 |
| `tll_array()` | 创建数组值 |
| `tll_map()` | 创建 Map 值 |
| `tll_function(int fnIdx, TLLClosureEnv *env)` | 创建函数值 |
| `tll_builtin(int idx)` | 创建内置函数值 |

### 3.3 Array/Map 操作

| 函数 | 说明 |
|------|------|
| `array_push(TLLArray*, TLLValue)` | 数组追加元素 |
| `array_get(TLLArray*, int)` | 获取数组元素 |
| `array_set(TLLArray*, int, TLLValue)` | 设置数组元素 |
| `map_set(TLLMap*, const char*, TLLValue)` | 设置 Map 键值 |
| `map_get(TLLMap*, const char*)` | 获取 Map 值 |
| `map_has(TLLMap*, const char*)` | 检查 Map 键是否存在 |

### 3.4 内存管理（引用计数）

| 函数 | 说明 |
|------|------|
| `tll_value_incref(TLLValue)` | 增加引用计数 |
| `tll_value_free(TLLValue)` | 减少引用计数，归零则释放 |

### 3.5 IO 内置函数

| 函数 | 说明 |
|------|------|
| `tll_io_print(TLLValue)` | 打印值（不换行） |
| `tll_io_println(TLLValue)` | 打印值（换行） |

### 3.6 算术运算

| 函数 | 说明 |
|------|------|
| `tll_add(TLLValue, TLLValue)` | 加法（支持字符串拼接） |
| `tll_sub(TLLValue, TLLValue)` | 减法 |
| `tll_mul(TLLValue, TLLValue)` | 乘法 |
| `tll_div(TLLValue, TLLValue)` | 除法（始终返回 float） |
| `tll_mod(TLLValue, TLLValue)` | 取模 |

### 3.7 比较运算

| 函数 | 说明 |
|------|------|
| `tll_eq(TLLValue, TLLValue)` | 等于 |
| `tll_neq(TLLValue, TLLValue)` | 不等于 |
| `tll_lt(TLLValue, TLLValue)` | 小于 |
| `tll_gt(TLLValue, TLLValue)` | 大于 |
| `tll_le(TLLValue, TLLValue)` | 小于等于 |
| `tll_ge(TLLValue, TLLValue)` | 大于等于 |

### 3.8 Runtime 初始化/清理

| 函数 | 说明 |
|------|------|
| `tll_native_init()` | 初始化 Native Runtime |
| `tll_native_cleanup()` | 清理 Native Runtime |

---

## 四、Minimal Integration Evidence

### 4.1 测试程序

**输入 TLL 源码** (`fn main() -> int { let x = 40; let y = 2; return x + y; }`)

### 4.2 TLL Compiler Native Target 输出

**生成的 C 代码**：
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "tll_native.h"

/* Forward declarations */
TLLValue tll_main(void);

TLLValue tll_main(void) {
    TLLValue x = tll_int(40);
    TLLValue y = tll_int(2);
    return tll_add(x, y);
}

/* C entry point */
int main(int argc, char *argv[]) {
    tll_native_init();
    TLLValue result = tll_main();
    tll_native_cleanup();
    if (result.type == TLL_INT) return (int)result.as.integer;
    if (result.type == TLL_BOOL) return result.as.boolean ? 0 : 1;
    return 0;
}
```

### 4.3 编译命令

```bash
cl /nologo /O2 /utf-8 /I native\runtime \
   native\test_integration.c \
   native\runtime\tll_native.c \
   /Fe:native\test_integration.exe
```

### 4.4 编译结果

- **编译状态**: 成功 (exit 0)
- **产物**: `native/test_integration.exe` (x86-64 Windows PE)
- **链接**: 静态链接 TLL Native Runtime (tll_native.c)
- **警告**: 无（使用 /utf-8 避免编码警告）

### 4.5 运行结果

```bash
native\test_integration.exe
→ Exit code: 42 ✅
```

### 4.6 完整流程验证

| 阶段 | 工具 | 输入 | 输出 | 状态 |
|------|------|------|------|------|
| 1. Lexer | lexer.tll | TLL source | 24 tokens | ✅ |
| 2. Parser | parser.tll | tokens | AST (1 statement) | ✅ |
| 3. TypeChecker | typechecker.tll | AST | 0 errors | ✅ |
| 4. Native Lowering | native_lower.tll | AST | C source (517 bytes) | ✅ |
| 5. C Compiler | MSVC cl /O2 | C source + tll_native.c | test_integration.exe | ✅ |
| 6. Native Execution | Windows CPU | test_integration.exe | exit code 42 | ✅ |

**Native Execution Gate (正式架构闭合): ✅ 通过**

---

## 五、Windows/Linux 双平台路径

### 5.1 Windows 路径（已验证）

```
TLL Source → C Source → MSVC (cl.exe) → PE (.exe) → Windows x86-64
```

- **编译器**: MSVC (VS 2022 Build Tools, vcvarsall.bat)
- **ABI**: Microsoft x64 calling convention
- **对象格式**: PE (Portable Executable)
- **Runtime**: MSVCRT + TLL Native Runtime
- **状态**: ✅ 已验证 (test_integration.exe, exit 42)

### 5.2 Linux 路径（架构可行，待验证）

```
TLL Source → C Source → GCC/Clang → ELF → Linux x86-64
```

- **编译器**: GCC 或 Clang（当前系统未安装，需安装或使用 WSL）
- **ABI**: System V AMD64 ABI
- **对象格式**: ELF (Executable and Linkable Format)
- **Runtime**: glibc + TLL Native Runtime
- **状态**: ⚠️ 架构可行，待验证（C 代码平台无关，只需 Linux C 编译器）

### 5.3 跨平台策略

- **Transpiler 输出平台无关的 C 代码**：不包含平台特定的 #ifdef
- **平台特定代码隔离在 TLL Native Runtime 层**：类似 host/c/ 的做法
- **构建系统**: CMake 或 Makefile，支持多平台
- **TLL Native Runtime 与 host/c/ 共享代码**：TLLValue、Array、Map、引用计数等核心数据结构完全一致

---

## 六、TLL 自研 vs 成熟工具链委托

### 6.1 职责划分

| 层级 | TLL 自研 | 委托成熟工具链 |
|------|----------|----------------|
| 前端 | ✅ Lexer, Parser, TypeChecker, AST | - |
| 中端 | ✅ Native Lowering (AST→C) | - |
| 后端 | - | ✅ C Compiler (MSVC/GCC/Clang) |
| 优化器 | - | ✅ C Compiler 优化器 (/O2, -O2) |
| 寄存器分配 | - | ✅ C Compiler |
| 指令选择 | - | ✅ C Compiler |
| 链接器 | - | ✅ OS Linker (link.exe, ld) |
| 对象格式 | - | ✅ PE/ELF (C Compiler 生成) |
| Runtime | ✅ TLL Native Runtime (TLLValue, Array, Map, 引用计数, IO, 算术) | - |
| 平台抽象 | ✅ TLL Native Runtime 接口 | ✅ libc (stdio, stdlib, string) |

### 6.2 TLL 必须自研的部分

1. **Lexer/Parser/TypeChecker**：TLL 语言特定的语法和语义
2. **Native Lowering**：TLL AST → C 的转换逻辑（TLL 语言特定）
3. **TLL Native Runtime**：TLLValue 表示、Array/Map、引用计数、TLL 特定的内置函数语义
4. **语言语义保证**：动态类型、函数级作用域、闭包语义等

### 6.3 委托成熟工具链的部分

1. **C 编译器**：MSVC/GCC/Clang（代码生成、优化、寄存器分配、指令选择）
2. **链接器**：OS 提供的链接器（PE/ELF 生成、重定位）
3. **libc**：标准 C 库（stdio, stdlib, string, math）
4. **OS ABI**：平台特定的调用约定和系统调用

---

## 七、修改的文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `compiler/native_lower.tll` | 新建 | TLL AST → C 代码生成器（Native Target 后端） |
| `compiler/compiler.tll` | 修改 | 增加 `compileNative(source)` 函数和 `native_lower` import |
| `native/runtime/tll_native.h` | 新建 | TLL Native Runtime ABI 头文件（TLLValue, Array, Map, IO, 算术, 比较） |
| `native/runtime/tll_native.c` | 新建 | TLL Native Runtime 最小实现 |
| `compiler/test_native_target.tll` | 新建 | Native Target 集成测试程序 |
| `native/test_integration.c` | 生成 | TLL Compiler Native Target 生成的 C 代码（测试用） |
| `native/test_integration.exe` | 生成 | MSVC 编译的 Native Executable（测试用） |
| `docs/PHASE2-01-B.2-NATIVE-BACKEND-ARCHITECTURE.md` | 新建 | 本报告 |

---

## 八、剩余 GAP (GAP Ledger)

### 8.1 Native Lowering 能力 GAP

当前 native_lower.tll 只支持最小子集，以下能力缺失：

| 能力 | 状态 | 优先级 |
|------|------|--------|
| 函数声明/定义 | ✅ 已支持 | - |
| let/const 变量 | ✅ 已支持 | - |
| return | ✅ 已支持 | - |
| if/else | ⚠️ 仅 if，无 else | P1 |
| while 循环 | ⚠️ 框架已支持，未充分测试 | P1 |
| for 循环 | ❌ 缺失 | P1 |
| break/continue | ❌ 缺失 | P2 |
| 数组字面量/操作 | ❌ 缺失 | P0 |
| Map 字面量/操作 | ❌ 缺失 | P0 |
| 字符串操作 | ⚠️ 仅字面量和拼接 | P1 |
| struct | ❌ 缺失 | P1 |
| enum/ADT | ❌ 缺失 | P2 |
| 闭包 | ❌ 缺失 | P1 |
| 高阶函数 | ❌ 缺失 | P2 |
| 异常 (try/catch) | ❌ 缺失 | P2 |
| 模块 (import/export) | ❌ 缺失 | P1 |
| 类型标注 | ⚠️ 部分支持 | P1 |

### 8.2 Native Runtime ABI GAP

| 能力 | 状态 | 优先级 |
|------|------|--------|
| TLLValue 表示 | ✅ 已实现 | - |
| 引用计数内存管理 | ✅ 已实现 | - |
| Array 操作 | ✅ 已实现 | - |
| Map 操作 | ✅ 已实现 | - |
| IO (print/println) | ✅ 已实现 | - |
| 算术运算 | ✅ 已实现 | - |
| 比较运算 | ✅ 已实现 | - |
| 字符串操作 (length, substring, etc.) | ❌ 缺失 | P1 |
| JSON 解析/序列化 | ❌ 缺失 | P1 |
| 闭包运行时 | ❌ 缺失 | P1 |
| 异常运行时 | ❌ 缺失 | P2 |
| 协程运行时 | ❌ 缺失 | P2 |
| 网络运行时 | ❌ 缺失 | P2 |
| 文件系统运行时 | ❌ 缺失 | P2 |
| 密码学运行时 | ❌ 缺失 | P2 |

### 8.3 工具链 GAP

| 能力 | 状态 | 优先级 |
|------|------|--------|
| Windows MSVC 编译 | ✅ 已验证 | - |
| Linux GCC/Clang 编译 | ❌ 未验证 | P1 |
| 构建系统 (CMake/Makefile) | ❌ 缺失 | P1 |
| 调试信息生成 | ❌ 缺失 | P2 |
| 优化级别控制 | ⚠️ 仅 /O2 | P2 |
| 增量编译 | ❌ 缺失 | P2 |

### 8.4 Architecture GAP

| 问题 | 状态 | 优先级 |
|------|------|--------|
| TLL Native Runtime 与 host/c/ 代码复用 | ⚠️ 目前独立实现，后续应共享 | P0 |
| 闭包 lowering 策略 | ❌ 未定义 | P1 |
| 异常 lowering 策略 | ❌ 未定义 | P2 |
| 模块/跨文件编译策略 | ❌ 未定义 | P1 |
| 类型特化优化（静态类型生成） | ❌ 未实现 | P2 |
| Native Target 与 Bytecode Target 的语义一致性测试 | ❌ 缺失 | P0 |

---

## 九、Evidence

### 9.1 测试命令与结果

1. **Native Lowering 编译**:
   - 命令: `tllvm.exe tllc.tllbc compile compiler/native_lower.tll compiler/native_lower.tllbc`
   - 结果: 编译成功，8 functions, 285 constants, 38,154 bytes ✅

2. **集成测试编译**:
   - 命令: `tllvm.exe tllc.tllbc compile compiler/test_native_target.tll compiler/test_native_target.tllbc`
   - 结果: 编译成功，107 functions, 2508 constants ✅

3. **集成测试运行** (TLL Compiler Native Target 生成 C 代码):
   - 命令: `tllvm.exe compiler/test_native_target.tllbc`
   - 结果: 成功生成 C 代码 (517 bytes)，包含 tll_main 函数定义 ✅

4. **C 代码编译** (MSVC + TLL Native Runtime):
   - 命令: `cl /nologo /O2 /utf-8 /I native\runtime native/test_integration.c native/runtime/tll_native.c /Fe:native/test_integration.exe`
   - 结果: 编译成功 (exit 0)，无警告 ✅

5. **Native Executable 运行**:
   - 命令: `native/test_integration.exe`
   - 结果: Exit code 42 ✅

### 9.2 环境

- OS: Windows 10/11
- 编译器: MSVC (VS 2022 Build Tools, x64)
- TLL VM: host/c/tllvm.exe
- TLL Compiler: tools/TLLC/tllc.tllbc (Stage-2 自举产物)
- 基线: b32dc67 + P2-01-A 修复
- 时间: 2026-09-09

---

## 十、结论与建议

### 10.1 结论

1. **TLL Compiler Native Target 架构已设计并实现**：
   - 共享前端（Lexer/Parser/TypeChecker/AST）
   - 双后端（Bytecode Target + Native Target）
   - Native Target: AST → native_lower.tll → C 代码

2. **TLL Native Runtime ABI 已定义并最小实现**：
   - TLLValue（与 host/c/ 一致的 tagged union）
   - Array/Map 操作
   - 引用计数内存管理
   - IO、算术、比较运算

3. **最小集成验证成功**：
   - TLL Source → TLL Compiler (Native Target) → C → MSVC → Native EXE → return 42
   - 完整流程 6 个阶段全部通过

4. **Windows 平台已验证**，Linux 平台架构可行待验证

5. **TLL 自研与成熟工具链委托的职责已明确划分**

### 10.2 下一步建议

**P2-01-B.3 — Native Target 能力增强 + Runtime 整合**

1. **增强 native_lower.tll**：
   - 支持数组字面量和操作（P0）
   - 支持 Map 字面量和操作（P0）
   - 支持 while/for 循环（P1）
   - 支持 if/else（P1）
   - 支持字符串操作（P1）

2. **整合 TLL Native Runtime 与 host/c/**：
   - 提取共享代码（TLLValue、Array、Map、引用计数）
   - 避免代码重复
   - 确保 Bytecode Target 和 Native Target 语义一致

3. **建立 Native Target 测试套件**：
   - 与 Bytecode Target 对比测试
   - 确保两个 Target 的语义一致
   - 测试更复杂的 TLL 程序

4. **验证 Linux 平台**：
   - 安装 GCC/Clang 或使用 WSL
   - 验证 C 代码可在 Linux 上编译运行

**不建议**：现在实现完整的 Native Backend（指令选择/寄存器分配/linker），或扩大 Python Transpiler。

---

**豆包 A 停止施工，等待架构师裁决。**

**P2-01-B.2 结论：Native Backend Integration Architecture 已设计并通过最小集成验证。TLL Compiler 正式支持 Native Target（AST→native_lower.tll→C→MSVC/GCC→Native Executable），与 Bytecode Target 共享前端。TLL Native Runtime ABI 已定义并最小实现（TLLValue/Array/Map/引用计数/IO/算术/比较）。最小集成验证成功：TLL Source→TLL Compiler (Native Target)→C→MSVC→Native EXE→return 42。Windows 平台已验证，Linux 架构可行待验证。未 Push GitHub。**
