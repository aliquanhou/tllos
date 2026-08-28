# TLL Capability Discovery Matrix
# P0-11.A: Missing-Capability Detection

## 探测方法
从"用 TLL 描述一个不断变化的真实世界系统"出发，主动寻找语言表达能力的空洞。
不照抄其他语言，每个能力通过最高级判断标准筛选：
1. 为什么普通函数做不到？
2. 为什么 Stdlib 做不到？
3. 为什么 Runtime API 做不到？
4. 为什么 Agent/LLM 做不到？
5. 为什么必须由语言本身理解？

## 当前 TLL 已验证能力（基座）
- Lexer/Parser/AST/Compiler/Bytecode/VM（C + TLL 双实现）
- 46 opcodes，register-based VM
- Function / Lambda / Closure（已修复真实 Bug）
- Struct（声明+字面量+字段访问+变更）
- Enum（声明+常量+访问）
- Module / Import
- Error Handling（try/catch/throw/finally）
- Array / Map / String / Number / Boolean / Null
- TLL Stdlib（array/string/math/json）
- HTTP Client / Server（MVP，Worker Pool 并发）
- Cookie / Session
- File / Persistence
- Process / Time / Environment
- 自托管编译器（TLL 写的 TLL 编译器）
- 商城 Dogfooding（用户/商品/购物车/订单/持久化）

---

## A. 时间维度

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| 即时执行 | ✅ 函数调用 3.3M/s | 否 | - | 已足够 |
| 延迟执行 | 🟡 time.sleep 存在 | 部分 | Stdlib | sleep 是阻塞的，缺少非阻塞延迟 |
| 周期执行 | 🔴 无 | 是 | Stdlib/Runtime | setInterval 类能力缺失，可用 Stdlib+线程实现 |
| 时间窗口 | 🔴 无 | 是 | Stdlib | sliding window / tumbling window，纯函数可实现 |
| 超时 | 🔴 无 | 是 | Runtime | 函数调用超时需要 VM 支持中断，普通函数做不到 |
| 截止时间 | 🔴 无 | 是 | Stdlib | deadline 检查可用函数实现 |
| 时间序列 | 🟡 可用 Array 模拟 | 部分 | Stdlib | 缺少专用时间序列结构，但 Array+函数足够 |
| 历史状态 | 🔴 无原生支持 | 是 | Stdlib/Language? | state history 需要观察状态变化，可能需要语言级 observe |
| 未来状态 | 🔴 无 | 是 | Agent | 预测是 Agent/LLM 职责，TLL 只提供数据 |
| 状态年龄 | 🔴 无 | 是 | Stdlib | 可用 struct+timestamp 实现 |
| 事件顺序 | 🟡 单线程天然有序 | 部分 | Runtime | 并发下事件顺序需要保证，当前全局锁天然有序 |
| 时间因果 | 🔴 无 | 是 | Stdlib | happens-before 关系可用事件时间戳实现 |

**时间维度结论：** 大部分可用 Stdlib 解决。唯一可能需要 Runtime 支持的是"函数调用超时"（需要 VM 中断机制）。历史状态可能需要语言级 observe 支持。

---

## B. 状态维度

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| 变量=值 | ✅ 完整 | 否 | - | 基础能力 |
| 状态变化 | 🟡 手动赋值 | 部分 | Language? | 缺少"状态变化时自动触发"的能力 |
| 状态历史 | 🔴 无 | 是 | Stdlib/Language? | 需要记录状态变化历史，手动实现繁琐 |
| 状态趋势 | 🔴 无 | 是 | Stdlib | 趋势计算是纯函数，Stdlib 足够 |
| delta | 🔴 无 | 是 | Stdlib | 差值计算是纯函数 |
| snapshot | 🔴 无 | 是 | Stdlib | 状态快照可用深拷贝函数实现 |
| version | 🔴 无 | 是 | Stdlib | 版本号可用 struct 字段实现 |
| rollback | 🔴 无 | 是 | Stdlib | 回滚需要 snapshot+restore，函数可实现 |
| diff | 🔴 无 | 是 | Stdlib | 状态比较是纯函数 |
| transition | 🔴 无 | 是 | Stdlib/Language? | 状态转换（created→paid→shipped）可用函数+校验实现 |

**状态维度结论：** 大部分可用 Stdlib 解决。关键问题是"状态变化时自动触发"——这需要语言级 observe 或 Stdlib 的 watch 函数。需要验证：Stdlib 的 watch 函数是否足够自然？还是需要语法支持？

---

