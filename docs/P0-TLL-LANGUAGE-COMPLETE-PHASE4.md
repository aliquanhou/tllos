# P0-TLL-LANGUAGE-COMPLETE Phase 4 — Compiler Diagnostic Foundation

**日期**: 2026-09-08
**分支**: p0-language-phase4-diagnostic
**基线**: main @ 5cd785b
**状态**: Implementation Complete, Tests Passing

---

## 一、施工目标

建立 TLL Compiler 的最小结构化诊断闭环，使编译器失败时能够：
- 输出结构化错误信息（错误码、消息、文件名、行号、列号）
- 提供稳定的人类可读输出格式
- 设置正确的进程 exit code（编译失败时 exit code != 0）
- 不崩溃（无 heap corruption / "Uncaught exception" 前缀）

---

## 二、Audit First 结论

### 当前错误传播路径（施工前）

| 阶段 | 机制 | 问题 |
|------|------|------|
| Lexer | `throw "Lexer error: unexpected char '...'"` | 无错误码、无行号、无列号 |
| Parser | `throw "Parse error: expected ... at line ..."` | 无错误码、无列号 |
| TypeChecker | 收集到列表，不 throw | 仅打印 warning，不阻塞 |
| Linker | 无 try/catch | 异常直接传播到 VM |
| Main CLI | `printError()` + `return` | **exit code 仍为 0** |
| VM | `fprintf(stderr, "Uncaught exception: %s")` + `exit(1)` | 有 "Uncaught exception:" 前缀 |

### 关键架构 GAP

1. **错误信息非结构化**：纯字符串，无错误码、无 severity
2. **Exit code 不正确**：编译器通过 result.ok=false 报告错误时，exit code 仍为 0
3. **无机器可解析格式**：只有人类可读文本
4. **Linker 无异常捕获**：try/catch 与复杂函数交互导致 Runtime heap corruption（已确认是 TLL Runtime bug，不在本阶段修复范围）

---

## 三、实现方案

由于 TLL Runtime 的 try/catch 在复杂函数（如 linkAndCompile）中会导致 heap corruption，本阶段采用**不使用 try/catch** 的替代方案：

### 方案：修改 throw 消息格式 + VM 层异常处理优化 + exit code 修复

#### 1. Lexer 错误消息格式化

**文件**: `compiler/lexer.tll`
**修改**: throw 消息从 `"Lexer error: unexpected char '...'"` 改为：
```
TLL-E001 Lexer error at line X column Y: unexpected char '...'
```

#### 2. Parser 错误消息格式化

**文件**: `compiler/parser.tll`
**修改**: 两个 throw 位置（parse_expect 和 parseIdentifierOrKeyword）从 `"Parse error: ... at line ..."` 改为：
```
TLL-E002 Parse error at line X column Y: expected ..., got ...
```

#### 3. VM 层异常处理优化

**文件**: `host/c/vm.c`
**修改**: 未捕获异常处理函数中，检查错误消息是否以 `TLL-E` 开头：
- 如果是编译器诊断错误（TLL-E###），直接输出消息，不加 "Uncaught exception:" 前缀
- 否则保留原有 "Uncaught exception: " 前缀

```c
if (strncmp(msg, "TLL-E", 5) == 0) {
    fprintf(stderr, "%s\n", msg);
} else {
    fprintf(stderr, "Uncaught exception: %s\n", msg);
}
```

#### 4. Exit code 修复

**文件**: `tools/TLLC/main.tll`
**修改**: 编译器错误时（parseArgs 失败、compile/check/info 失败），将 `return` 改为 `process.exit(1)`。

TLL 的 `process.exit(code)` 内置函数会设置 `tll_exit_code` 和 `tll_should_exit`，main 函数最终返回 `tll_exit_code`。

---

## 四、错误码体系

| 错误码 | 含义 | 来源 |
|--------|------|------|
| TLL-E001 | Lexer error（非法字符等） | compiler/lexer.tll |
| TLL-E002 | Parse error（语法错误） | compiler/parser.tll |

**原则**: 只建立实际需要的最小集合，禁止凭空建立大量错误码。后续阶段可根据需要扩展（TLL-E003 Type error, TLL-E004 Codegen error 等）。

---

## 五、测试结果

### 诊断基础测试（17/17 PASS）

测试脚本: `run_diagnostic_tests.py`

