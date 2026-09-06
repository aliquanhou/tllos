# TLL Language Fundamental Capability Matrix

**版本**: v1.0-draft
**日期**: 2026-09-06
**基线**: TLL OS 6875401
**分支**: feature/P0-tll-language-fundamentals
**状态**: 审计中

---

## 概述

本文档定义 TLL 编程语言的基础能力基线（Fundamental Baseline），并审计当前实现状态（Reality），生成差距分析（GAP Matrix）。

目标：把 TLL 补成一门具备完整、可预期、可实际编程使用的基础语言。

---

## 状态定义

| 状态 | 含义 |
|------|------|
| SEALED | 已完整实现，有测试和 CI 证据，已封板 |
| COMPLETE | 已完整实现，有测试证据，待封板 |
| PARTIAL | 部分实现，存在已知限制 |
| MISSING | 完全未实现 |
| NOT_DESIGNED | 明确的语言设计决策，不计划支持 |
| DEFERRED | 未来高级能力，暂缓实现 |

---

## 一、数值字面量

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| N-01 | 整数 | `42`, `-1`, `0` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| N-02 | 负整数 | `-42` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| N-03 | 浮点数 | `3.14`, `0.5` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| N-04 | 十六进制 | `0xFF`, `0xff` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | PARTIAL |
| N-05 | 二进制 | `0b1010` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | MISSING |
| N-06 | 八进制 | `0o755` | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | ❓ | MISSING |
| N-07 | 数字分隔符 | `1_000_000` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | NOT_DESIGNED |

---

## 二、算术运算

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| A-01 | 加法 | `a + b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-02 | 减法 | `a - b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-03 | 乘法 | `a * b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-04 | 除法 | `a / b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-05 | 模运算 | `a % b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-06 | 幂运算 | `a ** b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-07 | 正号一元 | `+a` | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❓ | PARTIAL |
| A-08 | 负号一元 | `-a` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| A-09 | 除零语义 | `1 / 0` | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |
| A-10 | 溢出语义 | 整数溢出 | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |

---

## 三、比较运算

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| C-01 | 等于 | `a == b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| C-02 | 不等于 | `a != b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| C-03 | 小于 | `a < b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| C-04 | 大于 | `a > b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| C-05 | 小于等于 | `a <= b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| C-06 | 大于等于 | `a >= b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| C-07 | 字符串比较 | `"a" < "b"` | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |
| C-08 | 引用比较 | 对象/结构体 == | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |

---

## 四、逻辑运算

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| L-01 | 逻辑与 | `a and b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| L-02 | 逻辑或 | `a or b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| L-03 | 逻辑非 | `not a` / `!a` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| L-04 | 符号与 | `a && b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | NOT_DESIGNED |
| L-05 | 符号或 | `a \|\| b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | NOT_DESIGNED |
| L-06 | 短路语义 | `false and X` | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |

**设计决策**: TLL 使用关键字 `and`/`or`/`not`，不使用符号 `&&`/`||`/`!`（`!` 作为 `not` 的别名已支持）。

---

## 五、位运算

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| B-01 | 位与 | `a & b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| B-02 | 位或 | `a \| b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| B-03 | 位异或 | `a ^ b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| B-04 | 位非 | `~a` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| B-05 | 左移 | `a << b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| B-06 | 右移 | `a >> b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| B-07 | 有符号/无符号 | 右移规则 | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |
| B-08 | 移位量边界 | `a << 64` | - | - | - | - | ❓ | ❓ | ❓ | PARTIAL |

**注**: 位运算在 P0-15 区块链压力测试中暴露缺口后已补齐，待正式封板。

---

## 六、三元表达式（关键 GAP）

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| T-01 | 三元表达式 | `cond ? a : b` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |

**根因分析**:
- Lexer 已定义 `TK_QUESTION` token（lexer.tll:97）
- Parser 中 `parseAssignment()` 直接调用 `parseOr()`，**缺少 `parseTernary()` 层**
- AST/Codegen/Runtime 均未实现
- Linker 中已有 "Ternary" 节点处理痕迹，说明设计时已预留但未完整实现

**必须补齐**: 完整实现 Lexer → Parser → AST → TypeChecker → Codegen → Runtime → 短路语义 → 测试 → CI。

---

## 七、赋值运算

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| AS-01 | 简单赋值 | `a = b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | SEALED |
| AS-02 | 加等 | `a += b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| AS-03 | 减等 | `a -= b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| AS-04 | 乘等 | `a *= b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| AS-05 | 除等 | `a /= b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| AS-06 | 模等 | `a %= b` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE |
| AS-07 | 位与等 | `a &= b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| AS-08 | 位或等 | `a \|= b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| AS-09 | 位异或等 | `a ^= b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| AS-10 | 左移等 | `a <<= b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| AS-11 | 右移等 | `a >>= b` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |

---

## 八、自增/自减

| ID | 能力 | 语法示例 | Lexer | Parser | AST | Codegen | Runtime | 测试 | CI | 状态 |
|----|------|----------|-------|--------|-----|---------|---------|------|----|------|
| INC-01 | 后置自增 | `i++` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| INC-02 | 前置自增 | `++i` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| INC-03 | 后置自减 | `i--` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |
| INC-04 | 前置自减 | `--i` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **MISSING** |

**设计决策待定**: 需要架构判断 ++/-- 是否属于 TLL 基础语言能力。如果支持，必须明确前置/后置返回值语义。

---

## 九、运算符优先级

| 优先级（高→低） | 运算符 | 状态 |
|-----------------|--------|------|
| 1 | postfix: `()` `.` `[]` | ✅ |
| 2 | unary: `+` `-` `!` `~` | ✅ |
| 3 | power: `**` | ✅ |
| 4 | multiplication: `*` `/` `%` | ✅ |
| 5 | addition: `+` `-` | ✅ |
| 6 | shift: `<<` `>>` | ✅ |
| 7 | range: `..` `..=` | ✅ |
| 8 | comparison: `<` `>` `<=` `>=` | ✅ |
| 9 | equality: `==` `!=` | ✅ |
| 10 | bitwise AND: `&` | ✅ |
| 11 | bitwise XOR: `^` | ✅ |
| 12 | bitwise OR: `\|` | ✅ |
| 13 | logical AND: `and` | ✅ |
| 14 | logical OR: `or` | ✅ |
| 15 | **ternary: `? :`** | **❌ MISSING** |
| 16 | assignment: `=` `+=` `-=` `*=` `/=` `%=` | ✅ |
| 17 | pipe: `\|>` | ✅ |

**GAP**: 三元表达式层缺失，导致 `parseAssignment()` 直接调用 `parseOr()`，跳过了 ternary 层。

---

## 十、表达式系统组合

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| E-01 | 算术组合 | `a + b * c` | ✅ |
| E-02 | 括号优先 | `(a + b) * c` | ✅ |
| E-03 | 比较逻辑组合 | `a > b and c < d` | ✅ |
| E-04 | 三元组合 | `x ? a + b : c * d` | ❌ |
| E-05 | 函数参数表达式 | `foo(a + b, c * d)` | ✅ |
| E-06 | 链式成员访问 | `user.profile.name` | ✅ |
| E-07 | 链式索引 | `items[0].price` | ✅ |
| E-08 | 嵌套函数调用 | `foo(bar(baz()))` | ✅ |

---

## 十一、函数与 Lambda

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| F-01 | 命名函数 | `fn foo() {}` | ✅ SEALED |
| F-02 | 匿名函数 | `fn() {}` | ✅ |
| F-03 | Lambda 箭头 | `->` / `=>` | ✅ |
| F-04 | 闭包 | 捕获外部变量 | ❓ PARTIAL |
| F-05 | 嵌套函数 | 函数内定义函数 | ✅ |
| F-06 | 递归函数 | 函数调用自身 | ✅ |
| F-07 | 函数作为值 | 赋值/传参/返回 | ✅ |
| F-08 | 函数参数类型 | `fn foo(x: int)` | ✅ |
| F-09 | 函数返回类型 | `fn foo() -> int` | ✅ |

