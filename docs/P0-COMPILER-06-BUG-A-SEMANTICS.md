# P0-COMPILER-06-BUG-A-SEMANTICS
## coroutine.yield / sleep / wait / scheduler 语义契约裁决

**日期:** 2026-09-07
**分支:** p0-compiler-keyword-fix
**HEAD:** 60c7b75
**状态:** SEMANTIC AUDIT COMPLETE（未修改任何代码）

---

## 1. Reality Audit — 当前真实实现审计

### 1.1 暴露的 API（codegen.tll 特殊处理，直接编译为 opcode）

| TLL API | Opcode | 实现位置 |
|---------|--------|---------|
| `coroutine.yield()` | OP_YIELD (55) | vm.c:1051-1057 |
| `coroutine.spawn(fn, args...)` | OP_SPAWN (54) | vm.c:1014-1049 |
| `coroutine.sleep(ms)` | OP_SLEEP | vm.c:1058-1080 |
| `coroutine.waitRead(fd)` | OP_WAIT_READ | vm.c:1081-1100 |
| `coroutine.waitWrite(fd)` | OP_WAIT_WRITE | vm.c:1101-1116 |
| `coroutine.waitChannel(channelMap)` | OP_WAIT_CHANNEL | vm.c:1117-1133 |
| `coroutine.wakeChannel(channelMap)` | builtin idx 144 | builtin.c:1868-1871 |

**不存在 `coroutine.wait()` 通用 API。** wait 是通过 waitRead/waitWrite/waitChannel 实现的。

### 1.2 coroutine_is_runnable() 判定规则 (vm.c:241-247)

```
runnable = NOT dead AND wakeTime == 0 AND waitingFd == 0 AND waitingChannel == NULL
```

| 状态 | runnable? |
|------|-----------|
| 正常活跃 | ✅ YES |
| dead (state==2) | ❌ NO |
| sleeping (wakeTime > 0) | ❌ NO |
| waiting IO (waitingFd > 0) | ❌ NO |
| waiting channel | ❌ NO |

### 1.3 coroutine_yield() 核心逻辑 (vm.c:270-395)

```
1. 保存当前 coroutine 状态 (old = currentCoroutine)
2. 如果当前 dead，销毁
3. 两次 pass (pass=0, pass=1):
   a. 唤醒过期 sleepers (wakeTime <= now → wakeTime=0)
   b. 环形搜索下一个 runnable:
      for i in 0..coroutineCount-1:
          idx = (old + 1 + i) % coroutineCount
          if coroutine_is_runnable(coroutines[idx]):
              next = idx; break
   c. 如果找到 next → 恢复 next，返回
   d. 如果没找到:
      - pass==0: 进入 IO/timer wait
        * 收集 IO fds 和 sleepers
        * ioCount==0 && sleepCount==0 → return (退出)
        * ioCount>0 → select() 等待 (带 timeout=minWake-now)
        * 只有 sleepers → Sleep/usleep 阻塞到 minWake
        * loop back to pass 1
      - pass==1: 恢复第一个 alive coroutine (避免 crash)
```

### 1.4 关键发现：环形搜索包含当前 coroutine 自己

搜索公式：`idx = (old + 1 + i) % coroutineCount`，i 从 0 到 `coroutineCount-1`。

当 `i = coroutineCount - 1` 时：`idx = (old + 1 + coroutineCount - 1) % coroutineCount = old`。

**因此搜索范围包含 old 自己。** 当没有其他 runnable coroutine 时，搜索最终会回到 old 自己。

---

## 2. A1/A2/A3 重新复现与 First Divergence

### 2.1 复现结果

| 测试 | 结果 | 说明 |
|------|------|------|
| A1: 20ms sleeper + main 100次 yield() | ❌ FAIL | sleeper NOT woken |
| A2: 20ms sleeper + main sleep(50) | ✅ PASS | sleeper woken via main sleep |
| A3: 10ms sleeper + main 200次 yield() | ❌ FAIL | sleeper NOT woken |

### 2.2 A1 执行时序分析（main=idx0, sleeper=idx1）

