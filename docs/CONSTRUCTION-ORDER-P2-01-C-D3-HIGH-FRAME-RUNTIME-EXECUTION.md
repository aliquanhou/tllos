# P2-01-C-D3 施工令：高帧率 Runtime 执行能力

**施工令签发：于秋鸿**  
**仓库：`aliquanhou/tllos`**  
**施工基线：`2588602799b60f0e33b2e5597ad0355e3a31062c`**  
**施工分支：`feature/P2-01-C-D3-runtime-high-frame-execution`**  
**前置状态：P2-01-C-D2 = PASS / SEALED**

---

## 一、总目标

在已经封板的 D2 基础上，继续提高 TLL Runtime 的**高帧率执行能力**。

D3 不重做 D1/D2，不重新讨论 Dynamic Frame、Worker、WAIT/WAKE，不进行一次性的大规模 Runtime 重构。

本阶段唯一主线：

> **降低 Runnable 调度的全局竞争与调度开销，让已经具备真正多 Worker 并行能力的 Runtime，在高频短任务场景下更高效、更稳定。**

D3 采用：

```text
Worker-local Runnable Queue
        ↓
本 Worker 优先消费
        ↓
本地队列空 → Global Runnable Queue
        ↓
无 Work Stealing
```

**明确：D3 不实现 Work Stealing。**

---

# 二、绝对基线，不得破坏

D3 必须从以下 commit 精确开始：

```text
2588602799b60f0e33b2e5597ad0355e3a31062c
```

不得回退或重写以下已经封板能力：

- Dynamic Frame
- `INVOKE_RET_REG` 已证明的语义
- Worker-local `TLLExecutionContext`
- TLS Worker selection
- D2 真正多 Worker 并行执行
- Worker claim exactly-once
- RUNNING / WAITING / RUNNABLE / COMPLETED 语义
- Sleep / IO / Channel WAIT/WAKE
- exact wake list
- wake list 动态分配
- malloc failure fail-closed
- D2 300/300 wake 测试
- D2 7/7 回归测试
- P0-RUNTIME-07
- P0-RUNTIME-08
- P2-01-B11/B12 ownership / ABI / cross-target 既有能力

### 严禁

本阶段不得顺手做：

- Work Stealing
- Atomic Heap 全面改造
- Global State 全面重构
- IO Reactor 全面重构
- GC 全面重构
- Scheduler 全面重写
- Opcode 大规模扩展
- 语言语法扩展
- 不相关性能优化
- 为满足“4GB”而扭曲架构

**4GB 不是 Runtime 正确性硬上限。** 内存只做效率指标和实际测量，不允许为了数字漂亮牺牲正确性。

---

# 三、D3 核心架构

当前 D2 已经具备：

```text
TLLVM
├── Program（共享）
├── Worker 0 → ctx0
├── Worker 1 → ctx1
└── Global Runnable Queue
```

D3 增量为：

```text
TLLVM
├── Program（shared / read-only）
├── Workers[]
│   ├── Worker 0
│   │   ├── ctx0
│   │   └── local Runnable Queue
│   └── Worker 1
│       ├── ctx1
│       └── local Runnable Queue
└── Global Runnable Queue
```

调度优先级：

```text
1. Worker local queue
2. Global queue
3. 无任务 → 等待
```

本阶段**不允许 Worker A 偷取 Worker B 的任务**。

---

# 四、Phase D3-A：Reality Audit（先审计，不写代码）

施工前必须先检查当前 D2 基线真实代码，不允许根据旧报告猜测。

重点审计：

### A1. Worker 当前任务获取路径

确认：

- Worker 从哪里 dequeue
- Global queue 的锁/条件变量/信号量
- Worker claim 在什么位置发生
- coroutine state 在什么锁保护下变化
- 当前 dequeue → claim → execute → completion 的完整链路

### A2. 当前 queue ownership

确认：

