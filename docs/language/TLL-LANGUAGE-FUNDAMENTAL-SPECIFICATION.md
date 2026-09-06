# TLL Language Fundamental Specification

**版本**: v1.0-draft
**日期**: 2026-09-06
**状态**: EXPECTED 基线建立中
**分支**: feature/P0-tll-language-fundamentals

---

## 概述

本文档定义 TLL 作为通用编程语言的完整基础能力基线（EXPECTED Baseline）。

**目标**：不是"所有语言特性今天全部塞进去"，而是"所有应该有的能力必须有明确结论"。

每一项能力最终必须得到架构决策：
- **MUST HAVE**: 必须实现，不能延期
- **SHOULD HAVE**: 应该实现，高优先级
- **DESIGNED BUT DEFERRED**: 设计确定，暂缓实现
- **NOT_DESIGNED**: 经过架构判断，目前不采用
- **NOT_APPLICABLE**: 不适用于 TLL

---

## 层级区分

| 层级 | 说明 | 示例 |
|------|------|------|
| **Language** | 语法/语义/类型系统 | `a + b`, `if`, `fn`, `struct` |
| **Compiler** | 编译器实现 | Lexer, Parser, AST, TypeChecker, Codegen |
| **Runtime** | 运行时行为 | GC, 内存管理, 并发调度 |
| **Stdlib** | 标准库 | `strings.length()`, `array.sort()` |
| **Toolchain** | 工具链 | 构建系统, 包管理, 调试器 |

---

## 01 Lexical Foundation（词法基础）

### 标识符

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| ASCII 标识符 `abc`, `abc123`, `_private` | MUST HAVE | - |
| 中文/Unicode 标识符 | SHOULD HAVE | 待审计 |
| 标识符最大长度 | SHOULD HAVE | 待定义 |
| 保留关键字 | MUST HAVE | 待审计 |

### 注释

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 行注释 `// comment` | MUST HAVE | - |
| 块注释 `/* comment */` | MUST HAVE | - |
| 多行块注释 | MUST HAVE | - |
| 嵌套块注释 | SHOULD HAVE | 待审计 |
| 文档注释 `///` | SHOULD HAVE | 待审计 |

### Token 类型

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| identifier | MUST HAVE | - |
| keyword | MUST HAVE | - |
| operator | MUST HAVE | - |
| delimiter | MUST HAVE | - |
| literal | MUST HAVE | - |

### 空白与 Unicode

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| space / tab / newline | MUST HAVE | - |
| CRLF / LF 支持 | MUST HAVE | - |
| UTF-8 源码 | MUST HAVE | - |
| Unicode 字符串 | MUST HAVE | - |
| Unicode escape `\uXXXX` | SHOULD HAVE | 待审计 |

### 转义序列

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| `\n` 换行 | MUST HAVE | - |
| `\r` 回车 | MUST HAVE | - |
| `\t` 制表符 | MUST HAVE | - |
| `\\` 反斜杠 | MUST HAVE | - |
| `\"` 双引号 | MUST HAVE | - |
| `\xNN` 十六进制 | SHOULD HAVE | 待审计 |
| `\uXXXX` Unicode | SHOULD HAVE | 待审计 |

---

## 02 Literals & Constants（字面量系统）

### 数值字面量

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 整数 | `0`, `123`, `-123` | MUST HAVE | - |
| 浮点数 | `1.23`, `0.5` | MUST HAVE | - |
| 科学计数法 | `1e10`, `1.5e-3` | SHOULD HAVE | 待审计 |
| 十六进制 | `0xFF`, `0xff` | SHOULD HAVE | 待审计 |
| 二进制 | `0b1010` | SHOULD HAVE | 待审计 |
| 八进制 | `0o755` | SHOULD HAVE | 待审计 |
| 数字分隔符 | `1_000_000` | DESIGNED BUT DEFERRED | - |

