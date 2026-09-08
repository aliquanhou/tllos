# PHASE 2-01-B.8 — Automatic Cross-Target Conformance

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
**阶段**: Phase 2 / P2-01-B Native Backend Foundation
**基线**: b32dc67
**日期**: 2026-09-09
**状态**: 施工完成 / 等待裁决

---

## 一、执行摘要

### 核心成果

**Automatic Cross-Target Conformance Framework 建立完成：将 P2-01-B.7 证明成功的一次 E2E，变成了可以重复运行的自动化验证机制。**

本阶段完成了架构师要求的 5 项任务：
1. ✅ **B8-01 参数化 Conformance Runner**：`cross-target-conformance.ps1` 支持任意 `.tll` 文件输入
2. ✅ **B8-02 建立 3 个 Native Conformance Cases**：01_basic、02_function、03_io
3. ✅ **B8-03 禁止手写 C**：所有测试用例的 C 代码均由 `native_lower.tll` 自动生成
4. ✅ **B8-04 Bytecode / Native 来自同一源文件**：每个 case 只有一份 `.tll`，两条编译路径共享
5. ✅ **B8-05 自动记录 Evidence**：每个 case 自动生成 `.evidence.txt`，包含完整构建/执行/比较状态

### 关键指标

| 指标 | 数值 |
|------|------|
| Conformance Cases | 4 个（cross_target_minimal + 01_basic + 02_function + 03_io） |
| 全部 PASS | ✅ 4/4 |
| stdout identical | ✅ 4/4 |
| exit code identical | ✅ 4/4 |
| MSVC 0 errors 0 warnings | ✅ 4/4 |
| C 代码由 native_lower 自动生成 | ✅ 4/4（非手写） |
| Bytecode/Native 同一源文件 | ✅ 4/4 |
| Evidence 文件自动生成 | ✅ 4/4 |
| Bootstrap Stage-0 regression | ✅ 通过 |
| batch1_basic regression | ✅ 通过（35 行输出一致） |
| conformance_minimal regression | ✅ 通过 |
| 总 regression | ✅ 无倒退 |
| BLOCKER | 0 |
| Git Push | ❌ 禁止 |

---

## 二、B8-01: 参数化 Conformance Runner

### native_compile_driver.tll 参数化

**文件**: `compiler/native_compile_driver.tll`

**修改前**: 硬编码输入文件 `tests/native/cross_target_minimal.tll`

**修改后**: 支持命令行参数
```
tllvm native_compile_driver.tllbc [input.tll] [output.c]
```

- `argv[2]`: 输入文件（默认 `tests/native/cross_target_minimal.tll`）
- `argv[3]`: 输出文件（默认自动推导：将 `.tll` 替换为 `.c`）

**验证**:
- 默认文件：✅ 正常工作
- 显式文件：✅ 正常工作（`test_param.c` 生成成功，603 字节）

### cross-target-conformance.ps1 自动化框架

**文件**: `scripts/cross-target-conformance.ps1`

**功能**: 完整的 6 步自动化 Conformance 测试
1. **Bytecode compile**: `tllc.tllbc` 编译 `.tll` → `.tllbc`
2. **Native lower**: `native_compile_driver.tllbc` 调用 `native_lower.tll` 生成 `.c`
3. **Native compile**: MSVC 编译 `.c` + Shared Runtime → `.exe`（0 errors, 0 warnings）
4. **Run Bytecode**: `tllvm` 运行 `.tllbc`，记录 stdout 和 exit code
5. **Run Native**: 运行 `.exe`，记录 stdout 和 exit code
6. **Compare**: 文件级 `Compare-Object` 比较 stdout，比较 exit code

**用法**:
```powershell
scripts/cross-target-conformance.ps1 [test_file.tll]
# 默认测试: tests/native/cross_target_minimal.tll
```

**Exit codes**:
- `0` = PASS（stdout 和 exit code 均一致）
- `1` = FAIL（差异检测到或构建错误）

