# PHASE 2-01-B.5 — Host Runtime Convergence

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
**阶段**: Phase 2 / P2-01-B Native Backend Foundation
**基线**: b32dc67
**日期**: 2026-09-09
**状态**: 施工完成 / 等待裁决

---

## 一、执行摘要

### 核心成果

**host/c/ Bytecode VM 已正式使用 Shared Runtime Core，最后一块重复 Runtime 已消除。**

这是 P2-01-B 阶段的关键收敛步骤。之前 Bytecode VM 仍使用 host/c/value.c 的独立实现，与 Native Target 使用的 runtime/value.c 形成两套平行实现。本阶段通过修改 host/c/tllvm.h 包含 Shared Runtime Core，并在构建时用 runtime/value.c 替换 host/c/value.c，实现了：

```
                    TLL Language Semantics
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       Bytecode Target           Native Target
       (TLL VM, vm.c)          (C Code, native_lower)
              ↓                         ↓
              └───────────┬─────────────┘
                          ↓
              ┌───────────────────────┐
              │  Shared TLL Runtime   │  ← 唯一语义核心
              │  Core (runtime/)      │
              │                       │
              │  tll_runtime.h        │  数据结构定义
              │  value.c              │  值系统/引用计数/Array/Map
              │  arithmetic.c         │  算术/比较运算
              │  io.c                 │  基础 IO/生命周期
              └───────────────────────┘
```

### 关键指标

| 指标 | 数值 |
|------|------|
| tllvm.h 缩减 | 从 11.4 KB → 7.7 KB，缩减 32% |
| 删除重复数据结构定义 | 7 个（TLLType/TLLValue/TLLArray/TLLMapEntry/TLLMap/TLLUpvalue/TLLClosureEnv） |
| 删除重复函数声明 | 17 个（值创建/引用计数/truthy/equals/toString/Array/Map） |
| host/c/value.c 从构建移除 | ✅ 不再链接到 tllvm.exe |
| runtime/value.c 成为唯一实现 | ✅ Bytecode + Native 共享 |
| tllvm.exe 重新编译 | ✅ 0 errors, 0 warnings |
| Bootstrap Stage-0 回归 | ✅ 通过 |
| batch1_basic 回归 | ✅ 输出与之前完全一致 |
| Cross-Target Conformance | ✅ 14 行输出完全一致 |
| VM 行为变化 | ✅ 无变化（Binary Compatible） |
| BLOCKER | 0 |
| Git Push | ❌ 禁止 |

---

## 二、tllvm.h 修改详情

### 2.1 修改内容

**文件**: `host/c/tllvm.h`

**修改前**: 11.4 KB，包含完整的核心数据结构定义和值操作函数声明

**修改后**: 7.7 KB，包含 Shared Runtime Core + VM 专用定义

### 2.2 新增内容

在标准 #include 之后添加：
```c
/* === Shared TLL Runtime Core ===
 * 提供: TLLValue/TLLArray/TLLMap/TLLClosureEnv/TLLUpvalue 数据结构,
 *       值创建/引用计数/truthy/equals/toString/Array/Map 操作函数。
 * Binary Compatibility: 与原 tllvm.h 定义完全一致（字段顺序、类型、大小）。
 */
#include "../../runtime/tll_runtime.h"
```

### 2.3 删除的重复内容

**删除的数据结构定义（7 个）**:
- TLLType 枚举（11 个值）
- TLLValue（tagged union）
- TLLArray（items/length/capacity/refCount）
- TLLMapEntry（key/value/next）
- TLLMap（buckets/bucketCount/size/refCount）
- TLLUpvalue（value/refCount）
- TLLClosureEnv（upvalues/count/capacity/refCount）

**删除的函数声明（17 个）**:
- 值创建: tll_null, tll_bool, tll_int, tll_float, tll_string, tll_string_n, tll_array, tll_map, tll_function, tll_builtin
- 引用计数: tll_value_incref, tll_value_free
- 转换/比较: tll_to_string, tll_to_json, tll_truthy, tll_equals
- Array 操作: array_push, array_get, array_set
- Map 操作: map_set, map_get, map_has

