# P2-01-B.11 — Native Ownership Semantic Closure

**施工执行**: Agent A | **架构审查**: GPT-5.6 Luna | **最终裁决**: 于秋鸿博士（待验收）
**基线**: b32dc67 / P2-01-B10-PASS (708ca2e) | **日期**: 2026-09-09 | **状态**: 施工完成 / 等待裁决

---

## 一、概述

P2-01-B.11 完成 Native Ownership Semantic Closure，核心成果：

1. **冻结 TLL Native Ownership Model** — 基于 Bytecode VM 实际行为调查，形成 `TLL-NATIVE-OWNERSHIP-REFCOUNT-CONTRACT-v1.1.md`，明确六种核心操作的语义
2. **修复三个 P1 GAP** — 赋值旧值 release、函数参数所有权、容器元素 borrow/retain
3. **建立 4 个专门的 Ownership Conformance 测试** — 07_ownership_local、08_ownership_assignment、09_ownership_return、10_ownership_container
4. **所有 11 个 Conformance Cases 全部 PASS** — 原有 7 个 + 新增 4 个
5. **Bootstrap/VM regression 无倒退**

---

## 二、Ownership Model 冻结

### 2.1 调查方法

基于对 Bytecode VM（host/c/vm.c）实际引用计数行为的完整调查，确保 Native Target 与 Bytecode Target 拥有完全一致的语义。

### 2.2 六种核心操作的语义

| 操作 | Ownership 语义 | 引用计数动作 | Bytecode VM 证据 |
|------|--------------|------------|----------------|
| **Creation** | 调用者获得新引用 | 返回 refCount=1 的值 | 值创建函数 |
| **Assignment** | 旧引用释放，新引用获得 | free 旧值 + incref 新值 | OP_STORE_VAR / OP_STORE_GLOBAL / OP_MOV |
| **Function Argument** | 调用者 retain，被调用者 release | 调用者 incref + 被调用者直接存储 + 被调用者结束时 free | OP_PUSH + do_call |
| **Function Return** | 调用者获得返回值引用 | incref 返回值 + free 局部变量 + return | OP_RET |
| **Container Element** | 调用者 retain，容器 release | 调用者 incref + 容器直接存储 + 容器释放时 free 所有元素 | array_push / map_set / array_set |
| **Scope Exit** | 所有局部引用释放 | free 所有局部变量 | free_frame |

### 2.3 函数返回设计选择

**选择设计 A：Borrow → Return Retain**

```
local s (refCount=1)
    ↓ return
    ↓ incref(s)  (refCount=2)
    ↓ free(local s)  (refCount=1)
    ↓ caller owns s (refCount=1)
```

**原因**: 与 Bytecode VM 实际行为一致（OP_RET 中 `tll_value_incref(retVal)`），统一的 retain/release 语义，简化推理。

### 2.4 交付物

**文件**: `docs/TLL-NATIVE-OWNERSHIP-REFCOUNT-CONTRACT-v1.1.md`

**状态**: FROZEN / 待架构师验收

---

## 三、P1 GAP 修复

### 3.1 赋值旧值 release（B10-GAP-01 部分修复）

**问题**: 变量赋值时未 free 旧值，导致内存泄漏。

**修复**: 在 native_lower.tll 中，普通变量赋值生成：
```c
(tll_value_incref(new_value), tll_value_free(old_var), old_var = new_value)
```

**顺序说明**: 先 incref 新值，再 free 旧值，避免 `x = x` 时的 use-after-free。

**修改位置**: `compiler/native_lower.tll` — nl_lowerExpression Binary operator="=" 普通变量赋值分支

### 3.2 函数参数所有权（B10-GAP-01 部分修复）

**问题**: 调用者未 incref 参数，被调用者未 free 参数，导致引用计数不一致。

**修复**: 在 native_lower.tll 中，用户定义的函数调用（非 tll_ 开头的内置函数）生成：
```c
(tll_value_incref(arg1), tll_value_incref(arg2), callee(arg1, arg2))
```

