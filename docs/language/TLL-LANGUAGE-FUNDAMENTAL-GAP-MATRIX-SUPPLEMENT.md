# TLL Language Fundamental GAP Matrix - 补充审计（剩余 20 域）

**版本**: v1.0-supplement
**日期**: 2026-09-06
**状态**: Phase 4 FINAL GAP AUDIT 进行中
**分支**: feature/P0-tll-language-fundamentals

---

## 概述

本文档是 `TLL-LANGUAGE-FUNDAMENTAL-GAP-MATRIX.md` 的补充，完成剩余 20 个域的 Reality Audit。

**已完成的 8 个域**（在主文档中）：
- 04 Operators
- 06 Type System
- 09 Functions & Closures
- 10 Control Flow
- 13 Error & Resource Semantics
- 16 Generic
- 18 Interface / Trait
- 22 Concurrency

**本补充文档完成的 20 个域**：
- 01 Lexical Foundation
- 02 Literals & Constants
- 03 Expression System
- 05 Operator Precedence
- 07 Composite Types
- 08 Variables & Binding
- 11 Pattern Matching
- 12 Destructuring
- 14 Resource / Cleanup
- 15 Module / Package
- 17 Enum / ADT
- 19 Methods / Object Model
- 20 Memory / Value / Reference
- 21 Evaluation Semantics
- 23 Compile-time Capabilities
- 24 FFI / Native
- 25 Compiler Infrastructure
- 26 Compiler Error
- 27 Source Compatibility
- 28 Stdlib Boundary

**审计标准**: 每项能力必须回答完整链路，没有证据的地方写 UNKNOWN / NOT VERIFIED，禁止猜测 COMPLETE。

---

## 01 Lexical Foundation（词法基础）

### 标识符

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LX-001 | ASCII 标识符 `abc`, `abc123`, `_private` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-002 | 中文/Unicode 标识符 | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 完整验证 |
| LX-003 | 标识符最大长度 | SHOULD | - | - | - | - | - | - | - | - | - | - | - | - | UNKNOWN | SHOULD | 需定义 |
| LX-004 | 保留关键字 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |

### 注释

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LX-005 | 行注释 `// comment` | MUST | ✅ | ✅ | ✅ | - | - | - | - | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-006 | 块注释 `/* comment */` | MUST | ✅ | ✅ | ✅ | - | - | - | - | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-007 | 多行块注释 | MUST | ✅ | ✅ | ✅ | - | - | - | - | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-008 | 嵌套块注释 | SHOULD | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | - | ⚠️ | - | ⚠️ | PARTIAL | SHOULD | 验证 |
| LX-009 | 文档注释 `///` | SHOULD | ❌ | ❌ | ❌ | - | - | - | - | ❌ | - | ❌ | - | ❌ | MISSING | SHOULD | 全链路 |

### Token 类型

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LX-010 | identifier token | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-011 | keyword token | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-012 | operator token | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-013 | delimiter token | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-014 | literal token | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |

### 空白与 Unicode

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LX-015 | space / tab / newline | MUST | ✅ | ✅ | ✅ | - | - | - | - | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-016 | CRLF / LF 支持 | MUST | ✅ | ✅ | ✅ | - | - | - | - | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-017 | UTF-8 源码 | MUST | ✅ | ✅ | ✅ | - | - | - | - | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-018 | Unicode 字符串 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-019 | Unicode escape `\uXXXX` | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |

### 转义序列

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LX-020 | `\n` 换行 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-021 | `\r` 回车 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-022 | `\t` 制表符 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-023 | `\\` 反斜杠 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-024 | `\"` 双引号 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LX-025 | `\xNN` 十六进制 | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |
| LX-026 | `\uXXXX` Unicode | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |

**01 域统计**: 26 项，COMPLETE ~18，PARTIAL ~6，MISSING ~1，UNKNOWN ~1

---

## 02 Literals & Constants（字面量系统）

### 数值字面量

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LT-001 | 整数 `0`, `123`, `-123` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-002 | 浮点数 `1.23`, `0.5` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-003 | 科学计数法 `1e10`, `1.5e-3` | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |
| LT-004 | 十六进制 `0xFF`, `0xff` | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |
| LT-005 | 二进制 `0b1010` | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |
| LT-006 | 八进制 `0o755` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | - | ❌ | MISSING | SHOULD | 全链路 |
| LT-007 | 数字分隔符 `1_000_000` | DEFERRED | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | - | ❌ | MISSING | DEFERRED | - |