**Evidence 自动记录**: 每个测试自动生成 `<test_name>.evidence.txt`，包含：
- 测试文件、时间戳
- 构建状态（Bytecode compile / Native lower / Native compile）
- 执行状态（Bytecode exit / Native exit / exit code identical）
- 输出比较（stdout identical / stdout lines）
- Overall: PASS / FAIL

---

## 三、B8-02: 3 个 Native Conformance Cases

### Case 01: basic

**文件**: `tests/native/01_basic.tll`

**覆盖能力**:
- 整数算术（+、-、*、/）
- 比较运算（>、<、==）
- 布尔逻辑（&&、||、!）
- let 变量声明
- return 语句
- io.println

**测试结果**: ✅ PASS
- stdout identical: True
- exit code identical: True（均为 0）
- MSVC: 0 errors, 0 warnings

### Case 02: function

**文件**: `tests/native/02_function.tll`

**覆盖能力**:
- 函数声明（fn add, fn multiply, fn compute）
- 函数参数（多参数）
- 嵌套函数调用（compute 调用 add 和 multiply）
- return 语句
- let 变量声明
- io.println

**测试结果**: ✅ PASS
- stdout identical: True
- exit code identical: True（均为 0）
- MSVC: 0 errors, 0 warnings

### Case 03: io

**文件**: `tests/native/03_io.tll`

**覆盖能力**:
- 字符串字面量
- 字符串拼接（"hello" + " " + "world"）
- io.println（字符串和数字混合输出）
- 空字符串
- let 变量声明
- 整数算术
- return 语句

**测试结果**: ✅ PASS
- stdout identical: True
- exit code identical: True（均为 0）
- MSVC: 0 errors, 0 warnings

### 已有 Case: cross_target_minimal

**文件**: `tests/native/cross_target_minimal.tll`（P2-01-B.7 建立）

**覆盖能力**:
- 函数声明和调用
- let 变量
- 整数算术
- return
- io.println
- 字符串

**测试结果**: ✅ PASS

---

## 四、B8-03: 禁止手写 C（验证）

**架构师要求**: 每一个 case 的 C 代码只能是生成物，禁止手写等价 C。

**验证结果**: ✅ 全部满足

| Case | C 代码来源 | 生成方式 |
|------|-----------|---------|
| cross_target_minimal | `native_lower.tll` 自动生成 | `native_compile_driver.tllbc` 调用 |
| 01_basic | `native_lower.tll` 自动生成 | `native_compile_driver.tllbc` 调用 |
| 02_function | `native_lower.tll` 自动生成 | `native_compile_driver.tllbc` 调用 |
| 03_io | `native_lower.tll` 自动生成 | `native_compile_driver.tllbc` 调用 |

**证据**: 每个 case 的 `.c` 文件在每次测试前被自动删除，然后由 `native_lower.tll` 重新生成。不存在任何手写 C 代码。

---

## 五、B8-04: Bytecode / Native 来自同一源文件（验证）

**架构师要求**: 禁止 Bytecode 用 A.tll、Native 用 C B；必须同一个 A.tll 走两条路径。

**验证结果**: ✅ 全部满足

每个 case 只有一份 `.tll` 源文件：
```
同一个 01_basic.tll
      │
      ├── Bytecode Target → tllc.tllbc → 01_basic.tllbc → tllvm → 输出
      └── Native Target   → native_lower.tll → 01_basic.c → MSVC → 01_basic.exe → 输出
```

**证据**: `cross-target-conformance.ps1` 的 Step 1 和 Step 2 使用同一个 `$TestFile` 变量，确保两条路径共享同一源文件。

---

## 六、B8-05: 自动记录 Evidence

**架构师要求**: 每个 case 至少记录 source、bytecode stdout、native stdout、bytecode exit、native exit、comparison、compiler status、native build status。

**验证结果**: ✅ 全部满足

每个 case 自动生成 `<test_name>.evidence.txt`，包含：

```
TLL Cross-Target Conformance Evidence
================================
Test file: tests/native/01_basic.tll
Timestamp: 2026-09-09 01:41:00

Build Status:
  Bytecode compile: PASS
  Native lower:     PASS
  Native compile:   PASS

Execution:
  Bytecode exit code: 0
  Native exit code:   0
  Exit code identical: True

Output Comparison:
  stdout identical: True
  Bytecode stdout lines: 12
  Native stdout lines:   12

Overall: PASS
```

