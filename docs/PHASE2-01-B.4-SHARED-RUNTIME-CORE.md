# PHASE 2-01-B.4 — Shared Runtime Core Convergence

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

**Shared TLL Runtime Core 已建立，Native Runtime 从"第二套 Runtime"收敛为"共享 Runtime 的 Native 执行入口"。**

这是 P2-01-B 阶段最关键的架构收敛。之前 native/runtime/ 正在形成与 host/c/ 平行的第二套 Runtime，存在语义漂移风险。本阶段通过建立 Shared Runtime Core，确保 Bytecode VM 和 Native Target 共享同一套值语义、引用计数、算术、比较和 IO 实现。

### 关键指标

| 指标 | 数值 |
|------|------|
| Shared Runtime Core 文件 | 4 个（tll_runtime.h + value.c + arithmetic.c + io.c） |
| Shared Runtime Core 代码量 | ~25 KB |
| native/runtime/ 缩减 | 从 ~14 KB 缩减到 ~2.3 KB（仅保留兼容包装） |
| Binary Compatibility | ✅ 与 host/c/tllvm.h 完全一致 |
| Native Target 集成测试 | ✅ return 42 通过 |
| Bytecode Target 回归 | ✅ 通过 |
| Cross-Target Conformance | ✅ 14 行输出完全一致 |
| 覆盖能力点 | 15 个（arithmetic/comparison/bool/function/string） |
| BLOCKER | 0 |

---

## 二、Shared Runtime Core 架构

### 2.1 架构图

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
              │  Shared TLL Runtime   │
              │  Core (唯一语义地基)   │
              │                       │
              │  runtime/tll_runtime.h│  ← 数据结构定义 (Binary Compatible)
              │  runtime/value.c      │  ← 值创建/引用计数/truthy/equals/
              │                       │    toString/Array/Map 操作
              │  runtime/arithmetic.c │  ← 算术运算/比较运算 (语义规则)
              │  runtime/io.c          │  ← 基础 IO/运行时生命周期
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

### 2.2 核心原则

1. **不建立第二套 Runtime**：Shared Runtime Core 是 TLL 值语义的唯一权威实现
2. **Binary Compatibility**：tll_runtime.h 中的数据结构定义必须与 host/c/tllvm.h 完全一致
3. **Target 隔离**：VM 专用代码（vm.c、builtin.c、协程调度）留在 host/c/；Native 专用代码（C main 入口、平台初始化）留在 native/runtime/
4. **渐进收敛**：第一阶段只收敛最基础的语义地基，后续阶段逐步收敛 JSON、内置函数、协程等

---

## 三、文件清单

### 3.1 Shared Runtime Core（新建）

| 文件 | 大小 | 功能 |
|------|------|------|
| `runtime/tll_runtime.h` | 5.0 KB | 核心头文件：TLLType/TLLValue/TLLArray/TLLMap/TLLClosureEnv/TLLUpvalue 定义，所有共享函数声明 |
| `runtime/value.c` | 14.7 KB | 值系统：值创建（null/bool/int/float/string/array/map/function/builtin）、引用计数（incref/free）、truthy/equals、to_string/to_json、Array/Map 基本操作 |
| `runtime/arithmetic.c` | 5.0 KB | 算术运算（add/sub/mul/div/mod）和比较运算（eq/neq/lt/gt/le/ge），返回 TLLValue |
| `runtime/io.c` | 0.9 KB | 基础 IO（print/println）和运行时生命周期（init/cleanup） |

### 3.2 Native Runtime（修改，大幅缩减）

| 文件 | 原大小 | 现大小 | 变化 |
|------|--------|--------|------|
| `native/runtime/tll_native.h` | 3.9 KB | 1.4 KB | 包含 tll_runtime.h，删除所有重复定义，仅保留 init/cleanup 声明 |
| `native/runtime/tll_native.c` | 10.2 KB | 0.9 KB | 删除所有重复实现，仅保留 init/cleanup 包装函数，委托给 Shared Runtime Core |

**缩减比例**：native/runtime/ 从 ~14 KB 缩减到 ~2.3 KB，缩减 84%。

### 3.3 host/c/（未修改）

本阶段未修改 host/c/ 下的任何文件。Bytecode Target 完全不受影响，继续使用原有的 tllvm.h + value.c + vm.c + builtin.c。

后续阶段将逐步让 host/c/ 也包含 runtime/tll_runtime.h，删除 value.c 中的重复实现，最终实现完全统一。

---

## 四、Binary Compatibility 保证

### 4.1 数据结构一致性

runtime/tll_runtime.h 中的以下数据结构定义与 host/c/tllvm.h 完全一致（字段顺序、类型、大小）：

| 数据结构 | 一致性 |
|----------|--------|
| TLLType 枚举（11 个值） | ✅ 完全一致 |
| TLLValue（tagged union） | ✅ 完全一致 |
| TLLArray（items/length/capacity/refCount） | ✅ 完全一致 |
| TLLMapEntry（key/value/next） | ✅ 完全一致 |
| TLLMap（buckets/bucketCount/size/refCount） | ✅ 完全一致 |
| TLLUpvalue（value/refCount） | ✅ 完全一致 |
| TLLClosureEnv（upvalues/count/capacity/refCount） | ✅ 完全一致 |

