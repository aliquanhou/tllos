# PHASE 2-01-A — Compiler Bootstrap Closure Audit Report

**施工队**: 豆包 A
**阶段**: Phase 2 / P2-01-A
**基线**: b32dc67 (TLL Phase 2 Starting Baseline)
**日期**: 2026-09-08
**Git 状态**: 本地审计，未 Push，工作区干净

---

## 一、执行摘要

**结论：Compiler Bootstrap Closure 尚未成立。**

Stage-0 → Stage-1 编译链可以正常工作，但 Stage-1 → Stage-2 虽然编译成功，生成的 `tllc.tllbc` 在运行时无法正常工作（`process.argv` 调用失败）。

原始的 `tools/TLLC/tllc.tllbc`（830,836 bytes，git tracked）工作正常，但它**无法用当前 bootstrap pipeline 重新生成**。这意味着当前仓库中的 tllc.tllbc 是一个历史种子产物，而不是可复现的自举产物。

---

## 二、Bootstrap Pipeline 文档化 (BOOTSTRAP-G1)

### 2.1 官方脚本

仓库中存在官方 bootstrap 脚本：
- `scripts/bootstrap-tllc.bat` (Windows)
- `scripts/bootstrap-tllc.sh` (Linux/macOS)

### 2.2 Pipeline 定义

```
Stage-0 (Seed)
├── host/c/tllvm.exe          (C VM, 1,378,304 bytes)
├── compiler/compiler.tllbc   (预编译编译器字节码, 592,514 bytes)
└── tools/TLLC/tllc.tllbc     (预编译 TLLC CLI, 830,836 bytes, git tracked)
         │
         ▼
Stage-1 (Bootstrap Compiler)
├── 输入: compiler/bootstrap_tllc.tll (通过替换 compiler.tll)
├── 编译器: compiler/compiler.tllbc (Stage-0 种子)
├── 输出: compiler/compiler_self_compiled.tllbc
└── 结果: 859,505 bytes, 173 functions, 5485 constants
         │
         ▼
Stage-2 (TLLC CLI)
├── 输入: tools/TLLC/main.tll
├── 编译器: compiler/compiler_self_compiled.tllbc (Stage-1)
├── 输出: tools/TLLC/tllc.tllbc
└── 结果: 860,276 bytes, 编译成功但运行时失败
```

### 2.3 文件替换机制

bootstrap 脚本使用文件替换技巧：
1. 备份 `compiler/compiler.tll`
2. 用 `compiler/bootstrap_tllc.tll` 替换 `compiler/compiler.tll`
3. Stage-0 编译器编译 `compiler.tll`（此时是 bootstrap_tllc.tll）
4. Stage-1 输出运行时，其 main() 编译 `../tools/TLLC/main.tll`
5. 恢复 `compiler/compiler.tll`

**BOOTSTRAP-G1 状态**: ✅ PASS — Pipeline 已文档化，有官方脚本。

---

## 三、Stage-0 → Stage-1 验证 (BOOTSTRAP-G2)

### 3.1 执行结果

| 指标 | 值 |
|------|-----|
| 输入 | compiler/bootstrap_tllc.tll (via compiler.tll swap) |
| 编译器 | compiler/compiler.tllbc (Stage-0 seed) |
| 输出 | compiler/compiler_self_compiled.tllbc |
| 输出大小 | 859,505 bytes |
| Functions | 173 |
| Constants | 5,485 |
| mainFunctionIndex | 172 |
| 编译耗时 | 18-20 秒 |
| 退出码 | 0 |

### 3.2 类型检查警告

Stage-1 编译过程中产生了大量类型检查警告（325+），主要包括：
- `arithmetic operator '-' requires numeric operands`
- `argument 2: expected map, got Map`
- `argument 2: expected list, got List`

这些警告不阻塞编译，属于 TLL 类型系统的已知限制（动态类型 + 部分静态检查）。

**BOOTSTRAP-G2 状态**: ✅ PASS — Stage-0 → Stage-1 编译成功。

---

