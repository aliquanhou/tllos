# PHASE 2-01-B.10 — Native Ownership & Structured Data Hardening

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
**阶段**: Phase 2 / P2-01-B Native Backend Foundation
**基线**: b32dc67 / P2-01-B9-PASS (2310baf)
**日期**: 2026-09-09
**状态**: 施工完成 / 等待裁决

---

## 一、执行摘要

### 核心成果

**P2-01-B.10 完成两个核心目标：Native Ownership/Refcount 基础框架 + Map Native Conformance。**

本阶段完成了架构师要求的 B.10 任务：
1. ✅ **Native Ownership / Refcount**: 建立所有权规则文档，实现基本的引用计数（函数结束时 free 局部变量，return 时 incref 返回值 + free 局部变量）
2. ✅ **Map Native Conformance**: Map literal、Map index 读/写，全部进入自动 Cross-Target Conformance
3. ✅ **Bool AST 修复**: 发现并修复 Bool.value 是布尔类型而非字符串的长期 bug
4. ✅ **tll_array_from 删除**: 无实际消费者，按照"不要产生死 API"原则删除
5. ✅ **7 个 Conformance Cases 全部 PASS**
6. ✅ **Bootstrap/VM regression 无倒退**

### 关键指标

| 指标 | B.9 状态 | B.10 状态 | 变化 |
|------|---------|---------|------|
| Conformance Cases | 6 个 | 7 个 | +1 (06_map) |
| 全部 PASS | ✅ 6/6 | ✅ 7/7 | +1 |
| Native 支持能力 | 15 项 | 17 项 | +2 (Map literal, Map index) |
| Shared Runtime 函数 | 38 个 | 37 个 | -1 (删除 tll_array_from) |
| Ownership/Refcount 文档 | ❌ 无 | ✅ v1.0 | 新增 |
| 基本引用计数实现 | ❌ 无 | ✅ 基础实现 | 新增 |
| Bootstrap/VM regression | ✅ | ✅ | 无倒退 |
| BLOCKER | 0 | 0 | 无 |
| Git Push | ❌ 禁止 | ❌ 禁止 | 不变 |

---

## 二、Native Ownership / Refcount

### 2.1 所有权规则文档

**文件**: `docs/TLL-NATIVE-OWNERSHIP-REFCOUNT-RULES-v1.0.md`

**核心规则**:
1. **创建**: 值创建函数返回的 TLLValue 引用计数为 1，调用者拥有
2. **赋值**: 变量赋值时，先 free 旧值，再 incref 新值
3. **函数参数**: 调用者传递参数时 incref，被调用者在函数结束时 free
4. **函数返回**: 函数返回值时 incref，调用者负责 free
5. **容器元素**: Array/Map 存储元素时 incref，释放时 free 所有元素
6. **作用域结束**: 变量作用域结束时 free 所有局部变量

### 2.2 基本引用计数实现

在 `native_lower.tll` 中实现了基本的引用计数：

1. **局部变量跟踪**: 新增全局变量 `nl_localVars`，在每个函数开始时重置，在 Let/Const 声明时记录变量名

2. **函数结束时 free 局部变量**: 在 `nl_lowerFunction` 中，如果函数不以显式 return 结束，在函数结束前生成 free 所有局部变量的代码

3. **return 时 incref 返回值 + free 局部变量**: 在 `nl_lowerStatement` 中处理 Return 时，先 incref 返回值，然后 free 所有局部变量，再 return

**生成的 C 代码示例**:
```c
TLLValue tll_main(void) {
    TLLValue x = tll_int(10);
    TLLValue s = tll_string("hello");
    // ... use x and s ...
    /* B.10: refcount cleanup before return */
    tll_value_incref(tll_int(0));
    tll_value_free(x);
    tll_value_free(s);
    return tll_int(0);
}
```

### 2.3 当前限制

- **变量赋值时的 free 旧值**: 尚未实现（当前直接覆盖，旧值泄漏）
- **函数参数的 incref/free**: 尚未实现
- **容器元素的完整引用计数**: array_set/map_set 内部 free 旧值，但未 incref 新值
- **多 return 点的处理**: 当前每个 return 点都会 free 局部变量，但如果 return 在 if/else 块中，可能会重复 free
- **块级作用域**: 当前所有局部变量在函数结束时 free，不支持块级作用域

