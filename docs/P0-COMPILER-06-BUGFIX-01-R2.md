# P0-COMPILER-06-BUGFIX-01-R2 — Root Cause Evidence Completion

**Date:** 2026-09-07
**Branch:** p0-compiler-keyword-fix
**Status:** BUG-A Semantic Gate Complete | BUG-B Root Cause CONFIRMED

---

## BUG-A: Scheduler Timer-Wait — Semantic Confirmation

### Language Contract Analysis

**Q1: yield 是否应该在没有 runnable coroutine 时进入 timer-wait？**

vm.c `coroutine_yield()` 注释（line 273-278）：
> "Yield: save current, destroy if dead, round-robin to next runnable.
> P0-15.16: IO-aware - if no runnable coroutines, collect WAITING_IO fds,
> call select() with timeout from earliest sleeper, wake ready fds."

设计意图**暗示**应该等待 sleeper，但关键歧义：
- "no runnable coroutines" 是否包括**当前 coroutine 自己**？
- 当前实现：环形搜索 `(old+1+i) % count`，绕回自己时认为找到 runnable，**不进入 wait**

**Q2: sleeping coroutine 到期是否应该自动成为 runnable？**

✅ **是**。`coroutine_yield()` Pass 0 开头有 "Wake expired sleepers" 逻辑：
```c
if (co->wakeTime > 0 && co->wakeTime <= now) {
    co->wakeTime = 0;  // becomes runnable
}
```
`coroutine_is_runnable()` 返回 `wakeTime == 0 && waitingFd < 0 && waitingChannel == NULL`。

**Q3: 如果当前 coroutine 是唯一 runnable，yield() 的预期行为是什么？**

| 维度 | 当前实现 | 可能的预期 |
|------|---------|-----------|
| 行为 | 立即恢复自己（环形搜索绕回） | 等待 sleeper/IO 到期 |
| 语义 | 非阻塞 "cooperative yield" | 阻塞 "yield until work available" |
| 注释支持 | 无明确说明 | "if no runnable coroutines, call select()" 暗示 |

**Q4: A1/A3 的原始测试预期是否符合现有语言语义？**

❌ **不符合**。现有测试证据：
- `tests/coroutine_sleep_test.tll`：主协程使用 `coroutine.sleep(50)` 等待 sleeper，**不是** yield() 循环
- 所有既有 coroutine 测试：yield() 用于多个 runnable coroutine 之间的轮询切换，**不用于**等待 sleeping coroutine

A1/A3 测试期望 "yield() 循环能等待 sleeper 到期"，这与现有语言用法**不一致**。

### Conclusion: SEMANTIC CONTRACT UNCLEAR

- 注释暗示 yield() 应等待 sleeper，但"no runnable"是否包括自己未定义
- 现有实现和测试都遵循 yield() 非阻塞
- A1/A3 测试预期与现有语义不符
- **需要总指挥裁决 yield() 的语义契约**，才能决定是否修复

### First Divergence (vm.c)

`coroutine_yield()` line 310-320（环形搜索）：
```c
for (i = 0; i < vm->coroutineCount; i++) {
    int idx = (old + 1 + i) % vm->coroutineCount;
    if (coroutine_is_runnable(vm->coroutines[idx])) {
        next = idx;  // wraps back to 'old' (self) when no other runnable
        break;
    }
}
```
条件：`idx == old && coroutine_is_runnable(self)` → 找到自己 → 恢复自己 → **跳过 wait 逻辑**。

### Evidence

- A1 FAIL trace（501行调试输出）：主协程每次 yield 都 `FOUND runnable: next=0`（自己），从不进入 `ONLY SLEEPERS` / `CALLING Sleep`
- A2 PASS 对照：主协程调用 sleep() 后自己也变成 non-runnable → 进入 wait 逻辑 → sleeper 被正确唤醒
- 加 fprintf 调试输出 → 执行变慢 → 系统时间自然流逝到 sleeper wakeTime → A1/A3 从 FAIL 变 PASS（时序敏感，非逻辑修复）

---

## BUG-B: Closure × Coroutine × try/catch — Root Cause CONFIRMED

### Runtime Identity Differential (v2 Instrumentation)

对 `bugb_test1_trycatch.tll`（FAIL）和 `bugb_test2_notrycatch.tll`（PASS）进行完整运行时追踪，锁定 7 个状态变量：

| 状态变量 | Test1 (try/catch) FAIL | Test2 (no try/catch) PASS |
|---------|------------------------|---------------------------|
| `result` local slot | 1 | 1 |
| **OP_BOX_LOCAL for result** | ❌ **缺失** | ✅ localSlot=1 → upvalueSlot=0 |
| **coroBody captureCount** | **0** | **1** |
| shared upvalue object | ❌ 无 | ✅ upval[0]=0x...1F2610 |
| coroBody closure env | 0x...3710 (empty) | 0x...8AB0 (1 capture) |
| **`result="modified"` 指令** | **OP_STORE_VAR** slot=1 (coroutine自己的局部变量) | **OP_SET_UPVALUE** slot=0 (共享upvalue) |
| 最终 result 值 | "initial" (未修改) | "modified" (正确修改) |