## 四、Stage-1 → Stage-2 验证 (BOOTSTRAP-G3)

### 4.1 编译结果

| 指标 | 值 |
|------|-----|
| 输入 | tools/TLLC/main.tll |
| 编译器 | compiler/compiler_self_compiled.tllbc (Stage-1) |
| 输出 | tools/TLLC/tllc.tllbc |
| 输出大小 | 860,276 bytes |
| 编译耗时 | ~39 秒 |
| 退出码 | 0 |

### 4.2 关键问题：生成的 tllc.tllbc 运行时失败

用 Stage-2 生成的 `tllc.tllbc` 运行任何命令都失败：

```
$ tllvm.exe tools/TLLC/tllc.tllbc help
=== ERROR ===
Unknown command:
```

### 4.3 根因分析

编译 `tools/TLLC/main.tll` 时出现关键警告：

```
Line 12: undefined identifier 'process'
Line 36: undefined identifier 'process'
Line 52: undefined identifier 'process'
Line 63: undefined identifier 'process'
Line 81: undefined identifier 'process'
```

**原因**：
1. `tools/TLLC/main.tll` 直接使用 `process.argv` 和 `process.exit()`
2. 但 `main.tll` 没有显式 `from "process" import ...`
3. `process` 是 C VM 内置模块，**不是 TLL stdlib 模块**（`stdlib/` 目录中没有 `process.tll`）
4. TLL 类型检查器无法识别未导入的内置模块，标记为 `undefined identifier`
5. 代码生成器虽然生成了字节码，但 `process.argv` 调用在运行时无法正确解析
6. 导致 `main()` 中 `process.argv` 返回空/无效值，`parseArgs(args)` 得到空命令，最终输出 "Unknown command:"

### 4.4 原始 tllc.tllbc 的状态

| 属性 | 原始 (git tracked) | Stage-2 重新生成 |
|------|-------------------|------------------|
| 大小 | 830,836 bytes | 860,276 bytes |
| 运行状态 | ✅ 工作正常 | ❌ "Unknown command:" |
| 生成方式 | 未知（历史产物） | 当前 bootstrap pipeline |
| Git 状态 | tracked | 覆盖后已恢复 |

**关键发现**：原始的 `tllc.tllbc` 无法用当前 bootstrap pipeline 重新生成。它是一个历史种子产物，可能是在 process 模块还能被正确识别的时候生成的，或者用了不同的编译入口。

**BOOTSTRAP-G3 状态**: ⚠️ PARTIAL — 编译成功，但生成的 tllc.tllbc 运行时失败。Bootstrap 链未闭合。

---

## 五、Deterministic Comparison (BOOTSTRAP-G4)

### 5.1 Stage-1 确定性验证

对 Stage-1 执行两次独立编译，比较输出：

| 运行 | 输出大小 | SHA256 |
|------|---------|--------|
| Run #1 | 859,505 bytes | `C84A83CEA3F52594F68541FFBEB1D8BF9D7E09BC0E652A66F38DA16AE3804A97` |
| Run #2 | 859,505 bytes | `C84A83CEA3F52594F68541FFBEB1D8BF9D7E09BC0E652A66F38DA16AE3804A97` |
| 结果 | **IDENTICAL** | **MATCH** |

### 5.2 Stage-2 确定性

由于 Stage-2 生成的 `tllc.tllbc` 运行时失败，无法进行有意义的功能比较。但编译过程本身应该是 deterministic 的（基于 Stage-1 的确定性）。

**BOOTSTRAP-G4 状态**: ✅ PASS (Stage-1) / ⚠️ N/A (Stage-2 产物无效)

---

## 六、Clean-Environment Reproduction (BOOTSTRAP-G5)

### 6.1 可复现性

`scripts/bootstrap-tllc.bat` 脚本定义了完整的自动化流程：
1. 检查/构建 tllvm.exe
2. 备份并替换 compiler.tll
3. Stage-1: 用 compiler.tllbc 编译 bootstrap_tllc.tll
4. Stage-2: 用 Stage-1 输出编译 tools/TLLC/main.tll
5. 验证 tllc.tllbc 生成
6. 恢复 compiler.tll