**已生成的 Evidence 文件**:
- `tests/native/cross_target_minimal.evidence.txt`
- `tests/native/01_basic.evidence.txt`
- `tests/native/02_function.evidence.txt`
- `tests/native/03_io.evidence.txt`

---

## 七、所有测试结果汇总

| Case | 覆盖能力 | Bytecode Compile | Native Lower | Native Compile | stdout Same | exit Same | Overall |
|------|---------|-----------------|-------------|---------------|------------|----------|---------|
| cross_target_minimal | function/let/arithmetic/return/io/string | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 01_basic | arithmetic/comparison/bool/let/return/io | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 02_function | function/params/nested call/return/let/io | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| 03_io | string/concat/mixed output/let/arithmetic/return | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |

**总计**: 4/4 PASS ✅

---

## 八、Bootstrap / VM Regression 验证

| 测试 | 结果 | 说明 |
|------|------|------|
| Bootstrap Stage-0 | ✅ PASS | `=== Bootstrap Level 5 Complete ===` |
| batch1_basic | ✅ PASS | 35 行输出，与之前完全一致 |
| conformance_minimal | ✅ PASS | 14 行输出 |
| **总 regression** | ✅ **无倒退** | |

---

## 九、GAP Ledger

### 9.1 本阶段新发现 GAP

| ID | 分类 | 描述 | 优先级 |
|----|------|------|--------|
| B8-GAP-01 | TEST | Conformance 脚本目前逐个运行测试用例，缺少批量运行器（一次运行所有 cases 并生成汇总报告） | P2 |
| B8-GAP-02 | COVERAGE | Native Lowering 当前仅支持 11 项能力（let/Int/arithmetic/comparison/bool/function/return/string/io.println/block/if），Array/Map/Closure/Exception/Coroutine 等尚未支持 | P1（后续阶段逐步扩展） |
| B8-GAP-03 | SEMANTICS | Native Target 暂不支持 process.exit(code)，进程 exit code 总是 0 | P2 |

### 9.2 已关闭 GAP

- **B7-GAP-02**（Conformance 脚本硬编码测试文件）: ✅ **已关闭**
  - `cross-target-conformance.ps1` 现在支持任意 `.tll` 文件参数
  - `native_compile_driver.tll` 现在支持命令行参数指定输入/输出文件

### 9.3 仍 OPEN（留待后续）

- B7-GAP-01: process.exit(code) 暂不支持
- B7-GAP-03: Native Lowering 覆盖范围有限
- B5-GAP-02: Full Runtime ABI Compatibility 尚未完全验证
- B6-GAP-01: 4 个文档构建命令示例需更新
- B6-GAP-02: GCC/Linux 构建路径需在 Linux 环境验证
- B6-GAP-03: CI 配置可能仍引用旧构建命令

---

## 十、对后续阶段的建议

### 10.1 P2-01-B.9 建议（Native Semantic Expansion）

**目标**: 逐步扩展 Native Lowering 的能力覆盖，每扩展一种能力就增加对应的 Conformance 测试。

**建议顺序**（按依赖关系和杠杆率排序）:
1. **String 操作**（length、比较、更多拼接）— 基础能力，依赖低
2. **Array**（字面量、索引、push、length）— 高频使用，杠杆高
3. **Map**（字面量、索引、set、get）— 高频使用，杠杆高
4. **更多控制流**（while、for、break、continue）— 基础能力
5. **Closure**（闭包捕获、环境）— 中等复杂度
6. **Exception**（throw、try/catch/finally）— 高复杂度

**原则**: 每扩展一种能力，必须同时建立对应的 Cross-Target Conformance 测试，确保 Bytecode 和 Native 输出一致。

### 10.2 P2-01-B.10 建议（Conformance Framework 增强）

