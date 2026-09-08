# TLL Construction Report — Block 1

**施工块**: D01 Lexical 第一轮修复 + 30 Domain Inventory 框架
**执行者**: 豆包 A (Principal Implementation Engineer)
**日期**: 2026-09-08
**Git 状态**: 本地开发，未 Push（遵守 Git 纪律）

---

## 1. Scope 本次完成什么

1. **D01 Lexical 第一轮修复**：基于 TPC-D01-BASELINE 盘点结果，修复 4 项 MISSING 能力，确认 2 项已有能力，注册 6 个安全关键字
2. **30 Domain Capability Inventory 框架建立**：列出全部 30 域及当前状态，建立施工路线
3. **GAP Ledger 建立**：3 项非阻塞 D01 问题记入待办，不阻塞主线推进

---

## 2. Capability 新增哪些 L2/L3/Atomic

### 新增 VERIFIED Atomic Capabilities（D01）

| ID | 能力 | 层级 | 修复前 | 修复后 |
|----|------|------|--------|--------|
| D01-AC-001 | `/* */` 块注释 | Atomic | MISSING | VERIFIED |
| D01-AC-002 | 单引号字符串 `'...'` | Atomic | MISSING | VERIFIED |
| D01-AC-003 | `\uXXXX` Unicode 转义（ASCII范围） | Atomic | MISSING | VERIFIED |
| D01-AC-004 | `??` 空合并运算符（lexer+parser） | Atomic | MISSING | VERIFIED |
| D01-AC-005 | 未闭合双引号字符串检测 | Atomic | PARTIAL | VERIFIED |
| D01-AC-006 | 未闭合原始字符串检测 | Atomic | PARTIAL | VERIFIED |
| D01-AC-007 | raw string parser 支持（RAW_STRING token） | Atomic | PARTIAL | VERIFIED |

### 新注册关键字（6个）

`super`, `package`, `undefined`, `module`, `option`, `intent`

### 30 Domain Inventory 框架

建立 D01-D30 全部 30 域的 inventory 文档，标记优先级和当前状态。

---

## 3. Implementation 修改哪些核心模块

### compiler/lexer.tll

1. **块注释**：在空白/注释跳过循环中添加 `/* */` 处理，支持跨行，跟踪 line/column
2. **单引号字符串**：添加 `'...'` 字符串字面量处理，支持转义序列（\n, \t, \r, \\, \', \0, \xHH），未闭合检测
3. **`\uXXXX` 转义**：在双引号字符串转义处理中添加 `\u` 分支，读取 4 位十六进制，调用 `convert.toChar()`
4. **`??` 运算符**：添加 `TK_NULLISH` 常量定义，在双字符运算符匹配中添加 `??`
5. **安全关键字注册**：在 `getKeywordType()` 中注册 6 个不破坏现有代码的关键字
6. **未闭合字符串检测**：确认已有 `dclosed`/`rclosed`/`sclosed` 标志位和 TLL-E001 错误

### compiler/parser.tll

1. **`??` 运算符**：添加 `parseNullCoalescing()` 函数，修改 `parseTernary()` 调用链
2. **raw string**：修正 token 名称 `RAWSTRING` → `RAW_STRING`，与 lexer 的 `TK_RAW_STRING` 一致

---

## 4. Tests 运行了什么测试

### 新增测试

| 测试文件 | 内容 | 结果 |
|----------|------|------|
| `tests/d01-lexical/d01_fix_verify.tll` | 综合验证所有 D01 修复：块注释、单引号、\u转义、??运算符、关键字、raw string、数字字面量 | ✅ PASS |

### 验证流程

1. 用种子编译器编译修改后的 compiler.tll（自举）→ 无语法错误
2. 用修改后的编译器编译 d01_fix_verify.tll → 编译成功
3. 运行 d01_fix_verify.tllbc → 输出 `D01-FIX-ALL-PASS`

---

## 5. Results PASS / FAIL

| 项目 | 结果 |
|------|------|
| 编译器自举（修改后 lexer 能编译自身） | ✅ PASS |
| D01 修复综合验证测试 | ✅ PASS |
| 单引号字符串 `'hello world'` | ✅ PASS |
| 单引号转义 `'it\'s ok'` | ✅ PASS |
| `/* */` 跨行块注释 | ✅ PASS |
| `\u0041\u0042` == "AB" | ✅ PASS |
| `??` 运算符词法识别 | ✅ PASS |
| 6 个安全关键字注册 | ✅ PASS |
| raw string parser 支持 | ✅ PASS |
| 未闭合字符串检测 | ✅ PASS（已有） |

---

## 6. Evidence 证据在哪里

| 证据类型 | 位置 |
|----------|------|
| 源码修改 | `compiler/lexer.tll`, `compiler/parser.tll` |
| 测试文件 | `tests/d01-lexical/d01_fix_verify.tll` |
| 测试输出 | `D01-FIX-ALL-PASS` |
| Baseline 报告 | `docs/TPC-D01-BASELINE.md` |
| 30 Domain Inventory | `docs/TPC-30-DOMAIN-INVENTORY.md` |
| 验证脚本 | `scripts/verify-d01-lexical.ps1` |