---

## 十二、集合基础

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| S-01 | Array 创建 | `[1, 2, 3]` | ✅ SEALED |
| S-02 | Array 索引 | `arr[0]` | ✅ |
| S-03 | Array 修改 | `arr[0] = 42` | ✅ |
| S-04 | Array 长度 | `arrays.length(arr)` | ✅ |
| S-05 | Map 创建 | `{key: value}` | ✅ |
| S-06 | Map 访问 | `map.key` / `map["key"]` | ✅ |
| S-07 | Map 修改 | `map.key = value` | ✅ |
| S-08 | Struct 定义 | `struct Foo { x: int }` | ✅ |
| S-09 | Struct 实例化 | `Foo { x: 42 }` | ✅ |
| S-10 | 嵌套集合 | `[[1,2], [3,4]]` | ✅ |
| S-11 | 集合遍历 | while / for | ✅ |

---

## 十三、控制流基础

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| CF-01 | if | `if cond {}` | ✅ SEALED |
| CF-02 | if-else | `if cond {} else {}` | ✅ |
| CF-03 | else-if | `else if cond {}` | ✅ |
| CF-04 | while | `while cond {}` | ✅ |
| CF-05 | for | `for i in range {}` | ✅ |
| CF-06 | foreach | `for item in arr {}` | ❓ PARTIAL |
| CF-07 | break | `break` | ✅ |
| CF-08 | continue | `continue` | ✅ |
| CF-09 | return | `return value` | ✅ |
| CF-10 | 嵌套控制流 | 嵌套 if/while/for | ✅ |

---

## 十四、类型基础

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| TY-01 | int | `let x: int = 42` | ✅ |
| TY-02 | float | `let x: float = 3.14` | ✅ |
| TY-03 | bool | `let x: bool = true` | ✅ |
| TY-04 | string | `let x: string = "hi"` | ✅ |
| TY-05 | null | `null` | ✅ |
| TY-06 | array | `let x: []int` | ❓ |
| TY-07 | map | `let x: {}string` | ❓ |
| TY-08 | struct | 自定义类型 | ✅ |
| TY-09 | function | 函数类型 | ❓ |
| TY-10 | 类型转换 | `convert.toInt(x)` | ✅ |
| TY-11 | 类型推断 | `let x = 42` | ✅ |
| TY-12 | TypeChecker | 编译期类型检查 | ⚠️ 603 warnings |

---

## 十五、错误/异常语义

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| ER-01 | try | `try {}` | ✅ |
| ER-02 | catch | `catch e {}` | ❓ |
| ER-03 | throw | `throw "error"` | ✅ |
| ER-04 | 异常类型 | 自定义异常 | ❓ |
| ER-05 | finally | `finally {}` | ❌ MISSING |
| ER-06 | Result 类型 | `Result<T, E>` | ❌ NOT_DESIGNED |
| ER-07 | Optional 类型 | `Option<T>` | ❌ NOT_DESIGNED |

---

## 十六、模块系统

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| M-01 | import | `import "./foo"` | ✅ SEALED |
| M-02 | from import | `from "./foo" import bar` | ✅ |
| M-03 | export | `export fn foo()` | ✅ |
| M-04 | package | 包管理 | ❓ PARTIAL |
| M-05 | 循环依赖 | 循环 import 处理 | ❓ |
| M-06 | 符号可见性 | public/private | ❓ |

---

## 十七、字符串基础能力

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| ST-01 | 字符串字面量 | `"hello"` | ✅ SEALED |
| ST-02 | 原始字符串 | `` `hello` `` | ✅ |
| ST-03 | 转义序列 | `\n`, `\t`, `\\` | ✅ |
| ST-04 | Unicode | 中文字符 | ✅ |
| ST-05 | 拼接 | `"a" + "b"` | ✅ |
| ST-06 | 长度 | `strings.length(s)` | ✅ |
| ST-07 | 索引 | `strings.charAt(s, i)` | ✅ |
| ST-08 | 子串 | `strings.substring(s, a, b)` | ✅ |
| ST-09 | 字符串插值 | `"\(name)"` / `` `${name}` `` | ❌ MISSING |