### 数值属性

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 整数宽度（32/64位） | MUST HAVE | 待定义 |
| 有符号/无符号 | SHOULD HAVE | 待审计 |
| 浮点精度（32/64位） | MUST HAVE | 待定义 |
| 溢出语义 | MUST HAVE | 待定义 |
| 下溢语义 | SHOULD HAVE | 待审计 |
| NaN / Infinity | SHOULD HAVE | 待审计 |
| 除零行为 | MUST HAVE | 待定义 |

### 布尔与 Null

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 布尔 | `true`, `false` | MUST HAVE | - |
| Null | `null` | MUST HAVE | - |

### 字符串字面量

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 普通字符串 | `"hello"` | MUST HAVE | - |
| 空字符串 | `""` | MUST HAVE | - |
| 原始字符串 | `` `hello` `` | SHOULD HAVE | 待审计 |
| 多行字符串 | SHOULD HAVE | 待审计 |
| 字符串插值 | `"\(name)"` / `` `${name}` `` | SHOULD HAVE | 待审计 |
| Unicode 字符串 | MUST HAVE | - |

### 集合字面量

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| Array | `[1, 2, 3]` | MUST HAVE | - |
| Map | `{"a": 1, "b": 2}` | MUST HAVE | - |
| 空 Array | `[]` | MUST HAVE | - |
| 空 Map | `{}` | MUST HAVE | - |
| 嵌套集合 | `[[1,2], [3,4]]` | MUST HAVE | - |

### Struct/Object 字面量

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| Struct 实例化 | `Person{ name: "Eric", age: 43 }` | MUST HAVE | - |
| 字段初始化规则 | MUST HAVE | 待定义 |
| 嵌套 Struct | MUST HAVE | - |

---

## 03 Expression System（表达式系统）

### 表达式类型

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 字面量表达式 | `42`, `"hello"` | MUST HAVE | - |
| 变量表达式 | `x` | MUST HAVE | - |
| 二元表达式 | `a + b` | MUST HAVE | - |
| 一元表达式 | `-a`, `!a` | MUST HAVE | - |
| 赋值表达式 | `a = b` | MUST HAVE | - |
| 条件表达式 | `cond ? a : b` | MUST HAVE | ✅ 已实现 |
| 函数调用 | `foo(a, b)` | MUST HAVE | - |
| 索引表达式 | `arr[0]` | MUST HAVE | - |
| 成员表达式 | `obj.field` | MUST HAVE | - |
| 范围表达式 | `a..b` | SHOULD HAVE | 待审计 |
| Lambda 表达式 | `fn(x) { x + 1 }` | MUST HAVE | - |
| Struct/Object 表达式 | `Person{...}` | MUST HAVE | - |
| Array 表达式 | `[1, 2, 3]` | MUST HAVE | - |
| Map 表达式 | `{"a": 1}` | MUST HAVE | - |
| 括号表达式 | `(a + b) * c` | MUST HAVE | - |

### 表达式组合

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 算术组合 | `foo(a + b * c)` | MUST HAVE | - |
| 链式成员访问 | `user.profile.items[0].price` | MUST HAVE | - |
| 三元组合 | `a > b ? foo(a) : bar(b)` | MUST HAVE | ✅ 已实现 |
| 括号组合 | `(x + y) * (a - b) / z` | MUST HAVE | - |
| 嵌套函数调用 | `foo(bar(baz()))` | MUST HAVE | - |

---

## 04 Operators（运算符全量审计）

### 算术运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `+` | 加法 | MUST HAVE | ✅ |
| `-` | 减法 | MUST HAVE | ✅ |
| `*` | 乘法 | MUST HAVE | ✅ |
| `/` | 除法 | MUST HAVE | ✅ |
| `%` | 模运算 | MUST HAVE | ✅ |
| `**` | 幂运算 | SHOULD HAVE | ✅ |

### 一元运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `+` | 正号 | SHOULD HAVE | 待审计 |
| `-` | 负号 | MUST HAVE | ✅ |
| `!` / `not` | 逻辑非 | MUST HAVE | ✅ |
| `~` | 位非 | SHOULD HAVE | ✅ |

### 比较运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `==` | 等于 | MUST HAVE | ✅ |
| `!=` | 不等于 | MUST HAVE | ✅ |
| `<` | 小于 | MUST HAVE | ✅ |
| `>` | 大于 | MUST HAVE | ✅ |
| `<=` | 小于等于 | MUST HAVE | ✅ |
| `>=` | 大于等于 | MUST HAVE | ✅ |