```
初始: main(runnable), sleeper(sleeping, wakeTime=now+20)

main 调用 yield():
  old = 0
  Pass 0:
    唤醒过期 sleepers: sleeper wakeTime=now+20 > now → 不唤醒
    搜索 runnable:
      i=0: idx=1 (sleeper) → wakeTime>0 → not runnable
      i=1: idx=0 (main) → wakeTime=0, not dead → RUNNABLE!
    找到 main 自己 → 恢复 main → 返回

  ⚠️ 永远不会进入 "no runnable → IO/timer wait" 逻辑
  ⚠️ sleeper 永远不会被唤醒（因为 main 每次 yield 都立即恢复自己）

结果: 100 次 yield 后，a1_done 仍然 false → FAIL
```

### 2.3 A2 为什么能成功（对照组）

```
初始: main(runnable), sleeper(sleeping, wakeTime=now+20)

main 调用 sleep(50):
  设置 main.wakeTime = now + 50 → main 变成 NOT runnable
  调用 yield():
    old = 0
    Pass 0:
      唤醒过期 sleepers: sleeper wakeTime=now+20 > now → 不唤醒
      搜索 runnable:
        i=0: idx=1 (sleeper) → wakeTime>0 → not runnable
        i=1: idx=0 (main) → wakeTime>0 → not runnable
      没有 runnable → 进入 IO/timer wait
        ioCount=0, sleepCount=2 → 只有 sleepers
        minWake = min(now+20, now+50) = now+20
        Sleep(20ms) 阻塞宿主线程
      Pass 1:
        唤醒过期 sleepers: sleeper wakeTime=now+20 <= now → wakeTime=0 → RUNNABLE
        搜索 runnable: idx=1 (sleeper) → runnable → 恢复 sleeper
      sleeper 运行完成 → 设置 a2_done=true → dead
      回到 main (main 的 sleep 50ms 可能还没到期，但 a2_done 已 true)

结果: a2_done = true → PASS
```

### 2.4 First Divergence 确认

**位置:** `vm.c:coroutine_yield()` pass 0 的 runnable 搜索循环 (line 298-306)

**问题:** 搜索范围包含当前 coroutine `old` 自己。当 `old` 是 runnable 的（yield() 不会设置自己为 not runnable），且没有其他 runnable coroutine 时，搜索最终找到 `old` 自己并立即返回，**跳过 timer-wait 逻辑**。

**对比:** `sleep()` 先设置自己的 wakeTime>0（使自己 not runnable），然后调用 yield()，此时搜索不会找到自己，才能进入 timer-wait。

---

## 3. Semantic Decision — 建议的正式语言契约

### 3.1 核心语义裁决

| API / 状态 | 正式语义 |
|-----------|---------|
| `coroutine.yield()` | **主动让出执行权**。如果存在其他 runnable coroutine，切换到下一个；如果没有其他 runnable coroutine，但存在 sleeping coroutine 或 IO-waiting coroutine，**应进入 timer/IO wait**（阻塞到最近的唤醒事件）；如果没有任何其他活跃 coroutine，立即返回继续执行。 |
| `coroutine.sleep(ms)` | **当前 coroutine 睡眠 ms 毫秒**。设置 wakeTime=now+ms（使自己 not runnable），然后 yield。scheduler 会在到期时自动唤醒。 |
| `coroutine.waitRead(fd)` | **当前 coroutine 等待 fd 可读**。设置 waitingFd 和 waitingEvents=READ（使自己 not runnable），然后 yield。scheduler 通过 select() 唤醒。 |
| `coroutine.waitWrite(fd)` | **当前 coroutine 等待 fd 可写**。同上，waitingEvents=WRITE。 |
| `coroutine.waitChannel(ch)` | **当前 coroutine 等待 channel 消息**。设置 waitingChannel（使自己 not runnable），然后 yield。需通过 `coroutine.wakeChannel(ch)` 显式唤醒。 |
| `runnable coroutine` | 满足：NOT dead AND wakeTime==0 AND waitingFd==0 AND waitingChannel==NULL |
| `sleeping coroutine` | wakeTime > 0，到期后自动变为 runnable |
| `main coroutine` | 与其他 coroutine 地位相同，受相同调度规则约束 |

### 3.2 三个关键 Case 裁决