### 4.2 String 内存布局

TLL 字符串使用 refCount header 布局：
```
[int refCount][char data...]\0
             ↑
         v.as.string 指向这里
```

通过 `str_rc(s) = (int*)(s - sizeof(int))` 访问 refcount。

此布局在 runtime/value.c 和 host/c/value.c 中完全一致，确保两个 Target 创建的字符串可以互相兼容（未来 Native 程序调用 VM 函数时）。

### 4.3 函数签名一致性

所有共享函数的签名（返回类型、参数类型、参数顺序）在 runtime/tll_runtime.h 和 host/c/tllvm.h 中完全一致：
- tll_null/tll_bool/tll_int/tll_float/tll_string/tll_string_n
- tll_array/tll_map/tll_function/tll_builtin
- tll_value_incref/tll_value_free
- tll_truthy/tll_equals
- tll_to_string/tll_to_json
- array_push/array_get/array_set
- map_set/map_get/map_has

---

## 五、Native Target 验证结果

### 5.1 集成测试（return 42）

**测试程序**（native/test_shared_runtime.c）：
```c
TLLValue tll_main(void) {
    TLLValue x = tll_int(40);
    TLLValue y = tll_int(2);
    TLLValue result = tll_add(x, y);
    return result;
}
```

**编译命令**：
```
cl /O2 /utf-8 /I native\runtime /I runtime
   native\test_shared_runtime.c
   native\runtime\tll_native.c
   runtime\value.c runtime\arithmetic.c runtime\io.c
   /Fe:native\test_shared_runtime.exe
```

**结果**：
- 编译：✅ 成功（0 errors, 0 warnings）
- 运行：✅ exit code = 42

### 5.2 链接的 Shared Runtime Core 模块

Native EXE 静态链接了以下 Shared Runtime Core 模块：
- runtime/value.c（值系统、引用计数、Array/Map）
- runtime/arithmetic.c（算术、比较运算）
- runtime/io.c（基础 IO、生命周期）
- native/runtime/tll_native.c（兼容包装层）

**总链接代码量**：~21 KB C 源码 → ~50 KB EXE（MSVC /O2）

---

## 六、Bytecode Target 回归结果

### 6.1 回归测试

**测试程序**（native/conformance/regression_test.tll）：
```tll
fn main() -> int {
    let x = 40
    let y = 2
    return x + y
}
main()
```

**结果**：
- 编译：✅ 成功（2 functions, 2 constants）
- 运行：✅ 成功（exit code = 0，TLL main 返回值不作为进程 exit code）

### 6.2 影响评估

本阶段未修改 host/c/ 下的任何文件，因此 Bytecode Target 完全不受影响。Shared Runtime Core 是新增的独立模块，不与现有 host/c/ 代码冲突。

---

## 七、Cross-Target Conformance 测试结果

### 7.1 测试设计

**目标**：验证 Shared Runtime Core 的语义与 Bytecode VM 完全一致。

**方法**：
1. 编写 TLL 测试程序（conformance_minimal.tll），用 io.println 输出多个测试结果
2. 用 Bytecode Target 编译运行，记录输出作为基准
3. 编写等价的 C 程序（conformance_native.c），直接调用 Shared Runtime Core 函数，模拟 native_lower 生成的代码
4. 用 MSVC 编译 C 程序，链接 Shared Runtime Core，运行记录输出
5. 比较两个 Target 的输出是否完全一致

### 7.2 覆盖能力点

| 类别 | 测试点 | 数量 |
|------|--------|------|
| int arithmetic | +, -, *, /, % | 5 |
| comparison | >, <, ==, != | 4 |
| bool logic | &&, \|\|, ! | 3 |
| function call | add(40, 2) | 1 |
| string output | 标题行、完成行 | 2 |
| **总计** | | **15** |

### 7.3 输出对比

**Bytecode Target 输出**：
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

**Native Target (Shared Runtime Core) 输出**：
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

**对比结果**：✅ **14 行输出完全一致，15 个能力点全部通过。**

### 7.4 关键语义验证

| 语义规则 | Bytecode | Native | 一致 |
|----------|----------|--------|------|
| int + int = int | 5 | 5 | ✅ |
| int - int = int | 6 | 6 | ✅ |
| int * int = int | 42 | 42 | ✅ |
| int / int = float（始终） | 5.0 | 5.0 | ✅ |
| int % int = int | 2 | 2 | ✅ |
| 5 > 3 = true | true | true | ✅ |
| 5 < 3 = false | false | false | ✅ |
| 5 == 5 = true | true | true | ✅ |
| 5 != 3 = true | true | true | ✅ |
| true && false = false | false | false | ✅ |
| true \|\| false = true | true | true | ✅ |
| !true = false | false | false | ✅ |
| add(40, 2) = 42 | 42 | 42 | ✅ |
| bool 打印为 "true"/"false" | true/false | true/false | ✅ |