### 逻辑运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `and` / `&&` | 逻辑与 | MUST HAVE | ✅ (and) |
| `or` / `\|\|` | 逻辑或 | MUST HAVE | ✅ (or) |
| `not` / `!` | 逻辑非 | MUST HAVE | ✅ |
| 短路语义 | MUST HAVE | 待验证 |

### 位运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `&` | 位与 | MUST HAVE | ✅ |
| `\|` | 位或 | MUST HAVE | ✅ |
| `^` | 位异或 | MUST HAVE | ✅ |
| `~` | 位非 | SHOULD HAVE | ✅ |
| `<<` | 左移 | MUST HAVE | ✅ |
| `>>` | 右移 | MUST HAVE | ✅ |
| 有符号/无符号右移 | SHOULD HAVE | 待定义 |

### 赋值运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `=` | 简单赋值 | MUST HAVE | ✅ |
| `+=` | 加等 | MUST HAVE | ✅ |
| `-=` | 减等 | MUST HAVE | ✅ |
| `*=` | 乘等 | MUST HAVE | ✅ |
| `/=` | 除等 | MUST HAVE | ✅ |
| `%=` | 模等 | MUST HAVE | ✅ |
| `&=` | 位与等 | SHOULD HAVE | ❌ MISSING |
| `\|=` | 位或等 | SHOULD HAVE | ❌ MISSING |
| `^=` | 位异或等 | SHOULD HAVE | ❌ MISSING |
| `<<=` | 左移等 | SHOULD HAVE | ❌ MISSING |
| `>>=` | 右移等 | SHOULD HAVE | ❌ MISSING |

### 条件运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `? :` | 三元表达式 | MUST HAVE | ✅ 已实现 |

### 范围运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `..` | 排他范围 | SHOULD HAVE | ✅ |
| `..=` | 包容范围 | SHOULD HAVE | 待审计 |

### 自增/自减

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `++` (后置) | 后置自增 | SHOULD HAVE | ❌ MISSING / 待设计决策 |
| `++` (前置) | 前置自增 | SHOULD HAVE | ❌ MISSING / 待设计决策 |
| `--` (后置) | 后置自减 | SHOULD HAVE | ❌ MISSING / 待设计决策 |
| `--` (前置) | 前置自减 | SHOULD HAVE | ❌ MISSING / 待设计决策 |

### Null 相关运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `??` | Nullish coalescing | DESIGNED BUT DEFERRED | - |
| `?.` | Optional chaining | DESIGNED BUT DEFERRED | - |

### 成员/身份运算符

| 运算符 | 名称 | EXPECTED | 决策 |
|--------|------|----------|------|
| `in` | 成员关系 | SHOULD HAVE | 待审计 |
| `is` | 类型判断 | SHOULD HAVE | 待审计 |

---

## 05 Operator Precedence（运算符优先级规范）

### 优先级表（高→低）

| 优先级 | 运算符 | 结合性 | 状态 |
|--------|--------|--------|------|
| 1 | postfix: `()` `.` `[]` | 左 | ✅ |
| 2 | unary: `+` `-` `!` `~` | 右 | ✅ |
| 3 | power: `**` | 右 | ✅ |
| 4 | multiplication: `*` `/` `%` | 左 | ✅ |
| 5 | addition: `+` `-` | 左 | ✅ |
| 6 | shift: `<<` `>>` | 左 | ✅ |
| 7 | range: `..` `..=` | 左 | ✅ |
| 8 | comparison: `<` `>` `<=` `>=` | 左 | ✅ |
| 9 | equality: `==` `!=` | 左 | ✅ |
| 10 | bitwise AND: `&` | 左 | ✅ |
| 11 | bitwise XOR: `^` | 左 | ✅ |
| 12 | bitwise OR: `\|` | 左 | ✅ |
| 13 | logical AND: `and` | 左 | ✅ |
| 14 | logical OR: `or` | 左 | ✅ |
| 15 | **ternary: `? :`** | 右 | ✅ 已实现 |
| 16 | assignment: `=` `+=` `-=` `*=` `/=` `%=` | 右 | ✅ |
| 17 | pipe: `\|>` | 左 | ✅ |

