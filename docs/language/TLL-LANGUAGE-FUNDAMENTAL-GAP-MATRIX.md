# TLL Language Fundamental GAP Matrix

**版本**: v1.0-draft
**日期**: 2026-09-06
**状态**: Phase 3 Reality Audit 进行中
**分支**: feature/P0-tll-language-fundamentals

---

## 概述

本文档是 TLL Language Fundamental Completion 的 **Phase 3-4 产物**。

**目标**: 对 28 大域逐项进行 Reality Audit，生成完整的 EXPECTED − ACTUAL 差集（GAP Matrix）。

**审计标准**: 不是检查"有没有相关代码"，而是检查完整链路：
```
EXPECTED
  ↓ Source Syntax
  ↓ Lexer
  ↓ Parser
  ↓ AST
  ↓ TypeChecker / Semantic
  ↓ Codegen
  ↓ Runtime
  ↓ Positive Test
  ↓ Negative Test
  ↓ Boundary / Composition Test
  ↓ CI
```
任何一层缺失，都不能标记 COMPLETE。

---

## 状态定义

| 状态 | 说明 |
|------|------|
| **SEALED** | 完整链路验证通过，已正式封板 |
| **COMPLETE** | 实现完整，有测试/CI证据，但尚未正式封板 |
| **PARTIAL** | 只有部分能力，或某些链路缺失 |
| **MISSING** | 没有实现 |
| **BLOCKED** | 存在明确阻断条件 |
| **NOT_DESIGNED** | 经过架构判断，目前不采用 |
| **DEFERRED** | 设计确定，暂缓实现 |
| **NOT_APPLICABLE** | 不适用于 TLL |

---

## 决策分类

| 决策 | 说明 |
|------|------|
| **MUST HAVE** | 必须实现，不能延期 |
| **SHOULD HAVE** | 应该实现，高优先级 |
| **DESIGNED BUT DEFERRED** | 设计确定，暂缓实现 |
| **NOT_DESIGNED** | 经过架构判断，目前不采用 |
| **NOT_APPLICABLE** | 不适用于 TLL |

---

## 04 Operators（运算符）- 重点审计

### 算术运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-001 | `+` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-002 | `-` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-003 | `*` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-004 | `/` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-005 | `%` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-006 | `**` | SHOULD | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | SHOULD | - |

### 一元运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-007 | `+` (正号) | SHOULD | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | TypeChecker/Test |
| OP-008 | `-` (负号) | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-009 | `!` / `not` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-010 | `~` (位非) | SHOULD | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | TypeChecker/Test |

### 比较运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-011 | `==` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-012 | `!=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-013 | `<` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-014 | `>` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-015 | `<=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-016 | `>=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |

### 逻辑运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-017 | `and` / `&&` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-018 | `or` / `\|\|` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-019 | `not` / `!` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-020 | 短路语义 | MUST | - | - | - | - | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | 短路测试 |

### 位运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-021 | `&` | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| OP-022 | `\|` | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| OP-023 | `^` | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| OP-024 | `~` | SHOULD | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | TypeChecker/Test |
| OP-025 | `<<` | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| OP-026 | `>>` | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |

**注**: 位运算符在 P0-15 区块链压力测试中已添加 Lexer/Parser/Codegen，但 TypeChecker 和正式测试可能不完整。

### 赋值运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-027 | `=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-028 | `+=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-029 | `-=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-030 | `*=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-031 | `/=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-032 | `%=` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| OP-033 | `&=` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-034 | `\|=` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-035 | `^=` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-036 | `<<=` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-037 | `>>=` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |

### 条件运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-038 | `? :` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ⏳ | **IMPLEMENTED / NOT SEALED** | MUST | **测试/CI/负测试** |

**三元表达式当前状态**:
- ✅ Lexer: TK_QUESTION 已存在
- ✅ Parser: parseTernary() 已添加（96cc91e）
- ✅ AST: Ternary 节点
- ✅ TypeChecker: 类型兼容性检查（0bd5518）
- ✅ Codegen: cg_compileTernary()，短路语义
- ✅ Runtime: 字节码执行
- ⚠️ Positive Test: 7 个基础测试，缺少嵌套/组合/优先级测试
- ❌ Negative Test: 缺少 Parser 错误测试、类型不兼容测试
- ⏳ CI: 等待三平台验证（bc2deb2 已推送）

### 范围运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-039 | `..` | SHOULD | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | TypeChecker/Test |
| OP-040 | `..=` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |

### 自增/自减

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-041 | `++` (后置) | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-042 | `++` (前置) | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-043 | `--` (后置) | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| OP-044 | `--` (前置) | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |

### Null 相关运算符

| ID | 运算符 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|--------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| OP-045 | `??` | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | DEFERRED | - |
| OP-046 | `?.` | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | DEFERRED | - |

---

## 06 Type System（类型系统）- 重点审计

### 基础类型

