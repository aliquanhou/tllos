# TLL Construction Report — Block 2

**施工块**: D02 Syntax + D03 Semantics 第一轮盘点与验证
**执行者**: 豆包 A (Principal Implementation Engineer)
**日期**: 2026-09-08
**Git 状态**: 本地开发，未 Push（遵守 Git 纪律）

---

## 1. Scope 本次完成什么

1. **D02 Syntax 第一轮盘点**：建立完整语法能力清单，验证 50+ 语法能力（编译+运行+assertion），发现 4 项 Spec/Implementation GAP，识别 9 项 MISSING 语法
2. **D03 Semantics 第一轮盘点**：建立语义能力清单，验证 12 项语义能力，发现函数级作用域等 PARTIAL 能力，识别 6 项 MISSING 语义
3. **30 Domain Inventory 更新**：D01-D03 详细状态填入 inventory 文档
4. **测试套件建立**：新增 D02/D03 综合验证测试，全部通过

---

## 2. Capability 新增哪些 L2/L3/Atomic

### D02 Syntax VERIFIED（50+ 项，编译+运行验证通过）

**Declarations (8)**: let, const, fn（含类型标注）, struct, enum, interface, import/export
**Statements (12)**: if/else if/else, while, for...in, break, continue, return, try/catch/finally, throw, match, block, expression statement
**Expressions (18)**: 算术(+ - * / % **), 比较(== != < > <= >=), 逻辑(&& || !), 位运算(& | ^ << >>), 三元(?:), 赋值(=), 空合并(??), 管道(|>), 范围(..), 函数调用, 成员访问, 索引, Lambda
**Literals (12)**: 数组, 映射, 双/单引号字符串, raw string, 多行字符串, 十进制/十六进制/二进制/八进制整数, 浮点数, 科学计数法, 数字分隔符, true/false/null

### D03 Semantics VERIFIED（12 项）

词法作用域（函数级）, 闭包捕获, 可变闭包状态, 递归, 一等函数, 高阶函数, 嵌套函数, 短路求值, 求值顺序（左到右）, return 语义, 异常传播, finally 执行

---

## 3. Implementation 修改哪些核心模块

本施工块**未修改生产代码**，仅进行盘点和验证。

**新增测试文件**:
- `tests/d02-syntax/d02_syntax_verify.tll` — D02 语法综合验证（50+ 断言）
- `tests/d03-semantics/d03_semantics_verify.tll` — D03 语义综合验证（12 项语义断言）

**更新文档**:
- `docs/TPC-30-DOMAIN-INVENTORY.md` — D01-D03 详细状态填入

---

## 4. Tests 运行了什么测试

| 测试 | 断言数 | 编译 | 运行 | 结果 |
|------|--------|------|------|------|
| d02_syntax_verify.tll | 50+ | ✅ | ✅ | `D02-SYNTAX-ALL-PASS` |
| d03_semantics_verify.tll | 12 | ✅ | ✅ | `D03-SEMANTICS-ALL-PASS` |

**验证流程**: 修改后 lexer 自举编译 → 新编译器编译测试 → 运行测试 → assertion 全部通过

---

## 5. Results PASS / FAIL

| 项目 | 结果 |
|------|------|
| D02 语法综合验证 | ✅ PASS（50+ 断言全部通过） |
| D03 语义综合验证 | ✅ PASS（12 项语义全部通过） |
| 编译器自举（D01 修改后） | ✅ PASS |
| 现有代码兼容性 | ✅ 无破坏 |

---

## 6. Evidence 证据在哪里

| 证据类型 | 位置 |
|----------|------|
| D02 语法测试 | `tests/d02-syntax/d02_syntax_verify.tll` |
| D03 语义测试 | `tests/d03-semantics/d03_semantics_verify.tll` |
| 测试输出 | `D02-SYNTAX-ALL-PASS` / `D03-SEMANTICS-ALL-PASS` |
| 30 Domain Inventory | `docs/TPC-30-DOMAIN-INVENTORY.md` |
| parser 源码 | `compiler/parser.tll`（1078 行，60+ 解析函数） |

---

## 7. Bugs 发现什么问题

### Bug 1: Spec/Implementation 语法不一致（4 项）

**现象**: spec/SYNTAX.md 声明的语法与实际 parser 实现不一致

| 语法 | Spec 声明 | 实际实现 |
|------|-----------|----------|
| for 循环 | C 风格 `for (init;cond;update)` | `for x in iterable` |
| match 语句 | `case x:` / `default:` | `x => body` / `_ => body` |
| catch 语法 | `catch (e)` | `catch e`（不带括号） |
| interface 方法 | 可能不需要 fn | 必须 `fn method()` |