这些限制列为 GAP，留待后续阶段完善。

---

## 三、Map Native Conformance

### 3.1 Map AST 结构确认

通过查看 `parser.tll` 源码，确认 Map 的 AST 结构：

- **kind**: "Map"
- **entries**: 列表，每个元素是 Entry 节点
  - **Entry.key**: 字符串（键名）
  - **Entry.value**: 表达式（值）

Map 索引访问使用 Index 节点，与 Array 相同：
- **Index.object**: Map 表达式
- **Index.index**: 键表达式（通常是字符串字面量）

### 3.2 Map literal 实现

在 `nl_lowerStatement` 的 Let/Const 处理中，添加 Map literal 特殊处理（与 Array literal 相同的方式，避免 MSVC C99 复合字面量问题）：

```c
TLLValue m = tll_map();
map_set(m.as.map, "a", tll_int(1));
map_set(m.as.map, "b", tll_int(2));
```

### 3.3 Map index 读访问

在 `nl_lowerExpression` 的 Index 处理中，区分 Array 和 Map：
- 如果 index 是字符串字面量，使用 `map_get(obj.as.map, "key")`
- 否则使用 `array_get(obj.as.array, idx.as.integer)`

### 3.4 Map index 写访问

在 `nl_lowerExpression` 的 Binary operator="=" 处理中，添加 Map index 赋值：
```c
(map_set(m.as.map, "key", value), value)
```

### 3.5 Map Conformance 测试

**文件**: `tests/native/06_map.tll`

**覆盖能力**:
- Map literal（`{"a": 1, "b": 2}`）
- Map index 读（`m["a"]`）
- Map index 写（`m["a"] = 100`）
- Map 新增键（`m["d"] = 400`）
- Map with string values
- Map with mixed values（int/string/bool）
- Empty map + nonexistent key

**结果**: ✅ PASS（stdout identical, exit code identical）

---

## 四、Bool AST 修复

### 4.1 问题发现

在 Map 测试中发现：`mixed["bool"]` 的值，Bytecode 输出 `true`，Native 输出 `false`。

检查生成的 C 代码发现：`true` 被转换成了 `tll_bool(0)` 而不是 `tll_bool(1)`。

### 4.2 根因

`native_lower.tll` 中 Bool 的处理：
```tll
if expr.value == "true" { return "tll_bool(1)" }
return "tll_bool(0)"
```

但是，通过查看 `parser.tll` 源码确认：AST 中 Bool 的 value 字段是**布尔类型**（`true`/`false`），不是字符串类型（`"true"`/`"false"`）。

所以 `expr.value == "true"` 永远不会成立，所有 bool 值都被转换成了 `tll_bool(0)`。

### 4.3 修复

```tll
// B.10 FIX: AST Bool.value is boolean type, not string
if expr.value { return "tll_bool(1)" }
return "tll_bool(0)"
```

### 4.4 影响

这个 bug 从 B.2 开始就存在，但之前的测试用例中没有直接使用 bool 字面量（01_basic 测试使用的是比较表达式的结果，不是 bool 字面量），所以一直没有被发现。

修复后，所有 7 个 Conformance Cases 仍然全部 PASS。

---

## 五、tll_array_from 删除

### 5.1 背景

B.9 中新增了 `tll_array_from(TLLValue *items, int count)` 函数，用于从 C 数组创建 TLL 数组。

但是，由于 MSVC 不支持 C99 复合字面量 `(TLLValue[]){...}`，最终 Array literal 使用了 `tll_array() + array_push()` 的方式，`tll_array_from` 没有实际消费者。

### 5.2 架构师要求

B.9 架构师裁决中明确要求：
> B.10 应该检查：tll_array_from 实际使用？如果没有：删除，或者：保留为明确的 Runtime API，并增加实际消费者。不要产生新的死 API。

### 5.3 决定：删除

经过评估，决定删除 `tll_array_from`，原因：
1. 当前没有实际消费者
2. MSVC 不支持 C99 复合字面量，这个函数在当前架构下很难使用
3. 避免产生死 API
4. 如果未来需要，可以重新添加

### 5.4 修改

- `runtime/value.c`: 删除 `tll_array_from` 函数实现
- `runtime/tll_runtime.h`: 删除 `tll_array_from` 函数声明
- `docs/TLL-SHARED-RUNTIME-ABI-CONTRACT-v1.0.md`: 更新函数数量（38→37），移除 `tll_array_from` 记录