## C. Observation 维度

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| observe X | 🔴 无 | 是 | Language? | 核心问题：是否需要 `observe price { ... }` 语法？ |
| when X changes | 🔴 无 | 是 | Language? | `when price changes { ... }` 是否需要语法支持？ |
| watch | 🔴 无 | 是 | Stdlib | `watch(obj, "field", callback)` 函数可实现 |
| 变化检测 | 🔴 无 | 是 | Runtime/Language | 自动检测状态变化需要编译器生成代码或运行时拦截 |
| 变化通知 | 🔴 无 | 是 | Stdlib | 通知是函数调用，Stdlib 可实现 |
| 条件观察 | 🔴 无 | 是 | Stdlib | `when price > 100` 可用轮询+条件函数实现 |

**Observation 维度结论：** 这是 TLL 与传统语言最大的区别点。关键判断：
- Stdlib 的 `watch(obj, field, callback)` 可以实现基本功能
- 但需要手动调用 watch，且无法观察局部变量
- 语言级 `observe` / `when changes` 可以让编译器自动生成变化检测代码
- **需要真实项目验证：Stdlib watch 是否足够？还是语言级 observe 显著更自然？**

---

## D. 高帧率核心

| 指标 | 当前状态 | 缺失? | 分类 |
|------|----------|-------|------|
| Observations/sec | 🔴 无测量 | 是 | Benchmark |
| State Transitions/sec | 🟡 函数调用 3.3M/s | 部分 | Benchmark |
| State Deltas/sec | 🔴 无测量 | 是 | Benchmark |
| Decision Cycles/sec | 🔴 无测量 | 是 | Benchmark |
| Events/sec | 🟡 208K/s (create+dispatch) | 部分 | Benchmark |
| Actions/sec | 🔴 无测量 | 是 | Benchmark |
| E2E Reaction Latency | 🔴 无测量 | 是 | Benchmark |

**高帧率结论：** 需要建立 Temporal Resolution 基准测试体系，测量完整的 observe→state→decision→action 闭环。

---

## E. 预测的语言基础

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| trend | 🔴 无 | 是 | Stdlib | 趋势计算是纯函数 |
| window | 🔴 无 | 是 | Stdlib | 时间窗口是纯函数+数据结构 |
| history | 🔴 无 | 是 | Stdlib | 历史记录是数据结构 |
| delta | 🔴 无 | 是 | Stdlib | 差值是纯函数 |
| rate | 🔴 无 | 是 | Stdlib | 变化率是纯函数 |
| velocity | 🔴 无 | 是 | Stdlib | 速度是纯函数 |
| threshold | 🔴 无 | 是 | Stdlib | 阈值检测是纯函数 |
| anomaly | 🔴 无 | 是 | Stdlib/Agent | 异常检测可能需要 Agent，但基础统计是 Stdlib |
| forecast input | 🔴 无 | 是 | Stdlib | 预测输入数据整理是 Stdlib |
| confidence | 🔴 无 | 是 | Agent | 置信度是 Agent/LLM 输出 |

**预测维度结论：** 全部可以用 Stdlib 实现。TLL 不负责预测，只提供高速事实、历史状态、趋势、变化。预测是 Agent/LLM 的职责。

---

## F. 事件模型

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| event | 🟡 可用 Map 模拟 | 部分 | Stdlib | 事件对象可用 struct/Map |
| emit | 🔴 无 | 是 | Stdlib | 事件发射是函数调用 |
| subscribe | 🔴 无 | 是 | Stdlib | 订阅是注册回调函数 |
| react | 🔴 无 | 是 | Stdlib/Language? | 响应式编程可能需要语言级支持 |
| watch | 🔴 无 | 是 | Stdlib | 观察是函数 |
| trigger | 🔴 无 | 是 | Stdlib | 触发是函数调用 |
| cancel | 🔴 无 | 是 | Stdlib | 取消订阅是函数 |
| debounce | 🔴 无 | 是 | Stdlib | 防抖是高阶函数 |
| throttle | 🔴 无 | 是 | Stdlib | 节流是高阶函数 |
| EventEmitter | 🔴 无 | 是 | Stdlib | 事件发射器是 struct+函数 |

**事件维度结论：** 大部分可用 Stdlib 实现（EventEmitter 模式）。关键问题：响应式编程（react）是否需要语言级支持？还是 EventEmitter Stdlib 足够？需要真实项目验证。

---