### 规范要求

| 项目 | EXPECTED | 决策 |
|------|----------|------|
| 优先级正式文档化 | MUST HAVE | 本文档 |
| 结合性定义 | MUST HAVE | 待完善 |
| 短路求值定义 | MUST HAVE | 待验证 |
| 求值顺序定义 | SHOULD HAVE | 待定义 |
| 副作用规则 | SHOULD HAVE | 待定义 |

---

## 06 Type System（类型系统）

### 基础类型

| 类型 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| int | `let x: int = 42` | MUST HAVE | ✅ |
| uint | `let x: uint = 42` | SHOULD HAVE | 待审计 |
| float | `let x: float = 3.14` | MUST HAVE | ✅ |
| bool | `let x: bool = true` | MUST HAVE | ✅ |
| string | `let x: string = "hi"` | MUST HAVE | ✅ |
| null | `null` | MUST HAVE | ✅ |
| array | `let x: []int` | SHOULD HAVE | 待审计 |
| map | `let x: {}string` | SHOULD HAVE | 待审计 |
| struct | 自定义类型 | MUST HAVE | ✅ |
| function | 函数类型 | SHOULD HAVE | 待审计 |

### 类型系统特性

| 特性 | EXPECTED | 决策 |
|------|----------|------|
| 类型推断 `let x = 42` | MUST HAVE | ✅ |
| 显式类型标注 `x: int = 10` | MUST HAVE | ✅ |
| 类型转换 `int(...)`, `float(...)`, `string(...)`, `bool(...)` | MUST HAVE | 待审计 |
| 类型兼容性 `int + float`, `string + int` | MUST HAVE | 待定义 |
| 类型检查器 | MUST HAVE | ⚠️ 603 warnings |
| 类型错误报告 | MUST HAVE | 待完善 |

---

## 07 Composite Types（复合类型）

### Array/List

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 创建 | MUST HAVE | ✅ |
| 索引读取 | MUST HAVE | ✅ |
| 索引修改 | MUST HAVE | ✅ |
| 长度 | MUST HAVE | ✅ |
| 遍历 | MUST HAVE | ✅ |
| 嵌套 | MUST HAVE | ✅ |
| 作为参数 | MUST HAVE | ✅ |
| 作为返回值 | MUST HAVE | ✅ |

### Map

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 创建 | MUST HAVE | ✅ |
| 读取 | MUST HAVE | ✅ |
| 设置 | MUST HAVE | ✅ |
| 删除 | SHOULD HAVE | 待审计 |
| 包含检查 | SHOULD HAVE | 待审计 |
| 遍历 | MUST HAVE | ✅ |
| 嵌套 | MUST HAVE | ✅ |

### Struct

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 定义 | MUST HAVE | ✅ |
| 构造 | MUST HAVE | ✅ |
| 字段读取 | MUST HAVE | ✅ |
| 字段修改 | MUST HAVE | ✅ |
| 嵌套 Struct | MUST HAVE | ✅ |
| 方法 | SHOULD HAVE | 待审计 |

### Tuple

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| Tuple 类型 `(int, string)` | SHOULD HAVE | 待审计 |
| 多返回值是否 Tuple 语义 | MUST HAVE | 待定义 |

---

## 08 Variables & Binding（变量与绑定）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 变量声明 `let` | MUST HAVE | ✅ |
| 常量声明 `const` | MUST HAVE | ✅ |
| 赋值 | MUST HAVE | ✅ |
| 作用域 | MUST HAVE | 待定义 |
| 变量遮蔽 (shadowing) | SHOULD HAVE | 待审计 |
| 局部变量 | MUST HAVE | ✅ |
| 全局变量 | SHOULD HAVE | 待审计 |
| 参数绑定 | MUST HAVE | ✅ |
| 返回值绑定 | MUST HAVE | ✅ |
| 块作用域 | SHOULD HAVE | 待审计 |
| 函数作用域 | MUST HAVE | ✅ |
| 模块作用域 | MUST HAVE | ✅ |