- 是否已有 Worker-local queue 雏形
- 是否存在可复用 queue node / queue API
- 是否有重复 enqueue 风险
- queue shutdown / cleanup 是否完整

### A3. 当前 wake path

确认 D2 的：

```text
WAITING
→ RUNNABLE
→ exact wake list
→ enqueue
→ Worker claim
```

不得改变其语义。

### A4. 当前 Worker 生命周期

确认：

- worker startup
- worker loop
- worker shutdown
- queue cleanup
- semaphore/condition cleanup

### A5. 当前测试基线

至少确认 D2 已封板测试仍然存在。

---

## Audit 输出

建立：

```text
docs/evidence/P2-01-C-D3-AUDIT.md
```

内容必须包含：

- 实际源码路径
- 当前调度路径
- 当前锁边界
- 当前 queue 行为
- 可复用组件
- D3 最小修改点
- 不修改区域
- 风险列表

**Phase A 只做 Reality Audit，不实现 D3。**

---

# 五、Phase D3-B：Worker Local Queue 最小实现

## B1. Local Queue 数据结构

为每个 Worker 增加独立 Runnable Queue。

要求：

- ownership 明确
- queue 生命周期与 Worker 生命周期一致
- Worker 自己消费自己的 local queue
- 其他 Worker 不直接操作该 local queue
- shutdown 后完整释放

如果当前项目已有成熟 queue primitive，优先复用；禁止重复造多个等价 queue。

---

## B2. Submit 路径

建立清晰的任务投递规则：

### Worker 内部产生的新 Runnable

优先投递当前 Worker local queue。

### 外部 submit / 无 Worker 上下文

投递 Global Runnable Queue。

### WAIT/WAKE

D3 不得破坏 D2 exact wake list。

如果 wake coroutine 能可靠确定其 Worker owner：

```text
wake → owner local queue
```

如果当前语义无法安全确定 owner：

```text
wake → global queue
```

**正确性优先于局部队列命中率。**

禁止为了追求性能强行猜测 owner。

---

# 六、Phase D3-C：Local-first Worker Loop

修改 Worker loop，使其严格执行：

```text
while running:
    1. local queue dequeue
    2. 若无任务 → global queue dequeue
    3. 若仍无任务 → 等待
    4. claim coroutine
    5. execute
    6. 根据状态决定 completion / requeue / waiting
```

## C1. Claim 规则不变

必须继续保持：

```text
RUNNABLE → RUNNING
```

只能有一个 Worker 成功 claim。

不得因为 local/global queue 双路径而产生：

- duplicate execution
- double claim
- lost coroutine
- state corruption

---

## C2. Queue 与 State 必须分离

严禁把：

```text
在 queue 中
```

错误地等同于：

```text
RUNNABLE
```

唯一 authoritative state 仍然是 coroutine state machine。

Queue 只是调度载体。

---

# 七、Phase D3-D：Batch Dispatch（仅做最小批处理）

如果 B/C 完成后测试证明 Global Queue contention 是主要开销，再增加极小范围 batch dequeue。

建议目标：

```text
一次唤醒 / 一次 global dequeue
→ Worker 获取有限数量任务
→ 其中任务进入自己的 local queue
```

要求：

- batch 上限必须有明确常量
- 不允许无限抓取
- 不允许一个 Worker 长时间霸占全局任务
- 不改变 coroutine ownership
- 不改变 WAITING 语义

**如果 batch 没有实际证据证明收益，可以不实现。**

D3 的核心是 local queue，不是为了“完成设计”强行增加 batch。

---

# 八、Phase D3-E：高帧率真实性测试

必须新增真实可重复测试，不接受只有单次输出。

## E1. 2 Worker / 1000 Runnable

要求：

- 2 Worker
- 1000 个独立短任务
- 每个任务可验证 exactly-once
- 最终完成数 = 1000
- 无重复执行
- 无丢失
- 两个 Worker 都实际执行任务