## G. 并发模型

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| Thread | 🟡 Worker Pool (Windows Thread) | 部分 | Runtime | 当前是 thread-per-worker，全局 VM 锁 |
| async/await | 🔴 无 | 是 | Language? | 是否需要 async/await 语法？还是其他并发模型？ |
| Future/Promise | 🔴 无 | 是 | Stdlib/Language? | 可用 struct+回调实现，或语言级支持 |
| mutex | 🟡 CRITICAL_SECTION (全局锁) | 部分 | Runtime | 当前只有全局 VM 锁，缺少细粒度锁 |
| Task | 🔴 无 | 是 | Stdlib/Runtime | 任务抽象可用 struct 实现 |
| Actor | 🔴 无 | 是 | Stdlib/Language? | Actor 模型可能需要语言级支持 |
| Worker | 🟡 Worker Pool 存在 | 部分 | Runtime | 当前 8 worker，全局锁 |
| Channel | 🔴 无 | 是 | Stdlib/Runtime | 通道通信需要并发安全队列 |
| Stream | 🔴 无 | 是 | Stdlib/Language? | 流处理可能需要语言级支持 |
| Event Loop | 🔴 无 | 是 | Runtime | 事件循环需要运行时支持 |
| Scheduler | 🟡 Worker Pool 简单调度 | 部分 | Runtime | 当前是简单的 accept→worker 调度 |

**并发维度结论：** 当前是 Worker Pool + 全局 VM 锁（IO 并发，计算串行）。这是 P0-10 发现的下一瓶颈。关键问题：
- TLL 需要什么样的并发模型？（async/await? Actor? CSP?）
- 全局锁是否可以细化？（per-object 锁？原子引用计数？）
- 这需要 Runtime 级别的大改动，可能影响语言语义

**判断：并发模型需要 Runtime 级别的深入研究，不是简单加 API。当前全局锁方案对于 IO 密集型应用已经足够。计算密集型并发需要 P0-12 专门研究。**

---

## H. Stream

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| stream | 🔴 无 | 是 | Stdlib/Language? | 流抽象可用迭代器+函数实现 |
| pipe | 🔴 无 | 是 | Stdlib | 管道是函数组合 |
| map | 🟡 array.map 存在 | 部分 | Stdlib | 流的 map 可用函数实现 |
| filter | 🟡 array.filter 存在 | 部分 | Stdlib | 流的 filter 可用函数实现 |
| window | 🔴 无 | 是 | Stdlib | 窗口是函数+数据结构 |
| reduce | 🟡 array.reduce 存在 | 部分 | Stdlib | 流的 reduce 可用函数实现 |
| merge | 🔴 无 | 是 | Stdlib | 合并流是函数 |
| split | 🔴 无 | 是 | Stdlib | 分流是函数 |
| backpressure | 🔴 无 | 是 | Runtime | 背压需要运行时支持 |

**Stream 维度结论：** 大部分可用 Stdlib 实现（基于迭代器模式）。背压需要 Runtime 支持。关键问题：TLL 是否需要语言级 Stream？还是 Stdlib 的迭代器+函数足够？需要真实项目验证。

---

## I. 资源生命周期

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| create | ✅ 函数 | 否 | - | 基础能力 |
| active | 🟡 手动管理 | 部分 | Stdlib | 状态标记可用 struct 字段 |
| pause | 🔴 无 | 是 | Stdlib | 暂停是函数 |
| resume | 🔴 无 | 是 | Stdlib | 恢复是函数 |
| cancel | 🔴 无 | 是 | Stdlib | 取消是函数 |
| close | 🟡 文件 close 存在 | 部分 | Stdlib | 关闭是函数 |
| expire | 🔴 无 | 是 | Stdlib | 过期可用时间戳+检查实现 |
| RAII/defer | 🔴 无 | 是 | Language? | 资源自动释放可能需要语言级 defer |
| 生命周期状态机 | 🔴 无 | 是 | Stdlib | 可用 struct+函数实现 |

**资源生命周期结论：** 大部分可用 Stdlib 实现。唯一可能需要语言级的是 `defer`（资源自动释放），但 try/finally 已经可以实现类似功能。

---

## J. 错误模型

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| try/catch | ✅ 完整 | 否 | - | 已实现 |
| throw | ✅ 完整 | 否 | - | 已实现 |
| finally | ✅ 完整 | 否 | - | 已实现 |
| 重试 | 🔴 无 | 是 | Stdlib | retry 是高阶函数 |
| 超时 | 🔴 无 | 是 | Runtime | 函数超时需要 VM 中断 |
| 取消 | 🔴 无 | 是 | Stdlib/Runtime | 取消需要协作式检查 |
| 恢复 | 🔴 无 | 是 | Stdlib | 恢复是函数 |
| 降级 | 🔴 无 | 是 | Stdlib | 降级是函数 |
| 部分成功 | 🔴 无 | 是 | Stdlib | 可用 Result 类型实现 |
| 最终失败 | 🟡 exception 存在 | 部分 | Stdlib | 已基本覆盖 |