---

## 09 Functions & Closures（函数与闭包）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 命名函数 | MUST HAVE | ✅ |
| 匿名函数 | MUST HAVE | ✅ |
| Lambda 箭头 | SHOULD HAVE | ✅ |
| 闭包 | MUST HAVE | ⚠️ 待验证 |
| 嵌套函数 | MUST HAVE | ✅ |
| 递归函数 | MUST HAVE | ✅ |
| 高阶函数 | MUST HAVE | ✅ |
| 函数作为值 | MUST HAVE | ✅ |
| 函数作为参数 | MUST HAVE | ✅ |
| 函数作为返回值 | MUST HAVE | ✅ |
| 可变参数 (variadic) | SHOULD HAVE | 待审计 |
| 默认参数 | SHOULD HAVE | 待审计 |
| 命名参数 | DESIGNED BUT DEFERRED | - |

### 闭包捕获语义

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 按值捕获 | MUST HAVE | 待定义 |
| 按引用捕获 | SHOULD HAVE | 待定义 |
| 可变捕获 | SHOULD HAVE | 待定义 |
| 生命周期 | MUST HAVE | 待定义 |
| 逃逸闭包 | SHOULD HAVE | 待审计 |

---

## 10 Control Flow（控制流）

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| if | `if cond {}` | MUST HAVE | ✅ |
| if-else | `if cond {} else {}` | MUST HAVE | ✅ |
| else-if | `else if cond {}` | MUST HAVE | ✅ |
| while | `while cond {}` | MUST HAVE | ✅ |
| do-while | `do {} while cond` | SHOULD HAVE | 待审计 |
| for | `for i in range {}` | MUST HAVE | ✅ |
| foreach | `for item in arr {}` | SHOULD HAVE | 待审计 |
| break | `break` | MUST HAVE | ✅ |
| continue | `continue` | MUST HAVE | ✅ |
| return | `return value` | MUST HAVE | ✅ |
| switch/case | SHOULD HAVE | 待设计决策 |
| match 模式匹配 | SHOULD HAVE | 待设计决策 |

---

## 11 Pattern Matching（模式匹配）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| match 表达式 | SHOULD HAVE | 待设计决策 |
| 字面量模式 | SHOULD HAVE | - |
| 变量模式 | SHOULD HAVE | - |
| 通配符 `_` | SHOULD HAVE | - |
| Struct 模式 | SHOULD HAVE | - |
| Tuple 模式 | SHOULD HAVE | - |
| Enum 模式 | SHOULD HAVE | - |
| 守卫 (guard) | SHOULD HAVE | - |

**架构决策待定**：Pattern Matching 是否属于 TLL v1 基础能力。

---

## 12 Destructuring（解构）

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| Tuple 解构 | `(a, b) = pair` | SHOULD HAVE | 待设计决策 |
| Struct 解构 | `{name, age} = user` | SHOULD HAVE | 待设计决策 |
| Array 解构 | `[a, b, ...rest] = arr` | DESIGNED BUT DEFERRED | - |
| 嵌套解构 | SHOULD HAVE | - |

**架构决策待定**：Destructuring 是否属于 TLL v1 基础能力。

---

## 13 Error & Resource Semantics（错误与资源语义）

### 错误模型

| 模型 | EXPECTED | 决策 |
|------|----------|------|
| error value | SHOULD HAVE | 待审计 |
| Result 类型 `Result<T, E>` | DESIGNED BUT DEFERRED | - |
| Option 类型 `Option<T>` | DESIGNED BUT DEFERRED | - |
| exception | MUST HAVE | ✅ (throw) |
| throw | MUST HAVE | ✅ |
| try/catch | MUST HAVE | ✅ |
| finally | SHOULD HAVE | ❌ MISSING |
| panic/recover | DESIGNED BUT DEFERRED | - |

**必须回答**：TLL 遇到错误到底怎么表达、传播、处理？

---

## 14 Resource / Cleanup（资源释放）