---

## E2. 2 Worker / 10,000 Runnable

要求：

- 10,000 tasks
- exactly-once
- 完成计数 = 10,000
- 无 deadlock
- 无 lost wake
- 无 duplicate execution

如果运行时间合理，应重复至少 3 次。

---

## E3. Local Queue 命中证据

测试必须能够证明：

```text
Worker 产生的 Runnable
→ 优先进入自己的 local queue
→ 被自己优先消费
```

统计至少包括：

```text
local_enqueue
local_dequeue
global_enqueue
global_dequeue
worker0_executed
worker1_executed
completed
```

这些统计只用于 Evidence，不能改变核心语义。

---

## E4. Contention / Fairness

构造大量短任务，检查：

- 单 Worker 是否异常垄断
- Global Queue 是否成为新的瓶颈
- local queue 是否降低 global queue 使用比例
- 是否存在 starvation

不要预设性能结论。

**先测，再下结论。**

---

# 九、Phase D3-F：性能测量

建立独立 benchmark：

```text
benchmarks/p2_01_c_d3_scheduler.tll
```

至少比较：

### Baseline

D2：

```text
Global Queue only
```

### Candidate

D3：

```text
Local Queue + Global fallback
```

测试规模至少：

```text
100
1,000
10,000
100,000
```

如果 100,000 测试过慢或不稳定，必须如实记录，不得伪造结果。

记录：

- total tasks
- elapsed time
- tasks/sec
- worker distribution
- local/global enqueue
- local/global dequeue
- completed
- failure count

### 性能结论规则

不得写：

```text
D3 提升 X 倍
```

除非 D2/D3 使用完全一致的测试方法、输入、环境和统计方式。

否则只能写：

```text
Observed measurement
```

---

# 十、Phase D3-G：Memory Efficiency Measurement

D3 不把 4GB 当硬限制。

但必须观察：

- Worker queue node overhead
- 100 / 1K / 10K / 100K task memory
- peak RSS（若环境可测）
- queue backlog peak
- allocator overhead（若可测）

比较：

```text
D2 Global Queue
vs
D3 Local + Global Queue
```

只报告真实测量。

如果没有可靠 RSS 工具，记录：

```text
RSS measurement unavailable
```

并保留其他可验证指标。

---

# 十一、Phase D3-H：Regression Gate

D3 必须重新执行 D2 已封板测试：

```text
multi_worker_parallel
overlap_proof
multi_worker_stress_2w_100t
worker_global_test
simple_sleep_wakeup
worker_ownership_boundary
wake_list_300_coroutines
```

并执行已有 Runtime 核心回归：

- simple coroutine
- coroutine 512
- coroutine sleep
- spawn
- dynamic frame
- Bytecode regression
- Native regression（当前环境能跑多少必须如实报告）

如果某测试由于环境原因无法执行：

- 不伪造 PASS
- 记录 B-GAP
- 不自动升级为 A 阻塞

---

# 十二、D3 正确性硬门槛

以下任何一项失败，D3 不得宣称 PASS：

### G1 Exactly-once

同一 coroutine 不得被两个 Worker 同时执行。

### G2 No lost runnable

RUNNABLE coroutine 必须最终有机会进入某个可消费 queue。

### G3 No duplicate queue amplification

同一 wake 事件不得产生重复 enqueue。

### G4 No state/queue contradiction

不能出现：

```text
WAITING + queue runnable
```

或：

```text
COMPLETED + queue runnable
```

### G5 Shutdown safety

Worker shutdown 不得：

- UAF
- double free
- queue node leak
- semaphore/condition leak
- orphan coroutine

### G6 Legacy compatibility

D2 legacy path 不得被 D3 意外破坏。

---

# 十三、A 级阻塞缺陷定义

只有以下问题可以作为 D3 A 级阻塞：

