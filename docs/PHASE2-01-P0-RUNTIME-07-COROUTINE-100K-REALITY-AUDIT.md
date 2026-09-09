# P0-RUNTIME-07 Coroutine 100K Root-Cause Closure — Reality Audit Report

**施工执行：** Agent A
**架构审查：** GPT-5.6 Luna
**最终裁决：** 于秋鸿博士（待验收）

**状态：** Reality Audit 完成，根因范围已定位，待精确修复

---

## 1. Root-Cause Statement

Coroutine 100K Stress Test 在 Ubuntu 24.04、macOS、Windows 三平台一致崩溃。

**根因范围：** Frame Pool 在达到 `FRAME_POOL_MAX=512` 后，新释放的 frame 会走"真正 free"路径（`free(frame->registers)` 等），该路径存在内存损坏问题。

**关键证据：** 511 个 worker coroutine 测试通过，512 个崩溃。512 worker + 1 main = 513 frames，第 513 个 frame 触发 pool 满。

---

## 2. Reproducer

### 最小复现测试

**文件：** `tests/coroutine_512_test.tll`

```tll
io.println("=== 512 immediate-return ===")
let completed = 0
fn worker() {
    completed = completed + 1
}
io.println("Spawning 512...")
let i = 0
while i < 512 {
    coroutine.spawn(worker)
    i = i + 1
}
io.println("Spawn done, yielding...")
let guard = 0
while completed < 512 && guard < 3000 {
    coroutine.yield()
    guard = guard + 1
}
io.println("completed=" + convert.toString(completed) + " guard=" + convert.toString(guard))
io.println("=== DONE ===")
```

### 阈值验证矩阵

| Worker 数量 | 结果 | 说明 |
|------------|------|------|
| 100 | ✅ PASS | 远低于 FRAME_POOL_MAX |
| 500 | ✅ PASS | 低于 FRAME_POOL_MAX |
| 510 | ✅ PASS | 低于 FRAME_POOL_MAX |
| 511 | ✅ PASS | 511+1(main)=512 ≤ FRAME_POOL_MAX |
| **512** | **❌ CRASH** | **512+1(main)=513 > FRAME_POOL_MAX，触发真正 free** |
| 600 | ❌ CRASH | 触发真正 free |
| 750 | ❌ CRASH | 触发真正 free |
| 1000 | ❌ CRASH | 触发真正 free |

---

## 3. CI / 平台失败详情

### Ubuntu 24.04 (CI Run 34318184247, Job 102358769317)

- **Exit code:** 139 (SIGSEGV, Segmentation Fault)
- **运行时间:** 约 5 分 30 秒 (06:20:43 → 06:26:14)
- **VM output log:** 空（进程崩溃后输出未 flush）
- **失败步骤:** Coroutine 100K Stress Test (Linux/macOS)

### macOS (CI Run 34318184247, Job 102358769307)

- **Exit code:** 139 (SIGSEGV)
- **运行时间:** 约 1 分 2 秒 (06:20:39 → 06:21:41)
- **VM output log:** 空
- **失败步骤:** Coroutine 100K Stress Test (Linux/macOS)

### Windows (本地复现)

- **Exit code:** -1073740940 (STATUS_HEAP_CORRUPTION)
- **运行时间:** 约 5 分 26 秒 (325838ms)
- **测试文件:** `tests/coroutine_stress_test.tll`

---

## 4. Frame Pool 机制分析

### 相关代码位置

**文件：** `host/c/vm.c`

```c
#define FRAME_POOL_INITIAL 64
#define FRAME_POOL_MAX 512  // line 51

static TLLFrame **g_frame_pool = NULL;
static int g_frame_pool_size = 0;
static int g_frame_pool_capacity = 0;

static TLLFrame *frame_pool_acquire(void) {
    if (g_frame_pool_size > 0) {
        return g_frame_pool[--g_frame_pool_size];
    }
    // 分配新 frame，包含 registers(4096), argStack(64), tryStack(16)
    ...
}

static void frame_pool_release(TLLFrame *frame) {
    if (g_frame_pool_size >= FRAME_POOL_MAX) {
        /* Pool full: actually free */
        free(frame->registers);   // line 77
        free(frame->locals);      // line 78
        free(frame->argStack);    // line 79
        free(frame->tryStack);    // line 80
        free(frame);              // line 81
        return;
    }
    // 添加到 pool
    ...
}
```

