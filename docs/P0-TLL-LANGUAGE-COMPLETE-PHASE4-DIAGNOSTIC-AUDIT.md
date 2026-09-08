# P0-TLL-LANGUAGE-COMPLETE Phase 4 — Diagnostic Foundation Audit (Pre-implementation)

**日期**: 2026-09-08
**分支**: p0-language-phase4-diagnostic
**基线**: main @ 5cd785b
**审计阶段**: 施工前 Reality Audit（Audit First，未修改代码）

---

## 一、CURRENT ERROR FLOW（当前错误传播路径）

### 1. Lexer 错误
- **位置**: `compiler/lexer.tll:421`
- **方式**: `throw "Lexer error: unexpected char '" + opCh + "'"`
- **信息**: 仅包含错误字符，**无文件名、无行号、无列号、无错误码**
- **传播**: 直接抛出字符串异常

### 2. Parser 错误
- **位置**: `compiler/parser.tll:59, 1084`
- **方式**: 
  - `throw "Parse error: expected " + message + ", got '" + t.tkValue + "' at line " + t.line`
  - `throw "Parse error: unexpected token '" + t.tkValue + "' at line " + t.line`
- **信息**: 包含行号，**无列号、无文件名、无错误码**
- **传播**: 直接抛出字符串异常

### 3. Codegen 错误
- **位置**: 无明确的 throw 错误处理
- **方式**: 主要是 `OP_THROW` 操作码（用于 TLL 程序中的 throw 语句，非编译器自身错误）
- **传播**: 代码生成错误可能导致 VM 崩溃（unknown opcode）或运行时异常

### 4. TypeChecker 错误
- **位置**: `compiler/typechecker.tll`
- **方式**: 使用 `tc_errors: list` 收集错误，`tc_error(line, message)` 函数
- **信息**: 包含行号和消息，**无列号、无文件名、无错误码、无 severity**
- **传播**: **不 throw**，返回错误列表；linker 打印为 "type warning(s)"，**不阻塞编译**

### 5. Linker
- **位置**: `compiler/linker.tll:993-1061` (`linkAndCompile()`)
- **方式**: 直接调用 `tokenize(source)` → `parse(tokens)` → `compile(mergedProgram)`
- **关键问题**: **没有 try/catch 包裹**，lexer/parser 的 throw 直接向上传播
- **TypeChecker**: 调用 `check(mergedProgram)`，打印 type warnings，但不阻塞

### 6. Compiler Driver
- **位置**: `tools/TLLC/compiler_driver.tll`
- **方式**: `compileFile()` 调用 `linkAndCompile()`，检查 `bytecode.hasError`
- **关键问题**: 如果 lexer/parser throw 异常，**不会被捕获**，直接传播到 VM 层
- **返回格式**: `{ok: bool, error: string, functions, constants, ...}`

### 7. Main CLI
- **位置**: `tools/TLLC/main.tll`
- **方式**: 检查 `parsed["ok"]` / `result["ok"]`，调用 `printError()`，然后 `return`
- **关键问题**: 
  - 编译器错误时 `return`，**没有设置 exit code**
  - 未捕获的异常直接传播到 VM 层
- **printError**: 来自 `formatter.tll`，仅打印文本

### 8. VM 层（最终兜底）
- **位置**: `host/c/vm.c:522-525`
- **方式**: `fprintf(stderr, "Uncaught exception: %s\n", msg); exit(1);`
- **传播**: 最终异常由 VM 捕获，打印到 stderr，exit code = 1
- **unknown opcode**: `vm.c:1258-1259`，打印到 stderr，exit(1)

### 9. Exit Code 行为
| 场景 | exit code | 说明 |
|------|-----------|------|
| 正常编译成功 | 0 | `tll_exit_code = 0` |
| 未捕获异常（lexer/parser throw） | 1 | VM 层 `exit(1)` |
| 编译器通过 result.ok=false 报告错误 | **0** ❌ | main.tll 仅 return，未设置 exit code |
| unknown opcode / VM 崩溃 | 1 | VM 层 `exit(1)` |

---

## 二、ARCHITECTURE GAP（架构缺陷）

### GAP-1: 错误信息非结构化
- lexer/parser 抛出纯字符串，**无错误码、无 severity、无结构化字段**
- Agent 无法可靠解析错误信息
- 列号缺失（parser 有 line 但无 column）

### GAP-2: 错误传播机制不一致
| 阶段 | 机制 | 是否阻塞 |
|------|------|----------|
| Lexer | throw 字符串 | 是（传播到 VM） |
| Parser | throw 字符串 | 是（传播到 VM） |
| TypeChecker | 收集到列表，不 throw | 否（仅打印 warning） |
| Codegen | 无明确错误处理 | 不确定 |
| Linker | 无 try/catch | 异常直接传播 |

### GAP-3: Exit Code 不正确
- 编译器通过 `result.ok=false` 报告错误时，**exit code 仍然是 0**
- CI/脚本无法通过 exit code 判断编译是否失败
- 这是 Agent 闭环的关键障碍

### GAP-4: 无机器可解析格式
- 当前只有人类可读文本输出
- 无 JSON diagnostic 格式
- Agent 无法程序化读取错误并自动修复

### GAP-5: 无稳定错误码体系
- 没有错误码（如 TLL-E001）
- 错误信息文本变化会破坏依赖
- 无法按错误码分类统计