在干净环境中可以完整复现此流程。

### 6.2 复现结果

但复现的结果是：**生成的 tllc.tllbc 不工作**。

这意味着 clean-environment reproduction 只能复现失败状态，不能复现一个可用的 tllc.tllbc。

**BOOTSTRAP-G5 状态**: ⚠️ PARTIAL — 流程可复现，但结果是失败的产物。

---

## 七、Hidden Manual Step 检查 (BOOTSTRAP-G6)

### 7.1 半自动步骤

bootstrap 脚本中存在文件替换操作：
- `compiler.tll` ↔ `bootstrap_tllc.tll` 交换
- 这是脚本自动化的，不需要人工干预，但属于"非直接"的编译流程

### 7.2 未文档化的历史产物

**关键问题**：原始 `tools/TLLC/tllc.tllbc`（830,836 bytes，工作正常）的生成方式没有完整文档。
- 它不是用当前 `bootstrap-tllc.bat` 生成的（因为那个脚本生成的 tllc.tllbc 不工作）
- 可能是历史上用不同的入口文件或不同的编译器版本生成的
- 无法从当前源码 + 当前工具链重新生成

### 7.3 compiler.tllbc 种子

`compiler/compiler.tllbc`（592,514 bytes）也是一个预编译种子产物：
- 它的 main() 编译 `compiler.tll`
- 它工作正常（Stage-1 成功）
- 但它的生成方式同样没有完整文档

**BOOTSTRAP-G6 状态**: ⚠️ PARTIAL — 有文件替换步骤（脚本自动化），且原始种子产物生成方式不明确。

---

## 八、BOOTSTRAP-GATE 总评

| Gate | 描述 | 状态 | 说明 |
|------|------|------|------|
| G1 | Bootstrap pipeline documented | ✅ PASS | 有官方 bootstrap-tllc.bat/.sh 脚本 |
| G2 | Stage-0 → Stage-1 succeeds | ✅ PASS | 编译成功，859,505 bytes, 173 functions |
| G3 | Stage-1 → Stage-2 succeeds | ⚠️ PARTIAL | 编译成功但产物运行时失败（process.argv） |
| G4 | Stage-1/Stage-2 deterministic | ✅ PASS | Stage-1 两次运行 SHA256 完全一致 |
| G5 | Clean-environment reproduction | ⚠️ PARTIAL | 流程可复现，但结果是失败的 tllc.tllbc |
| G6 | No hidden manual step | ⚠️ PARTIAL | 有文件替换（脚本化），种子产物生成方式不明确 |

**总体结论**: ❌ BOOTSTRAP NOT CLOSED

---

## 九、核心发现

### 9.1 发现 #1: process 模块链接缺陷

**WHAT**: `tools/TLLC/main.tll` 使用 `process.argv` 和 `process.exit()` 但没有显式 import process。

**WHY**: `process` 是 C VM 内置模块，不是 TLL stdlib 模块。TLL 类型检查器无法识别未导入的内置模块。

**WHERE**: `tools/TLLC/main.tll` lines 12, 36, 52, 63, 81

**TEST**: 用 bootstrap pipeline 生成 tllc.tllbc，运行 `tllc.tllbc help`

**RESULT**: "Unknown command:" 错误，process.argv 返回无效值

**LIMITATION**: 需要修复 TLL 编译器对内置模块的处理，或者修改 main.tll 显式 import process

### 9.2 发现 #2: 原始 tllc.tllbc 不可复现

**WHAT**: git tracked 的 `tools/TLLC/tllc.tllbc`（830,836 bytes）工作正常，但无法用当前 bootstrap pipeline 重新生成。

**WHY**: 当前 pipeline 生成的 tllc.tllbc（860,276 bytes）有 process.argv 缺陷。原始产物可能是在不同条件下生成的历史种子。

**WHERE**: `tools/TLLC/tllc.tllbc`