---

## 十八、null / optional 语义

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| NU-01 | null 字面量 | `null` | ✅ |
| NU-02 | null 比较 | `x == null` | ✅ |
| NU-03 | null 赋值 | `x = null` | ✅ |
| NU-04 | null 返回 | `return null` | ✅ |
| NU-05 | null 解引用 | `null.field` | ❓ 运行时错误 |
| NU-06 | nullish coalescing | `a ?? b` | ❌ MISSING |
| NU-07 | optional chaining | `a?.b` | ❌ MISSING |

---

## 十九、范围 Range

| ID | 能力 | 语法示例 | 状态 |
|----|------|----------|------|
| R-01 | 排他范围 | `a..b` | ✅ |
| R-02 | 包容范围 | `a..=b` | ✅ |
| R-03 | 范围迭代 | `for i in 0..10` | ✅ |
| R-04 | 降序范围 | `10..0` | ❓ |
| R-05 | 步长 | `0..10 step 2` | ❌ MISSING |

---

## 二十、并发相关（Language vs Runtime 区分）

| ID | 能力 | 层级 | 状态 |
|----|------|------|------|
| CC-01 | spawn | Runtime API | ✅ |
| CC-02 | worker pool | Runtime | ✅ |
| CC-03 | channel | Runtime API | ❓ |
| CC-04 | mutex | Runtime API | ❓ |
| CC-05 | atomic | Runtime API | ❓ |
| CC-06 | async/await | Language | ❌ NOT_DESIGNED |
| CC-07 | go 语句 | Language | ❌ NOT_DESIGNED |

---

## GAP 汇总（必须补齐）

### 高优先级（基础表达式能力）

| 优先级 | ID | 能力 | 当前状态 | 目标 |
|--------|----|------|----------|------|
| P0 | T-01 | 三元表达式 `? :` | MISSING | COMPLETE → SEALED |
| P1 | AS-07 | 位与等 `&=` | MISSING | COMPLETE |
| P1 | AS-08 | 位或等 `\|=` | MISSING | COMPLETE |
| P1 | AS-09 | 位异或等 `^=` | MISSING | COMPLETE |
| P1 | AS-10 | 左移等 `<<=` | MISSING | COMPLETE |
| P1 | AS-11 | 右移等 `>>=` | MISSING | COMPLETE |

### 中优先级（语言设计决策）

| 优先级 | ID | 能力 | 当前状态 | 目标 |
|--------|----|------|----------|------|
| P2 | INC-01~04 | 自增/自减 `++`/`--` | MISSING | 设计决策 |
| P2 | ST-09 | 字符串插值 | MISSING | 设计决策 |
| P2 | NU-06 | nullish coalescing `??` | MISSING | 设计决策 |
| P2 | NU-07 | optional chaining `?.` | MISSING | 设计决策 |

### 低优先级（完善项）

| 优先级 | ID | 能力 | 当前状态 | 目标 |
|--------|----|------|----------|------|
| P3 | N-04~06 | 十六进制/二进制/八进制字面量 | PARTIAL | COMPLETE |
| P3 | L-06 | 短路语义验证 | PARTIAL | 测试补齐 |
| P3 | ER-05 | finally | MISSING | 设计决策 |
| P3 | R-05 | 范围步长 | MISSING | 设计决策 |

---

## 施工顺序

1. **P0**: 三元表达式 `? :` 完整实现（Lexer → Parser → AST → TypeChecker → Codegen → Runtime → 短路 → 测试 → CI）
2. **P1**: 位运算复合赋值 `&= |= ^= <<= >>=`
3. **P2**: 自增/自减设计决策与实现（如决定支持）
4. **P3**: 其他完善项
5. **回归测试**: 确保现有 TLL 测试不回归
6. **自举验证**: 编译器自编译不回归
7. **三平台 CI**: Linux / Windows / macOS 全绿
8. **Capability Matrix 更新**
9. **Evidence 与 commit 对齐**
10. **架构师审计 → 合并**

---

**文档结束**