- crash
- use-after-free
- double-free
- deadlock
- duplicate execution
- lost coroutine
- lost wake 导致永久不可运行
- state corruption
- shutdown corruption
- 明确的数据损坏

以下不自动阻塞：

- Linux/macOS 尚未验证
- ASan 暂不可运行
- Channel/IO E2E 测试环境困难
- 性能没有提升
- RSS 暂不可测
- benchmark 较慢

这些进入 B-GAP，除非进一步证据证明它们属于上述 A 类正确性问题。

---

# 十四、Evidence First

必须建立：

```text
docs/evidence/P2-01-C-D3-HIGH-FRAME-RUNTIME.md
```

Evidence 至少记录：

1. 基线 commit
2. Phase A Reality Audit
3. 修改文件
4. Local Queue architecture
5. ownership model
6. enqueue/dequeue semantics
7. claim semantics
8. wake semantics
9. 100/1K/10K/100K tests
10. exactly-once evidence
11. worker distribution
12. local/global queue statistics
13. benchmark
14. memory measurements
15. regression results
16. environment limitations
17. B-GAP
18. A-GAP（如果存在）
19. Git commit
20. GitHub branch

原则：

> **没有 Evidence，不生成 Claim。**

---

# 十五、Git 要求

施工完成后：

```text
git diff --check
```

必须通过。

提交信息建议：

```text
P2-01-C-D3: worker-local runnable queue high-frame runtime execution
```

必须 push 到：

```text
feature/P2-01-C-D3-runtime-high-frame-execution
```

然后报告：

- commit SHA
- changed files
- tests
- benchmark
- Evidence 文件
- push result

**不得自行宣布 PASS / SEALED。**

---

# 十六、停止条件

D3 完成后立即停止施工。

不得顺手进入：

```text
D4 Work Stealing
D5 Atomic Heap
D6 IO Reactor
D7 Global State
```

这些属于后续独立阶段。

D3 的任务只有：

> **把 D2 的真正多 Worker 执行模型，进一步变成低全局队列竞争的高帧率 Runtime 执行模型。**

---

# 十七、最终交付格式

豆包完成后只需按以下格式回报：

```text
P2-01-C-D3 施工报告

Base:
<commit>

Final:
<commit>

Branch:
<branch>

Phase A Audit:
PASS / GAP

Local Queue:
PASS / GAP

Worker Scheduling:
PASS / GAP

Exactly-once:
PASS / GAP

100 tasks:
PASS / FAIL

1,000 tasks:
PASS / FAIL

10,000 tasks:
PASS / FAIL

100,000 tasks:
PASS / FAIL / NOT RUN

D2 Regression:
<results>

Performance:
<observed measurements>

Memory:
<observed measurements / unavailable>

A-GAP:
<none or exact list>

B-GAP:
<exact list>

Evidence:
<path>

Git diff --check:
PASS / FAIL

Push:
PASS / FAIL

请等待独立审计，不得自行宣布 PASS / SEALED。
```

---

# 十八、架构师最终命令

**现在开工。**

第一步必须是 **Phase D3-A Reality Audit**。

审计完成后立即进入 D3-B，不等待新的理论讨论。

如果遇到缺口：

```text
发现什么缺口 → 修什么缺口
```

但修复必须保持 D3 单一范围，不得借机扩大到其他 Runtime 子系统。

如果某项优化没有实际收益证据：

```text
不做。
```

如果某项优化影响正确性：

```text
退回。
```

如果某项问题只是跨平台/工具环境限制：

```text
记录 B-GAP，继续主线。
```

如果出现 A 级正确性问题：

```text
立即停止扩展，先关闭 A-GAP。
```

**本施工令不是理论研究任务，而是可运行 Runtime 的实际施工任务。**

**目标不是把设计写得漂亮，而是让 TLL OS 更快、更稳、更接近真正可运行的桌面机器人操作系统。**

—— **于秋鸿**