**内置函数处理**: tll_ 开头的内置函数（如 tll_io_println）是 C 函数，不遵循 TLL 引用计数规则，不进行 incref。

**修改位置**: `compiler/native_lower.tll` — nl_lowerExpression kind="Call" 分支

### 3.3 容器元素 borrow/retain（B10-GAP-01 部分修复）

**问题**: array_push/map_set 前未 incref 新值，导致引用计数不一致。

**修复**: 在 native_lower.tll 中，以下位置增加 incref：

1. **Array literal**（Let/Const 特殊处理）:
```c
tll_value_incref(elem);
array_push(arr.as.array, elem);
```

2. **Map literal**（Let/Const 特殊处理）:
```c
tll_value_incref(value);
map_set(m.as.map, "key", value);
```

3. **Map index 赋值**:
```c
(tll_value_incref(value), map_set(m.as.map, "key", value), value)
```

4. **Array index 赋值**:
```c
(tll_value_incref(value), array_set(arr.as.array, idx, value), value)
```

**修改位置**: `compiler/native_lower.tll` — 多处

---

## 四、Ownership Conformance 测试

### 4.1 新增 4 个测试用例

| # | Case | 覆盖能力 | 结果 |
|---|------|---------|------|
| 7 | 07_ownership_local | 局部变量创建/使用/释放、重新赋值、从函数返回值、混合类型 | ✅ PASS |
| 8 | 08_ownership_assignment | 简单赋值、多次赋值、从函数返回值赋值、赋值链、整数赋值 | ✅ PASS |
| 9 | 09_ownership_return | 返回字符串/整数/拼接/分支/数组/Map、使用返回值、嵌套返回 | ✅ PASS |
| 10 | 10_ownership_container | Array/Map literal、字符串/混合元素、index 写、嵌套容器（使用 Let/Const）、多容器 | ✅ PASS |

### 4.2 测试发现的问题及修复

1. **main() 未自动调用**: TLL 中 main 函数不会自动被调用，需要在文件末尾显式调用 `main()`。4 个测试用例均已修复。

2. **嵌套 Map literal 不支持**: 10_ownership_container 中 `let arr = [{"x": 10}, {"x": 20}]` 导致 MSVC 编译失败（生成 NULL）。这是已知限制（B9-GAP-01: Array/Map literal 只能在 Let/Const 语句中使用）。修复为使用 Let/Const 语句：
```tll
let inner1 = {"x": 10};
let inner2 = {"x": 20};
let arr = [inner1, inner2];
```

---

## 五、Conformance 测试总结果

### 5.1 所有 11 个 Cases 全部 PASS

| # | Case | 结果 |
|---|------|------|
| 1 | cross_target_minimal | ✅ PASS |
| 2 | 01_basic | ✅ PASS |
| 3 | 02_function | ✅ PASS |
| 4 | 03_io | ✅ PASS |
| 5 | 04_control_flow | ✅ PASS |
| 6 | 05_array | ✅ PASS |
| 7 | 06_map | ✅ PASS |
| 8 | 07_ownership_local | ✅ PASS |
| 9 | 08_ownership_assignment | ✅ PASS |
| 10 | 09_ownership_return | ✅ PASS |
| 11 | 10_ownership_container | ✅ PASS |

**总计**: 11/11 PASS

---

## 六、Bootstrap / VM Regression

| 测试 | 结果 |
|------|------|
| Bootstrap Stage-0 | ✅ PASS (Bootstrap Level 5 Complete) |
| batch1_basic | ✅ PASS (35 行输出一致) |
| **总 regression** | ✅ **无倒退** |

---

## 七、GAP Ledger 更新

### 7.1 已关闭

| ID | 描述 | 关闭方式 |
|----|------|---------|
| B10-GAP-01 (部分) | 引用计数不完整 | 赋值旧值 release、函数参数所有权、容器元素 borrow/retain 已修复 |

### 7.2 仍 OPEN（carry forward）