**根因**: spec 文档与实现不同步，spec 可能参考了其他语言的语法

**处理**: 记入 GAP Ledger，非阻塞。后续需决定是更新 spec 还是补全实现。

### Bug 2: 函数级作用域而非块级作用域

**现象**: if/for 块内的 `let x = 2` 会覆盖外部的 `let x = 1`

**根因**: TLL 变量作用域是函数级（function-level），不是块级（block-level）

**影响**: 这是语言设计选择，不是 bug。但与大多数现代语言（JS let, Rust, C++）不同，需在文档中明确说明。

**处理**: 标记为 PARTIAL，记入 GAP Ledger。后续可考虑引入块级作用域或明确文档化当前行为。

### Bug 3: 函数必须先声明后使用（无 hoisting）

**现象**: 在 main 函数内部声明的函数，类型检查器报告 "undefined identifier"，但运行时正常

**根因**: 类型检查器不支持函数前向引用，运行时可能通过延迟解析支持

**处理**: 标记为 PARTIAL。测试中已将函数移到 main 外部以避免此问题。

---

## 8. GAP 哪些能力仍然 PARTIAL/MISSING

### D02 Syntax MISSING（9 项）

| 能力 | 说明 | 优先级 |
|------|------|--------|
| C 风格 for 循环 | spec 声明但未实现 | P2 |
| tuple 元组语法 | (a, b) 元组 | P1 |
| 解构赋值 destructuring | let [a,b] = arr / let {x} = obj | P1 |
| 泛型语法 generic | fn<T> / struct<T> | P1 |
| ADT 代数数据类型 | enum 带数据变体 | P2 |
| defer 语句 | defer cleanup() | P2 |
| 注解/装饰器 | @decorator | P3 |
| 默认参数值 | fn(a=1) | P2 |
| 可变参数 | fn(...args) | P2 |

### D03 Semantics PARTIAL（3 项）

| 能力 | 状态 | 说明 |
|------|------|------|
| 块级作用域 | PARTIAL | 当前为函数级作用域 |
| 函数前向引用 | PARTIAL | 类型检查器不支持，运行时部分支持 |
| 类型推断 | PARTIAL | 动态类型，类型检查器警告较多 |

### D03 Semantics MISSING（6 项）

| 能力 | 说明 | 优先级 |
|------|------|--------|
| 块级作用域隔离 | if/for 块内变量不隔离 | P1 |
| 函数 hoisting | 函数必须先声明后使用 | P2 |
| 解构语义 | 无解构赋值语义 | P1 |
| 生成器/迭代器协议 | for...in 可能仅支持数组 | P2 |
| 协程语义 | yield/async | P2 |
| 运算符重载 | 自定义运算符 | P3 |

---

## 9. Dogfooding 真实项目是否使用

本施工块未新增 Dogfooding 项目。但 D02/D03 验证测试本身就是 TLL 程序，使用了 TLL 的语法和语义能力进行自验证。

编译器自举（修改后 lexer 能编译 compiler.tll 自身）继续验证了基础语言能力的稳定性。

---

## 10. Runtime Impact 是否影响 VM/Compiler/Stdlib

| 模块 | 影响 | 说明 |
|------|------|------|
| Lexer | ⚪ 无新增修改 | D01 修改继续生效 |
| Parser | ⚪ 无修改 | 仅盘点验证 |
| VM/Runtime | ⚪ 无影响 | 未修改运行时 |
| Stdlib | ⚪ 无影响 | 未修改标准库 |
| 现有代码兼容性 | ✅ 无破坏 | 盘点验证未修改生产代码 |

---

## 11. Next 下一步最值得施工的能力

### 建议下一施工块：D04 Type System + D05 Values & Data 盘点

**理由**:
1. D01-D03 基础语言核心已完成第一轮盘点，能力地图初步建立
2. D04 Type System（类型系统）和 D05 Values & Data（值与数据）是 P0 基础语言闭环的核心，直接影响后续所有域
3. D02 盘点发现的泛型、ADT、解构等 MISSING 能力都依赖类型系统
4. 按照"纵向铺开"策略，继续快速推进 D04-D08

**具体计划**:
1. 盘点 D04 Type System 现状（基础类型、类型标注、类型推断、泛型、类型别名等）
2. 盘点 D05 Values & Data 现状（基本值、复合值、可变性、相等性、序列化等）
3. 修复发现的阻塞性 GAP
4. 更新 30 Domain Inventory

**备选**: 如果 D04 盘点发现类型系统有大量阻塞性问题，可先集中修复 D04 再推进。

---

**施工块 2 完成。等待架构师裁决后进入下一施工块。**

**Git 纪律**：所有修改在本地，未 Push。