| 机制 | EXPECTED | 决策 |
|------|----------|------|
| defer | SHOULD HAVE | 待设计决策 |
| finally | SHOULD HAVE | ❌ MISSING |
| using/with | SHOULD HAVE | 待设计决策 |
| RAII-like | DESIGNED BUT DEFERRED | - |

**重要性**：对于 TLL OS（文件、socket、数据库、lock、transaction），必须至少有一种正式资源释放机制。

---

## 15 Module / Package（模块与包）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| import | MUST HAVE | ✅ |
| export | MUST HAVE | ✅ |
| from import | MUST HAVE | ✅ |
| package | SHOULD HAVE | 待审计 |
| module | SHOULD HAVE | 待审计 |
| namespace | DESIGNED BUT DEFERRED | - |
| 可见性 (private/public) | SHOULD HAVE | 待审计 |
| 符号解析 | MUST HAVE | ✅ |
| alias | SHOULD HAVE | 待审计 |
| 循环依赖 | SHOULD HAVE | 待审计 |
| 重复符号 | MUST HAVE | 待定义 |
| 包版本 | DESIGNED BUT DEFERRED | - |
| 依赖解析 | DESIGNED BUT DEFERRED | - |

---

## 16 Generic / Parametric Types（泛型）

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 泛型函数 | `fn foo<T>(x: T)` | SHOULD HAVE | 待设计决策 |
| 泛型 Struct | `struct List<T> { ... }` | SHOULD HAVE | 待设计决策 |
| 类型参数约束 | `T: Comparable` | DESIGNED BUT DEFERRED | - |
| 泛型实例化 | `List<int>` | SHOULD HAVE | - |

**架构决策待定**：泛型是否属于 TLL v1 基础能力，还是 v2 高级能力。

---

## 17 Enum / Algebraic Data Types（枚举与代数数据类型）

| 能力 | 语法示例 | EXPECTED | 决策 |
|------|----------|----------|------|
| 简单枚举 | `enum Status { Pending, Paid, Shipped }` | MUST HAVE | ✅ |
| 带值枚举 | `enum Result<T> { Ok(T), Err(string) }` | SHOULD HAVE | 待设计决策 |
| 枚举方法 | SHOULD HAVE | 待审计 |

**重要性**：对于订单状态机、Agent 状态、错误模型非常重要。

---

## 18 Interface / Trait / Protocol（接口与特质）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| interface | SHOULD HAVE | 待设计决策 |
| trait | SHOULD HAVE | - |
| protocol | SHOULD HAVE | - |
| 抽象类型 | SHOULD HAVE | - |
| 方法契约 | SHOULD HAVE | - |
| 实现 | SHOULD HAVE | - |
| 多态 | SHOULD HAVE | - |

**重要性**：直接影响未来 PaymentProvider、StorageProvider、LLMProvider、AgentProvider 架构。

---

## 19 Methods / Object Model（方法与对象模型）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 方法 | SHOULD HAVE | 待审计 |
| 静态方法 | SHOULD HAVE | 待审计 |
| 构造函数 | SHOULD HAVE | 待审计 |
| this/self | SHOULD HAVE | 待审计 |
| 字段可见性 | SHOULD HAVE | 待审计 |
| 方法分派 | SHOULD HAVE | 待审计 |
| 继承 | DESIGNED BUT DEFERRED | - |
| 组合 | MUST HAVE | ✅ |
| 嵌入 (embedding) | SHOULD HAVE | 待设计决策 |

**必须回答**：TLL 选择什么对象模型？不一定要支持传统 OOP，但必须有明确语言设计。

---

## 20 Memory / Value / Reference Semantics（内存/值/引用语义）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 赋值是 copy 还是 reference | MUST HAVE | 待定义 |
| 值类型 | MUST HAVE | 待定义 |
| 引用类型 | MUST HAVE | 待定义 |
| 可变/不可变 | MUST HAVE | 待定义 |
| 别名 (aliasing) | SHOULD HAVE | 待定义 |
| 所有权 (ownership) | DESIGNED BUT DEFERRED | - |
| 生命周期 | DESIGNED BUT DEFERRED | - |
| 逃逸分析 | SHOULD HAVE | 待审计 |

