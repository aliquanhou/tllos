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

**审计覆盖**: 16/28 Domains 已详细审计，12/28 Domains 待展开

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

## 07 Composite Types（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-07-001 | Array/List 创建 | MUST | COMPLETE | parser.tll:882 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | [1, 2, 3] |
| LANG-07-002 | Array 索引读取 | MUST | COMPLETE | parser.tll:768 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | arr[i] |
| LANG-07-003 | Array 索引写入 | MUST | COMPLETE | vm.tll:672 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | arr[i] = x |
| LANG-07-004 | Array 长度 | MUST | COMPLETE | stdlib | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | arrays.length(arr) |
| LANG-07-005 | Array 遍历 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | for x in arr |
| LANG-07-006 | Array 嵌套 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | [[1,2], [3,4]] |
| LANG-07-007 | Array 传参 | MUST | COMPLETE | vm.tll:575 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 引用传递 |
| LANG-07-008 | Array 返回 | MUST | COMPLETE | vm.tll:595 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 引用返回 |
| LANG-07-009 | Array 别名 (aliasing) | MUST | COMPLETE | vm.tll:89 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | 引用语义，a=b 后 a[0] 修改影响 b[0] |
| LANG-07-010 | Map 创建 | MUST | COMPLETE | parser.tll:899 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | {"a": 1} |
| LANG-07-011 | Map 键读取 | MUST | COMPLETE | parser.tll:768 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | map["key"] |
| LANG-07-012 | Map 键写入 | MUST | COMPLETE | vm.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | map["key"] = x |
| LANG-07-013 | Map 包含检查 | MUST | COMPLETE | stdlib | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | maps.contains(map, key) |
| LANG-07-014 | Map 遍历 | MUST | COMPLETE | stdlib | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | maps.keys/maps.values |
| LANG-07-015 | Map 嵌套 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | {"a": {"b": 1}} |
| LANG-07-016 | Map 别名 (aliasing) | MUST | COMPLETE | vm.tll:89 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | 引用语义 |
| LANG-07-017 | Struct 定义 | MUST | COMPLETE | parser.tll:168 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | struct Person { name: string, age: int } |
| LANG-07-018 | Struct 构造 | MUST | COMPLETE | parser.tll:168 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Person{name: "x", age: 1} |
| LANG-07-019 | Struct 字段读取 | MUST | COMPLETE | parser.tll:760 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | person.name |
| LANG-07-020 | Struct 字段写入 | MUST | COMPLETE | vm.tll:703 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | person.name = "y" |
| LANG-07-021 | Struct 嵌套 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 嵌套 Struct |
| LANG-07-022 | Struct 传参 | MUST | COMPLETE | vm.tll:575 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 引用传递 |
| LANG-07-023 | Struct 返回 | MUST | COMPLETE | vm.tll:595 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 引用返回 |
| LANG-07-024 | Struct 别名 (aliasing) | MUST | COMPLETE | vm.tll:89 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | 引用语义，a=b 后 a.x 修改影响 b.x |
| LANG-07-025 | Tuple 类型 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 Tuple 类型，多返回值通过其他机制 |
| LANG-07-026 | 多返回值 | MUST | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 支持多返回值，但非 Tuple 语义 |
| LANG-07-027 | 复合类型相等比较 | SHOULD | PARTIAL | - | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 基本类型相等已支持，复合类型引用相等 |
| LANG-07-028 | 空复合类型 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | [], {} |
| LANG-07-029 | 复合类型闭包捕获 | MUST | COMPLETE | vm.tll:552 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | 引用捕获 |
| LANG-07-030 | 复合类型可变性 | MUST | COMPLETE | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 默认可变 |

**结论**: Array/Map/Struct 全部 COMPLETE，引用语义；Tuple 类型 MISSING；多返回值 PARTIAL（非 Tuple 语义）。

---