| 测试 | 内容 | 结果 |
|------|------|------|
| TEST-01 | Lexer error（非法字符 $） | ✅ exit!=0, TLL-E001, line info |
| TEST-02 | Parser error（语法错误） | ✅ exit!=0, TLL-E002, line+column |
| TEST-03 | 正确行号 | ✅ error at line 7 (EOF) |
| TEST-04 | 稳定错误码 | ✅ 相同错误类型 → 相同 code |
| TEST-05 | Exit code != 0 | ✅ 编译错误时 exit=1 |
| TEST-06 | 编译器不崩溃 | ✅ exit=1（非负数/crash） |
| TEST-07 | 合法程序编译运行 | ✅ compile=0, run=0, output correct |
| TEST-08 | 合法程序无诊断 | ✅ 无 TLL-E 输出 |

### 验收测试回归（12/12 PASS）

测试脚本: `run_acceptance_regression.py`

| 测试 | 结果 |
|------|------|
| 01_hello | ✅ |
| 02_variables | ✅ |
| 03_functions | ✅ |
| 04_control_flow | ✅ |
| 05_arrays | ✅ |
| 06_maps | ✅ |
| 07_recursion | ✅ |
| 08_strings | ✅ |
| 09_exceptions | ✅ |
| 10_firstclass | ✅ |
| 11_math | ✅ |
| 12_json | ✅ |

---

## 六、修改文件清单

| 文件 | 修改内容 | 行数变化 |
|------|----------|----------|
| compiler/lexer.tll | throw 消息添加 TLL-E001 + 行列 | +1/-1 |
| compiler/parser.tll | 两个 throw 消息添加 TLL-E002 + 行列 | +2/-2 |
| host/c/vm.c | 异常处理：TLL-E 前缀错误干净输出 | +6/-1 |
| tools/TLLC/main.tll | 编译器错误时 process.exit(1) | +3/-3 |
| **合计** | | **+12/-7** |

---

## 七、已知 GAP（非阻塞，后续阶段处理）

1. **JSON diagnostic 格式**：当前只有人类可读文本输出，尚未实现 `--json` 机器可解析格式
2. **TypeChecker 错误结构化**：TypeChecker 错误仍为纯字符串，未添加错误码
3. **Codegen 错误处理**：Codegen 阶段无明确的错误处理机制
4. **多错误收集**：当前第一个错误即停止，未实现多错误收集
5. **Hint/Suggestion**：尚未实现错误提示和修复建议
6. **try/catch Runtime bug**：TLL Runtime 的 try/catch 在复杂函数中导致 heap corruption，需后续修复
7. **文件名信息**：当前错误消息不包含源文件名（lexer/parser 不知道文件名）

---

## 八、与 TLL + Agent 闭环的关系

本阶段建立的诊断基础是未来 TLL + Agent 闭环的基础设施：

```
TLL Compiler
      ↓
Diagnostic (TLL-E###, line, column, message)
      ↓
Agent 读取结构化错误
      ↓
Agent 修复代码
      ↓
再次编译
```

当前已实现：
- ✅ 稳定的错误码（TLL-E001/TLL-E002）
- ✅ 行号和列号信息
- ✅ 干净的错误输出（无 "Uncaught exception:" 前缀）
- ✅ 正确的 exit code

后续需实现：
- ⏳ JSON 格式输出（Agent 可直接解析）
- ⏳ 更多阶段的错误码覆盖（TypeChecker, Codegen 等）
- ⏳ 错误提示和修复建议

---

## 九、验收标准对照

| 验收标准 | 状态 |
|----------|------|
| 结构化错误消息（错误码、行号、列号） | ✅ |
| 稳定的人类可读输出格式 | ✅ |
| 编译错误时 exit code != 0 | ✅ |
| 编译器不崩溃（无 heap corruption） | ✅ |
| 合法程序正常编译运行 | ✅ |
| 回归测试通过 | ✅ 12/12 |
| 诊断测试通过 | ✅ 17/17 |

---

## 十、结论

**Phase 4 Compiler Diagnostic Foundation 实现完成。**

通过最小化修改（4 个文件，+12/-7 行），建立了 TLL Compiler 的结构化诊断基础：
- 错误码体系（TLL-E001/TLL-E002）
- 行列信息
- 干净的错误输出
- 正确的 exit code

所有测试通过，无回归。可进入架构师验收阶段。