**关键问题**：`a = b; a.x = 10;` 时，`b.x` 会不会变化？

---

## 21 Evaluation Semantics（求值语义）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 求值顺序 | MUST HAVE | 待定义 |
| 副作用 | MUST HAVE | 待定义 |
| 短路求值 | MUST HAVE | 待验证 |
| 赋值求值 | SHOULD HAVE | 待定义 |
| 函数参数求值顺序 | SHOULD HAVE | 待定义 |

**关键问题**：`foo(a(), b())` 中，`a()` 和 `b()` 哪个先执行？

---

## 22 Concurrency Language Semantics（并发语言语义）

| 能力 | 层级 | EXPECTED | 决策 |
|------|------|----------|------|
| async/await | Language | DESIGNED BUT DEFERRED | - |
| spawn | Runtime API | MUST HAVE | ✅ |
| yield | Language | DESIGNED BUT DEFERRED | - |
| channel | Runtime API | SHOULD HAVE | 待审计 |
| select | Language | DESIGNED BUT DEFERRED | - |
| actor | Runtime | SHOULD HAVE | 待审计 |
| atomic | Runtime API | SHOULD HAVE | 待审计 |
| data race | Runtime | MUST HAVE | 待定义 |
| memory visibility | Runtime | MUST HAVE | 待定义 |
| happens-before | Runtime | SHOULD HAVE | 待定义 |

**特别区分**：语言语法 vs Runtime API，不能混在一起。

---

## 23 Compile-time Capabilities（编译期能力）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 常量表达式 | SHOULD HAVE | 待审计 |
| 编译期求值 | DESIGNED BUT DEFERRED | - |
| 宏 (macro) | DESIGNED BUT DEFERRED | - |
| 元编程 | DESIGNED BUT DEFERRED | - |
| 注解/属性 (attributes) | SHOULD HAVE | 待设计决策 |
| 条件编译 | SHOULD HAVE | 待审计 |

---

## 24 FFI / Native Interop（FFI 与原生互操作）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| C 函数调用 | MUST HAVE | ✅ |
| native 函数 | MUST HAVE | ✅ |
| 函数指针 | SHOULD HAVE | 待审计 |
| Struct ABI | SHOULD HAVE | 待审计 |
| 基础类型 ABI | MUST HAVE | ✅ |
| 字符串 ABI | SHOULD HAVE | 待审计 |
| 数组 ABI | SHOULD HAVE | 待审计 |
| callback | SHOULD HAVE | 待审计 |
| 内存所有权 | MUST HAVE | 待定义 |

**重要性**：TLL 现在本身就依赖 C/C++ Runtime，关系到未来 TLL 自举。

---

## 25 Compiler Language Infrastructure（编译器语言基础设施）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| Lexer | MUST HAVE | ✅ |
| Parser | MUST HAVE | ✅ |
| AST | MUST HAVE | ✅ |
| AST transforms | SHOULD HAVE | 待审计 |
| Type checker | MUST HAVE | ⚠️ 603 warnings |
| Symbol resolver | MUST HAVE | ✅ |
| Constant folding | SHOULD HAVE | 待审计 |
| Optimization | SHOULD HAVE | 待审计 |
| Code generation | MUST HAVE | ✅ |
| Linking | MUST HAVE | ✅ |
| Runtime binding | MUST HAVE | ✅ |
| Error reporting | MUST HAVE | 待完善 |
| Debug information | SHOULD HAVE | 待审计 |
| Source location | MUST HAVE | ✅ |
| Deterministic compilation | MUST HAVE | ✅ (P4 验证) |
| Incremental compilation | DESIGNED BUT DEFERRED | - |
| Self-hosting | MUST HAVE | ✅ |
| Bootstrap compiler | MUST HAVE | ✅ |

---

