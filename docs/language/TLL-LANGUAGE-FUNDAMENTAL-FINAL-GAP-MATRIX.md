# TLL Language Fundamental Final GAP Matrix

**版本**: v1.0-draft
**日期**: 2026-09-06
**状态**: Phase 4 FINAL EVIDENCE CLOSURE 进行中
**分支**: feature/P0-tll-language-fundamentals
**基线**: TLL OS 6875401

---

## 概述

本文档是 TLL Language Fundamental Completion 的唯一 Canonical GAP Matrix，合并了：
- TLL-LANGUAGE-FUNDAMENTAL-GAP-MATRIX.md（主文档，8 个关键域详细审计）
- TLL-LANGUAGE-FUNDAMENTAL-GAP-MATRIX-SUPPLEMENT.md（补充审计，20 个域）
- TLL-LANGUAGE-FUNDAMENTAL-AUDIT-CLOSURE.md（审计闭环，Memory/Evaluation 语义证据）

**目标**: Reality = Evidence = Truth，UNKNOWN = 0，所有能力项有真实证据。

---

## 状态定义

| 状态 | 定义 |
|------|------|
| SEALED | 有正式 Evidence，满足封板条件，三平台 CI 通过 |
| COMPLETE | 实现完整，有测试/CI 证据，但尚未封板 |
| PARTIAL | 只有部分能力，存在已知限制 |
| MISSING | 没有实现，全链路缺失 |
| BLOCKED | 存在明确阻断条件 |
| NOT_DESIGNED | 经过架构判断，目前不采用 |
| DEFERRED | 属于高级能力，设计确定但暂缓实现 |
| NOT_APPLICABLE | 不适用于 TLL 语言 |

---

## 统一字段说明

每个能力项包含以下字段：
- **ID**: 唯一标识符（LANG-XX-NNN）
- **Domain**: 所属域（01-28）
- **Capability**: 能力名称
- **Expected**: 预期状态（MUST HAVE / SHOULD HAVE / NOT_DESIGNED / DEFERRED）
- **Actual**: 实际状态（SEALED / COMPLETE / PARTIAL / MISSING / ...）
- **Source**: 源码证据（文件:行号）
- **Lexer**: Lexer 层状态
- **Parser**: Parser 层状态
- **AST**: AST 层状态
- **Semantic/TypeChecker**: 语义/类型检查层状态
- **Codegen**: 代码生成层状态
- **Runtime**: 运行时层状态
- **Positive Test**: 正测试状态
- **Negative Test**: 负测试状态
- **Boundary Test**: 边界测试状态
- **Composition Test**: 组合测试状态
- **CI**: CI 状态
- **Evidence**: 证据说明
- **Missing Layer**: 缺失层（如有）
- **Root Cause**: 根本原因（如有）
- **Decision**: 架构决策
- **Priority**: 优先级（P0/P1/P2/P3）
- **Implementation Scope**: 实现范围
- **Test Requirement**: 测试要求
- **CI Requirement**: CI 要求

---

## 统计（初步，待最终更新）

| 状态 | 数量 | 占比 |
|------|------|------|
| SEALED | 0 | 0% |
| COMPLETE | 待统计 | 待统计 |
| PARTIAL | 待统计 | 待统计 |
| MISSING | 待统计 | 待统计 |
| BLOCKED | 0 | 0% |
| NOT_DESIGNED | 待统计 | 待统计 |
| DEFERRED | 待统计 | 待统计 |
| NOT_APPLICABLE | 待统计 | 待统计 |
| UNKNOWN | 待清零 | 待清零 |
| **TOTAL** | **待统计** | **100%** |

**目标**: UNKNOWN = 0，sum(statuses) == TOTAL

---

## 01 Lexical Foundation（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-01-001 | ASCII 标识符 | MUST | COMPLETE | lexer.tll:320 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | isAlpha + isAlphanumeric |
| LANG-01-002 | Unicode 标识符 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | isAlpha 只检查 ASCII |
| LANG-01-003 | 标识符长度限制 | NOT_DESIGNED | NOT_DESIGNED | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 无长度检查，属于设计决策 |
| LANG-01-004 | 行注释 `//` | MUST | COMPLETE | lexer.tll:188 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 跳过到行尾 |
| LANG-01-005 | 块注释 `/* */` | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Lexer 只有行注释处理 |
| LANG-01-006 | 嵌套块注释 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 块注释本身缺失 |
| LANG-01-007 | 空白处理 | MUST | COMPLETE | lexer.tll:185 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | space/tab/r/n |
| LANG-01-008 | UTF-8 源码 | MUST | COMPLETE | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 源码文件 UTF-8 编码 |
| LANG-01-009 | 关键字 | MUST | COMPLETE | lexer.tll:326 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | getKeywordType |
| LANG-01-010 | Token 类型 | MUST | COMPLETE | lexer.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | identifier/keyword/operator/delimiter/literal |