## 08 Variables & Binding（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-08-001 | 变量声明 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | let x = 10 |
| LANG-08-002 | 变量初始化 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | let x = 10（声明时初始化） |
| LANG-08-003 | 变量重新赋值 | MUST | COMPLETE | vm.tll:89 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | x = 20 |
| LANG-08-004 | 局部作用域 | MUST | COMPLETE | vm.tll:100 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 函数内局部变量 |
| LANG-08-005 | 块作用域 | SHOULD | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | {} 块内变量，需验证作用域规则 |
| LANG-08-006 | 函数作用域 | MUST | COMPLETE | vm.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 函数参数和局部变量 |
| LANG-08-007 | 模块/全局作用域 | MUST | COMPLETE | vm.tll:105 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 全局变量 |
| LANG-08-008 | 变量遮蔽 (shadowing) | SHOULD | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 内层变量遮蔽外层，需验证 |
| LANG-08-009 | 参数绑定 | MUST | COMPLETE | vm.tll:575 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 函数参数绑定 |
| LANG-08-010 | 返回值绑定 | MUST | COMPLETE | vm.tll:595 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | return x |
| LANG-08-011 | 可变绑定 | MUST | COMPLETE | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 默认所有变量可变 |
| LANG-08-012 | const/immutable | NOT_DESIGNED | NOT_DESIGNED | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 无 const 关键字，属于设计决策 |
| LANG-08-013 | 未定义变量 | MUST | COMPLETE | typechecker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | TypeChecker 报错 undefined symbol |
| LANG-08-014 | 使用前定义 (use-before-def) | MUST | PARTIAL | typechecker.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 需验证是否检测使用前定义 |
| LANG-08-015 | 变量生命周期 | MUST | COMPLETE | vm.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 函数调用栈管理 |
| LANG-08-016 | 变量逃逸 (escape) | SHOULD | PARTIAL | vm.tll:552 | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 闭包捕获导致变量逃逸 |
| LANG-08-017 | 显式类型标注 | SHOULD | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | let x: int = 10（需验证支持程度） |
| LANG-08-018 | 类型推断 | MUST | COMPLETE | typechecker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | let x = 10 推断为 int |
| LANG-08-019 | 解构赋值 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无解构赋值（见 LANG-12） |
| LANG-08-020 | 多变量声明 | SHOULD | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | let a = 1, b = 2（需验证） |

**结论**: 变量绑定基本 COMPLETE，块作用域/遮蔽/使用前定义 PARTIAL，const/immutable NOT_DESIGNED，解构赋值 MISSING。

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

## 14 Resource / Cleanup（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-14-001 | defer 语句 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 defer 关键字 |
| LANG-14-002 | finally 块 | MUST | PARTIAL | parser.tll:317 | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | try/catch/finally 存在，需验证资源清理 |
| LANG-14-003 | using/with 语句 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 using/with 语句 |
| LANG-14-004 | RAII 语义 | NOT_DESIGNED | NOT_DESIGNED | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 不采用 RAII，属于设计决策 |
| LANG-14-005 | 资源释放机制 | MUST | PARTIAL | stdlib | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 依赖手动释放，无自动机制 |
| LANG-14-006 | 文件句柄管理 | MUST | PARTIAL | stdlib | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | io 模块，需验证自动关闭 |
| LANG-14-007 | Socket 句柄管理 | MUST | PARTIAL | stdlib | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | net 模块，需验证自动关闭 |
| LANG-14-008 | 数据库连接管理 | MUST | PARTIAL | stdlib | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | sqlite 模块，需验证自动关闭 |
| LANG-14-009 | 锁/事务管理 | SHOULD | PARTIAL | stdlib | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 需验证 |
| LANG-14-010 | 清理顺序保证 | MUST | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 defer/finally 顺序保证 |
| LANG-14-011 | 异常时清理 | MUST | PARTIAL | parser.tll:317 | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | finally 块可处理异常时清理 |
| LANG-14-012 | 内存/资源句柄 | MUST | COMPLETE | vm.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | VM 管理对象生命周期 |