**错误模型结论：** 大部分可用 Stdlib 实现。函数超时需要 Runtime 支持（VM 中断机制）。当前 try/catch/throw/finally 已经足够基础使用。

---

## K. 数据模型

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| Value | ✅ 完整 | 否 | - | 基础类型 |
| Struct | ✅ 基础 | 部分 | Language | 已实现声明/字面量/访问/变更 |
| Enum | ✅ 基础 | 部分 | Language | 已实现声明/常量/访问 |
| Array | ✅ 完整 | 否 | - | 已实现 |
| Map | ✅ 完整 | 否 | - | 已实现 |
| Tuple | 🔴 无 | 是 | Stdlib | 可用 Array 模拟，或语言级支持 |
| Optional | 🔴 无 | 是 | Stdlib/Language? | 可用 null 模拟，或语言级 Optional |
| Result | 🔴 无 | 是 | Stdlib | 可用 Struct {ok, value, error} 实现 |
| Stream | 🔴 无 | 是 | Stdlib/Language? | 见 H 维度 |
| State | 🔴 无 | 是 | Stdlib/Language? | 见 B 维度 |
| Snapshot | 🔴 无 | 是 | Stdlib | 深拷贝函数 |
| Delta | 🔴 无 | 是 | Stdlib | 差值函数 |

**数据模型结论：** Tuple/Optional/Result 可以用现有类型模拟或 Stdlib 实现。State/Snapshot/Delta 见相关维度。当前数据模型对于基础使用已经足够。

---

## L. Agent Native

| 能力 | 当前状态 | 缺失? | 分类 | 判断 |
|------|----------|-------|------|------|
| Agent | 🔴 无 | 是 | Stdlib | Agent 可用 struct+function+event 实现 |
| Goal | 🔴 无 | 是 | Stdlib | 目标是 struct 字段 |
| Task | 🔴 无 | 是 | Stdlib | 任务是 struct+函数 |
| Tool | 🔴 无 | 是 | Stdlib | 工具是函数注册 |
| Context | 🔴 无 | 是 | Stdlib | 上下文是 Map/Struct |
| Memory | 🔴 无 | 是 | Stdlib | 记忆是数据存储 |
| Observation | 🔴 无 | 是 | Stdlib/Language? | 见 C 维度 |
| Decision | 🔴 无 | 是 | Agent | 决策是 LLM 职责 |
| Action | 🔴 无 | 是 | Stdlib | 行动是函数调用 |
| Feedback | 🔴 无 | 是 | Stdlib | 反馈是数据 |

**Agent Native 结论：** 全部可以用 Stdlib 实现（struct + function + event）。按照施工令，Agent 原语只有在证明普通函数+struct+event+stream 无法优雅表达后，才能进入核心。当前判断：不需要进入 Language Core，先用 Stdlib 实现，真实项目验证后再决定。

---

## 综合分类结果

### 🔴 可能需要 Language Core 的能力（需进一步验证）
1. **Observation / Reactivity**（observe/when changes）- 状态变化自动触发
2. **State History / Delta** - 状态变化的自动记录
3. **Event / React** - 响应式编程模型

### 🟡 需要 Runtime 级别的能力
1. **函数调用超时** - 需要 VM 中断机制
2. **并发模型细化** - 从全局锁到细粒度锁（P0-12 研究）
3. **背压** - Stream 背压需要运行时支持

### 🟢 可以用 Stdlib 解决的能力
- EventEmitter（emit/subscribe/cancel）
- 时间窗口/周期/截止时间
- 趋势/异常/变化率计算
- 资源生命周期管理
- 错误重试/降级/恢复
- Tuple/Optional/Result 类型
- Agent 原语（struct+function+event）
- Stream 操作（map/filter/reduce/merge/split）

### ⚪ 属于 Agent/LLM 的能力
- 预测/推理/规划
- 决策
- 置信度

---

## 下一步：验证核心假设

最关键的验证问题：
**Stdlib 的 watch(obj, field, callback) + EventEmitter 是否足够自然地表达"世界发生了变化，我立即响应"？**

还是需要语言级 `observe price { ... }` / `when price changes { ... }` 语法？

验证方法：用 TLL 实现一个真实的实时行情系统，先用 Stdlib 的 watch+EventEmitter，然后评估是否需要语言级支持。