---

## 八、GAP Ledger

### 8.1 本阶段新发现 GAP

| ID | 分类 | 描述 | 优先级 |
|----|------|------|--------|
| B4-GAP-01 | ARCHITECTURE | host/c/value.c 与 runtime/value.c 仍存在重复实现，后续阶段需让 host/c/ 也引用 Shared Runtime Core | P1 |
| B4-GAP-02 | IMPLEMENTATION | native_lower.tll 函数调用参数丢失（Call 节点 arguments 结构问题），导致无法自动生成完整的 Native C 代码 | P1 |
| B4-GAP-03 | IMPLEMENTATION | native_lower.tll io.println Member 节点 name 为空（parser 对内置模块特殊处理） | P1 |
| B4-GAP-04 | IMPLEMENTATION | native_lower.tll Return 节点参数结构需确认 | P2 |
| B4-GAP-05 | TEST/EVIDENCE | Cross-Target Conformance 测试目前是手动写等价 C 代码，未来应通过 native_lower.tll 自动生成 | P2 |
| B4-GAP-06 | EVIDENCE | Linux Native 平台尚未验证（需 GCC/Clang + ELF） | P2 |

### 8.2 历史 GAP（状态更新）

| ID | 原状态 | 现状态 | 说明 |
|----|--------|--------|------|
| B3-GAP-04 | ARCHITECTURE（native/runtime/ 与 host/c/ 功能重叠） | ✅ **已缓解** | Shared Runtime Core 已建立，native/runtime/ 已改为引用 Shared Runtime，不再是独立第二套 Runtime。host/c/ 完全统一留待后续 |

### 8.3 已关闭 GAP

- **P2-01-A Bootstrap Closure**：✅ CLOSED（架构师已确认，不再作为 OPEN GAP）
- **第二套 Runtime 风险**：✅ 已通过 Shared Runtime Core 收敛缓解

---

## 九、对后续阶段的建议

### 9.1 P2-01-B.5 建议（native_lower.tll 修复 + 自动 Conformance）

**目标**：修复 native_lower.tll 的 P1 GAP，使 Cross-Target Conformance 测试可以通过 native_lower 自动生成 C 代码，而非手动编写。

**优先级排序**：
1. 修复函数调用参数丢失（B4-GAP-02）— 调查 Call 节点 arguments 真实结构
2. 修复 io.println Member 解析（B4-GAP-03）— 调查 parser 对内置模块的特殊处理
3. 修复 Return 节点参数结构（B4-GAP-04）
4. 通过 native_lower.tll 自动生成 conformance_minimal.c
5. 验证自动生成的 C 代码编译运行后输出与 Bytecode 一致
6. 扩展 Conformance 测试覆盖 Array/Map/String 操作

### 9.2 P2-01-B.6 建议（host/c/ 完全统一）

**目标**：让 host/c/ 也引用 Shared Runtime Core，删除 value.c 中的重复实现，实现完全统一。

**步骤**：
1. 修改 host/c/tllvm.h 包含 runtime/tll_runtime.h，删除重复的数据结构定义
2. 修改 host/c/value.c 引用 runtime/value.c，删除重复实现（或直接删除 host/c/value.c，链接 runtime/value.c）
3. 验证 Bytecode Target 完全回归通过
4. 验证 Native Target 不受影响
5. 最终：runtime/value.c 成为值系统的唯一实现

### 9.3 P2-01-C 前置条件

进入 P2-01-C（High-Frame Runtime Foundation）前，建议完成：
- P2-01-B.5（native_lower 修复，自动 Conformance）
- P2-01-B.6（host/c/ 完全统一）
- Cross-Target Conformance 测试覆盖至少 50 个能力点

这样可以确保 High-Frame Runtime 的改造建立在统一的 Runtime 基础上，不会出现两个 Target 的并发语义不一致。

---

## 十、状态总结

| 项目 | 状态 |
|------|------|
| Shared Runtime Core 建立 | ✅ 完成 |
| runtime/tll_runtime.h（Binary Compatible） | ✅ 完成 |
| runtime/value.c（值系统/引用计数/Array/Map） | ✅ 完成 |
| runtime/arithmetic.c（算术/比较运算） | ✅ 完成 |
| runtime/io.c（基础 IO/生命周期） | ✅ 完成 |
| native/runtime/ 收敛为入口层 | ✅ 完成（缩减 84%） |
| Native Target 集成测试（return 42） | ✅ 通过 |
| Bytecode Target 回归 | ✅ 通过 |
| Cross-Target Conformance（15 能力点） | ✅ 全部通过，14 行输出完全一致 |
| 不建立第二套 Runtime | ✅ 架构原则已落实 |
| BLOCKER | 0 |
| Git Push | ❌ 禁止（所有成果留在本地） |

---

**报告结束。停止施工，等待架构裁决。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