**目标**: 建立批量运行器和 Conformance Matrix
1. 批量运行所有测试用例，生成汇总报告
2. 建立 Conformance Matrix（能力 × 测试用例 × 状态）
3. 集成到 CI 流程
4. 支持 Linux/GCC 平台

### 10.3 P2-01-C 前置条件

进入 P2-01-C（High-Frame Runtime Foundation）前，建议完成：
- P2-01-B.9（Native Lowering 扩展到 Array/Map/String/控制流）
- P2-01-B.10（Conformance Framework 增强 + 批量运行器）
- Full Runtime ABI Compatibility 验证（B5-GAP-02）
- 文档构建命令更新（B6-GAP-01）
- CI 配置检查更新（B6-GAP-03）
- GCC/Linux 构建验证（B6-GAP-02）

---

## 十一、交付物清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `compiler/native_compile_driver.tll` | 修改：参数化，支持命令行输入/输出文件 | ✅ |
| `scripts/cross-target-conformance.ps1` | 重写：完整的 6 步自动化 Conformance Framework | ✅ |
| `tests/native/01_basic.tll` | 新建：Conformance Case 01（arithmetic/comparison/bool） | ✅ |
| `tests/native/02_function.tll` | 新建：Conformance Case 02（function/params/nested call） | ✅ |
| `tests/native/03_io.tll` | 新建：Conformance Case 03（string/concat/mixed output） | ✅ |
| `tests/native/*.evidence.txt` | 自动生成：4 个 Evidence 文件 | ✅ |
| `docs/PHASE2-01-B.8-AUTOMATIC-CROSS-TARGET-CONFORMANCE.md` | 新建：完整报告 | ✅ |

---

## 十二、状态总结

| 项目 | 状态 |
|------|------|
| B8-01 参数化 Conformance Runner | ✅ 完成 |
| B8-02 3 个 Native Conformance Cases | ✅ 完成（01_basic, 02_function, 03_io） |
| B8-03 禁止手写 C | ✅ 全部由 native_lower.tll 自动生成 |
| B8-04 Bytecode/Native 同一源文件 | ✅ 全部满足 |
| B8-05 自动记录 Evidence | ✅ 4 个 Evidence 文件自动生成 |
| Conformance Cases 总数 | 4 个（含 cross_target_minimal） |
| 全部 PASS | ✅ 4/4 |
| stdout identical | ✅ 4/4 |
| exit code identical | ✅ 4/4 |
| MSVC 0 errors 0 warnings | ✅ 4/4 |
| Bootstrap/VM regression | ✅ 无倒退 |
| 历史 GAP 关闭 | ✅ 1 个（B7-GAP-02） |
| BLOCKER | 0 |
| Git Push | ❌ 禁止 |

---

## 十三、最终架构状态

```
                    TLL Language Semantics
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
       Bytecode Target           Native Target
       (tllc.tllbc)              (native_lower.tll)
              ↓                         ↓
          .tllbc                    .c (自动生成)
              ↓                         ↓
           tllvm.exe               MSVC (0 errors)
              ↓                         ↓
          运行输出                  运行输出
              └───────────┬───────────┘
                          ↓
                   自动比较一致性 ✅
                   stdout: IDENTICAL
                   exit code: IDENTICAL
                          ↓
                   自动记录 Evidence ✅
                   .evidence.txt

Conformance Cases: 4 个，全部 PASS ✅
  cross_target_minimal: function/let/arithmetic/io/string
  01_basic:            arithmetic/comparison/bool
  02_function:         function/params/nested call
  03_io:               string/concat/mixed output

Shared Runtime Core (runtime/):
  tll_runtime.h, value.c, arithmetic.c, io.c
  ← Bytecode 和 Native 共享同一套语义 ✅
```

**P2-01-B.8 完成后，TLL 拥有了一个可以持续约束 Native Backend 不偏离 TLL 语义的"自动尺子"。**

这不是增加 Native 功能，而是建立了质量保障机制：以后 Native 每增加一种能力，就往 Conformance Matrix 里增加测试，自动验证与 Bytecode 一致。

---

**报告结束。停止施工，等待架构裁决。**

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