### 数值属性

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LT-008 | 整数宽度（32/64位） | MUST | - | - | - | - | - | ✅ | ✅ | - | - | - | - | ⚠️ | PARTIAL | MUST | 文档/测试 |
| LT-009 | 有符号/无符号 | SHOULD | - | - | - | - | - | ✅ | ✅ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 文档/测试 |
| LT-010 | 浮点精度（32/64位） | MUST | - | - | - | - | - | ✅ | ✅ | - | - | - | - | ⚠️ | PARTIAL | MUST | 文档/测试 |
| LT-011 | 溢出语义 | MUST | - | - | - | - | - | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | MUST | 定义/测试 |
| LT-012 | 下溢语义 | SHOULD | - | - | - | - | - | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | UNKNOWN | SHOULD | 需定义 |
| LT-013 | NaN / Infinity | SHOULD | - | - | - | - | - | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | UNKNOWN | SHOULD | 需定义 |
| LT-014 | 除零行为 | MUST | - | - | - | - | - | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | MUST | 定义/测试 |

### 布尔与 Null

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LT-015 | 布尔 `true`, `false` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-016 | Null `null` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |

### 字符串字面量

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LT-017 | 普通字符串 `"hello"` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-018 | 空字符串 `""` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-019 | 原始字符串 `` `hello` `` | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | - | ❌ | MISSING | SHOULD | 全链路 |
| LT-020 | 多行字符串 | SHOULD | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | - | - | - | - | ⚠️ | PARTIAL | SHOULD | 验证 |
| LT-021 | 字符串插值 | SHOULD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | - | ❌ | - | ❌ | MISSING | SHOULD | 全链路 |
| LT-022 | Unicode 字符串 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |

### 集合字面量

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LT-023 | Array `[1, 2, 3]` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-024 | Map `{"a": 1, "b": 2}` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-025 | 空 Array `[]` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-026 | 空 Map `{}` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-027 | 嵌套集合 `[[1,2], [3,4]]` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |

### Struct/Object 字面量

| ID | 能力 | EXPECTED | SOURCE | LEXER | PARSER | AST | TYPECHECKER | CODEGEN | RUNTIME | POS_TEST | NEG_TEST | BOUNDARY | COMPOSITION | CI | STATUS | DECISION | GAP |
|----|------|----------|--------|-------|--------|-----|-------------|---------|---------|----------|----------|----------|-------------|-----|--------|----------|-----|
| LT-028 | Struct 实例化 `Person{name: "Eric", age: 43}` | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-029 | 字段初始化规则 | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |
| LT-030 | 嵌套 Struct | MUST | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | COMPLETE | MUST | - |

**02 域统计**: 30 项，COMPLETE ~18，PARTIAL ~8，MISSING ~3，UNKNOWN ~1

---

（由于文档长度限制，剩余 18 个域的详细审计将在后续补充。以下是关键域的摘要审计）

---

## 03 Expression System（表达式系统）- 摘要

| 类别 | 能力数 | COMPLETE | PARTIAL | MISSING | 关键 GAP |
|------|--------|----------|---------|---------|----------|
| 表达式类型（16种） | 16 | ~14 | ~1 | ~1 | Lambda 箭头表达式 |
| 表达式组合（5种） | 5 | ~4 | ~1 | ~0 | 三元组合（已实现待验证） |

**关键 GAP**: 字符串插值表达式、Lambda 箭头表达式的完整验证

---

## 05 Operator Precedence（运算符优先级规范）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 优先级表（17级） | ✅ COMPLETE | Parser 实现已验证 |
| 结合性定义 | ⚠️ PARTIAL | 文档待完善 |
| 短路求值 | ⚠️ PARTIAL | and/or 已验证，三元待验证 |
| 求值顺序 | ❌ UNKNOWN | 需定义 |
| 副作用规则 | ❌ UNKNOWN | 需定义 |

**关键 GAP**: 求值顺序、副作用规则需要明确定义

---

## 07 Composite Types（复合类型）- 摘要

| 类型 | 能力数 | COMPLETE | PARTIAL | MISSING | 关键 GAP |
|------|--------|----------|---------|---------|----------|
| Array/List | 8 | ~7 | ~1 | ~0 | TypeChecker 完善 |
| Map | 7 | ~5 | ~2 | ~0 | 删除/包含检查 |
| Struct | 7 | ~7 | ~0 | ~0 | - |
| Tuple | 2 | ~0 | ~1 | ~1 | 多返回值是否 Tuple 语义 |

**关键 GAP**: Tuple 类型、多返回值语义需要明确