**结论**: defer/using MISSING，finally PARTIAL，资源释放依赖手动管理，无自动机制。

---

## 15 Module / Package（详细审计）

| ID | Capability | Expected | Actual | Source | Lexer | Parser | AST | TypeChecker | Codegen | Runtime | Test | CI | Evidence |
|----|-----------|----------|--------|--------|-------|--------|-----|-------------|---------|---------|------|-----|----------|
| LANG-15-001 | import 语句 | MUST | COMPLETE | parser.tll:343 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | import module from "path" |
| LANG-15-002 | export 语句 | MUST | COMPLETE | parser.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | export function/struct |
| LANG-15-003 | module 关键字 | SHOULD | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 需验证 module 块支持 |
| LANG-15-004 | package 概念 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无 package 管理系统 |
| LANG-15-005 | namespace | SHOULD | PARTIAL | linker.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 模块命名空间，需验证 |
| LANG-15-006 | 符号解析 | MUST | COMPLETE | linker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Linker 解析导入符号 |
| LANG-15-007 | import alias | SHOULD | COMPLETE | parser.tll:343 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | import x as y |
| LANG-15-008 | 可见性 (public/private) | SHOULD | PARTIAL | parser.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 需验证 private 关键字支持 |
| LANG-15-009 | 重复符号检测 | MUST | COMPLETE | typechecker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | TypeChecker 报错 duplicate symbol |
| LANG-15-010 | 缺失符号检测 | MUST | COMPLETE | typechecker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | TypeChecker 报错 undefined symbol |
| LANG-15-011 | 循环依赖 | SHOULD | PARTIAL | linker.tll | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | 需验证循环依赖处理 |
| LANG-15-012 | 模块边界 | MUST | COMPLETE | linker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 模块独立编译/链接 |
| LANG-15-013 | 包版本 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无包版本管理 |
| LANG-15-014 | 包兼容性 | SHOULD | MISSING | - | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 无包兼容性检查 |
| LANG-15-015 | 相对导入 | MUST | COMPLETE | linker.tll:611 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 相对路径导入 |
| LANG-15-016 | 绝对导入 | MUST | COMPLETE | linker.tll | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 绝对路径导入 |

**结论**: import/export/符号解析 COMPLETE，package/版本/兼容性 MISSING，可见性/循环依赖 PARTIAL。

---

## 16 Generic（详细审计，见主文档）

（4 项泛型详细审计，已在主文档中完成，全链路缺失）

---

## 17 Enum / ADT（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-17-001 | enum 声明 | MUST | PARTIAL | parser.tll | 需验证 enum 关键字支持 |
| LANG-17-002 | 枚举值 | MUST | PARTIAL | parser.tll | 枚举常量 |
| LANG-17-003 | 枚举比较 | MUST | PARTIAL | - | 需验证 |
| LANG-17-004 | 枚举 switch/match | SHOULD | MISSING | - | 无 Pattern Matching（见 LANG-11） |
| LANG-17-005 | 带值枚举 (tagged union) | MUST | MISSING | - | 无 ADT/tagged union |
| LANG-17-006 | 枚举 payload | MUST | MISSING | - | 无 payload |
| LANG-17-007 | 枚举构造 | MUST | MISSING | - | 无带值构造 |
| LANG-17-008 | 枚举提取 | MUST | MISSING | - | 无 payload 提取 |
| LANG-17-009 | 枚举类型检查 | MUST | PARTIAL | typechecker.tll | 简单枚举类型检查 |
| LANG-17-010 | 枚举代码生成 | MUST | PARTIAL | codegen.tll | 简单枚举代码生成 |
| LANG-17-011 | 枚举运行时表示 | MUST | PARTIAL | vm.tll | 简单枚举作为整数 |
| LANG-17-012 | 枚举方法 | SHOULD | MISSING | - | 无枚举方法 |