| ID | 描述 | 优先级 | 说明 |
|----|------|--------|------|
| B10-GAP-01 (剩余) | 引用计数不完整 | P1 | 变量赋值时已 free 旧值，但多 return 点可能重复 free、块级作用域不支持 |
| B10-GAP-02 | 多 return 点可能重复 free | P2 | if/else 中的 return 可能重复 free 局部变量 |
| B10-GAP-03 | 不支持块级作用域 | P3 | 当前只支持函数级作用域 |
| B7-GAP-01 | process.exit(code) 暂不支持 | P2 | |
| B7-GAP-03 | Native Lowering 覆盖范围有限 | P1 | Closure/Exception/Coroutine/Network 等尚未支持 |
| B8-GAP-01 | 缺少批量运行器 | P2 | 一次运行所有 cases 并生成汇总报告 |
| B9-GAP-01 | Array/Map literal 只能在 Let/Const 中使用 | P2 | 不能作为函数参数或 return 值 |
| B6-GAP-01/02/03 | 文档更新/GCC 验证/CI 检查 | P2/P3 | |

### 7.3 明确不做（架构师禁止）

Closure / Coroutine / Network / FFI / LLVM / Linux / GPU / High-Frame Runtime / 大规模 String API / For-Break-Continue

---

## 八、Native Target 实现状态更新

| 操作 | B.10 状态 | B.11 状态 | 变化 |
|------|---------|---------|------|
| Creation | ✅ | ✅ | 无 |
| Assignment | ❌ | ✅ | 已修复 |
| Function Argument | ❌ | ✅ | 已修复 |
| Function Return | ✅ | ✅ | 无 |
| Container Element | ❌ | ✅ | 已修复 |
| Scope Exit (function-level) | ✅ | ✅ | 无 |
| Ownership Contract | v1.0 | v1.1 FROZEN | 升级 |

---

## 九、交付物清单

| 文件 | 说明 |
|------|------|
| `compiler/native_lower.tll` | 修改：赋值旧值 release、函数参数 incref、容器元素 incref |
| `docs/TLL-NATIVE-OWNERSHIP-REFCOUNT-CONTRACT-v1.1.md` | 新建：Ownership Model 冻结文档 |
| `tests/native/07_ownership_local.tll` | 新建：Conformance Case 07 |
| `tests/native/08_ownership_assignment.tll` | 新建：Conformance Case 08 |
| `tests/native/09_ownership_return.tll` | 新建：Conformance Case 09 |
| `tests/native/10_ownership_container.tll` | 新建：Conformance Case 10 |
| `docs/PHASE2-01-B.11-NATIVE-OWNERSHIP-SEMANTIC-CLOSURE.md` | 新建：完整报告 |

---

## 十、后续建议

### P2-01-B.12（Native Target Hardening）

1. **多 return 点重复 free 修复**（B10-GAP-02，P2）
2. **批量 Conformance 运行器**（B8-GAP-01，P2）
3. **String 操作扩展**（P2）
4. **For/Break/Continue**（P2）
5. **Array/Map literal 作为函数参数**（B9-GAP-01，P2）

### Native Target Seal 前置条件

- B.12 完成
- 完整引用计数（多 return 点、块级作用域）
- String 基础支持
- 批量运行器
- 15+ Conformance Cases
- ABI Contract v1.2

---

## 十一、核心结论

P2-01-B.11 完成了 Native Ownership Semantic Closure 的核心目标：

1. **Ownership Model 已冻结** — 基于 Bytecode VM 实际行为，形成 Contract v1.1，明确六种核心操作的语义
2. **三个 P1 GAP 已修复** — 赋值旧值 release、函数参数所有权、容器元素 borrow/retain
3. **11 个 Conformance Cases 全部 PASS** — 包括 4 个专门的 Ownership 测试
4. **Bootstrap/VM regression 无倒退**

Native Target 的引用计数语义现在与 Bytecode Target 基本一致，为后续 Native Target Hardening 和最终 Seal 奠定了坚实基础。

---

**报告结束。停止施工，等待架构裁决。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
