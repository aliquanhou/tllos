# TLL Frame Ownership Contract v1.0

**P0-RUNTIME-07-R2: Main Coroutine Frame Ownership / Double-Free Closure**

## 1. 核心原则

**一个 Frame 只能有一个最终释放责任。**

Frame 的生命周期必须严格遵循单一所有权原则，任何 Frame 不得被两个不同的代码路径同时声称拥有并释放。

## 2. Frame 所有权状态机

```
ALLOC (frame_pool_acquire: pool 获取或 calloc 新分配)
    ↓
ACTIVE (push_frame → vm->callStack[...])
    ↓
SUSPENDED (coroutine_save_current → co->callStack = vm->callStack)
    ↓
DEAD (函数返回 / OP_RET / 自然返回, frame 被 pop_frame 弹出)
    ↓
POOL (free_frame → frame_pool_release → g_frame_pool[...])
    ↓
DESTROY (pool 满时 frame_pool_release 真正 free)
```

## 3. 所有权规则

### 3.1 谁拥有 Frame？

- **ACTIVE 状态**：Frame 归 `vm->callStack` 所有，同时也是当前 coroutine 的 `callStack` 的一部分。
- **SUSPENDED 状态**：Frame 归所属 coroutine 的 `callStack` 所有。
- **DEAD 状态**：Frame 被 `pop_frame` 从 `vm->callStack` 弹出后，所有权转移给 `free_frame`，由 `free_frame` 负责最终释放（放入 pool 或真正 free）。
- **POOL 状态**：Frame 归 `g_frame_pool` 所有，等待复用。
- **DESTROY 状态**：Frame 被真正 free，所有权消失。

### 3.2 谁可以把 Frame 放入 Pool？

只有 `free_frame()` 可以调用 `frame_pool_release()` 将 Frame 放入 pool。

`free_frame()` 的调用者必须确保：
1. Frame 已经从 `vm->callStack` 中弹出（通过 `pop_frame`）。
2. 当前 coroutine 的 `callStackSize` 已经同步更新，不再包含该 Frame。
3. 没有其他 coroutine 的 `callStack` 仍然指向该 Frame。

### 3.3 谁可以从 Pool 回收？

只有 `frame_pool_acquire()` 可以从 `g_frame_pool` 中获取 Frame。

获取的 Frame 处于 ALLOC 状态，必须通过 `push_frame` 加入 `vm->callStack` 后才能使用。

### 3.4 谁负责最终 free？

只有 `frame_pool_release()` 在 pool 满时（`g_frame_pool_size >= FRAME_POOL_MAX`）可以真正 free Frame。

free 的顺序必须是：
1. `free(frame->registers)`
2. `free(frame->locals)`
3. `free(frame->argStack)`
4. `free(frame->tryStack)`
5. `free(frame)`

## 4. 关键同步点

### 4.1 push_frame 同步

```c
static void push_frame(TLLVM *vm, TLLFrame *frame) {
    // ... capacity check ...
    vm->callStack[vm->callStackSize++] = frame;
    // P0-RUNTIME-07-R2: 同步当前 coroutine 的 callStackSize
    if (vm->coroutineCount > 0 && vm->currentCoroutine >= 0 &&
        vm->currentCoroutine < vm->coroutineCount) {
        vm->coroutines[vm->currentCoroutine]->callStackSize = vm->callStackSize;
    }
}
```

**原因**：push_frame 后，Frame 加入 vm->callStack，当前 coroutine 的 callStackSize 必须同步增加，否则 coroutine_destroy 时会遗漏该 Frame。

### 4.2 pop_frame 同步

```c
static TLLFrame *pop_frame(TLLVM *vm) {
    if (vm->callStackSize <= 0) return NULL;
    TLLFrame *f = vm->callStack[--vm->callStackSize];
    // P0-RUNTIME-07-R2: 同步当前 coroutine 的 callStackSize
    if (vm->coroutineCount > 0 && vm->currentCoroutine >= 0 &&
        vm->currentCoroutine < vm->coroutineCount) {
        vm->coroutines[vm->currentCoroutine]->callStackSize = vm->callStackSize;
    }
    return f;
}
```

**原因**：pop_frame 后，Frame 从 vm->callStack 弹出，当前 coroutine 的 callStackSize 必须同步减少，否则 coroutine_destroy 时会再次释放该 Frame（double-free）。

### 4.3 OP_RET 后的所有权转移

```
OP_RET 执行:
    1. 保存返回值到调用者的寄存器
    2. pop_frame(vm) → Frame 从 vm->callStack 弹出
       → 当前 coroutine 的 callStackSize 同步减少
    3. free_frame(f) → Frame 被释放（放入 pool 或真正 free）
    4. Frame 所有权从 coroutine 转移到 free_frame
```