**结论**: 简单枚举 PARTIAL，带值枚举/ADT/tagged union 全链路 MISSING。

---

## 18 Interface / Trait（详细审计，见主文档）

（6 项接口/特质详细审计，已在主文档中完成，全链路缺失）

---

## 19 Methods / Object Model（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-19-001 | 方法定义 | MUST | COMPLETE | parser.tll | struct 内方法定义 |
| LANG-19-002 | self/this | MUST | COMPLETE | parser.tll | self 关键字 |
| LANG-19-003 | 构造函数 | SHOULD | PARTIAL | parser.tll | Struct{...} 字面量构造，无专门 constructor |
| LANG-19-004 | 静态方法 | SHOULD | PARTIAL | parser.tll | 需验证 static 关键字 |
| LANG-19-005 | 字段可见性 | SHOULD | PARTIAL | parser.tll | 需验证 private/public 字段 |
| LANG-19-006 | 方法接收者 | MUST | COMPLETE | vm.tll | 方法调用时 self 绑定 |
| LANG-19-007 | 方法分派 | MUST | COMPLETE | codegen.tll | 静态分派（Struct 方法） |
| LANG-19-008 | 继承 (inheritance) | NOT_DESIGNED | NOT_DESIGNED | - | 不采用类继承，属于设计决策 |
| LANG-19-009 | 组合 (composition) | MUST | COMPLETE | parser.tll | Struct 嵌套组合 |
| LANG-19-010 | 嵌入 (embedding) | SHOULD | MISSING | - | 无 Go 式嵌入 |
| LANG-19-011 | 多态 (polymorphism) | MUST | PARTIAL | - | 接口多态缺失（见 LANG-18），函数多态有限 |
| LANG-19-012 | 方法重写 | NOT_DESIGNED | NOT_DESIGNED | - | 无继承，无重写 |
| LANG-19-013 | 抽象方法 | NOT_DESIGNED | NOT_DESIGNED | - | 无抽象类/接口（见 LANG-18） |
| LANG-19-014 | 对象相等 | SHOULD | PARTIAL | - | 引用相等，无值相等重载 |

**结论**: 方法/self/组合 COMPLETE，继承/嵌入/抽象 NOT_DESIGNED 或 MISSING，多态 PARTIAL。

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

## 23 Compile-time Capabilities（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-23-001 | 常量表达式 | MUST | COMPLETE | parser.tll | 字面量和常量表达式 |
| LANG-23-002 | 常量折叠 (constant folding) | SHOULD | PARTIAL | codegen.tll | 需验证常量折叠优化 |
| LANG-23-003 | 编译时求值 | SHOULD | MISSING | - | 无编译时函数求值 |
| LANG-23-004 | 宏 (macro) | SHOULD | MISSING | - | 无宏系统 |
| LANG-23-005 | 元编程 (metaprogramming) | SHOULD | MISSING | - | 无元编程能力 |
| LANG-23-006 | 注解/属性 (annotation/attribute) | SHOULD | MISSING | - | 无注解系统 |
| LANG-23-007 | 条件编译 | SHOULD | MISSING | - | 无 #ifdef 条件编译 |
| LANG-23-008 | 编译器内建 (compiler intrinsic) | MUST | COMPLETE | codegen.tll | builtin 函数调用 |
| LANG-23-009 | 编译期类型计算 | SHOULD | MISSING | - | 无编译期类型计算 |
| LANG-23-010 | 编译期断言 | SHOULD | MISSING | - | 无 static_assert |

**结论**: 常量表达式/编译器内建 COMPLETE，常量折叠 PARTIAL，宏/元编程/注解/条件编译 MISSING。

---

