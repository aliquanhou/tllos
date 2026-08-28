# TLL Missing Capability Report
# P0-11: TLL Language Missing-Capability Detection & Completion

## 1. Executive Summary

P0-11 对 TLL 编程语言进行了系统性的缺失能力探测，从 20 个维度（时间、状态、Observation、事件、并发、Stream、资源生命周期、错误模型、数据模型、Agent Native 等）进行了全面审计。

**核心发现：**
1. **Stdlib observable + events 足够表达响应式编程** - 通过实时行情系统 Dogfooding 验证，Observation 不需要语言级支持
2. **发现重要语言级 Bug：匿名 lambda 闭包崩溃** - 命名函数闭包工作正常，但匿名 lambda 闭包导致程序无输出（崩溃）
3. **大部分缺失能力可用 Stdlib 解决** - 不需要进入 Language Core

## 2. Capability Discovery Matrix 摘要

| 维度 | 状态 | 分类 | 建议 |
|------|------|------|------|
| 时间（即时/延迟/周期/窗口/超时） | 🟡 部分 | Stdlib | time.sleep 存在，周期/窗口/超时可用 Stdlib 实现 |
| 状态（delta/snapshot/history/version） | 🔴 缺失 | Stdlib | 可用 observable 模式 + Stdlib 实现 |
| Observation（observe/watch/when changes） | 🔴 缺失 | Stdlib ✅ | **已验证 Stdlib 足够**，不需要语言级 |
| 事件（emit/subscribe/react） | 🔴 缺失 | Stdlib ✅ | EventEmitter 模式可用 Stdlib 实现 |
| 并发（Task/Actor/Channel/Stream） | 🟡 部分 | Runtime | Worker Pool + 全局锁存在，细粒度并发需 Runtime 级研究 |
| Stream（pipe/map/filter/window） | 🔴 缺失 | Stdlib | 可用迭代器 + 函数实现 |
| 资源生命周期（create/pause/cancel/close） | 🟡 部分 | Stdlib | 文件 close 存在，通用生命周期可用 Stdlib |
| 错误模型（重试/超时/取消/降级） | 🟡 部分 | Stdlib/Runtime | try/catch/throw/finally 存在，重试/降级可用 Stdlib，超时需 Runtime |
| 数据模型（Tuple/Optional/Result） | 🟡 部分 | Stdlib | 可用现有类型模拟或 Stdlib 实现 |
| Agent Native（Agent/Goal/Tool/Memory） | 🔴 缺失 | Stdlib | 可用 struct + function + event 实现，不需要语言级 |

## 3. Discovered Bug: Anonymous Lambda Closure Crash

### 严重程度
🔴 **High** - 影响所有使用匿名 lambda 闭包的程序

### 现象
- 匿名 lambda 闭包 `let f = fn() { ... }` 导致程序无输出（崩溃）
- 命名函数闭包 `fn f() { ... }` 工作正常
- 闭包读取被捕获的变量时返回无效值或崩溃

### 复现
```tll
// 崩溃（无输出）
fn test() {
    let x = 42
    let f = fn() {
        io.println("x = " + convert.toString(x))
    }
    f()
}
test()

// 正常工作
fn test() {
    let x = 42
    fn get() { return x }
    io.println("x = " + convert.toString(get()))
}
test()
```

### 已知工作的闭包模式
- `makeAdder(n) { return fn(x) { return x + n } }` - 从 d6fa89a 修复后工作
- 命名函数闭包 `fn inc() { n = n + 1; return n }` - 工作正常
- makeCounterD 模式 - 工作正常

### 根因分析
编译器中匿名 lambda 的处理（codegen.tll 第 1146-1192 行）：
- 第 1156 行：`if cg_closureEnvSize > 0` 决定是否使用 OP_CLOSURE
- 匿名 lambda 可能在错误的上下文中编译，导致 `cg_closureEnvSize` 未正确设置
- 如果 `cg_closureEnvSize == 0`，会走第 1169 行分支，创建没有 env 的 map `{__fn, fnIdx, env:null}`
- 这导致闭包无法访问捕获的变量，进而崩溃

### 临时解决方案
使用命名函数闭包代替匿名 lambda：
```tll
// 不要这样
let handler = fn(data) { ... }

// 改为这样
fn handler(data) { ... }
```

### 修复建议
需要深入编译器 codegen.tll，检查匿名 lambda 编译时 `cg_closureEnvSize` 和 `cg_upvalueMap` 的设置是否正确。这是 P0-12 的任务。

## 4. Dogfooding Verification: Real-time Market System

### 项目
`examples/realtime_market.tll` - 实时行情系统

### 功能
- 4 个交易对（XAUUSD, EURUSD, BTCUSD, SPX500）
- 2000 次价格更新
- Observable 模式观察价格变化
- 趋势计算（5 周期移动平均）
- 异常检测（>0.5% 变化触发警报）
- 交易信号生成（趋势>0.1% 触发 BUY/SELL）
- EventEmitter 模式分发事件