---

## 02 Literals & Constants（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-02-001 | 整数字面量 | MUST | COMPLETE | lexer.tll:264 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 0, 1, 123, -123 |
| LANG-02-002 | 浮点字面量 | MUST | COMPLETE | lexer.tll:304 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 0.5, 1.25 |
| LANG-02-003 | 十六进制 `0x` | MUST | COMPLETE | lexer.tll:270 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 0xFF, 0X1A |
| LANG-02-004 | 八进制 `0o` | MUST | COMPLETE | lexer.tll:279 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 0o755, 0O17 |
| LANG-02-005 | 二进制 `0b` | MUST | COMPLETE | lexer.tll:288 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 0b1010, 0B1100 |
| LANG-02-006 | 科学计数法 | MUST | COMPLETE | lexer.tll:307 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 1e10, 1E-5, 1.5e+3 |
| LANG-02-007 | 数字分隔符 | SHOULD | COMPLETE | lexer.tll:302 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 1_000_000 |
| LANG-02-008 | 布尔字面量 | MUST | COMPLETE | lexer.tll:821 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | true, false |
| LANG-02-009 | null 字面量 | MUST | COMPLETE | lexer.tll:831 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | null |
| LANG-02-010 | 字符串字面量 | MUST | COMPLETE | lexer.tll:203 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | "hello" |
| LANG-02-011 | 原始字符串 `r"..."` | SHOULD | COMPLETE | lexer.tll:249 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | r"raw string" |
| LANG-02-012 | 转义 `\n \t \r \\ \" \0` | MUST | COMPLETE | lexer.tll:218 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 6 种基础转义 |
| LANG-02-013 | 十六进制转义 `\xNN` | MUST | COMPLETE | lexer.tll:224 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | \x41 = 'A' |
| LANG-02-014 | Unicode 转义 `\uXXXX` | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 字符串转义无 `u` 分支 |
| LANG-02-015 | 数组字面量 `[...]` | MUST | COMPLETE | parser.tll:882 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | [1, 2, 3] |
| LANG-02-016 | Map 字面量 `{...}` | MUST | COMPLETE | parser.tll:899 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | {"a": 1} |
| LANG-02-017 | Struct 字面量 | MUST | COMPLETE | parser.tll:168 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Person{name: "x", age: 1} |
| LANG-02-018 | 整数宽度 | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主 int，无明确宽度定义 |
| LANG-02-019 | 有符号/无符号 | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 默认有符号，无 unsigned 类型 |
| LANG-02-020 | 浮点精度 | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主 float，无明确精度定义 |
| LANG-02-021 | 溢出语义 | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主行为，无明确溢出定义 |
| LANG-02-022 | 下溢语义 | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主行为 |
| LANG-02-023 | NaN | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主 float |
| LANG-02-024 | Infinity | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主 float |
| LANG-02-025 | 除零行为 | NOT_DESIGNED | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖宿主行为，整数除零可能崩溃 |
| LANG-02-026 | 多行字符串 | SHOULD | PARTIAL | lexer.tll:207 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | 字符串可跨行，但无专门语法 |
| LANG-02-027 | 字符串插值 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 `\(expr)` 或 `${expr}` 插值 |
| LANG-02-028 | 空字符串 | MUST | COMPLETE | lexer.tll:203 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | "" |
| LANG-02-029 | 负数 | MUST | COMPLETE | lexer.tll:691 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | -1, -1.5（一元负号） |
| LANG-02-030 | 常量定义 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | let x = 10（无 const 关键字） |

---