## 24 FFI / Native Interop（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-24-001 | C ABI | MUST | PARTIAL | runtime | TLL Runtime 本身是 C/C++，但无显式 C ABI 调用 |
| LANG-24-002 | native 函数调用 | MUST | PARTIAL | stdlib | builtin 函数调用 native 实现 |
| LANG-24-003 | 基本类型 ABI | MUST | COMPLETE | runtime | int/float/bool/string ABI |
| LANG-24-004 | Struct ABI | SHOULD | PARTIAL | runtime | 需验证 Struct 与 C 交互 |
| LANG-24-005 | 数组 ABI | SHOULD | PARTIAL | runtime | 需验证数组与 C 交互 |
| LANG-24-006 | 字符串 ABI | MUST | COMPLETE | runtime | 字符串与 native 交互 |
| LANG-24-007 | 指针 (pointer) | SHOULD | MISSING | - | 无显式指针类型 |
| LANG-24-008 | 回调 (callback) | SHOULD | PARTIAL | runtime | 需验证函数指针回调 |
| LANG-24-009 | 所有权边界 | MUST | PARTIAL | runtime | 需验证内存所有权边界 |
| LANG-24-010 | 调用约定 (calling convention) | SHOULD | PARTIAL | runtime | 依赖宿主调用约定 |
| LANG-24-011 | 错误边界 | MUST | PARTIAL | runtime | 需验证 native 错误传播 |
| LANG-24-012 | 函数指针 | SHOULD | PARTIAL | runtime | 函数作为值，需验证与 C 交互 |

**结论**: 基本类型/字符串 ABI COMPLETE，C ABI/native 调用 PARTIAL，指针 MISSING。

---

## 25 Compiler Infrastructure（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-25-001 | Lexer | MUST | COMPLETE | compiler/lexer.tll | 20KB 词法分析器 |
| LANG-25-002 | Parser | MUST | COMPLETE | compiler/parser.tll | 27KB 语法分析器，17 级优先级 |
| LANG-25-003 | AST | MUST | COMPLETE | compiler/parser.tll | AST 节点定义 |
| LANG-25-004 | 符号解析 (Symbol Resolution) | MUST | COMPLETE | compiler/typechecker.tll | 符号表和解析 |
| LANG-25-005 | 类型/语义分析 | MUST | COMPLETE | compiler/typechecker.tll | 15KB 类型检查器，603 warnings |
| LANG-25-006 | 常量折叠 | SHOULD | PARTIAL | compiler/codegen.tll | 需验证常量折叠 |
| LANG-25-007 | 优化 (Optimization) | SHOULD | PARTIAL | compiler/codegen.tll | 需验证优化级别 |
| LANG-25-008 | 代码生成 (Codegen) | MUST | COMPLETE | compiler/codegen.tll | 72KB 代码生成器 |
| LANG-25-009 | 字节码 (Bytecode) | MUST | COMPLETE | compiler/compiler.tllbc | 592KB 编译后字节码 |
| LANG-25-010 | 链接器 (Linker) | MUST | COMPLETE | compiler/linker.tll | 38KB 链接器 |
| LANG-25-011 | Runtime 绑定 | MUST | COMPLETE | runtime/vm.tll | 39KB 虚拟机 |
| LANG-25-012 | 执行 (Execution) | MUST | COMPLETE | runtime/vm.tll | VM 执行循环 |
| LANG-25-013 | Bootstrap | MUST | COMPLETE | compiler/compiler.tll | 自举编译器 |
| LANG-25-014 | 确定性构建 (Deterministic Build) | MUST | COMPLETE | P4 Evidence | 两次自举 SHA256 一致 |
| LANG-25-015 | 增量编译 | SHOULD | MISSING | - | 无增量编译 |
| LANG-25-016 | 编译器自举 (Self-hosting) | MUST | COMPLETE | P4 Evidence | TLL 编译器用 TLL 编写 |
| LANG-25-017 | 调试信息 (Debug Info) | SHOULD | PARTIAL | compiler/codegen.tll | 需验证源位置信息 |
| LANG-25-018 | 源映射 (Source Mapping) | SHOULD | PARTIAL | compiler/codegen.tll | 需验证行号映射 |
| LANG-25-019 | 字节码兼容性 | SHOULD | PARTIAL | runtime/vm.tll | 需验证字节码版本兼容 |
| LANG-25-020 | Artifact Provenance | MUST | COMPLETE | P4 Evidence | SHA256 provenance |