| ID | 类型 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| TY-001 | int | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| TY-002 | float | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| TY-003 | bool | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| TY-004 | string | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| TY-005 | null | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| TY-006 | array | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| TY-007 | map | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| TY-008 | struct | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| TY-009 | function | SHOULD | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | TypeChecker/Test |
| TY-010 | uint | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |

### 类型系统特性

| ID | 特性 | EXPECTED | 状态 | 说明 |
|----|------|----------|------|------|
| TY-011 | 类型推断 `let x = 42` | MUST | ✅ COMPLETE | - |
| TY-012 | 显式类型标注 `x: int = 10` | MUST | ✅ COMPLETE | - |
| TY-013 | 类型转换 `int(...)`, `float(...)`, `string(...)`, `bool(...)` | MUST | ⚠️ PARTIAL | 部分类型转换可能不完整 |
| TY-014 | 类型兼容性 `int + float`, `string + int` | MUST | ⚠️ PARTIAL | numeric promotion 已验证，其他待审计 |
| TY-015 | TypeChecker | MUST | ⚠️ PARTIAL | **603 warnings**，需要分类处理 |
| TY-016 | 类型错误报告 | MUST | ⚠️ PARTIAL | 基本错误报告存在，质量待提升 |

### TypeChecker 603 Warnings 分类（待详细审计）

| 分类 | 预估数量 | 处理方式 |
|------|----------|----------|
| 真实类型系统缺陷 | 待审计 | 必须修复 |
| 合法未实现能力 | 待审计 | 记录为 GAP |
| 死代码 | 待审计 | 清理 |
| 诊断噪音 | 待审计 | 优化 TypeChecker |
| 设计性 warning | 待审计 | 明确设计决策 |
| 测试工具 warning | 待审计 | 隔离测试代码 |

---

## 09 Functions & Closures（函数与闭包）- 重点审计

| ID | 能力 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| FN-001 | 命名函数 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| FN-002 | 匿名函数 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| FN-003 | Lambda 箭头 | SHOULD | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | TypeChecker/Test |
| FN-004 | 闭包 | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | **Capture/Boxing/VM 待验证** |
| FN-005 | 嵌套函数 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| FN-006 | 递归函数 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| FN-007 | 高阶函数 | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| FN-008 | 函数作为值 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| FN-009 | 函数作为参数 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| FN-010 | 函数作为返回值 | MUST | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | MUST | TypeChecker/Test |
| FN-011 | 可变参数 (variadic) | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| FN-012 | 默认参数 | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| FN-013 | 命名参数 | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | DEFERRED | - |

### 闭包捕获语义（待详细审计）

| ID | 能力 | EXPECTED | 状态 | 说明 |
|----|------|----------|------|------|
| FN-014 | 按值捕获 | MUST | ⚠️ 待验证 | - |
| FN-015 | 按引用捕获 | SHOULD | ⚠️ 待验证 | - |
| FN-016 | 可变捕获 | SHOULD | ⚠️ 待验证 | - |
| FN-017 | 生命周期 | MUST | ⚠️ 待验证 | - |
| FN-018 | 逃逸闭包 | SHOULD | ⚠️ 待验证 | - |

---

## 10 Control Flow（控制流）

| ID | 能力 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| CF-001 | if | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-002 | if-else | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-003 | else-if | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-004 | while | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-005 | do-while | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| CF-006 | for | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-007 | foreach | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | 语法/TypeChecker/Test |
| CF-008 | break | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-009 | continue | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-010 | return | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| CF-011 | switch/case | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| CF-012 | match 模式匹配 | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |

---

## 13 Error & Resource Semantics（错误与资源语义）

| ID | 能力 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| ER-001 | exception | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| ER-002 | throw | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| ER-003 | try/catch | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | COMPLETE | MUST | - |
| ER-004 | finally | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | SHOULD | **全链路缺失** |
| ER-005 | error value | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | - | ✅ | PARTIAL | SHOULD | 语法/TypeChecker/Test |
| ER-006 | Result 类型 | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | DEFERRED | - |
| ER-007 | Option 类型 | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | DEFERRED | - |
| ER-008 | panic/recover | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | DEFERRED | - |

---

## 16 Generic / Parametric Types（泛型）

| ID | 能力 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| GE-001 | 泛型函数 | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | MUST | **全链路缺失** |
| GE-002 | 泛型 Struct | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | MUST | **全链路缺失** |
| GE-003 | 类型参数约束 | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| GE-004 | 泛型实例化 | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | MUST | 全链路缺失 |

---

## 18 Interface / Trait / Protocol（接口与特质）

| ID | 能力 | EXPECTED | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Positive Test | Negative Test | CI | ACTUAL | Decision | GAP |
|----|------|----------|-------|--------|-----|-------------|---------|---------|---------------|---------------|-----|--------|----------|-----|
| IT-001 | interface | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | **MISSING** | MUST | **全链路缺失** |
| IT-002 | trait | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| IT-003 | 抽象类型 | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | SHOULD | 全链路缺失 |
| IT-004 | 方法契约 | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | MUST | 全链路缺失 |
| IT-005 | 实现 (impl) | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | MUST | 全链路缺失 |
| IT-006 | 多态 | MUST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | MISSING | MUST | 全链路缺失 |