## 03 Expression System（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-03-001 | 字面量表达式 | MUST | COMPLETE | parser.tll:797 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | int/float/string/bool/null |
| LANG-03-002 | 变量表达式 | MUST | COMPLETE | parser.tll:873 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Ident |
| LANG-03-003 | 二元表达式 | MUST | COMPLETE | parser.tll:631 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | + - * / % ** & | ^ << >> == != < > <= >= and or |
| LANG-03-004 | 一元表达式 | MUST | COMPLETE | parser.tll:691 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | + - ! ~ |
| LANG-03-005 | 赋值表达式 | MUST | COMPLETE | parser.tll:498 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | = += -= *= /= %= |
| LANG-03-006 | 条件表达式（三元） | MUST | IMPLEMENTED | parser.tll:482 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⏳ | ? :（本次添加，待 CI 封板） |
| LANG-03-007 | 函数调用表达式 | MUST | COMPLETE | parser.tll:752 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | foo(a, b) |
| LANG-03-008 | 索引表达式 | MUST | COMPLETE | parser.tll:768 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | arr[i], map[key] |
| LANG-03-009 | 成员访问表达式 | MUST | COMPLETE | parser.tll:760 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | obj.field |
| LANG-03-010 | 范围表达式 | MUST | COMPLETE | parser.tll:616 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | a..b, a..=b |
| LANG-03-011 | Lambda 表达式 | MUST | COMPLETE | parser.tll:850 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | fn(x) { return x } |
| LANG-03-012 | Struct 表达式 | MUST | COMPLETE | parser.tll:168 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Person{name: "x"} |
| LANG-03-013 | 数组表达式 | MUST | COMPLETE | parser.tll:882 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | [1, 2, 3] |
| LANG-03-014 | Map 表达式 | MUST | COMPLETE | parser.tll:899 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | {"a": 1} |
| LANG-03-015 | 括号表达式 | MUST | COMPLETE | parser.tll:835 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | (a + b) * c |
| LANG-03-016 | 管道表达式 | SHOULD | COMPLETE | parser.tll:469 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | a |> f() |
| LANG-03-017 | 表达式组合能力 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | foo(a + b * c), user.profile.items[0].price |

---

## 04 Operators（详细审计，见主文档）

（46 项运算符详细审计，已在主文档中完成）

---

## 05 Operator Precedence（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-05-001 | 17 级优先级表 | MUST | COMPLETE | parser.tll:465-797 | parseExpression→parsePipe→parseAssignment→parseTernary→parseOr→parseAnd→parseBitwiseOr→parseBitwiseXor→parseBitwiseAnd→parseEquality→parseComparison→parseRange→parseAddition→parseShift→parseMultiplication→parsePower→parseUnary→parsePostfix→parsePrimary |
| LANG-05-002 | 结合性 | MUST | PARTIAL | parser.tll | 左结合已验证，右结合（赋值/三元）需验证 |
| LANG-05-003 | 短路求值 | MUST | COMPLETE | codegen.tll | and/or/三元支持短路 |
| LANG-05-004 | 副作用顺序 | MUST | PARTIAL | vm.tll | Left-to-right 初步验证，复杂表达式需测试 |
| LANG-05-005 | 赋值交互 | MUST | PARTIAL | parser.tll:498 | 赋值优先级最低，RHS 先求值 |
| LANG-05-006 | 三元交互 | MUST | PARTIAL | parser.tll:482 | 三元在赋值和 Or 之间 |
| LANG-05-007 | 函数调用交互 | MUST | COMPLETE | parser.tll:752 | 函数调用最高优先级（postfix） |
| LANG-05-008 | 索引/成员交互 | MUST | COMPLETE | parser.tll:760,768 | 索引/成员最高优先级（postfix） |
| LANG-05-009 | 一元交互 | MUST | COMPLETE | parser.tll:691 | 一元在 Power 和 Postfix 之间 |
| LANG-05-010 | 幂运算交互 | MUST | COMPLETE | parser.tll:677 | Power 在 Multiplication 和 Unary 之间 |

---

## 06 Type System（详细审计，见主文档）

（16 项类型系统详细审计，已在主文档中完成）

---

## 07 Composite Types（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 08 Variables & Binding（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 09 Functions & Closures（详细审计，见主文档）

（18 项函数与闭包详细审计，已在主文档中完成）

---

## 10 Control Flow（详细审计，见主文档）

（12 项控制流详细审计，已在主文档中完成）

---

## 11 Pattern Matching（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-11-001 | match 表达式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 parseMatch，无 Match AST |
| LANG-11-002 | 字面量模式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-003 | 变量模式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-004 | 通配符模式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-005 | Struct 模式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-006 | Tuple 模式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-007 | 枚举模式 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-008 | 模式守卫 (guard) | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-009 | 嵌套模式 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |
| LANG-11-010 | 模式穷尽性检查 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无模式匹配 |

