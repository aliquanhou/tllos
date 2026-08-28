# TLL Language Conformance Matrix
# P0-12: Language Capability Closure

## 说明
本矩阵验证 TLL 语言能力的真实性，确保"文档声称的能力"与"实际代码实现"一致。

状态定义：
- ✅ 已验证通过
- 🟡 部分实现 / 存在已知限制
- 🔴 缺失 / 未实现
- ⚠️ 存在 Bug
- ❓ 未验证

## 1. Language Core

| 能力 | Spec | Compiler | Bytecode | C VM | TLL VM | Test | Dogfood | 备注 |
|------|------|----------|----------|------|--------|------|---------|------|
| Lexer | ✅ | ✅ | - | - | ✅ | ✅ | ✅ | |
| Parser | ✅ | ✅ | - | - | ✅ | ✅ | ✅ | |
| AST | ✅ | ✅ | - | - | ✅ | ✅ | ✅ | |
| Compiler | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ | 自举 |
| Bytecode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 46+ opcodes |
| VM (C) | ✅ | - | ✅ | ✅ | - | ✅ | ✅ | |
| VM (TLL) | 🟡 | - | ✅ | - | 🟡 | 🟡 | ❓ | 并行实现，部分 opcode |
| Function | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Lambda (匿名) | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | P0-12 修复 |
| Closure | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | P0-12 修复 |
| Closure 读取 | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| Closure 写入 | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| 嵌套 Closure | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ❓ | |
| 兄弟 Closure | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ❓ | Shared box |
| 命名函数通过 lambda 读取 | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❓ | ❌ | ❌ | P0-12 已知 Bug |
| Struct 声明 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | |
| Struct 实例化 | 🟡 | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | 使用 __struct hack |
| Struct 字段访问 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Enum 声明 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | |
| Enum 访问 | 🟡 | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | Color.Red → 常量 |
| Module | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| Import | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| Exception | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | try/catch/throw/finally |
| Package Manifest | ✅ | ✅ | - | - | - | 🟡 | ❓ | package.tll 存在 |
| Package Workflow | 🔴 | 🔴 | - | - | - | ❌ | ❌ | 完整 workflow 未验证 |

## 2. Type System

| 能力 | Spec | Compiler | Bytecode | C VM | TLL VM | Test | Dogfood | 备注 |
|------|------|----------|----------|------|--------|------|---------|------|
| 类型标注 | ✅ | ✅ | - | - | ✅ | ✅ | ✅ | fn(a: int) -> int |
| 类型检查 | 🟡 | 🟡 | - | - | 🟡 | 🟡 | ❌ | experimental/warning-only |
| 类型推导 | 🔴 | 🔴 | - | - | - | ❌ | ❌ | |
| 泛型 | 🔴 | 🔴 | - | - | - | ❌ | ❌ | |
| 类型反射 | 🔴 | 🔴 | - | - | - | ❌ | ❌ | |

## 3. Runtime

| 能力 | Spec | Compiler | Bytecode | C VM | TLL VM | Test | Dogfood | 备注 |
|------|------|----------|----------|------|--------|------|---------|------|
| 单线程执行 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| Worker Pool | ✅ | - | ✅ | ✅ | - | 🟡 | ✅ | HTTP 并发 |
| 全局 VM 锁 | ✅ | - | ✅ | ✅ | - | ✅ | ✅ | |
| 真并行 | 🔴 | 🔴 | 🔴 | 🔴 | - | ❌ | ❌ | |
| Frame Pool | ✅ | - | ✅ | ✅ | - | ✅ | ✅ | P0-10 |
| maxRegister 优化 | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | P0-10 |
| 原子引用计数 | 🔴 | 🔴 | 🔴 | 🔴 | - | ❌ | ❌ | 普通 ++/-- |
| GC | 🟡 | - | 🟡 | 🟡 | - | 🟡 | ❌ | 引用计数 |
| 函数超时 | 🔴 | 🔴 | 🔴 | 🔴 | - | ❌ | ❌ | |
| 取消 | 🔴 | 🔴 | 🔴 | 🔴 | - | ❌ | ❌ | |

## 4. Standard Library

| 能力 | Spec | Compiler | C VM | TLL VM | Test | Dogfood | 备注 |
|------|------|----------|------|--------|------|---------|------|
| arrays | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| strings | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| math | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| json | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| map | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | |
| observable | 🟡 | ✅ | ✅ | ❌ | 🟡 | ✅ | P0-11 新增 |
| events | 🟡 | ✅ | ✅ | ❌ | 🟡 | 🟡 | P0-11 新增，once 有 Bug |
| fs | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| time | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| http client | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | |
| http server | 🟡 | ✅ | ✅ | ❌ | 🟡 | ✅ | MVP |
| process | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | |
| convert | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |
| io | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | |

## 5. Stdlib vs C Host 重复实现

| 能力 | C Host 实现 | TLL Stdlib 实现 | 状态 | 建议 |
|------|------------|-----------------|------|------|
| array.map/filter/reduce | ✅ | ✅ | 重复 | 逐步迁移到 TLL |
| string 操作 | ✅ | ✅ | 重复 | 逐步迁移到 TLL |
| math 函数 | ✅ | ✅ | 重复 | 逐步迁移到 TLL |
| json parse/stringify | ✅ | ✅ | 重复 | 逐步迁移到 TLL |

## 6. ABI / Spec 一致性

| 项目 | Spec | C Host | 测试 | 状态 |
|------|------|--------|------|------|
| BUILTINS.json | 0-97, 120-122 | 0-131 | ❌ | 🔴 漂移 |
| HOST_ABI.md | 0-131 | 0-131 | ✅ | ✅ |
| HTTP Stub 标记 | Stub | 已实现 | ✅ | 🔴 文档过期 |
| README 版本 | v1.1.0 | P0-12 | ❌ | 🔴 严重滞后 |

## 7. Dogfooding 项目

| 项目 | 状态 | 覆盖能力 | 备注 |
|------|------|---------|------|
| TLL Compiler (自举) | ✅ | Compiler/VM/Module | 核心验证 |
| TLL Shop (商城) | 🟡 | HTTP/Session/Persistence/JSON | Dogfooding |
| 实时行情系统 | ✅ | Observable/Events/Closure | P0-11 验证 |
| EventEmitter 测试 | 🟡 | Events/Closure | once 有 Bug |

## 8. P0-12 修复记录

| Bug | 根因 | 修复 | 状态 |
|-----|------|------|------|
| 匿名 lambda 闭包崩溃 | 函数索引错位 | 第二遍循环添加 main 占位符 | ✅ 已修复 |
| 匿名 lambda 捕获变量错误 | OP_CLOSURE 操作数错误 | 根据实际引用变量查找 slot | ✅ 已修复 |
| 命名函数被嵌套函数引用时未装箱 | 缺少 OP_BOX_LOCAL | Fn 语句后添加 OP_BOX_LOCAL | ✅ 已修复 |
| 命名函数名称不在 boundNames 中 | cg_collectAllParamsAndLocals 遗漏 Fn | 添加 Fn 名称到 boundNames | ✅ 已修复 |
| 通过匿名 lambda 读取命名函数得到 null | 待深入调试 | 临时方案：let 变量中转 | ⚠️ 已知限制 |
| EventEmitter once() 不工作 | 依赖上述 Bug | 临时方案：避免 once | ⚠️ 已知限制 |

## 9. 总结

### 已验证为真实的能力
- Lexer/Parser/AST/Compiler/Bytecode/VM 完整链路
- Function / Lambda / Closure（P0-12 重大修复）
- Struct / Enum（基础能力）
- Module / Import
- Exception / try-catch-finally
- HTTP Client / HTTP Server MVP
- FS / Time / Process
- JSON / Math / Array / String
- Worker Pool + 全局 VM 锁（HTTP 并发）
- Frame Pool + maxRegister 优化（P0-10）
- 自举编译器
- 商城 Dogfooding
- 实时行情系统 Dogfooding

### 存在已知限制的能力
- Struct 实例化（使用 __struct hack）
- Enum 访问（常量替换，非真正 Variant）
- Type Checker（experimental/warning-only）
- TLL VM（并行实现，部分 opcode）
- Package（只有 Manifest，完整 workflow 未验证）
- HTTP Server（MVP，非完整 Application Runtime）
- EventEmitter once()（受闭包 Bug 影响）
- 通过匿名 lambda 读取命名函数（已知 Bug）

### 明确缺失的能力
- 真并行执行（全局 VM 锁）
- 原子引用计数
- 函数超时 / 取消
- 泛型 / 类型推导 / 类型反射
- Stream / Buffer / Binary
- TCP / 低级网络
- 数据库
- 调试器 / LSP
- 完整 Package Manager
- Formatter / Linter（基础存在，未完善）

### Spec / 文档漂移
- BUILTINS.json 与实际 ABI 漂移（0-97,120-122 vs 0-131）
- HOST_ABI.md HTTP 标记为 Stub（实际已实现）
- README 版本严重滞后（v1.1.0 vs P0-12）
