# P0-COMPILER-06-BUGFIX-02 — Closure Capture × try/catch Codegen Fix

**Date:** 2026-09-07
**Branch:** p0-compiler-keyword-fix
**Status:** COMPLETE

---

## A. 修复前 (BEFORE)

| Test | Result |
|------|--------|
| B4-1: function + coroutine + try/catch + closure capture | ❌ FAIL (`result` = "initial") |
| B4-3: function + coroutine + closure capture (no try/catch) | ✅ PASS (`result` = "modified") |

**现象：** 嵌套 coroutine/closure 内部的 try/catch 代码块引用外部局部变量时，capture analysis 未正确识别，导致变量未被 box、closure captureCount=0、赋值被编译为 OP_STORE_VAR（局部变量）而非 OP_SET_UPVALUE（共享 upvalue）。

---

## B. First Divergence

**文件：** `compiler/codegen.tll`
**函数：** `cg_collectIdentsInExpr()` (line 226-262) 和 `cg_collectFnExprsInExpr()` (line 274-302)
**具体条件：** AST traversal 的 keys 列表中，Try 节点字段名错误

### Try 节点 AST 结构 (parser.tll line 320-324)
```
node.block         = try body
node.catchParam    = catch parameter name
node.catchBlock    = catch body
node.finallyBlock  = finally body
```

### 修复前的 keys 列表 (codegen.tll line 253-255)
```
"body", "elseBody", "statements", ..., "catchBody", "finallyBlock"
```

### 问题
1. ❌ 缺少 `"block"` — try 体字段是 `block`，不是 `body`
2. ❌ `"catchBody"` ≠ `"catchBlock"` — catch 体字段名不匹配
3. ✅ `"finallyBlock"` 正确 — finally 体能被正确递归

**结果：** try 体和 catch 体内的变量引用完全不会被 capture analysis 收集，finally 体可以。

---

## C. Patch

### 修改内容
在两个 AST traversal 函数的 keys 列表中：
1. 添加 `"block"`
2. 将 `"catchBody"` 改为 `"catchBlock"`

### 修改文件
- `compiler/codegen.tll` (2 处 keys 列表)

### 为什么这是最小修复
- 只修 traversal，不修 runtime
- 没有增加新的全局特殊规则（如 `if (try) force capture`）
- 保持一般性：任意 nested function/coroutine 中，通过 try/catch/finally 引用外部变量，都进入正常 capture analysis
- 不需要修改 VM/runtime/OP_SPAWN/closure 机制

### 为什么不需要修改 VM/runtime
- 根因在 compiler 的 AST traversal 字段名错误
- VM 的 closure/upvalue 机制本身是正确的（无 try/catch 时工作正常）
- OP_SPAWN 正确传递 closure env（已验证）
- 修复 compiler 后，正确的字节码自然生成，VM 无需改动

---

## D. Regression

### BUG-B 相关测试 (全部 PASS)
| Test | Result |
|------|--------|
| probe_b_closure_coroutine.tll (B1-B5) | ✅ 5/5 PASS |
| probe_b3_simplified_closure.tll (B3-1~B3-3) | ✅ 3/3 PASS |
| probe_b4_try_catch_closure.tll (B4-1~B4-4) | ✅ 4/4 PASS |
| bugb_test1_trycatch.tll (原 FAIL) | ✅ FIXED ("modified") |
| bugb_test2_notrycatch.tll (原 PASS) | ✅ 保持 PASS |

### 新增回归测试 (5/5 PASS)
`tests/compiler/regression_try_catch_capture.tll`
1. try body writes external variable ✅
2. catch body writes external variable ✅
3. try body reads external variable ✅
4. multiple captured variables in try/catch ✅
5. module-level try/catch closure capture ✅

### P0-06 Baseline
- probe_async_concurrency.tll: ✅ 19/19 PASS

### P0-01 ~ P0-05 回归
- P0-02 Control Flow: 66/67 (1 个已知失败: for string 遍历限制，非本次引入)
- P0-03 Data & Type: ✅ 62/62 PASS
- P0-05 Error / Resource: ✅ 23/23 PASS

### Compiler Bootstrap
- 新编译器编译自身 → 生成 tllc_bootstrap.tllbc ✅
- Bootstrap 编译器编译 B4-1 → 输出 "modified" ✅
- 两代编译后修复仍然生效 ✅

### BUG-A (未修改，保持预期状态)
- A1 FAIL (sleeper not woken after 100 yields) — 预期，BUG-A 保持 BLOCKED
- A2 PASS (control: main sleep()) — 保持
- A3 FAIL (10ms sleeper not woken) — 预期

---

## E. CI

提交后触发 GitHub Actions CI，全部通过。

| Workflow | Run ID | 结果 |
|----------|--------|------|
| CI (三平台 native-build-test) | 34115644348 | ✅ SUCCESS |
| P1-01 Secure Random Tests | 34115641777 | ✅ SUCCESS |

**三平台结果：**
- Ubuntu (ubuntu-latest): ✅ success
- Windows (windows-latest): ✅ success
- macOS (macos-latest): ✅ success

CI URL: https://github.com/aliquanhou/tllos/actions/runs/34115644348

---

## F. 提交信息

```
fix(codegen): preserve nested captures across try/catch

Root cause: cg_collectIdentsInExpr() and cg_collectFnExprsInExpr()
AST traversal keys list had wrong field names for Try nodes:
- missing "block" (try body field is "block", not "body")
- "catchBody" should be "catchBlock"

This caused variables referenced inside try/catch blocks to be
invisible to closure capture analysis, resulting in:
- no OP_BOX_LOCAL for captured variables
- closure captureCount=0
- assignments compiled as OP_STORE_VAR (local) instead of OP_SET_UPVALUE

Fix: add "block" and rename "catchBody" to "catchBlock" in both
traversal functions. Minimal traversal fix, no runtime changes.

Tests:
- BUG-B B4-1: FAIL -> PASS
- All existing closure/coroutine tests: PASS
- New regression: regression_try_catch_capture.tll 5/5 PASS
- P0-06 baseline 19/19 PASS
- Compiler bootstrap: PASS
```

---

## G. 已知限制

- BUG-A Scheduler Timer-Wait 保持 BLOCKED，未在本次修复中处理
- P0-02 Control Flow 6.4 (for string 遍历) 保持已知 PARTIAL，非本次引入
- switch/match 保持 MISSING，非本次范围
- 字符串乘法 `"x" * N` 保持 UNKNOWN，非本次范围

---

## H. 结论

**BUG-B BEFORE: ❌ FAIL → AFTER: ✅ PASS**

修复了 compiler codegen 中 AST traversal 字段名错误，使 try/catch/finally 块内的变量引用能够正确进入 closure capture analysis。最小修复，仅修改 compiler，不涉及 VM/runtime/OP_SPAWN/closure 机制。

**等待总指挥审计 BUGFIX-02 报告。**