**结论**: Pattern Matching 全链路缺失，不属于 NOT_DESIGNED，架构师已决定 MUST HAVE。

---

## 12 Destructuring（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-12-001 | Tuple 解构 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-002 | Struct 解构 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-003 | Array 解构 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-004 | Map 解构 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-005 | 嵌套解构 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-006 | 默认值解构 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-007 | 重命名解构 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |
| LANG-12-008 | 函数参数解构 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构解析 |

**结论**: Destructuring 全链路缺失，不属于 NOT_DESIGNED，架构师已决定 MUST HAVE。

---

## 13 Error & Resource Semantics（详细审计，见主文档）

（8 项错误与资源语义详细审计，已在主文档中完成）

---

## 14 Resource / Cleanup（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 15 Module / Package（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 16 Generic（详细审计，见主文档）

（4 项泛型详细审计，已在主文档中完成，全链路缺失）

---

## 17 Enum / ADT（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 18 Interface / Trait（详细审计，见主文档）

（6 项接口/特质详细审计，已在主文档中完成，全链路缺失）

---

## 19 Methods / Object Model（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 20 Memory / Value / Reference（详细审计，基于 Runtime 证据）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-20-001 | 赋值语义 | MUST | COMPLETE | vm.tll:89 | `vm_registers[idx] = value`，直接引用赋值，无拷贝 |
| LANG-20-002 | 基本类型值语义 | MUST | COMPLETE | vm.tll | int/float/bool/string/null 不可变，表现为值语义 |
| LANG-20-003 | 复合类型引用语义 | MUST | COMPLETE | vm.tll:672,703 | array/map/struct 作为对象存储，赋值传递引用 |
| LANG-20-004 | 参数传递语义 | MUST | COMPLETE | vm.tll:575 | `vm_setLocal(pi, arrays.get(args, pi))`，直接引用传递 |
| LANG-20-005 | 返回值语义 | MUST | COMPLETE | vm.tll:595 | `vm_setReg(retReg, returnValue)`，直接引用返回 |
| LANG-20-006 | 闭包捕获语义 | MUST | COMPLETE | vm.tll:552 | `callClosureEnv = possibleFn["env"]`，闭包持有环境对象引用 |
| LANG-20-007 | Struct 赋值语义 | MUST | COMPLETE | vm.tll | Struct 作为对象存储，赋值传递引用 |
| LANG-20-008 | Array/Map 赋值语义 | MUST | COMPLETE | vm.tll | Array/Map 作为对象存储，赋值传递引用 |
| LANG-20-009 | 可变性 | MUST | COMPLETE | - | 无 const/immutable 关键字，所有变量默认可变 |
| LANG-20-010 | 别名 (aliasing) | MUST | COMPLETE | vm.tll | 引用语义天然允许多个变量指向同一对象 |
| LANG-20-011 | 深拷贝 | SHOULD | MISSING | - | 无内置 deep copy 函数 |
| LANG-20-012 | 浅拷贝 | SHOULD | PARTIAL | stdlib | arrays.slice 可用于数组浅拷贝，Map/Struct 无 |
| LANG-20-013 | 所有权 (Ownership) | NOT_DESIGNED | NOT_DESIGNED | - | 不采用 Rust 式所有权，属于架构决策 |
| LANG-20-014 | 借用 (Borrowing) | NOT_DESIGNED | NOT_DESIGNED | - | 不采用 Rust 式借用，属于架构决策 |
| LANG-20-015 | 生命周期 (Lifetime) | NOT_DESIGNED | NOT_DESIGNED | - | 不采用 Rust 式生命周期，属于架构决策 |

**结论**: TLL 采用引用语义（Reference Semantics），复合类型按引用传递和赋值；基本类型因不可变性表现为值语义。Ownership/Borrowing/Lifetime 明确 NOT_DESIGNED。

---