---

## 六、Conformance Cases（7/7 PASS）

| # | Case | 覆盖能力 | 结果 |
|---|------|---------|------|
| 1 | cross_target_minimal | function/let/arithmetic/return/io/string | ✅ PASS |
| 2 | 01_basic | arithmetic/comparison/bool | ✅ PASS |
| 3 | 02_function | function/params/nested call | ✅ PASS |
| 4 | 03_io | string/concat/mixed output | ✅ PASS |
| 5 | 04_control_flow | reassignment/while/if-else/nested | ✅ PASS |
| 6 | 05_array | array literal/index read/index assign/length/iteration | ✅ PASS |
| 7 | 06_map | map literal/index read/index write/mixed values/empty map | ✅ PASS |

**总计**: 7/7 PASS ✅

---

## 七、Bootstrap / VM Regression

| 测试 | 结果 | 说明 |
|------|------|------|
| Bootstrap Stage-0 | ✅ PASS | Bootstrap Level 5 Complete |
| batch1_basic | ✅ PASS | 35 行输出，与之前完全一致 |
| conformance_minimal | ✅ PASS | 14 行输出 |
| **总 regression** | ✅ **无倒退** | |

---

## 八、GAP Ledger（编号归并）

### 8.1 已关闭 GAP

| ID | 描述 | 关闭阶段 |
|----|------|---------|
| B9-GAP-01 | tll_array_from 无消费者 | B.10（删除函数） |
| B5-GAP-02 | Full Runtime ABI Compatibility | B.9（ABI Contract v1.0 建立，Ownership/Refcount 仍为 OPEN） |

### 8.2 仍 OPEN GAP（carry forward）

| ID | 分类 | 描述 | 优先级 |
|----|------|------|--------|
| B7-GAP-01 | SEMANTICS | Native Target 暂不支持 process.exit(code) | P2 |
| B7-GAP-03 | COVERAGE | Native Lowering 覆盖范围有限（当前 17 项，Closure/Exception/Coroutine/Network 等尚未支持） | P1 |
| B8-GAP-01 | TEST | 缺少批量运行器（一次运行所有 cases 并生成汇总报告） | P2 |
| B9-GAP-01 | COVERAGE | Array/Map literal 只能在 Let/Const 语句中使用，不能作为函数参数或 return 值 | P2 |
| B10-GAP-01 | MEMORY | Native Target 引用计数不完整（变量赋值时未 free 旧值，函数参数未 incref/free，容器元素未完整 incref） | P1 |
| B10-GAP-02 | MEMORY | 多 return 点可能重复 free 局部变量 | P2 |
| B10-GAP-03 | MEMORY | 不支持块级作用域（所有局部变量在函数结束时 free） | P3 |
| B6-GAP-01 | DOCUMENTATION | 4 个文档构建命令示例需更新 | P3 |
| B6-GAP-02 | PLATFORM | GCC/Linux 构建路径需在 Linux 环境验证 | P2 |
| B6-GAP-03 | CI | CI 配置可能仍引用旧构建命令 | P2 |

### 8.3 明确不做（架构师禁止）

- Closure Native lowering
- Coroutine Native lowering
- Network Native lowering
- FFI Native lowering
- LLVM backend
- Linux Native
- GPU Runtime
- High-Frame Runtime
- For/Break/Continue（排队）
- 大量 String API（排队）

---

## 九、对后续阶段的建议

### 9.1 P2-01-B.11 建议（Native Target Hardening）

**目标**: 巩固 Native Target，解决关键 GAP，准备 Seal。

**建议优先级**:
1. **完整引用计数实现**（B10-GAP-01，P1）: 变量赋值时 free 旧值，函数参数 incref/free，容器元素完整 incref
2. **批量 Conformance 运行器**（B8-GAP-01，P2）: 一次运行所有 cases，生成汇总报告
3. **String 操作扩展**（B7-GAP-03，P2）: length、比较、切片、拼接
4. **For/Break/Continue**（B7-GAP-03，P2）: 更多控制流
5. **Array/Map literal 作为函数参数**（B9-GAP-01，P2）: 扩展 literal 使用场景

### 9.2 Native Target Seal 前置条件