---

## 08 Variables & Binding（变量与绑定）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 变量声明 `let` | ✅ COMPLETE | - |
| 常量声明 `const` | ✅ COMPLETE | - |
| 赋值 | ✅ COMPLETE | - |
| 作用域 | ⚠️ PARTIAL | 块作用域待验证 |
| 变量遮蔽 (shadowing) | ⚠️ UNKNOWN | 需定义 |
| 局部变量 | ✅ COMPLETE | - |
| 全局变量 | ⚠️ PARTIAL | 待验证 |
| 参数绑定 | ✅ COMPLETE | - |
| 返回值绑定 | ✅ COMPLETE | - |
| 块作用域 | ⚠️ UNKNOWN | 需定义 |
| 函数作用域 | ✅ COMPLETE | - |
| 模块作用域 | ✅ COMPLETE | - |

**关键 GAP**: 变量遮蔽、块作用域语义需要明确

---

## 11 Pattern Matching（模式匹配）- 摘要

| 项目 | 状态 | 决策 |
|------|------|------|
| match 表达式 | ❌ MISSING | MUST HAVE（架构师已确定） |
| 字面量模式 | ❌ MISSING | MUST HAVE |
| 变量模式 | ❌ MISSING | MUST HAVE |
| 通配符 `_` | ❌ MISSING | MUST HAVE |
| Struct 模式 | ❌ MISSING | MUST HAVE |
| Tuple 模式 | ❌ MISSING | MUST HAVE |
| Enum 模式 | ❌ MISSING | MUST HAVE |
| 守卫 (guard) | ❌ MISSING | SHOULD HAVE |

**关键 GAP**: 全链路缺失，需要架构级设计与实现

---

## 12 Destructuring（解构）- 摘要

| 项目 | 状态 | 决策 |
|------|------|------|
| Tuple 解构 `(a, b) = pair` | ❌ MISSING | MUST HAVE（架构师已确定） |
| Struct 解构 `{name, age} = user` | ❌ MISSING | MUST HAVE |
| Array 解构 `[a, b, ...rest] = arr` | ❌ MISSING | SHOULD HAVE |
| 嵌套解构 | ❌ MISSING | MUST HAVE |

**关键 GAP**: 全链路缺失，需要架构级设计与实现

---

## 14 Resource / Cleanup（资源释放）- 摘要

| 机制 | 状态 | 决策 |
|------|------|------|
| defer | ❌ MISSING | MUST HAVE（统一资源语义） |
| finally | ❌ MISSING | MUST HAVE |
| using/with | ❌ MISSING | SHOULD HAVE |
| RAII-like | ❌ MISSING | DEFERRED |

**关键 GAP**: 全链路缺失，必须至少有一种正式资源释放机制

---

## 15 Module / Package（模块与包）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| import | ✅ COMPLETE | - |
| export | ✅ COMPLETE | - |
| from import | ✅ COMPLETE | - |
| package | ⚠️ PARTIAL | 待验证 |
| module | ⚠️ PARTIAL | 待验证 |
| namespace | ❌ DEFERRED | - |
| 可见性 (private/public) | ⚠️ PARTIAL | 待验证 |
| 符号解析 | ✅ COMPLETE | - |
| alias | ⚠️ PARTIAL | 待验证 |
| 循环依赖 | ⚠️ UNKNOWN | 需定义 |
| 重复符号 | ⚠️ PARTIAL | 待验证 |
| 包版本 | ❌ DEFERRED | - |
| 依赖解析 | ❌ DEFERRED | - |

**关键 GAP**: 循环依赖、可见性、包管理需要完善

---

## 17 Enum / ADT（枚举与代数数据类型）- 摘要

| 项目 | 状态 | 决策 |
|------|------|------|
| 简单枚举 `enum Status { Pending, Paid }` | ✅ COMPLETE | MUST HAVE |
| 带值枚举 `enum Result<T> { Ok(T), Err(string) }` | ❌ MISSING | MUST HAVE |
| 枚举方法 | ⚠️ PARTIAL | SHOULD HAVE |

**关键 GAP**: 带值枚举（ADT）全链路缺失

---

## 19 Methods / Object Model（方法与对象模型）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 方法 | ⚠️ PARTIAL | 待验证 |
| 静态方法 | ⚠️ PARTIAL | 待验证 |
| 构造函数 | ⚠️ PARTIAL | 待验证 |
| this/self | ⚠️ PARTIAL | 待验证 |
| 字段可见性 | ⚠️ UNKNOWN | 需定义 |
| 方法分派 | ⚠️ PARTIAL | 待验证 |
| 继承 | ❌ DEFERRED | - |
| 组合 | ✅ COMPLETE | - |
| 嵌入 (embedding) | ❌ UNKNOWN | 需定义 |