**关键**：pop_frame 同步后，coroutine 的 callStackSize 不再包含该 Frame，因此 coroutine_destroy 不会再次释放它。

### 4.4 函数自然返回后的所有权转移

与 OP_RET 相同，函数 pc 超出指令数时：
1. pop_frame(vm) → Frame 弹出，callStackSize 同步
2. free_frame(f) → Frame 释放

## 5. coroutine_destroy 的所有权边界

`coroutine_destroy(vm, idx)` 只释放仍归该 coroutine ownership 的 Frame：

```c
for (i = 0; i < co->callStackSize; i++) {
    if (co->callStack[i]) {
        free_frame(co->callStack[i]);
    }
}
```

**前提条件**：`co->callStackSize` 必须准确反映该 coroutine 当前拥有的 Frame 数量。

- 如果 coroutine 是 SUSPENDED 状态：callStackSize 是 coroutine_save_current 时保存的值，准确。
- 如果 coroutine 是 DEAD 状态（函数已返回）：callStackSize 必须是 0（因为 pop_frame 已经同步减少），coroutine_destroy 不会释放任何 Frame。
- 如果 coroutine 是当前正在运行的 coroutine：callStackSize 与 vm->callStackSize 一致。

## 6. 已修复的 Bug

### Bug: Main Coroutine Frame Double-Free

**根因**：
1. main 函数返回 → OP_RET → pop_frame 弹出 main frame → free_frame(main frame)
2. 但是 main coroutine 的 callStackSize 仍然是 1（没有同步）
3. allDead 处理 → coroutine_destroy(main) → 遍历 callStack（callStackSize = 1）→ 再次 free_frame(main frame)
4. 第二次 free_frame 访问 frame->closureEnv → heap-use-after-free

**触发条件**：
- 511 workers：511 + 1 main = 512 frames。main frame 被释放时 pool size = 511 < 512，所以 main frame 被添加到 pool（内存仍有效），第二次释放不会立即崩溃。
- 512 workers：512 + 1 main = 513 frames。main frame 被释放时 pool size = 512 >= 512，所以 main frame 被真正 free（内存已释放），第二次释放导致 heap-use-after-free → 崩溃。

**修复**：
在 push_frame 和 pop_frame 中同步当前 coroutine 的 callStackSize，确保 coroutine 的 callStack ownership 始终与 vm->callStack 一致。

## 7. 验证矩阵

| 场景 | 验证方法 | 结果 |
|------|---------|------|
| main coroutine OP_RET 后 frame 只释放一次 | 512 coroutine 测试 + ASan | ✅ PASS |
| worker coroutine normal return 后 frame 只释放一次 | 10K coroutine 测试 + ASan | ✅ PASS |
| yield/resume 后 suspended frame 不被提前释放 | coroutine_final_test, coroutine_lifecycle_test | ✅ PASS |
| coroutine_destroy 只处理仍归 coroutine ownership 的 frame | scope_07_coroutine, scope_10_complete_chain | ✅ PASS |
| frame pool 中 frame 再次 acquire/release 正常 | 512 + 10K 测试（pool 满后真正 free） | ✅ PASS |
| pool 满时真正 free 路径正常 | 512 测试（pool size = 512 时 main frame 真正 free） | ✅ PASS |
| 512 边界测试 | coroutine_512_test | ✅ PASS |
| 100K 完整 stress | coroutine_stress_test | ✅ PASS |
| MSVC ASan | 512 + 10K 测试 | ✅ 无内存错误 |
| Bootstrap 回归 | bootstrap-tllc.bat | ✅ PASS |
| Scope 回归 | scope_01-10 | ✅ 10/10 PASS |
| Coroutine regression | 5 个测试 | ✅ 5/5 PASS |

## 8. 已知限制

1. **Frame Pool 不是线程安全的**：当前 TLL VM 是单线程的，frame pool 不需要线程安全。未来引入多线程时需要加锁。
2. **FRAME_POOL_MAX = 512 是静态配置**：如果需要更大的 frame pool，可以修改这个常量。但 512 已经足够覆盖大多数场景，因为 pool 满时会真正 free frame，不会泄漏。
3. **coroutine_destroy 不检查 frame 是否在 pool 中**：由于 push_frame/pop_frame 同步了 callStackSize，coroutine_destroy 不会释放已经在 pool 中的 frame。这是设计保证，不是运行时检查。

## 9. 签署

- 施工执行：Agent A
- 架构审查：GPT-5.6 Luna
- 最终裁决：于秋鸿博士（待验收）