## 21 Evaluation Semantics（详细审计，基于 Runtime 证据）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-21-001 | 求值顺序 | MUST | COMPLETE | vm.tll | VM 指令按顺序执行，codegen 按从左到右生成指令 |
| LANG-21-002 | 参数求值顺序 | MUST | COMPLETE | vm.tll:488 | argStack 按从左到右压入，按顺序读取 |
| LANG-21-003 | 操作数求值顺序 | MUST | COMPLETE | codegen.tll | 二元运算 codegen 先求左操作数，再求右操作数 |
| LANG-21-004 | 赋值 RHS 求值 | MUST | COMPLETE | codegen.tll | 赋值表达式先计算 RHS，再执行赋值 |
| LANG-21-005 | 副作用 | MUST | COMPLETE | vm.tll | 表达式中允许函数调用等副作用 |
| LANG-21-006 | 短路求值 | MUST | COMPLETE | codegen.tll | and/or/三元表达式支持短路，codegen 生成条件跳转 |
| LANG-21-007 | 条件分支求值 | MUST | COMPLETE | codegen.tll | if/三元只执行满足条件的分支，codegen 生成跳转 |
| LANG-21-008 | 链式赋值求值 | SHOULD | PARTIAL | codegen.tll | `a = b = c` 求值顺序需进一步验证 |
| LANG-21-009 | 索引表达式求值 | MUST | COMPLETE | codegen.tll | 先求对象，再求索引，再取值 |
| LANG-21-010 | 成员访问求值 | MUST | COMPLETE | codegen.tll | 先求对象，再访问成员 |

**重要区分**: "赋值先求 RHS" ≠ "赋值求值顺序 Right-to-left"。赋值表达式 `a = b` 的执行顺序是：先求 `b`（RHS），再赋值给 `a`（LHS）。

**结论**: TLL 采用从左到右求值顺序（Left-to-right Evaluation Order），赋值表达式先求 RHS 再赋值，短路求值支持。

---

## 22 Concurrency（详细审计，见主文档）

（7 项并发详细审计，已在主文档中完成，需与 High-Frame Runtime 一体设计）

---

## 23 Compile-time Capabilities（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 24 FFI / Native（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 25 Compiler Infrastructure（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 26 Compiler Error（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 27 Source Compatibility（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 28 Stdlib Boundary（摘要，待展开）

（待展开为逐项 Capability Matrix）

---

## 架构决策汇总

### MUST HAVE（架构师已确定）

1. 三元表达式 `? :`（已实现，待封板）
2. 位运算复合赋值 `&= |= ^= <<= >>=`
3. 自增/自减 `++`/`--`
4. Pattern Matching
5. Destructuring
6. Generic
7. Interface / Trait
8. Error Model
9. Resource Cleanup
10. Module / Package
11. ADT / Enum
12. Memory / Value / Reference Semantics（已验证）
13. Evaluation Semantics（已验证）
14. Concurrency foundation
15. FFI / ABI
16. Compiler Diagnostics
17. Compiler Infrastructure
18. Range
19. Iterator / Generator

### MUST HAVE，但必须先做架构设计

- async / await（必须与 Future/Task/ExecutionContext/Worker/Scheduler/High-Frame Runtime 一体设计）
- Ownership / Lifetime semantics（先架构决策，不机械照搬 Rust）
- Compile-time capabilities（先完成架构边界）

### SHOULD HAVE

- `??` nullish coalescing
- `?.` optional chaining
- advanced macro system
- attributes
- advanced metaprogramming

### NOT_DESIGNED

- Ownership / Borrow（不机械照搬 Rust）
- 标识符长度限制（无限制）

---

## 四个架构级 GAP（暂不施工，只冻结决策）

1. **Generic（泛型）** - MUST HAVE，全链路缺失
2. **Interface / Trait（接口/特质）** - MUST HAVE，全链路缺失
3. **Error + Resource Semantics（错误+资源语义）** - MUST HAVE，部分缺失
4. **Concurrency / Async（并发/异步）** - MUST HAVE，需与 High-Frame Runtime 一体设计

---

## 待完成项

1. ⏳ 14 个摘要域展开为逐项 Capability Matrix（07, 08, 14, 15, 17, 19, 23, 24, 25, 26, 27, 28）
2. ⏳ 603 TypeChecker warnings 分类（A-H 8 类）
3. ⏳ UNKNOWN 清零（所有状态必须有真实证据）
4. ⏳ Exact Count 自动校验（使用 audit/final-gap-check.py）
5. ⏳ 三元表达式 CI 验证封板
6. ⏳ 最终统计更新（TOTAL = exact number，UNKNOWN = 0）

---

**文档结束（Phase 4 FINAL EVIDENCE CLOSURE 进行中）**