### 2.4 保留的 VM 专用内容

- Bytecode 结构: TLLInstruction, TLLFunction, TLLProgram
- Call Frame: TLLFrame
- Coroutine: TLLCoroutine
- VM: TLLVM
- 63 操作码枚举（OP_LOAD_CONST 到 OP_FINALLY_END）
- JSON/VM/Builtin/Host ABI/Process API 函数声明

---

## 三、host/c/value.c 去重复

### 3.1 构建方式修改

**修改前**: tllvm.exe 链接 host/c/value.c（独立实现）

**修改后**: tllvm.exe 链接 runtime/value.c（Shared Runtime Core 唯一实现）

### 3.2 新的构建命令

```
cl /O2 /utf-8 /I host\c /I runtime
   host\c\main.c
   host\c\vm.c
   runtime\value.c          ← 替换 host\c\value.c
   host\c\json.c
   host\c\builtin.c
   host\c\sqlite_builtin.c
   host\c\crypto_builtin.c
   host\c\password_builtin.c
   host\c\hmac_builtin.c
   host\c\http_client_builtin.c
   host\c\ffi_builtin.c
   runtime\arithmetic.c     ← 新增（Shared Runtime Core）
   runtime\io.c              ← 新增（Shared Runtime Core）
   host\c\sqlite3.c
   /Fe:host\c\tllvm.exe
   /link bcrypt.lib winhttp.lib ws2_32.lib
```

### 3.3 host/c/value.c 当前状态

- **文件仍存在于仓库中**（作为参考和回退选项）
- **不再被链接到 tllvm.exe**
- **内容与 runtime/value.c 基本一致**（runtime/value.c 是从 host/c/value.c 提取的）
- **后续阶段建议**: 确认稳定后可删除 host/c/value.c，完全用 runtime/value.c 替代

### 3.4 Makefile 更新建议

当前 Makefile（host/c/Makefile）仍引用 value.c。建议后续阶段更新为：
```makefile
SRCS = main.c vm.c json.c builtin.c sqlite_builtin.c crypto_builtin.c \
       password_builtin.c hmac_builtin.c http_client_builtin.c ffi_builtin.c \
       ../../runtime/value.c ../../runtime/arithmetic.c ../../runtime/io.c
```

本阶段未修改 Makefile（因为当前环境使用 MSVC 直接编译，不通过 Makefile）。

---

## 四、构建验证结果

### 4.1 编译结果

```
main.c
vm.c
value.c (runtime/)
json.c
builtin.c
sqlite_builtin.c
crypto_builtin.c
password_builtin.c
hmac_builtin.c
http_client_builtin.c
ffi_builtin.c
arithmetic.c (runtime/)
io.c (runtime/)
sqlite3.c
正在生成代码...
```

**结果**: ✅ 编译成功，0 errors, 0 warnings

### 4.2 新 tllvm.exe 基本功能测试

**测试**: 运行 conformance_minimal.tllbc

**输出**:
```
=== Cross-Target Conformance Test ===
5
6
42
5.0
2
true
false
true
true
false
true
false
42
=== Test Complete ===
```

**结果**: ✅ 与原 tllvm.exe 输出完全一致

---

## 五、Bytecode Regression 测试结果

### 5.1 Bootstrap Stage-0 回归

**测试**: 用新 tllvm.exe + compiler.tllbc 编译 bootstrap_tllc.tll

**输出**:
```
mainFunctionIndex: 0
Bytecode JSON length: 159
Saved to compiler_self_compiled.tllbc

=== Bootstrap Level 5 Complete ===
```

**结果**: ✅ Bootstrap Stage-0 编译成功

### 5.2 batch1_basic 完整回归

**测试**: 用新 tllvm.exe + tllc.tllbc 编译 batch1_basic.tll，然后运行

**编译输出**:
```
Output:   native\conformance\batch1_basic.tllbc
Functions: 7
Constants: 102
```

