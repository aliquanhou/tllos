# P2-01-B.11 施工令 — Native Ownership Semantic Closure

> 架构裁决：GPT-5.6 Luna
> 最终验收：于秋鸿博士
> 施工执行：Agent A（本地执行、编译、测试、Evidence、报告）
> 协作模式：Luna 直接进行仓库级施工；Agent A 负责本地环境验证。
> 状态：待执行

## 0. 基线与前置

P2-01-B.10 已完成施工并经架构师裁决为 **PASS / 未封板**。

B.10 的核心成果：
- Native Map literal / index read / index write 已建立。
- Cross-Target Conformance 7/7 PASS。
- Bool AST 类型判断 bug 已修复。
- Native Ownership/Refcount 基础框架已建立。
- `tll_array_from` 无消费者，已删除。
- Shared Runtime ABI 文档已修正为：布局/签名/调用约定稳定；语义与 ownership 仍为 OPEN。

B.10 明确留下的 P1 GAP：
- 变量赋值时旧值未完整 release/free。
- 函数参数 ownership 未完整定义/实现。
- 容器元素 ownership 未完整定义/实现。

## 1. 本阶段唯一核心目标

**冻结并实现 TLL Native Ownership Model，使 Bytecode Target 与 Native Target 对 TLLValue、String、Array、Map 的 ownership / retain / release / transfer 语义形成一致、可验证的合同。**

本阶段不是“大规模 Native 功能扩展”。

## 2. 必须先做：Ownership Contract v1.1

新增或更新：

`docs/TLL-NATIVE-OWNERSHIP-REFCOUNT-RULES-v1.1.md`

必须明确以下六类生命周期：

1. Creation
2. Assignment / Re-assignment
3. Function Argument
4. Function Return
5. Container Element
6. Scope Exit

对每一类明确：
- owner 是谁
- borrow 是什么
- retain/incref 何时发生
- release/free 何时发生
- ownership transfer 何时发生
- 是否允许 alias
- 返回值如何避免 premature free

### 重要约束

不得通过“测试能过”反推 ownership 规则。

必须先根据现有 Bytecode VM 与 Shared Runtime 的真实行为确定语义，再让 Native lowering 实现该语义。

如果 Bytecode 当前行为与文档/设计冲突，必须报告 GAP，不得擅自修改 Bytecode 语义以迁就 Native。

## 3. Native 实现范围

### 3.1 Assignment

解决：

```tll
let x = "a";
x = "b";
```

必须避免旧值泄漏，同时避免新值 premature free / double free。

需要覆盖：
- primitive value
- string
- array
- map

### 3.2 Function Arguments

至少验证：

```tll
fn consume(x) { ... }
consume(value)
```

明确 caller / callee 的 ownership 边界。

### 3.3 Container Elements

验证：
- `array_push`
- `array_set`（如果现有 API 支持）
- `map_set`
- `array_get`
- `map_get`

明确容器保存的是 borrow 还是 retained reference，并与现有 Shared Runtime / Bytecode 语义一致。

## 4. Conformance 必须增加 Ownership 专项

新增最小测试，不追求数量：

- `07_ownership_local.tll`
- `08_ownership_assignment.tll`
- `09_ownership_return.tll`
- `10_ownership_container.tll`

每个测试必须使用**同一份 TLL 源代码**分别经过：

```text
TLL Source
 ├── Bytecode Target → tllbc → tllvm
 └── Native Target   → C → MSVC → native executable
```

自动比较：
- stdout
- exit code
- compiler status
- native build status

如果环境允许，优先使用成熟的 ASan / Debug Runtime / CRT 检测能力发现：
- use-after-free
- double-free
- leak
- invalid ownership transition

不得自行重复开发一个内存检测器。

## 5. 必须检查的危险场景

至少覆盖：

```text
local creation → scope exit
local → reassignment
local → function argument
function return → caller
value → array/map
array/map → read
array/map → replacement
multiple references / aliases
```

特别检查：
- double free
- premature free
- leaked reference
- return value 被 local cleanup 销毁
- assignment 覆盖旧值造成泄漏
- container 保存悬空引用

## 6. Regression Gate

B.11 完成前必须保持：

- Bootstrap Stage-0 PASS
- existing Bytecode regression PASS
- existing Native Conformance 7/7 PASS
- new Ownership Conformance 全部 PASS
- MSVC build 0 errors
- 不得通过删除、跳过、弱化测试制造绿色

CI 如果发现问题，必须保留问题并报告真实根因。

## 7. 严格禁止扩张范围

本施工阶段禁止主动进入：

- Closure
- Coroutine
- Network
- FFI
- LLVM
- Linux
- GPU
- High-Frame Runtime
- For / Break / Continue
- 大规模 String API
- 新的 OS 能力
- 新的 TLL OS 仓库

本阶段只解决 **Native Ownership Semantic Closure**。

## 8. Dead API 原则

任何新增 Runtime API 必须有实际消费者和测试证据。

禁止为了“以后可能需要”增加死 API。

` tll_array_from ` 已被 B.10 删除；不得重新引入等价的无消费者接口。

## 9. Git / 仓库施工纪律

本阶段开始采用新的协作模式：

```text
Luna
  ↓
仓库级施工
  ↓
Git branch / commit
  ↓
Agent A 拉取
  ↓
本地编译 / 测试 / Evidence
  ↓
Agent A 报告
  ↓
Luna 审查
  ↓
下一施工动作
```

要求：

1. 正式施工必须在独立分支进行。
2. 不直接把未验证代码强推 `main`。
3. 调试文件、编译产物不得混入正式提交。
4. 每个架构 PASS 建立对应 Milestone Tag。
5. Agent A 不得声明 SEALED/CLOSED。
6. 最终 SEALED/CLOSED 只能由于秋鸿博士裁决。

## 10. 交付报告必须回答

Agent A 完成后必须提交：

1. 修改文件清单
2. Ownership Contract v1.1 具体规则
3. Bytecode 真实 ownership 行为依据
4. Native lowering 修改点
5. 07–10 Ownership Conformance 结果
6. 原有 7 个 Conformance 是否保持 PASS
7. Bootstrap / regression 结果
8. 是否存在 double-free / leak / UAF 风险
9. 剩余 GAP（按既有编号归并，不重复造号）
10. Git commit SHA
11. 是否建议进入 Native Target Hardening

报告结尾必须写：

> 施工完成，等待架构师审查与于秋鸿博士最终验收。

不得写“SEALED”“CLOSED”作为 Agent 自主结论。

## 11. B.11 完成判定

只有满足以下条件，架构师才考虑判定 B.11 PASS：

- Ownership Contract v1.1 完整
- Assignment ownership 闭合
- Function argument ownership 闭合
- Container ownership 闭合
- Return/scope cleanup 闭合
- Ownership Conformance 全部 PASS
- Existing 7/7 Conformance 无倒退
- Bootstrap/regression 无倒退
- 无已知 double-free / premature-free / UAF blocker

**注意：B.11 PASS 仍不等于 Native Target SEALED。**

## 12. 后续方向（仅作为路线锚点，不属于本施工范围）

```text
P2-01-B.11
   ↓
Native Ownership Semantic Closure
   ↓
Native Target Hardening
   ↓
Native Target SEALED
   ↓
P2-01-C High-Frame Runtime
```

---

**施工令版本：v1.0**

**核心原则：核心自主，外围复用；依赖实现，不依赖控制权。**