#### Case A: 当前 coroutine yield + 存在其他 runnable coroutine
**裁决:** 切换到其他 runnable coroutine（round-robin）。
**当前实现:** ✅ 正确。搜索从 old+1 开始，会先找到其他 runnable。

#### Case B: 当前 coroutine yield + 没有其他 runnable + 存在 sleeping coroutine
**裁决:** **应进入 timer-wait**，阻塞到最近的 sleeper 到期，然后唤醒它。
**当前实现:** ❌ 错误。搜索找到 old 自己（old 是 runnable 的），立即返回，跳过 timer-wait。
**这就是 BUG-A 的根因。**

#### Case C: 当前 coroutine yield + 没有其他 runnable + 没有 sleeping + 没有 IO
**裁决:** 立即返回继续执行当前 coroutine（没有其他事情可做）。
**当前实现:** ⚠️ 部分正确。搜索找到 old 自己并返回，效果相同。但如果严格按照 Case B 的语义，应该先确认没有任何等待中的 coroutine，再返回。

### 3.3 sleep(0) 语义

**裁决:** `sleep(0)` 设置 wakeTime=now+0=now。在下一次 scheduler 循环中，`wakeTime <= now` 会被立即唤醒（wakeTime=0）。效果等同于 yield()，但会经历一次完整的 scheduler 循环（包括唤醒过期 sleepers 的检查）。

**当前实现:** ✅ 正确。`wakeTime = now + 0 = now`，pass 0 的唤醒检查 `wakeTime <= now` 会立即设置 wakeTime=0。

### 3.4 scheduler 是否应该因为 timer 等待而阻塞宿主线程？

**裁决:** 是的。当所有 coroutine 都在等待（sleeping 或 IO-waiting）时，scheduler 应该阻塞宿主线程（通过 Sleep/usleep/select），直到有事件发生。这是协作式调度的标准行为，避免忙等（busy-waiting）消耗 CPU。

**当前实现:** ✅ 正确（在能进入 timer-wait 的路径上）。只有 sleepers 时用 Sleep/usleep，有 IO 时用 select。

---

## 4. 语义缺口判定

### 4.1 这是 Language Semantics GAP 还是 Runtime Bug？

**判定: 这是 Runtime Bug，不是 Semantics GAP。**

理由：
1. `coroutine.yield()` 的注释 (vm.c:264-268) 明确写了：
   - "Yield: save current, destroy if dead, round-robin to next runnable."
   - "P0-15.16: IO-aware - if no runnable coroutines, collect WAITING_IO fds, call select() with timeout from earliest sleeper, wake ready fds."
2. 代码中已经实现了完整的 IO/timer wait 逻辑 (line 313-382)，包括只有 sleepers 时的 Sleep/usleep。
3. 问题只是 runnable 搜索循环包含了 old 自己，导致在"没有其他 runnable 但有 sleeper"时，搜索找到 old 自己并提前返回，**永远无法到达已经实现好的 timer-wait 逻辑**。
4. 设计意图（注释）与 A2（sleep 能正常工作）都证明：yield() 在没有其他 runnable 时应该进入 timer-wait。

因此，**语义是明确的，实现有 Bug。** 不需要重新设计语义，只需要修复实现。

### 4.2 语义契约总结

```
yield() = 主动让出执行权
  ├─ 有其他 runnable → 切换到下一个 (round-robin)
  ├─ 无其他 runnable + 有 sleeping/IO → 进入 timer/IO wait (阻塞)
  └─ 无其他 runnable + 无 sleeping/IO → 立即返回继续执行
```

---

## 5. Implementation Proposal — BUG-A 修复方案（本次不实施）

### 5.1 修复目标

让 `coroutine_yield()` 在"没有其他 runnable coroutine，但存在 sleeping/IO-waiting coroutine"时，正确进入 timer/IO wait，而不是找到自己并立即返回。

### 5.2 最小修复方案

**修改文件:** `host/c/vm.c`
**修改函数:** `coroutine_yield()` (line 270-395)
**修改位置:** pass 0 的 runnable 搜索循环 (line 298-306)

**修复思路:** 在搜索 runnable 时，**排除当前 coroutine `old` 自己**（在 pass 0 中）。只有在 pass 1（已经过 IO/timer wait 后）仍然没有 runnable 时，才允许恢复自己或第一个 alive coroutine。