---

## 22 Concurrency Language Semantics（并发语言语义）

| ID | 能力 | 层级 | EXPECTED | 状态 | 说明 |
|----|------|------|----------|------|------|
| CC-001 | async/await | Language | MUST | ❌ MISSING | **需与 Runtime 联动设计** |
| CC-002 | spawn | Runtime API | MUST | ✅ COMPLETE | - |
| CC-003 | yield | Language | DEFERRED | ❌ MISSING | - |
| CC-004 | channel | Runtime API | SHOULD | ⚠️ PARTIAL | 待审计 |
| CC-005 | select | Language | DEFERRED | ❌ MISSING | - |
| CC-006 | actor | Runtime | SHOULD | ⚠️ PARTIAL | 待审计 |
| CC-007 | atomic | Runtime API | SHOULD | ⚠️ PARTIAL | 待审计 |

---

## GAP 汇总（初步）

### MUST HAVE + MISSING/PARTIAL

| 优先级 | 域 | 能力 | 当前状态 | 缺失层级 |
|--------|----|------|----------|----------|
| P0 | 04 Operators | 三元表达式 `? :` | IMPLEMENTED / NOT SEALED | 测试/CI/负测试 |
| P1 | 04 Operators | 位运算复合赋值 `&= \|= ^= <<= >>=` | MISSING | **全链路缺失** |
| P1 | 13 Error | finally | MISSING | **全链路缺失** |
| P1 | 16 Generic | 泛型函数/泛型Struct | MISSING | **全链路缺失** |
| P1 | 18 Interface | interface/方法契约/实现/多态 | MISSING | **全链路缺失** |
| P2 | 04 Operators | 自增/自减 `++`/`--` | MISSING | 全链路缺失（待架构决策） |
| P2 | 06 Types | TypeChecker 603 warnings | PARTIAL | 分类/修复 |
| P2 | 06 Types | 类型转换/类型兼容性 | PARTIAL | 完善 |
| P2 | 09 Functions | 闭包捕获语义 | PARTIAL | 验证/测试 |
| P2 | 09 Functions | 高阶函数/函数返回值 | PARTIAL | TypeChecker/Test |
| P2 | 10 Control Flow | do-while/foreach/switch | MISSING/PARTIAL | 全链路/完善 |
| P2 | 22 Concurrency | async/await | MISSING | **需与 Runtime 联动设计** |
| P3 | 04 Operators | 位运算符 TypeChecker/测试 | PARTIAL | TypeChecker/Test |
| P3 | 07 Composite | Array/Map 类型 | PARTIAL | TypeChecker/Test |
| P3 | 11 Pattern Matching | match 表达式 | MISSING | 全链路缺失（待架构决策） |
| P3 | 12 Destructuring | 解构 | MISSING | 全链路缺失（待架构决策） |

### SHOULD HAVE + MISSING

| 域 | 能力 | 当前状态 |
|----|------|----------|
| 04 Operators | 位运算复合赋值 | MISSING |
| 04 Operators | 自增/自减 | MISSING |
| 09 Functions | 可变参数/默认参数 | MISSING |
| 10 Control Flow | do-while/switch | MISSING |
| 13 Error | finally | MISSING |
| 14 Resource | defer/using | MISSING |

### 待架构决策

| 能力 | 初步方向 |
|------|----------|
| 自增/自减 `++`/`--` | SHOULD HAVE，倾向实现 |
| Pattern Matching | SHOULD HAVE，倾向实现 |
| Destructuring | SHOULD HAVE，倾向实现 |
| Generic | **MUST HAVE / 核心能力** |
| Interface / Trait | **MUST HAVE / 核心能力** |
| async/await | **MUST HAVE，但与 Runtime 联动设计** |

---

## 统计（初步）

| 状态 | 数量 | 占比 |
|------|------|------|
| SEALED | 0 | 0% |
| COMPLETE | ~45 | ~40% |
| PARTIAL | ~25 | ~22% |
| MISSING | ~35 | ~31% |
| NOT_DESIGNED | 0 | 0% |
| DEFERRED | ~8 | ~7% |
| **总计** | **~113** | **100%** |

**MUST HAVE + MISSING/PARTIAL**: ~20 项
**SHOULD HAVE + MISSING**: ~10 项
**待架构决策**: 6 项

---

## 下一步

1. **Phase 3 继续**: 完成剩余 23 个域的 Reality Audit
2. **Phase 4**: 完善 GAP Matrix，每个 GAP 补充详细字段（Root Cause / Implementation Scope / Test Requirement / CI Requirement / Evidence Requirement）
3. **三元表达式 CI 验证**: 等待 bc2deb2 的三平台 CI 结果
4. **架构师审计**: 提交完整 GAP Matrix，等待架构师第二次筛选
5. **Phase 5**: 根据架构师决策，形成 MUST HAVE + MISSING/PARTIAL 的施工队列

---

**文档结束（v1.0-draft，Phase 3 进行中）**