进入 Native Target Seal 前，建议完成：
- P2-01-B.11（Native Target Hardening）
- 完整引用计数实现
- String 操作基础支持
- 批量 Conformance 运行器
- 10+ Conformance Cases 全部 PASS
- ABI Contract 升级到 v1.1（包含完整引用计数规则验证）

### 9.3 P2-01-C 前置条件

进入 P2-01-C（High-Frame Runtime Foundation）前，必须完成：
- Native Target Seal
- Full Runtime ABI Compatibility 验证
- 文档构建命令更新
- CI 配置检查更新
- GCC/Linux 构建验证

---

## 十、交付物清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `compiler/native_lower.tll` | 修改：Map literal/index、Bool 修复、引用计数基础实现、局部变量跟踪 | ✅ |
| `runtime/value.c` | 修改：删除 tll_array_from 函数 | ✅ |
| `runtime/tll_runtime.h` | 修改：删除 tll_array_from 声明 | ✅ |
| `tests/native/06_map.tll` | 新建：Conformance Case 06（Map literal/index/mixed/empty） | ✅ |
| `docs/TLL-NATIVE-OWNERSHIP-REFCOUNT-RULES-v1.0.md` | 新建：Native 所有权和引用计数规则文档 | ✅ |
| `docs/TLL-SHARED-RUNTIME-ABI-CONTRACT-v1.0.md` | 修改：更新函数数量（38→37），移除 tll_array_from，Ownership/Refcount = OPEN | ✅ |
| `docs/PHASE2-01-B.10-NATIVE-OWNERSHIP-MAP.md` | 新建：完整报告 | ✅ |

---

## 十一、状态总结

| 项目 | 状态 |
|------|------|
| Native Ownership/Refcount 规则文档 | ✅ 完成（v1.0） |
| 基本引用计数实现 | ✅ 完成（函数结束 free + return incref） |
| Map literal | ✅ 完成（Let/Const 特殊处理） |
| Map index 读/写 | ✅ 完成（map_get/map_set） |
| Bool AST 修复 | ✅ 完成（Bool.value 是布尔类型） |
| tll_array_from 删除 | ✅ 完成（无消费者，避免死 API） |
| 新增 Conformance Cases | ✅ 1 个（06_map） |
| 全部 Conformance Cases | ✅ 7/7 PASS |
| Bootstrap/VM regression | ✅ 无倒退 |
| GAP 编号归并 | ✅ 完成 |
| BLOCKER | 0 |
| Git Push | ❌ 禁止 |

---

## 十二、最终架构状态

```
                    TLL Language Semantics
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       Bytecode Target           Native Target
       (tllc.tllbc)              (native_lower.tll)
              ↓                         ↓
          .tllbc                    .c (自动生成)
              ↓                         ↓
           tllvm.exe               MSVC (0 errors)
              ↓                         ↓
          运行输出                  运行输出
              └───────────┬───────────┘
                          ↓
                   自动比较一致性 ✅
                   stdout: IDENTICAL
                   exit code: IDENTICAL
                          ↓
                   自动记录 Evidence ✅

Conformance Cases: 7 个，全部 PASS ✅
  cross_target_minimal / 01_basic / 02_function
  03_io / 04_control_flow / 05_array / 06_map

Native 能力: 17 项
  let/const/Int/Float/String/Bool/Null
  arithmetic/comparison/boolean logic
  function declaration/call/return
  io.println/io.print
  block/if-else/while
  variable reassignment
  Array literal/index read/index write/length
  Map literal/index read/index write

Shared Runtime Core (runtime/):
  tll_runtime.h, value.c, arithmetic.c, io.c
  37 个函数，7 个数据结构
  ABI Contract v1.0 ✅
  Ownership/Refcount Rules v1.0 ✅
  基本引用计数实现 ✅
  ← Bytecode 和 Native 共享同一套语义 ✅
```

**P2-01-B.10 完成后，TLL Native Target 从"具备基础结构化数据"扩展到"具备 Map + 基本引用计数管理"的状态，并且每一种能力都有自动 Cross-Target Conformance 保障。同时，Native Ownership/Refcount 规则文档的建立，标志着 TLL 从"能跑"进入"有明确内存管理规则"的工程化阶段。**

---

**报告结束。停止施工，等待架构裁决。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