**具体修改（候选）:**

```c
/* Find next runnable coroutine — exclude self in pass 0 */
int next = -1;
for (i = 0; i < vm->coroutineCount; i++) {
    int idx = (old + 1 + i) % vm->coroutineCount;
    if (pass == 0 && idx == old) continue;  /* 排除自己 */
    if (coroutine_is_runnable(vm->coroutines[idx])) {
        next = idx;
        break;
    }
}
```

**为什么这是最小修复:**
1. 只修改搜索循环的一个条件，不改变 scheduler 的整体架构
2. 不改变 coroutine_is_runnable() 的判定规则
3. 不改变 IO/timer wait 逻辑（已经正确实现）
4. pass 1 仍然允许恢复自己（作为最后的安全网）
5. 不影响有其他 runnable coroutine 时的正常 round-robin 行为

### 5.3 需要验证的回归场景

| 场景 | 预期 |
|------|------|
| P0-06 baseline 19/19 | 全部保持 PASS |
| A1 (yield loop + sleeper) | FAIL → PASS |
| A2 (sleep wait) | 保持 PASS |
| A3 (yield loop + shorter sleeper) | FAIL → PASS |
| 多 coroutine round-robin | 保持正确 |
| channel send/recv | 保持正确 |
| IO wait (waitRead/waitWrite) | 保持正确 |
| 只有 main coroutine 时 yield | 立即返回（不阻塞） |
| sleep(0) | 等同于 yield，立即返回 |

### 5.4 需要新增的 regression tests

1. **yield-timer-wait:** 验证 yield() 循环能正确等待 sleeping coroutine（A1/A3 的正式版）
2. **yield-no-other-runnable:** 验证只有 main coroutine 时 yield() 立即返回（不阻塞、不崩溃）
3. **yield-with-io:** 验证 yield() 与 IO wait 混合场景
4. **yield-round-robin:** 验证多 coroutine 时 yield() 正确 round-robin（不排除自己导致跳过）

### 5.5 风险评估

- **低风险:** 修改仅限于搜索循环的一个条件
- **需要注意:** pass 0 排除自己后，如果只有 main coroutine 且没有 sleeping/IO，搜索会找不到任何 runnable，进入 IO/timer wait 逻辑。此时 ioCount=0 && sleepCount=0 → `return`（line 342），正确退出。不会阻塞。
- **需要注意:** 如果有多个 runnable coroutine，搜索从 old+1 开始，会先找到其他 runnable，不会到达排除自己的条件。正常 round-robin 不受影响。

---

## 6. 本次施工范围确认

| 项目 | 状态 |
|------|------|
| 修改 scheduler | ❌ 未修改 |
| 修改 coroutine runtime | ❌ 未修改 |
| 修改 VM | ❌ 未修改 |
| 修改 opcode | ❌ 未修改 |
| 修改 compiler | ❌ 未修改 |
| 修改 A1/A2/A3 测试期望值 | ❌ 未修改 |
| 添加 workaround | ❌ 未添加 |
| 添加 artificial sleep | ❌ 未添加 |
| 添加 debug delay | ❌ 未添加 |
| git diff | 仅新增本文档 |

---

## 7. 结论

1. **BUG-A 根因已确认:** `coroutine_yield()` 的 runnable 搜索循环包含当前 coroutine 自己，导致在"没有其他 runnable 但有 sleeping coroutine"时，搜索找到自己并立即返回，跳过已实现的 timer-wait 逻辑。

2. **语义是明确的，不是 Semantics GAP:** 代码注释和 A2（sleep 能正常工作）都证明 yield() 在没有其他 runnable 时应该进入 timer-wait。这是 Runtime Bug，不是设计缺口。

3. **修复方案已形成:** 在 pass 0 的搜索循环中排除当前 coroutine 自己。最小修改，不改变 scheduler 架构。

4. **本次未实施修复:** 按照施工令，本次只做审计和语义裁决，修复留待 `P0-COMPILER-06-BUG-A-FIX` 施工令。

---

**STOP. 未实施 BUG-A 修复。等待架构师审核后，再下发 P0-COMPILER-06-BUG-A-FIX 施工令。**