**结论**: 编译器基础设施基本 COMPLETE，增量编译 MISSING，优化/调试信息 PARTIAL。

---

## 26 Compiler Error System（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-26-001 | 语法错误 | MUST | COMPLETE | compiler/parser.tll | expected ')', got '?' |
| LANG-26-002 | 意外 token | MUST | COMPLETE | compiler/parser.tll | unexpected token 报错 |
| LANG-26-003 | 缺失 token | MUST | COMPLETE | compiler/parser.tll | missing token 报错 |
| LANG-26-004 | 源位置 (source location) | MUST | COMPLETE | compiler/lexer.tll | line/column 记录 |
| LANG-26-005 | 行号 (line) | MUST | COMPLETE | compiler/lexer.tll | 行号记录 |
| LANG-26-006 | 列号 (column) | MUST | COMPLETE | compiler/lexer.tll | 列号记录 |
| LANG-26-007 | 期望 token | MUST | COMPLETE | compiler/parser.tll | expected token 报告 |
| LANG-26-008 | 实际 token | MUST | COMPLETE | compiler/parser.tll | actual token 报告 |
| LANG-26-009 | 类型不匹配 | MUST | COMPLETE | compiler/typechecker.tll | type mismatch 报错 |
| LANG-26-010 | 未定义符号 | MUST | COMPLETE | compiler/typechecker.tll | undefined symbol 报错 |
| LANG-26-011 | 重复符号 | MUST | COMPLETE | compiler/typechecker.tll | duplicate symbol 报错 |
| LANG-26-012 | 无效操作符 | MUST | COMPLETE | compiler/typechecker.tll | invalid operator 报错 |
| LANG-26-013 | 无效调用 | MUST | COMPLETE | compiler/typechecker.tll | invalid call 报错 |
| LANG-26-014 | 无效成员 | MUST | COMPLETE | compiler/typechecker.tll | invalid member 报错 |
| LANG-26-015 | 错误传播 | MUST | PARTIAL | compiler/typechecker.tll | 需验证多错误传播 |
| LANG-26-016 | 诊断质量 | SHOULD | PARTIAL | compiler/typechecker.tll | 603 warnings，需提升质量 |
| LANG-26-017 | 错误恢复 | SHOULD | MISSING | - | 无错误恢复（遇错即停） |
| LANG-26-018 | 多错误报告 | SHOULD | PARTIAL | compiler/typechecker.tll | 需验证批量错误报告 |
| LANG-26-019 | 错误建议 (suggestion) | SHOULD | MISSING | - | 无自动修复建议 |
| LANG-26-020 | 上下文信息 | SHOULD | PARTIAL | compiler/typechecker.tll | 需验证错误上下文 |

**结论**: 基本错误报告 COMPLETE，诊断质量/错误恢复 PARTIAL 或 MISSING。

---

## 27 Source Compatibility（详细审计）

| ID | Capability | Expected | Actual | Source | Evidence |
|----|-----------|----------|--------|--------|----------|
| LANG-27-001 | 保留关键字 | MUST | COMPLETE | compiler/lexer.tll | 关键字列表 |
| LANG-27-002 | 标识符规则 | MUST | COMPLETE | compiler/lexer.tll | ASCII 标识符规则 |
| LANG-27-003 | 语法稳定性 | SHOULD | PARTIAL | - | 语言仍在演进，无正式稳定性保证 |
| LANG-27-004 | 版本管理 | SHOULD | MISSING | - | 无语言版本号 |
| LANG-27-005 | 废弃语法 (deprecated) | SHOULD | MISSING | - | 无废弃机制 |
| LANG-27-006 | 向后兼容 | SHOULD | PARTIAL | - | 需验证旧代码兼容性 |
| LANG-27-007 | 破坏性变更 | SHOULD | MISSING | - | 无破坏性变更管理 |
| LANG-27-008 | 源码迁移策略 | SHOULD | MISSING | - | 无迁移工具/策略 |
| LANG-27-009 | 语言规范 | MUST | PARTIAL | docs | 有规范文档，但不完整 |
| LANG-27-010 | 语法演进 | SHOULD | PARTIAL | - | 语言持续演进，无正式流程 |