**TEST**: 运行 `git checkout -- tools/TLLC/tllc.tllbc` 恢复原始版本，验证其工作正常

**RESULT**: 原始版本工作正常，重新生成版本失败

**LIMITATION**: 需要修复 process 模块问题后才能重新生成可用的 tllc.tllbc

### 9.3 发现 #3: Stage-1 编译器是 deterministic 的

**WHAT**: Stage-1 编译（compiler.tllbc → compiler_self_compiled.tllbc）两次运行产生完全相同的输出。

**WHY**: TLL 编译器是确定性的，没有时间戳、随机数或非确定性行为。

**WHERE**: `compiler/compiler_self_compiled.tllbc`

**TEST**: 两次独立编译，比较 SHA256

**RESULT**: SHA256 完全一致: `C84A83CE...`

**LIMITATION**: 仅验证了 Stage-1，Stage-2 产物无效无法验证

---

## 十、依赖 Host 的环节

| 环节 | 依赖 | 说明 |
|------|------|------|
| VM 执行 | Host C Runtime | tllvm.exe 是 MSVC 编译的 C 程序 |
| process 模块 | Host OS | process.argv/exit 由 C VM 内置实现 |
| 文件 I/O | Host OS | fs.readFile/writeFile 由 C builtin 实现 |
| 编译器种子 | 历史产物 | compiler.tllbc 和 tllc.tllbc 是预编译种子，不可从源码复现 |

---

## 十一、建议的修复方向（不立即执行）

### 选项 A: 修改 main.tll 显式 import process

在 `tools/TLLC/main.tll` 顶部添加：
```
from "process" import argv, exit
```

但需要确认 TLL 的 import 语法是否支持内置模块，以及 process 模块导出了哪些符号。

### 选项 B: 修复编译器内置模块处理

修改 `compiler/typechecker.tll` 和 `compiler/codegen.tll`，使其能够正确识别和处理 C VM 内置模块（process, io, math 等），即使没有显式 import。

### 选项 C: 调查原始 tllc.tllbc 的生成方式

检查 git history，找到 tllc.tllbc 最初是如何生成的，是否有特殊的编译入口或标志。

---

## 十二、P2-01-A 最终状态

| 项目 | 状态 |
|------|------|
| Pipeline 文档化 | ✅ |
| Stage-0 → Stage-1 | ✅ 成功 |
| Stage-1 → Stage-2 | ⚠️ 编译成功，产物失败 |
| Deterministic | ✅ Stage-1 |
| Clean reproduction | ⚠️ 可复现失败 |
| No hidden steps | ⚠️ 种子产物不明确 |
| Bootstrap Closed | ❌ **NOT CLOSED** |
| 代码修改 | ❌ 无（仅审计） |
| Git Push | ❌ 无 |
| 工作区 | ✅ 干净 |

---

## 十三、Evidence

| 证据 | 位置 | 状态 |
|------|------|------|
| Stage-1 输出 | `compiler/compiler_self_compiled.tllbc` (859,505 bytes) | 已验证 |
| Stage-1 SHA256 | `C84A83CEA3F52594F68541FFBEB1D8BF9D7E09BC0E652A66F38DA16AE3804A97` | 两次运行一致 |
| Stage-2 输出 | `tools/TLLC/tllc.tllbc` (860,276 bytes, 已恢复原始版本) | 运行时失败 |
| 原始 tllc.tllbc | `tools/TLLC/tllc.tllbc` (830,836 bytes, git tracked) | 工作正常 |
| Bootstrap 脚本 | `scripts/bootstrap-tllc.bat`, `scripts/bootstrap-tllc.sh` | 存在 |
| 编译日志 | 本报告 | 已记录 |

---

**豆包 A 停止施工，提交报告，等待架构裁决。**

**P2-01-A 结论：Compiler Bootstrap Closure 尚未成立。Stage-0→Stage-1 工作，Stage-1→Stage-2 产物因 process 模块链接缺陷而运行时失败。原始 tllc.tllbc 是不可复现的历史种子产物。**