### First Divergence: Codegen Capture Analysis Phase

**分叉点：`cg_compileFunction()` 的 capture 分析（codegen.tll line 666-690）**

```
testWithTryCatch 函数编译
  ↓
cg_collectCapturedByNested(fnDecl)  ← 收集被嵌套函数捕获的变量
  ↓
  无 try/catch: 识别到 coroBody 引用了 result → result 加入 capturedByNested
  有 try/catch: ❌ 未识别到 result 被捕获 → capturedByNested 为空
  ↓
result 未加入 cg_upvalueMap
  ↓
无 OP_BOX_LOCAL (codegen.tll line 870-878 条件不满足)
  ↓
coroBody OP_CLOSURE captureCount=0
  ↓
无 shared upvalue
  ↓
result="modified" 编译为 OP_STORE_VAR (普通局部变量赋值)
  ↓
coroutine 中修改的是自己 frame 的局部变量，与外部函数无关
  ↓
外部函数 result 保持 "initial"
```

### Root Cause

**`cg_collectCapturedByNested()` 或其调用的 `cg_collectReferencedNames()` 在处理嵌套函数内部的 try/catch 块时，递归遍历存在缺陷，导致 try/catch 块内的变量引用未被识别为"对外部变量的捕获"。**

具体嫌疑位置：
- `cg_collectReferencedNames()` (codegen.tll line 330-345)：调用 `cg_collectIdentsInExpr(fnDecl.body, allIdents)`
- `cg_collectIdentsInExpr()` (codegen.tll line 226-262)：keys 列表包含 `"catchBody"` 和 `"finallyBlock"`，**表面上**支持 try/catch 递归
- 但 `cg_collectCapturedByNested()` (line 347-) 遍历嵌套函数时，可能在某个环节没有正确传递 try/catch 块的 AST 结构

**需要进一步定位具体是哪个函数的哪一行递归逻辑缺失**（当前已锁定到 codegen capture 分析阶段，精确到函数级别）。

### OP_SPAWN Hypothesis Verification: OP_SPAWN is NOT root cause

```
function value.env (coroBody's env)  ==  expected closure env?
```

- Test1: fnVal.env = 0x...3710，这是 coroBody 自己的 closure env（虽然是空的）
- Test2: fnVal.env = 0x...8AB0，这是 coroBody 自己的 closure env（包含 1 个 capture）

**结论：OP_SPAWN 正确地从函数值获取 env 并传递给 coroutine_create。问题不在于 OP_SPAWN，而在于 coroBody 的 closure env 本身就是空的（captureCount=0），因为 codegen 阶段没有正确识别 result 被捕获。**

Function + Coroutine + Closure（无 try/catch）组合已 PASS，证明 OP_SPAWN 和 closure 构造的基础逻辑正确。缺陷仅在 try/catch 存在时触发。

### Proof

1. **编译期证据**：两个测试的唯一区别是 try/catch 块，其他代码完全相同
2. **运行时证据**：v2 instrumentation 完整追踪了 OP_BOX_LOCAL → OP_CLOSURE → OP_SPAWN → OP_SET_UPVALUE/OP_STORE_VAR 的完整状态链
3. **差分证据**：First Divergence 精确锁定在 codegen capture 分析阶段（OP_BOX_LOCAL 缺失是第一个可观测的分叉）
4. **排除证据**：OP_SPAWN 不是根因（env 传递正确，问题在 env 内容为空）

---

## Summary

| Bug | Phase | Result | Status |
|-----|-------|--------|--------|
| A: Scheduler Timer-Wait | Semantic Confirmation | SEMANTIC CONTRACT UNCLEAR | 🟡 等待总指挥裁决语义 |
| B: Closure × Coroutine × try/catch | Root Cause | **CONFIRMED** — codegen capture 分析在 try/catch 块存在时失败，导致 result 未被 box/捕获 | 🔴 根因已定位，等待批准修复 |

## Next Steps (pending总指挥裁决)

- **BUG-A**：总指挥裁决 yield() 语义契约后，决定是修复实现、修改测试、还是补充文档
- **BUG-B**：总指挥批准后，进入 BUGFIX-02 阶段，精确定位 `cg_collectCapturedByNested`/`cg_collectReferencedNames` 中 try/catch 递归缺陷的具体代码行，然后最小修复 + 全量回归

**STOP. 不修改任何代码。等待总指挥裁决。**