**结论**: 保留关键字/标识符规则 COMPLETE，版本管理/废弃机制/迁移策略 MISSING，语法稳定性 PARTIAL。

---

## 28 Stdlib Boundary（详细审计）

| ID | Capability | Layer | Actual | Source | Evidence |
|----|-----------|-------|--------|--------|----------|
| LANG-28-001 | crypto | STDLIB | COMPLETE | stdlib/crypto | Ed25519/SHA256/HMAC/bcrypt/Random |
| LANG-28-002 | HTTP | STDLIB | PARTIAL | stdlib/http | Linux/Windows COMPLETE，macOS KNOWN ISSUE |
| LANG-28-003 | filesystem | STDLIB | COMPLETE | stdlib/io | 文件读写 |
| LANG-28-004 | JSON | STDLIB | COMPLETE | stdlib/json | JSON 解析/序列化 |
| LANG-28-005 | SQLite | STDLIB | COMPLETE | stdlib/sqlite | 数据库操作 |
| LANG-28-006 | random | STDLIB | COMPLETE | stdlib/crypto | crypto.randomBytes |
| LANG-28-007 | process | RUNTIME | COMPLETE | runtime/vm.tll | 进程管理 |
| LANG-28-008 | networking | STDLIB | PARTIAL | stdlib/net | Socket 操作 |
| LANG-28-009 | time | STDLIB | COMPLETE | stdlib/time | 时间操作 |
| LANG-28-010 | collections (array) | LANGUAGE | COMPLETE | parser.tll | 数组字面量/索引 |
| LANG-28-011 | collections (map) | LANGUAGE | COMPLETE | parser.tll | Map 字面量/索引 |
| LANG-28-012 | collections (struct) | LANGUAGE | COMPLETE | parser.tll | Struct 定义/访问 |
| LANG-28-013 | string operations | STDLIB | COMPLETE | stdlib/strings | 字符串操作 |
| LANG-28-014 | math | STDLIB | COMPLETE | stdlib/math | 数学函数 |
| LANG-28-015 | conversion | STDLIB | COMPLETE | stdlib/convert | 类型转换 |
| LANG-28-016 | arrays utility | STDLIB | COMPLETE | stdlib/arrays | 数组工具函数 |
| LANG-28-017 | maps utility | STDLIB | COMPLETE | stdlib/maps | Map 工具函数 |
| LANG-28-018 | io | STDLIB | COMPLETE | stdlib/io | 输入输出 |
| LANG-28-019 | os | STDLIB | PARTIAL | stdlib/os | 操作系统接口 |
| LANG-28-020 | regex | STDLIB | MISSING | - | 无正则表达式 |

**重要边界**: 
- **Language**: 数组/Map/Struct 字面量和操作（LANG-28-010/011/012）
- **Compiler**: 编译器内建函数
- **Runtime**: 进程/VM 执行（LANG-28-007）
- **Stdlib**: crypto/HTTP/filesystem/JSON/SQLite/random/networking/time/string/math/conversion/collections utility/io/os
- **Toolchain**: 编译器/链接器/构建工具

**禁止把 Stdlib 功能错误计入 Language Fundamental GAP**：crypto/HTTP/SQLite/filesystem 等是标准库能力，不是语言语法能力。

**结论**: Stdlib 基本 COMPLETE，HTTP/networking/os PARTIAL，regex MISSING。边界清晰，Language/Compiler/Runtime/Stdlib/Toolchain 分层明确。

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