### 结果
| 指标 | 值 |
|------|-----|
| Ticks | 2000 |
| Time | 43ms |
| Observation rate | 46,511 ticks/sec |
| Trades | 489 |
| Alerts | 250 |
| Total XAUUSD delta | -241.351 |
| History entries | 490 |

### 结论
✅ **Stdlib observable + events 足够表达"世界变化，立即响应"**

watcher 回调被正确触发（489 trades, 250 alerts），状态历史正确记录（490 entries），趋势计算和异常检测工作正常。

**Observation 不需要语言级支持**，Stdlib 的 observable + EventEmitter 模式已经足够自然和高效。

## 5. Missing Capability Classification

### 🔴 需要 Language Core（经过最高级判断标准筛选）
**当前未发现必须进入 Language Core 的能力。**

所有探测到的缺失能力都可以通过以下方式解决：
- Stdlib 实现（observable, events, stream, collections）
- Runtime 实现（并发细化，函数超时）
- Agent/LLM 实现（预测，推理，规划）

### 🟡 需要 Runtime 级实现
1. **函数调用超时** - 需要 VM 中断机制
2. **并发模型细化** - 从全局锁到细粒度锁（P0-12 研究）
3. **Stream 背压** - 需要运行时支持

### 🟢 需要 Stdlib 实现
1. **Observable/Watch** - ✅ 已验证可行
2. **EventEmitter** - ✅ 已验证可行
3. **Stream 操作**（map/filter/reduce/merge/split/window）
4. **Collections**（Tuple/Optional/Result/Queue/Stack）
5. **时间工具**（周期/窗口/截止时间/超时检查）
6. **资源生命周期管理**
7. **错误处理工具**（重试/降级/恢复）
8. **Agent 原语**（struct + function + event）

### ⚪ 属于 Agent/LLM
1. 预测/推理/规划
2. 语义决策
3. 置信度评估

## 6. Highest-level Judgment Standard Results

对每个探测到的缺失能力，回答以下问题：

### Observation (observe/watch)
- 为什么普通函数做不到？→ 可以做到，observable 模式就是函数
- 为什么 Stdlib 做不到？→ **可以做到**，已验证
- 为什么 Runtime API 做不到？→ 不需要
- 为什么 Agent/LLM 做不到？→ 不需要
- 为什么必须由语言本身理解？→ **不需要**
- **结论：Stdlib 足够，不进入 Language Core**

### Event (emit/subscribe)
- 为什么普通函数做不到？→ 可以做到，EventEmitter 就是函数
- 为什么 Stdlib 做不到？→ **可以做到**
- **结论：Stdlib 足够，不进入 Language Core**

### Stream (pipe/map/filter)
- 为什么普通函数做不到？→ 可以做到，迭代器+函数
- 为什么 Stdlib 做不到？→ **可以做到**
- **结论：Stdlib 足够，不进入 Language Core**

### 并发 (async/await/actor)
- 为什么普通函数做不到？→ 并发需要运行时调度
- 为什么 Stdlib 做不到？→ 基础并发需要 Runtime 支持
- 为什么 Runtime API 做不到？→ **可以做到**，Worker Pool 已存在
- **结论：Runtime 级，不进入 Language Core**

### Agent (Agent/Goal/Tool)
- 为什么普通函数做不到？→ 可以做到，struct+function
- 为什么 Stdlib 做不到？→ **可以做到**
- **结论：Stdlib 足够，不进入 Language Core**

## 7. Recommendations

### P0-12 优先级
1. **修复匿名 lambda 闭包 Bug**（高优先级，影响语言表达能力）
2. **Stdlib: observable + events 正式化**（将 examples 中的实现移入 stdlib/）
3. **Stdlib: stream 操作**（map/filter/reduce/merge/split/window）
4. **Runtime: 并发模型细化研究**（从全局锁到细粒度锁）
5. **Stdlib: collections**（Tuple/Optional/Result/Queue）

### 不建议
- 不建议为了"语言完整"而引入 TypeScript/JavaScript 式的静态类型系统
- 不建议引入 async/await 语法（TLL 可以用自己的并发模型）
- 不建议将 Agent 原语硬编码进语言核心（Stdlib 足够）
- 不建议引入 predict() 语言原语（预测是 Agent/LLM 职责）

## 8. Conclusion

P0-11 系统探测了 TLL 语言的缺失能力，得出以下核心结论：

1. **TLL 当前语言核心已经足够表达大部分编程需求**
2. **大部分缺失能力可以通过 Stdlib 解决**，不需要进入 Language Core
3. **Observation 不需要语言级支持**，Stdlib observable 模式已经足够自然和高效（46,511 ticks/sec）
4. **发现重要 Bug：匿名 lambda 闭包崩溃**，需要 P0-12 修复
5. **TLL 不应该照抄其他语言的功能**，应该围绕自己的核心目标（AI-Native、高帧率、持续状态）成长

**最高级判断标准的结论：当前未发现必须进入 Language Core 的能力。** 所有探测到的缺失能力都可以通过 Stdlib、Runtime 或 Agent/LLM 解决。

这是一个重要的发现：TLL 的语言核心设计是合理的，未来的成长应该主要在 Stdlib 和 Runtime 层面，而不是不断扩展语言语法。