### GAP-6: 无 Severity 区分
- 没有 error/warning 正式区分
- TypeChecker 错误被称为 "warnings" 但不阻塞
- 无法控制哪些 warning 升级为 error

### GAP-7: Linker 层无异常捕获
- lexer/parser 的 throw 直接传播到 VM 层
- 无法在编译器层统一格式化错误
- 无法收集多个错误（第一个 throw 就中断）

---

## 三、MINIMAL DESIGN（最小设计）

### 3.1 Diagnostic 结构体

```tll
// compiler/diagnostic.tll (新增)
struct Diagnostic {
    severity: string    // "error" | "warning"
    code: string        // "TLL-E001", "TLL-W001"
    message: string
    file: string
    line: int
    column: int
    hint: string        // optional, "" if none
}
```

### 3.2 错误码体系（最小集合）

| 错误码 | 含义 | 来源 |
|--------|------|------|
| TLL-E001 | Lexer error（非法字符等） | lexer.tll |
| TLL-E002 | Parse error（语法错误） | parser.tll |
| TLL-E003 | File not found | compiler_driver.tll |
| TLL-E004 | Invalid bytecode format | compiler_driver.tll |
| TLL-W001 | Type warning | typechecker.tll |

**原则**: 只建立实际需要的最小集合，禁止凭空建立大量错误码。

### 3.3 最小实现路径（渐进式，Phase 4 只做这些）

#### Stage 1: Linker 层异常捕获 + 结构化转换
- 在 `linkAndCompile()` 中用 `try/catch` 包裹 `tokenize()` 和 `parse()`
- 捕获 throw 的字符串，解析为结构化 Diagnostic
- 从 parser 错误消息中提取 line 信息
- 设置 `bytecode.hasError = true`，`bytecode.error = 结构化消息`
- **不修改 lexer/parser 的 throw 方式**（保留现有 throw，在 linker 层捕获转换）

#### Stage 2: 错误码 + 输出格式化
- 新增 `compiler/diagnostic.tll` 模块
- 实现 `formatDiagnostic(diag) -> string`（人类可读）
- 实现 `diagnosticToJson(diag) -> string`（JSON 格式）
- 人类可读格式:
  ```
  Error TLL-E002 at main.tll:12: expected ')', got ';'
  ```
- JSON 格式（通过 `--json` 标志启用）:
  ```json
  {"diagnostics":[{"severity":"error","code":"TLL-E002","message":"expected ')', got ';'","file":"main.tll","line":12,"column":0}]}
  ```

#### Stage 3: Exit Code 修复
- 在 `main.tll` 中，编译器错误时设置 exit code != 0
- TLL 程序中通过 `process.exit(code)` 或类似机制设置 exit code
- 验证：编译失败时 exit code = 1，编译成功时 exit code = 0

#### Stage 4: 持久化测试
- TEST-01: 非法字符 / Lexer error → 结构化输出 + exit code != 0
- TEST-02: 非法语法 / Parser error → 结构化输出 + 行号正确
- TEST-03: 错误行列信息验证
- TEST-04: 错误码稳定（TLL-E001/TLL-E002）
- TEST-05: exit code != 0
- TEST-06: compiler 不 crash（不出现 Uncaught exception）
- TEST-07: JSON diagnostic 可被机器解析
- TEST-08: 合法程序不产生 diagnostic + exit code = 0

### 3.4 明确不做（Phase 4 范围外）

- ❌ 不重构 lexer/parser 的错误抛出方式（保留 throw，在 linker 层捕获转换）
- ❌ 不实现完整的 warning framework（typechecker 警告保持现有行为）
- ❌ 不修改 typechecker 的错误处理
- ❌ 不实现 codegen 的结构化错误
- ❌ 不实现多错误收集（第一个错误即停止，保持现有行为）
- ❌ 不实现列号（parser 当前无 column 信息，后续补充）
- ❌ 不实现 hint/suggestion 系统
- ❌ 不实现 --json 之外的其他输出格式

### 3.5 验收标准

```
TLL Source (with error)
   ↓
Lexer / Parser failure
   ↓
Linker try/catch captures
   ↓
Structured Diagnostic (code, message, file, line)
   ↓
Human-readable output (stderr)
   ↓
compiler exit code = 1
   ↓
process 不崩溃 (no "Uncaught exception")
   ↓
Optional: JSON output (--json)
```

---

## 四、施工计划

| Stage | 内容 | 预计修改文件 |
|-------|------|-------------|
| 1 | Linker 层 try/catch + 异常转换 | compiler/linker.tll |
| 2 | Diagnostic 模块 + 格式化 + 错误码 | compiler/diagnostic.tll (新增) |
| 3 | Exit code 修复 | tools/TLLC/main.tll |
| 4 | 持久化测试 | tests/compiler/probe_diagnostic.tll |
| 5 | Evidence 文档 | docs/P0-TLL-LANGUAGE-COMPLETE-PHASE4.md |

---

## 五、审计结论

**Audit First 完成，可以进入施工。**

- 当前错误传播路径已完整梳理
- 7 个架构 GAP 已识别
- 最小设计已确定（4 个 Stage，范围严格控制）
- 明确不做的事项已列出
- 验收标准已定义

**下一步**: 进入 Stage 1 施工（Linker 层 try/catch + 异常转换）。