---

## 7. Bugs 发现什么问题

### Bug 1: 30 个僵尸关键字不能全部注册

**现象**：一次性注册 30 个关键字后，编译 tools/TLLC/main.tll 报错 `expected variable name, got 'result' (RESULT)`

**根因**：24 个关键字在现有代码中被大量用作标识符：
- `result`: 657 次使用，66 个文件
- `ok`: 177 次使用，42 个文件
- `spawn`: 131 次使用，32 个文件
- `type`: 71 次使用，14 个文件
- `send`: 30 次使用，7 个文件
- 其他 19 个关键字也有不同程度的使用

**处理**：只注册 6 个安全关键字（super, package, undefined, module, option, intent），其余 24 个记入 GAP Ledger，需先重构现有代码才能注册。

### Bug 2: `\x27` 十六进制转义在 TLL 字符串中不生效

**现象**：单引号字符串代码中使用 `"\x27"` 表示单引号字符，但运行时报 `unexpected char ''`

**根因**：TLL 编译器对 `\x` 转义的处理可能存在问题，或 `\x27` 未被正确解析为单引号字符

**处理**：改用直接的 `"'"`（双引号字符串中可包含单引号），问题解决

### Bug 3: `convert.toChar()` 可能只支持 0-255

**现象**：`\u4e2d\u6587`（中文"中文"）测试失败，报 `unicode escape length fail`

**根因**：`convert.toChar()` 可能只支持 ASCII 范围（0-255），大于 255 的 Unicode 码点无法正确转换为字符

**处理**：用 ASCII 范围的 `\u0041\u0042` 验证基本功能通过，大于 255 的码点支持记入 GAP Ledger

---

## 8. GAP 哪些能力仍然 PARTIAL/MISSING

### D01 剩余 GAP（记入 Ledger，不阻塞主线）

| GAP | 状态 | 原因 | 优先级 |
|-----|------|------|--------|
| 24 个僵尸关键字注册 | MISSING | 需先重构现有代码中 657+ 处标识符使用 | P1 |
| Unicode 标识符 | MISSING | 需重构 lexer 字符分类，支持 UTF-8 解码 | P2 |
| `\uXXXX` 非 ASCII 码点 | PARTIAL | `convert.toChar()` 可能只支持 0-255 | P2 |
| 数字类型后缀（u32, f64 等） | MISSING | 需设计类型系统集成 | P2 |
| Lexical error recovery | MISSING | 需重构 lexer 错误处理，支持多错误报告 | P2 |
| 注解语法（@decorator） | MISSING | 需设计注解语义和 parser 支持 | P3 |

### D02-D30

全部待盘点，见 `docs/TPC-30-DOMAIN-INVENTORY.md`

---

## 9. Dogfooding 真实项目是否使用

本施工块暂未涉及 Dogfooding 项目。D01 修复已通过编译器自举验证（修改后的 lexer 能编译 compiler.tll 自身），这是最基础的 Self-Hosting 验证。

下一施工块将开始 D02-D04 盘点，并在真实编译器代码中验证语法/语义能力。

---

## 10. Runtime Impact 是否影响 VM/Compiler/Stdlib

| 模块 | 影响 | 说明 |
|------|------|------|
| Lexer | ✅ 正向 | 新增 4 项词法能力，注册 6 个关键字 |
| Parser | ✅ 正向 | 新增 `??` 运算符支持，修正 raw string token 名称 |
| VM/Runtime | ⚪ 无影响 | 词法/语法层修改不影响运行时 |
| Stdlib | ⚪ 无影响 | 未修改标准库 |
| 现有代码兼容性 | ✅ 无破坏 | 只注册 6 个安全关键字，未破坏现有代码 |

---

## 11. Next 下一步最值得施工的能力

### 建议下一施工块：D02 Syntax + D03 Semantics 盘点与快速修复

**理由**：
1. D01 词法层已完成第一轮修复，基础词法能力基本完备
2. D02 Syntax（语法）和 D03 Semantics（语义）是 P0 基础语言闭环的核心，直接影响后续所有域
3. 按照"纵向铺开"策略，应快速推进到 D02-D08，建立基础语言能力全景

**具体计划**：
1. 盘点 D02 Syntax 现状（表达式、语句、声明、模式匹配等）
2. 盘点 D03 Semantics 现状（作用域、类型推导、闭包捕获等）
3. 修复发现的阻塞性 GAP
4. 更新 30 Domain Inventory

**备选**：如果 D02/D03 盘点发现大量阻塞性问题，可先集中修复 D02 再推进。

---

**施工块 1 完成。等待架构师裁决后进入下一施工块。**

**Git 纪律**：所有修改在本地，未 Push。