## 26 Compiler Error System（编译器错误系统）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| Source location (line/column) | MUST HAVE | ✅ |
| Expected tokens | SHOULD HAVE | 待完善 |
| Actual token | SHOULD HAVE | 待完善 |
| Semantic context | SHOULD HAVE | 待完善 |
| Type mismatch 报告 | MUST HAVE | 待完善 |
| Symbol not found | MUST HAVE | ✅ |
| 修复建议 (suggestion) | SHOULD HAVE | 待审计 |
| 错误恢复 | SHOULD HAVE | 待审计 |
| 多错误报告 | SHOULD HAVE | 待审计 |

**重要性**：未来 Agent 编程尤其依赖高质量 Compiler Diagnostics。

---

## 27 Source Compatibility（源码兼容性）

| 能力 | EXPECTED | 决策 |
|------|----------|------|
| 保留关键字 | MUST HAVE | 待定义 |
| 标识符冲突 | MUST HAVE | 待定义 |
| 版本兼容性 | SHOULD HAVE | 待定义 |
| 语法演进 | SHOULD HAVE | 待定义 |
| 废弃 (deprecation) | SHOULD HAVE | 待审计 |

---

## 28 Stdlib Boundary（标准库边界）

### Language vs Stdlib 区分

| 类别 | 示例 | 层级 |
|------|------|------|
| Language | `a + b`, `a[i]`, `foo()`, `if`, `while`, `lambda` | 语言核心 |
| Stdlib | `strings.length()`, `array.sort()`, `map.keys()`, `math.sqrt()` | 标准库 |

### 标准库基础模块

| 模块 | EXPECTED | 决策 |
|------|----------|------|
| strings | MUST HAVE | ✅ |
| arrays | MUST HAVE | ✅ |
| maps | MUST HAVE | ✅ |
| math | SHOULD HAVE | 待审计 |
| io | MUST HAVE | ✅ |
| os | SHOULD HAVE | 待审计 |
| time | SHOULD HAVE | 待审计 |
| json | SHOULD HAVE | ✅ |
| http | MUST HAVE | ⚠️ P1-04 macOS 已知问题 |
| crypto | MUST HAVE | ✅ (P1-01~03 SEALED) |
| sqlite | SHOULD HAVE | ✅ |
| random | MUST HAVE | ✅ (P1-01 SEALED) |

---

## GAP 汇总（初步）

### MUST HAVE + MISSING/PARTIAL

| 优先级 | 域 | 能力 | 当前状态 |
|--------|----|------|----------|
| P0 | 04 Operators | 三元表达式 `? :` | ✅ 已实现，待验收 |
| P1 | 04 Operators | 位运算复合赋值 `&= \|= ^= <<= >>=` | ❌ MISSING |
| P1 | 13 Error | finally | ❌ MISSING |
| P1 | 14 Resource | 资源释放机制 | ❌ 待设计 |
| P2 | 06 Types | TypeChecker 603 warnings | ⚠️ PARTIAL |
| P2 | 25 Compiler | TypeChecker 完善 | ⚠️ PARTIAL |
| P2 | 26 Compiler | 错误报告系统 | ⚠️ PARTIAL |

### SHOULD HAVE + 待设计决策

| 域 | 能力 | 决策状态 |
|----|------|----------|
| 04 Operators | 自增/自减 `++`/`--` | 待架构决策 |
| 11 Pattern Matching | match 表达式 | 待架构决策 |
| 12 Destructuring | 解构 | 待架构决策 |
| 16 Generic | 泛型 | 待架构决策 |
| 18 Interface | 接口/特质 | 待架构决策 |
| 22 Concurrency | async/await | 待架构决策 |

---

## 下一步

1. **Phase 3**: 对 TLL 当前仓库进行逐项 Reality Audit
2. **Phase 4**: 生成完整 GAP Matrix（EXPECTED vs ACTUAL）
3. **Phase 5**: 把所有 MUST HAVE + MISSING/PARTIAL 一次性形成施工队列
4. **Phase 6**: 逐项补齐
5. **Phase 7**: 统一测试（Positive/Negative/Boundary/Composition/Regression）
6. **Phase 8**: 三平台 CI
7. **Phase 9**: 更新文档
8. **Phase 10**: 架构师审计后合并

---

**文档结束（v1.0-draft，持续完善中）**