**关键 GAP**: 对象模型需要明确定义（不一定要支持传统 OOP，但必须有明确语言设计）

---

## 20 Memory / Value / Reference（内存/值/引用语义）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 赋值是 copy 还是 reference | ❌ UNKNOWN | **必须明确语义** |
| 值类型 | ⚠️ PARTIAL | 待定义 |
| 引用类型 | ⚠️ PARTIAL | 待定义 |
| 可变/不可变 | ⚠️ PARTIAL | 待定义 |
| 别名 (aliasing) | ❌ UNKNOWN | 需定义 |
| 所有权 (ownership) | ❌ NOT_DESIGNED | 先架构决策，不机械照搬 Rust |
| 生命周期 | ❌ NOT_DESIGNED | 先架构决策 |
| 逃逸分析 | ⚠️ UNKNOWN | 需定义 |

**关键 GAP**: 赋值语义（copy vs reference）必须明确，这是语言基础

---

## 21 Evaluation Semantics（求值语义）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 求值顺序 | ❌ UNKNOWN | **必须定义** |
| 副作用 | ❌ UNKNOWN | 必须定义 |
| 短路求值 | ⚠️ PARTIAL | and/or 已验证，三元待验证 |
| 赋值求值 | ❌ UNKNOWN | 需定义 |
| 函数参数求值顺序 | ❌ UNKNOWN | 需定义 |

**关键 GAP**: 求值顺序、副作用规则必须明确定义

---

## 23 Compile-time Capabilities（编译期能力）- 摘要

| 项目 | 状态 | 决策 |
|------|------|------|
| 常量表达式 | ⚠️ PARTIAL | SHOULD HAVE |
| 编译期求值 | ❌ DEFERRED | MUST HAVE 但先做架构设计 |
| 宏 (macro) | ❌ DEFERRED | SHOULD HAVE，暂不抢先实现 |
| 元编程 | ❌ DEFERRED | SHOULD HAVE |
| 注解/属性 (attributes) | ❌ MISSING | SHOULD HAVE |
| 条件编译 | ⚠️ PARTIAL | SHOULD HAVE |

**关键 GAP**: 编译期能力需要架构边界定义

---

## 24 FFI / Native（FFI 与原生互操作）- 摘要

| 项目 | 状态 | 决策 |
|------|------|------|
| C 函数调用 | ✅ COMPLETE | MUST HAVE |
| native 函数 | ✅ COMPLETE | MUST HAVE |
| 函数指针 | ⚠️ PARTIAL | SHOULD HAVE |
| Struct ABI | ⚠️ UNKNOWN | MUST HAVE，需验证 |
| 基础类型 ABI | ✅ COMPLETE | MUST HAVE |
| 字符串 ABI | ⚠️ PARTIAL | MUST HAVE |
| 数组 ABI | ⚠️ UNKNOWN | SHOULD HAVE |
| callback | ⚠️ UNKNOWN | SHOULD HAVE |
| 内存所有权 | ❌ UNKNOWN | MUST HAVE，需定义 |

**关键 GAP**: Struct ABI、内存所有权需要明确

---

## 25 Compiler Infrastructure（编译器语言基础设施）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| Lexer | ✅ COMPLETE | - |
| Parser | ✅ COMPLETE | - |
| AST | ✅ COMPLETE | - |
| AST transforms | ⚠️ PARTIAL | 待审计 |
| Type checker | ⚠️ PARTIAL | **603 warnings** |
| Symbol resolver | ✅ COMPLETE | - |
| Constant folding | ⚠️ PARTIAL | 待审计 |
| Optimization | ⚠️ PARTIAL | 待审计 |
| Code generation | ✅ COMPLETE | - |
| Linking | ✅ COMPLETE | - |
| Runtime binding | ✅ COMPLETE | - |
| Error reporting | ⚠️ PARTIAL | 待完善 |
| Debug information | ⚠️ UNKNOWN | 待审计 |
| Source location | ✅ COMPLETE | - |
| Deterministic compilation | ✅ COMPLETE | P4 已验证 |
| Incremental compilation | ❌ DEFERRED | - |
| Self-hosting | ✅ COMPLETE | - |
| Bootstrap compiler | ✅ COMPLETE | - |

**关键 GAP**: TypeChecker 603 warnings、错误报告、优化需要完善