### 触发条件

当 `g_frame_pool_size >= 512` 时，新释放的 frame 走"真正 free"路径。

在 512 worker + 1 main 的场景中：
- 前 512 个被释放的 frame 被添加到 pool
- 第 513 个被释放的 frame 触发 pool 满，走真正 free 路径
- 真正 free 路径中存在内存损坏

---

## 5. 验证实验

### 实验 1：增大 FRAME_POOL_MAX

**修改：** `#define FRAME_POOL_MAX 1024`

**结果：** 512 worker 测试 ✅ PASS (192ms)

**结论：** 确认问题与 FRAME_POOL_MAX 阈值相关，增大 pool 后不触发真正 free 路径，测试通过。

### 实验 2：减小 FRAME_POOL_MAX

**修改：** `#define FRAME_POOL_MAX 1`

**结果：** 100 worker 测试 ❌ CRASH (STATUS_ACCESS_VIOLATION, 2337ms)

**结论：** 减小 pool 后更快触发真正 free 路径，确认问题与真正 free 路径相关。

### 实验 3：511 worker 边界测试

**结果：** 511 worker 测试 ✅ PASS (49ms)

**结论：** 511+1(main)=512 ≤ FRAME_POOL_MAX，不触发真正 free 路径，测试通过。

---

## 6. 待精确定位的问题

目前已确认问题发生在 `frame_pool_release()` 的真正 free 路径中，但尚未精确定位是哪个 `free()` 调用导致崩溃：

1. `free(frame->registers)` — 4096 个 TLLValue 的数组
2. `free(frame->locals)` — 局部变量数组
3. `free(frame->argStack)` — 参数栈数组
4. `free(frame->tryStack)` — try 栈数组
5. `free(frame)` — frame 结构体本身

**可能的原因：**
- Double-free（同一个 frame 被释放两次）
- Use-after-free（frame 被释放后仍被访问）
- Heap overflow（frame 的某个数组越界写入，破坏堆元数据）
- frame->locals 为 NULL 时 free(NULL) 应该是安全的，但需要确认

---

## 7. 未修改的内容

- ❌ 未删除任何测试
- ❌ 未降低任何断言
- ❌ 未修改 expected result
- ❌ 未降低测试规模
- ❌ 未修改 coroutine 语义
- ❌ 未修改 scheduler 逻辑

---

## 8. 下一步建议

1. **精确定位崩溃点：** 在 `frame_pool_release()` 的每个 `free()` 前后添加调试输出，确认是哪个 free 导致崩溃
2. **检查 double-free：** 确认同一个 frame 是否被 `free_frame()` 调用两次
3. **检查 use-after-free：** 确认 frame 被释放后是否仍被 `vm->callStack` 或其他地方引用
4. **检查 heap overflow：** 确认 frame 的 registers/locals/argStack 数组是否有越界写入
5. **最小修复：** 定位根因后进行最小修复
6. **验证：** 重新运行 512/1000/100K 测试，确认修复有效
7. **CI 验证：** 触发 GitHub CI，确认三平台通过

---

## 9. Git 状态

- **当前分支：** `feature/P0-RUNTIME-07-coroutine-100k-root-cause`
- **基线：** `8190ede`
- **已修改文件：** 无（Reality Audit 阶段，未提交修复）
- **临时调试文件：** `tests/coroutine_100_test.tll`、`tests/coroutine_500_test.tll`、`tests/coroutine_510_test.tll`、`tests/coroutine_511_test.tll`、`tests/coroutine_512_test.tll`、`tests/coroutine_600_test.tll`、`tests/coroutine_750_test.tll`、`tests/coroutine_1000_test.tll`、`tests/coroutine_stress_test1_only.tll`（未提交，待清理）
- **Commit SHA：** 无（尚未提交修复）

---

**施工完成，等待架构师独立审查与最终验收。**