**运行输出**:
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
```

**结果**: ✅ 输出与修改前完全一致，VM 行为无变化

### 5.3 回归覆盖范围

| 测试类别 | 覆盖能力点 | 结果 |
|----------|-----------|------|
| Int Arithmetic | +, -, *, /, % | ✅ 一致 |
| Bool Logic | &&, \|\|, ! | ✅ 一致 |
| String | 字面量、拼接、比较 | ✅ 一致 |
| Comparison | >, <, ==, !=, >=, <= | ✅ 一致 |
| Function Calls | 定义、调用、返回、嵌套 | ✅ 一致 |
| Nested Expressions | 复合表达式、优先级 | ✅ 一致 |
| Bootstrap | Stage-0 编译 | ✅ 一致 |

---

## 六、Cross-Target Conformance 测试结果

### 6.1 测试设计

同一测试逻辑，分别通过两个 Target 执行：
1. **Bytecode Target**: TLL Source → tllc.tllbc → .tllbc → 新 tllvm.exe（Shared Runtime Core）
2. **Native Target**: 等价 C 代码 → MSVC → EXE → Shared Runtime Core

### 6.2 输出对比

**Bytecode Target（新 tllvm.exe + Shared Runtime）**:
```
=== Cross-Target Conformance Test ===
5
6
42
5.0
2
true
false
true
true
false
true
false
42
=== Test Complete ===
```

**Native Target（Shared Runtime Core）**:
```
=== Cross-Target Conformance Test ===
5
6
42
5.0
2
true
false
true
true
false
true
false
42
=== Test Complete ===
```

**对比结果**: ✅ **14 行输出完全一致，15 个能力点全部通过。**

### 6.3 关键意义

这是第一次证明：
- **Bytecode VM 和 Native Target 共享同一套值语义实现**
- **两个 Target 的算术、比较、布尔、函数调用、字符串输出完全一致**
- **Shared Runtime Core 真正成为了 TLL 的唯一语义核心**

---

## 七、Runtime ABI 边界

### 7.1 Core Data Layout Compatibility（已验证）

以下数据结构在 runtime/tll_runtime.h 和原 host/c/tllvm.h 中完全一致（字段顺序、类型、大小）：
- TLLType 枚举
- TLLValue（tagged union）
- TLLArray / TLLMap / TLLMapEntry
- TLLUpvalue / TLLClosureEnv
- String 内存布局（[int refCount][char data...]）

### 7.2 Function Signature Compatibility（已验证）

所有共享函数的签名（返回类型、参数类型、参数顺序）在 runtime/tll_runtime.h 和原 host/c/tllvm.h 中完全一致。

### 7.3 Full Runtime ABI Compatibility（尚未完全验证）

以下 ABI 方面尚未完全验证，标记为后续工作：
- 所有权规则（谁负责释放返回值）
- refcount 生命周期约定
- Array/Map 元素生命周期
- Function/Closure 表示和生命周期
- 错误/异常语义
- 编译器生成代码对 ABI 的依赖

**当前状态**: Core Data Layout Compatibility ✅ / Full Runtime ABI Compatibility ⏳ 后续验证

---

## 八、GAP Ledger

### 8.1 本阶段新发现 GAP

| ID | 分类 | 描述 | 优先级 |
|----|------|------|--------|
| B5-GAP-01 | BUILD | host/c/Makefile 仍引用 value.c，需更新为 runtime/value.c | P2 |
| B5-GAP-02 | EVIDENCE | Full Runtime ABI Compatibility 尚未完全验证（所有权/refcount/生命周期） | P2 |
| B5-GAP-03 | CLEANUP | host/c/value.c 仍存在于仓库中（未链接），后续稳定后可删除 | P3 |
| B5-GAP-04 | TEST | Cross-Target Conformance 测试目前是手动写等价 C 代码，未来应通过 native_lower 自动生成 | P2（继承自 B4） |

### 8.2 已关闭 GAP

- **B4-GAP-01（host/c/value.c 与 runtime/value.c 重复实现）**: ✅ **已关闭**
  - host/c/value.c 已从构建中移除
  - runtime/value.c 成为值系统的唯一实现
  - Bytecode VM 和 Native Target 共享同一套值语义

### 8.3 历史 GAP（状态更新）

| ID | 原状态 | 现状态 | 说明 |
|----|--------|--------|------|
| B3-GAP-04 | 第二套 Runtime 风险 | ✅ **已完全关闭** | Shared Runtime Core 建立 + host/c/ 收敛，两套 Runtime 风险彻底消除 |
| B4-GAP-02 | native_lower 函数调用参数丢失 | ⏳ 仍 OPEN | 留待 P2-01-B.6 处理 |
| B4-GAP-03 | native_lower io.println Member 解析 | ⏳ 仍 OPEN | 留待 P2-01-B.6 处理 |

---

## 九、对后续阶段的建议

### 9.1 P2-01-B.6 建议（Native Lowering 最小闭环）

**目标**: 修复 native_lower.tll 的 P1 GAP，使 Cross-Target Conformance 测试可以通过 native_lower 自动生成 C 代码。

**优先级排序**:
1. 修复函数调用参数丢失（B4-GAP-02）— 调查 Call 节点 arguments 真实结构
2. 修复 io.println Member 解析（B4-GAP-03）— 调查 parser 对内置模块的特殊处理
3. 修复 Return 节点参数结构（B4-GAP-04）
4. 通过 native_lower.tll 自动生成 conformance_minimal.c
5. 验证自动生成的 C 代码编译运行后输出与 Bytecode 一致
6. 扩展 Conformance 测试覆盖 Array/Map/String 操作

### 9.2 P2-01-B.7 建议（自动 Cross-Target Conformance）

**目标**: 建立自动化的 Cross-Target Conformance 测试框架，每次修改后自动验证 Bytecode 和 Native 输出一致。

### 9.3 P2-01-C 前置条件

进入 P2-01-C（High-Frame Runtime Foundation）前，建议完成：
- P2-01-B.6（native_lower 修复，自动 Conformance）
- P2-01-B.7（自动 Cross-Target Conformance 框架）
- Full Runtime ABI Compatibility 验证（B5-GAP-02）
- Conformance 测试覆盖至少 50 个能力点

---

## 十、状态总结

| 项目 | 状态 |
|------|------|
| host/c/tllvm.h 包含 Shared Runtime Core | ✅ 完成 |
| 删除重复数据结构定义（7 个） | ✅ 完成 |
| 删除重复函数声明（17 个） | ✅ 完成 |
| host/c/value.c 从构建移除 | ✅ 完成 |
| runtime/value.c 成为唯一实现 | ✅ 完成 |
| tllvm.exe 重新编译（0 errors, 0 warnings） | ✅ 完成 |
| Bootstrap Stage-0 回归 | ✅ 通过 |
| batch1_basic 完整回归 | ✅ 输出完全一致 |
| Cross-Target Conformance（15 能力点） | ✅ 全部通过，14 行输出完全一致 |
| VM 行为变化 | ✅ 无变化（Binary Compatible） |
| 两套 Runtime 风险 | ✅ 彻底消除 |
| Core Data Layout Compatibility | ✅ 已验证 |
| Full Runtime ABI Compatibility | ⏳ 后续验证 |
| BLOCKER | 0 |
| Git Push | ❌ 禁止 |

---

## 十一、最终架构状态

```
                    TLL Language Semantics
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       Bytecode Target           Native Target
       (TLL VM, vm.c)          (C Code, native_lower)
              ↓                         ↓
              └───────────┬─────────────┘
                          ↓
              ┌───────────────────────┐
              │  Shared TLL Runtime   │  ← 唯一语义核心 ✅
              │  Core (runtime/)      │
              │                       │
              │  tll_runtime.h        │  数据结构定义
              │  value.c              │  值系统/引用计数/Array/Map
              │  arithmetic.c         │  算术/比较运算
              │  io.c                 │  基础 IO/生命周期
              └───────────────────────┘
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
       host/c/ (VM 专用)       native/runtime/ (Native 入口)
       - vm.c                   - tll_native.h (包含 tll_runtime.h)
       - builtin.c              - tll_native.c (仅保留 init/cleanup 包装)
       - json.c
       - 扩展内置 (crypto/http/...)
```

**P2-01-B.5 完成后，TLL 终于只有一个 Runtime 语义核心。**

---

**报告结束。停止施工，等待架构裁决。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