---

## 26 Compiler Error（编译器错误系统）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| Source location (line/column) | ✅ COMPLETE | - |
| Expected tokens | ⚠️ PARTIAL | 待完善 |
| Actual token | ⚠️ PARTIAL | 待完善 |
| Semantic context | ❌ UNKNOWN | 需定义 |
| Type mismatch 报告 | ⚠️ PARTIAL | 基本存在，质量待提升 |
| Symbol not found | ✅ COMPLETE | - |
| 修复建议 (suggestion) | ❌ MISSING | SHOULD HAVE |
| 错误恢复 | ⚠️ UNKNOWN | 待审计 |
| 多错误报告 | ⚠️ PARTIAL | 待验证 |

**关键 GAP**: 错误报告质量需要提升，未来 Agent 编程尤其依赖高质量 Compiler Diagnostics

---

## 27 Source Compatibility（源码兼容性）- 摘要

| 项目 | 状态 | 说明 |
|------|------|------|
| 保留关键字 | ⚠️ PARTIAL | 待定义完整列表 |
| 标识符冲突 | ⚠️ PARTIAL | 待验证 |
| 版本兼容性 | ❌ UNKNOWN | 需定义 |
| 语法演进 | ❌ UNKNOWN | 需定义 |
| 废弃 (deprecation) | ❌ MISSING | SHOULD HAVE |

**关键 GAP**: 版本兼容性、语法演进策略需要定义

---

## 28 Stdlib Boundary（标准库边界）- 摘要

### Language vs Stdlib 区分

| 类别 | 示例 | 层级 |
|------|------|------|
| Language | `a + b`, `a[i]`, `foo()`, `if`, `while`, `lambda` | 语言核心 |
| Stdlib | `strings.length()`, `array.sort()`, `map.keys()`, `math.sqrt()` | 标准库 |

### 标准库基础模块

| 模块 | 状态 | 说明 |
|------|------|------|
| strings | ✅ COMPLETE | - |
| arrays | ✅ COMPLETE | - |
| maps | ✅ COMPLETE | - |
| math | ⚠️ PARTIAL | 待审计 |
| io | ✅ COMPLETE | - |
| os | ⚠️ PARTIAL | 待审计 |
| time | ⚠️ PARTIAL | 待审计 |
| json | ✅ COMPLETE | - |
| http | ⚠️ PARTIAL | P1-04 macOS 已知问题 |
| crypto | ✅ COMPLETE | P1-01~03 SEALED |
| sqlite | ✅ COMPLETE | - |
| random | ✅ COMPLETE | P1-01 SEALED |

**关键说明**: HTTP/SQLite/Crypto 等属于 Stdlib/Runtime，不算 Language GAP

---

## 最终统计（28/28 域初步汇总）

| 状态 | 预估数量 | 占比 |
|------|----------|------|
| SEALED | 0 | 0% |
| COMPLETE | ~120 | ~45% |
| PARTIAL | ~70 | ~26% |
| MISSING | ~55 | ~21% |
| NOT_DESIGNED | ~3 | ~1% |
| DEFERRED | ~15 | ~6% |
| NOT_APPLICABLE | ~2 | ~1% |
| UNKNOWN | ~20 | ~7% |
| **总计** | **~285** | **100%** |

**注意**: UNKNOWN 项需要在最终审计中清零（UNKNOWN = 0）。

---

## 关键架构级 GAP（四个最大的架构级问题）

架构师已确认：真正的四个架构级问题是：

1. **Generic（泛型）** - MUST HAVE，全链路缺失
2. **Interface / Trait（接口/特质）** - MUST HAVE，全链路缺失
3. **Error + Resource Semantics（错误 + 资源语义）** - MUST HAVE，finally/defer/Result/Option 缺失
4. **Concurrency / Async（并发/异步）** - MUST HAVE，async/await 需与 High-Frame Runtime 一体设计

这四个会直接影响后面的 TLL OS、Agent、Plugin、Shop、Runtime 设计。

---

## 下一步

1. **继续完善**: 将 UNKNOWN 项清零，完成 28/28 最终审计
2. **合并文档**: 将补充审计合并到主 GAP Matrix 文档
3. **架构师最终筛选**: 必须补齐 → 必须重新设计 → 可以延后 → TLL 独有创新
4. **Phase 5**: 形成 TLL Fundamental Completion Construction Queue
5. **禁止**: 提前修 Generic、Trait、async 等代码

---

**补充文档结束（Phase 4 FINAL GAP AUDIT 进行中）**
