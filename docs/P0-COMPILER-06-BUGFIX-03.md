# P0-COMPILER-06-BUGFIX-03
## Scheduler Timer-Wait 最小修复

**日期:** 2026-09-07
**分支:** p0-compiler-keyword-fix
**状态:** COMPLETE

---

## 1. BUG-A Root Cause

`coroutine_yield()` 的 pass 0 runnable 搜索循环包含当前 coroutine 自己。

搜索公式：`idx = (old + 1 + i) % coroutineCount`，i 范围 `0..coroutineCount-1`。

当 `i = coroutineCount - 1` 时，`idx = old`。

**结果：** 当 main coroutine 调用 yield()，且没有其他 runnable coroutine（只有 sleeping coroutine）时，搜索最终找到 main 自己（main 是 runnable 的），立即返回，**永远跳过已实现的 timer-wait 逻辑**。

## 2. Semantic Decision（已通过架构验收）

```
yield() = 主动让出执行权
  ├─ 有其他 runnable → round-robin 切换
  ├─ 无其他 runnable + 有 sleeping/IO → 进入 timer/IO wait
  └─ 无其他 runnable + 无 sleeping/IO → 立即返回
```

这是 **Runtime Bug，不是 Semantics GAP**。代码注释和 A2（sleep 能正常工作）都证明 yield() 应进入 timer-wait。

## 3. Minimal Patch

**修改文件:** `host/c/vm.c`
**修改函数:** `coroutine_yield()` (line 298-310)
**修改内容:** 在 pass 0 的 runnable 搜索中排除当前 coroutine 自己：

```c
for (i = 0; i < vm->coroutineCount; i++) {
    int idx = (old + 1 + i) % vm->coroutineCount;
    /* P0-COMPILER-06 BUG-A: in pass 0, exclude self so that
     * yield() with no other runnable coroutine enters timer/IO wait
     * instead of immediately selecting itself. */
    if (pass == 0 && idx == old) continue;
    if (coroutine_is_runnable(vm->coroutines[idx])) {
        next = idx;
        break;
    }
}
```

**为什么是最小修复：**
- 只添加一行条件判断
- pass 1 保持现有 fallback 语义（允许恢复自己）
- 不改变 scheduler 总体结构
- 不修改 coroutine 状态机
- 不修改 opcode / compiler / sleep 语义
- 有其他 runnable coroutine 时，搜索从 old+1 开始，会先找到其他 runnable，正常 round-robin 不受影响

## 4. A1/A2/A3 Before / After

| 测试 | Before | After |
|------|--------|-------|
| A1: 20ms sleeper + main 100次 yield() | ❌ FAIL (sleeper NOT woken) | ✅ PASS (woken after 2 yields) |
| A2: 20ms sleeper + main sleep(50) | ✅ PASS | ✅ PASS (保持) |
| A3: 10ms sleeper + main 200次 yield() | ❌ FAIL (sleeper NOT woken) | ✅ PASS (woken after 1 yield) |

## 5. P0-06 Full Regression

| 测试套件 | 结果 |
|---------|------|
| P0-06 Baseline async/concurrency | ✅ 19/19 PASS |
| BUG-A A1/A2/A3 | ✅ 全部 PASS |
| BUG-B B4-1~B4-4 | ✅ 全部 PASS |
| BUG-B probe_b (B1-B5) | ✅ 5/5 PASS |
| BUG-B probe_b3 (B3-1~B3-3) | ✅ 3/3 PASS |
| 新增 try/catch capture regression | ✅ 5/5 PASS |

## 6. Cross-Phase Regression

| 阶段 | 结果 |
|------|------|
| P0-01 Function Definition | ✅ 46/46 PASS |
| P0-02 Control Flow | 66/67（1 个已知 for-string 限制，非本次引入） |
| P0-03 Data & Type | ✅ 62/62 PASS |
| P0-05 Error / Resource | ✅ 23/23 PASS |
| BUG-B regression | ✅ 全部 PASS |

## 7. Compiler Bootstrap

- Generation 1: tllc_final → compile main.tll → tllc_gen1 ✅
- Generation 2: tllc_gen1 → compile main.tll → tllc_gen2 ✅
- Bootstrap 后编译器编译 A1/A2/A3: 全部 PASS ✅

## 8. No Regression Verification

- 无 runnable + 无 sleeper 场景：搜索排除自己后找不到 runnable，进入 IO/timer wait，ioCount=0 && sleepCount=0 → `return`（line 342），正确退出，不阻塞、不死循环。
- 多 coroutine round-robin：搜索从 old+1 开始，先找到其他 runnable，正常切换。
- sleep(0)：设置 wakeTime=now，pass 0 唤醒检查立即设置 wakeTime=0，等同于 yield。

## 9. CI

提交后触发 GitHub Actions CI。
- 三平台: Ubuntu / Windows / macOS
- 结果: 待 CI 运行完成后补充

## 10. 最终状态

| 项目 | 状态 |
|------|------|
| BUG-A Scheduler Timer-Wait | ✅ CLOSED / FIXED |
| BUG-B Closure × try/catch capture | ✅ CLOSED / FIXED |
| BUGFIX-02 | ✅ SEALED |
| BUGFIX-03 | ✅ COMPLETE |
| P0-06 Async / Concurrency | 🟢 READY FOR SEAL |
