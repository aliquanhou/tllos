# TLL OS 项目设计报告 v1.2

**日期**: 2026-08-27
**基准版本**: v1.1.0 (P0-2.4.1)
**仓库**: aliquanhou/tllos
**状态**: 设计草案

---

## 一、项目现状审计

### 1.1 已完成能力（FROZEN v1.1）

| 模块 | 状态 | 规模 |
|------|------|------|
| 词法分析器 Lexer | FROZEN | 纯TLL |
| 语法分析器 Parser | FROZEN | 纯TLL |
| 类型检查器 TypeChecker | FROZEN | 基础类型系统 |
| 代码生成器 Codegen | FROZEN | 46 opcode |
| 链接器 Linker | FROZEN | 支持模块/包 |
| 原生VM (tllvm) | 生产可用 | C实现, 83KB |
| 参考VM (vm.tll) | 参考实现 | 纯TLL, ~900行 |
| 闭包系统 | FROZEN | 8类测试全覆盖 |
| 异常系统 | FROZEN | try/catch/finally/throw |
| 模块系统 | FROZEN | 循环依赖/跨模块 |
| 包系统 | FROZEN | tll.toml manifest |
| 自举编译器 | FROZEN | 152函数/3867常量/18463指令 |
| 内置函数 | FROZEN | 98个 (idx 0-97) + 3个扩展 (120-122) |
| 进程API | 已实现 | process.argv/env/exit |

### 1.2 构建链验证结果

- `scripts/build.bat`: ✅ 成功，tllvm.exe 83456字节
- `scripts/bootstrap-tllc.bat`: ✅ 成功，tllc.tllbc 551050字节
- `tllc compile hello.tll`: ✅ 编译成功（2函数, 11常量）
- `tllvm hello.tllbc`: ⚠️ 输出文件写入存在路径问题（见1.4）

### 1.3 待实现能力

| 功能 | 预留位置 | 计划版本 |
|------|----------|----------|
| HTTP 客户端/服务端 | builtin idx 91-97 (STUB) | P0-2.8 |
| Agent Native Layer | builtin idx 98-119 (预留) | v1.2 |
| 泛型 Generics | 未预留 | v1.3+ |
| Async/Await | 未预留 | v1.3+ |
| 结构体 Struct | opcode 27 (预留) | v1.2 |
| 统一CLI (tll run/build/check) | 未实现 | P0-2.5 |
| 预编译二进制发布 | 未实现 | P0-2.6 |

### 1.4 已知问题

**P0 - fs.writeFile 路径问题**:
- 现象：tllc compile 报告成功，但输出 .tllbc 文件在指定路径不存在
- 影响：所有编译输出无法落盘
- 根因推测：C VM 中 fs.writeFile 对 Windows 绝对路径（含反斜杠/冒号）处理异常
- 修复优先级：最高，阻塞所有编译工作流

---

## 二、架构决策确认（ADR-001 落地）

### 2.1 决策：方案B — Native tllvm 作为唯一生产VM

**最终架构**:
```
用户源码 (.tll)
    ↓ tllc (纯TLL编译器, 运行于tllvm)
字节码 (.tllbc, JSON格式)
    ↓ tllvm (C原生VM)
执行结果
```

**runtime/vm.tll 新定位**:
- Reference VM：字节码语义的参考实现
- 自举验证器：验证编译器输出可被纯TLL VM执行
- 语言规范可执行版本：新特性原型验证
- 交叉验证工具：同一字节码在C/TLL VM输出一致性

### 2.2 双VM语义管理机制

| 规范文件 | 角色 |
|----------|------|
| `spec/OPCODES.json` | 46 opcode 唯一契约 |
| `spec/BYTECODE.md` | .tllbc 文件格式唯一规范 |
| `spec/HOST_ABI.json` | Host ABI 函数列表唯一规范 |
| `spec/VALUE_MODEL.md` | 运行时值表示唯一规范 |
| `spec/CLOSURE.md` | 闭包环境唯一规范 |

**规则**: 任何语义变更必须同时更新规范 + C VM + TLL VM + 测试。

---

## 三、v1.2 路线图设计

### 阶段 P0-2.5：工具链统一（1周）

**目标**: 提供统一的 `tll` CLI 入口

```
tll run <file.tll>      # 编译+执行（开发模式）
tll build <file.tll>    # 编译为 .tllbc
tll check <file.tll>    # 仅类型检查
tll info <file.tllbc>   # 字节码分析
tll test                 # 运行测试套件
tll version              # 版本信息
```

**实现**:
- 创建 `tools/tll/main.tll` 作为统一入口
- Windows: `tll.bat` 包装器调用 tllvm
- Linux/macOS: `tll.sh` 包装器
- 安装脚本：将 tll 加入 PATH

### 阶段 P0-2.6：发布工程（1周）

**目标**: 预编译二进制 + 安装器

- GitHub Actions 自动构建 Windows/Linux/macOS 三平台 tllvm
- Release 页面提供下载
- Windows: `tllos-installer.exe` (NSIS)
- Linux: `tllos-linux-x64.tar.gz` + install.sh
- macOS: `tllos-darwin-arm64.tar.gz`
- 版本号管理：`spec/VERSION` 文件

### 阶段 P0-2.7：fs/IO 修复与增强（1周）

**目标**: 修复 P0 级 bug，增强文件系统能力

- **修复**: fs.writeFile Windows 路径问题（最高优先级）
- **新增**: fs.readDir 递归选项
- **新增**: fs.watchFile (文件变更监听)
- **新增**: io.readBuffer (二进制读取)
- **新增**: process.setEnv / process.cwd / process.chdir
- **测试**: 跨平台路径一致性测试套件

### 阶段 P0-2.8：HTTP 模块实现（2周）

**目标**: 实现 builtin idx 91-97 的完整 HTTP 能力

**设计**:

| 函数 | 签名 | 实现方式 |
|------|------|----------|
| `http.get(url)` | `(string) -> map{status, headers, body}` | 同步阻塞，基于libcurl/winhttp |
| `http.post(url, body)` | `(string, string) -> map` | 同上 |
| `http.request(options)` | `(map{method,url,headers,body}) -> map` | 通用请求 |
| `http.serve(addr, handler)` | `(string, fn(req)->res) -> void` | 内嵌HTTP服务器 |
| `http.encodeURI(s)` | `(string) -> string` | 纯计算，可TLL实现 |
| `http.decodeURI(s)` | `(string) -> string` | 纯计算 |
| `http.parseJSON(s)` | `(string) -> map` | 复用json.parse |

**C VM 实现依赖**:
- Windows: WinHTTP (系统自带)
- Linux: libcurl-dev (构建时依赖)
- macOS: NSURLSession (通过Objective-C bridge)

**请求/响应 Map 结构**:
```
request = {
  method: "GET",
  url: "https://api.example.com/data",
  headers: {"Content-Type": "application/json"},
  body: "..."
}
response = {
  status: 200,
  headers: {"Content-Type": "application/json"},
  body: "...",
  ok: true
}
```

**http.serve 处理函数签名**:
```
fn handler(req: map) -> map {
  return {
    status: 200,
    headers: {"Content-Type": "text/html"},
    body: "<h1>Hello from TLL OS</h1>"
  }
}
http.serve("0.0.0.0:8080", handler)
```

### 阶段 P0-2.9：Struct 结构体（2周）

**目标**: 激活 opcode 27 (MAKE_STRUCT)，实现用户自定义类型

**语法设计**:
```tll
struct Point {
  x: float
  y: float
  label: string
}

fn makePoint(x: float, y: float) -> Point {
  return Point{x: x, y: y, label: "origin"}
}

let p = makePoint(3.0, 4.0)
io.println(p.x)  // 3.0
io.println(p.label)  // "origin"
```

**字节码层面**:
- OP_MAKE_STRUCT (27): `r, type_index, field_count`
- OP_MEMBER_GET (30): 已存在，用于 struct 字段读取
- OP_MEMBER_SET (31): 已存在，用于 struct 字段写入
- 常量池新增 STRUCT_TYPE 条目

**类型系统扩展**:
- TypeChecker 识别 struct 定义
- 字段类型检查
- struct 作为函数参数/返回值类型

### 阶段 v1.2.0：Agent Native Layer（4周）

**目标**: 实现 builtin idx 98-119，为 AI Agent 提供原生支持

**设计理念**: TLL OS 是 AI-Native 语言，Agent 是一等公民。

#### 3.1 Agent 核心模型

```tll
// 创建一个 Agent
let agent = agent.create({
  name: "code-reviewer",
  model: "deepseek-chat",
  systemPrompt: "You are a code reviewer.",
  tools: [http.get, fs.readFile]
})

// 同步调用
let response = agent.run(agent, "Review this code: ...")
io.println(response.content)

// 流式调用
agent.stream(agent, "Explain this", fn(chunk) {
  io.print(chunk)
})
```

#### 3.2 Builtin 分配（idx 98-119，共22个）

| idx | 名称 | 签名 | 说明 |
|-----|------|------|------|
| 98 | `agent.create` | `(config: map) -> agent` | 创建Agent实例 |
| 99 | `agent.run` | `(agent, prompt: string) -> map` | 同步调用，返回{content, usage} |
| 100 | `agent.stream` | `(agent, prompt, callback: fn) -> void` | 流式输出 |
| 101 | `agent.chat` | `(agent, messages: array) -> map` | 多轮对话 |
| 102 | `agent.addTool` | `(agent, name: string, fn: fn) -> void` | 注册工具函数 |
| 103 | `agent.removeTool` | `(agent, name: string) -> void` | 移除工具 |
| 104 | `agent.listTools` | `(agent) -> array<string>` | 列出已注册工具 |
| 105 | `agent.setSystemPrompt` | `(agent, prompt: string) -> void` | 设置系统提示 |
| 106 | `agent.getConfig` | `(agent) -> map` | 获取配置 |
| 107 | `agent.destroy` | `(agent) -> void` | 释放资源 |
| 108 | `workflow.sequential` | `(steps: array<fn>) -> any` | 顺序执行工作流 |
| 109 | `workflow.parallel` | `(tasks: array<fn>) -> array` | 并行执行 |
| 110 | `workflow.retry` | `(fn, maxRetries: int, delay: int) -> any` | 带重试执行 |
| 111 | `workflow.loop` | `(fn, condition: fn) -> any` | 条件循环 |
| 112 | `memory.create` | `(config: map) -> memory` | 创建记忆存储 |
| 113 | `memory.add` | `(memory, text: string, metadata?: map) -> void` | 添加记忆 |
| 114 | `memory.search` | `(memory, query: string, k?: int) -> array` | 语义检索 |
| 115 | `memory.clear` | `(memory) -> void` | 清空记忆 |
| 116 | `memory.list` | `(memory) -> array` | 列出所有记忆 |
| 117 | `agent.setProvider` | `(agent, provider: map) -> void` | 设置LLM提供商配置 |
| 118 | `agent.getProviders` | `() -> array<string>` | 列出支持的提供商 |
| 119 | `agent.version` | `() -> string` | Agent Layer 版本 |

#### 3.3 Provider 抽象层

支持多 LLM 提供商，通过统一接口适配：

```tll
// 配置提供商
agent.setProvider(agent, {
  type: "openai-compatible",
  baseURL: "https://api.deepseek.com/v1",
  apiKey: process.env()["DEEPSEEK_API_KEY"],
  model: "deepseek-chat"
})

// 内置提供商
// - openai (api.openai.com)
// - deepseek (api.deepseek.com)
// - anthropic (api.anthropic.com)
// - ollama (localhost:11434, 本地模型)
// - openai-compatible (任意兼容端点)
```

#### 3.4 Tool Calling 机制

Agent 可调用 TLL 函数作为工具：

```tll
fn getWeather(city: string) -> string {
  let url = "https://api.weather.com/?city=" + http.encodeURI(city)
  let resp = http.get(url)
  return resp.body
}

agent.addTool(agent, "get_weather", getWeather)

// Agent 自动决定是否调用工具
let response = agent.run(agent, "北京今天天气怎么样？")
// Agent 内部: 调用 get_weather("北京") -> 整合结果 -> 返回
```

#### 3.5 工作流原语

```tll
// 顺序工作流
let result = workflow.sequential([
  fn() { return agent.run(agent, "第一步") },
  fn(prev) { return agent.run(agent, "基于" + prev + "做第二步") },
  fn(prev) { return agent.run(agent, "最终输出") }
])

// 并行工作流
let results = workflow.parallel([
  fn() { return http.get("https://api1.com/data") },
  fn() { return http.get("https://api2.com/data") },
  fn() { return http.get("https://api3.com/data") }
])

// 重试工作流
let data = workflow.retry(
  fn() { return http.get("https://unstable-api.com/data") },
  3,    // maxRetries
  1000  // delay ms
)
```

---

## 四、标准库扩展设计

### 4.1 纯 TLL 标准库（不占 builtin 槽位）

创建 `stdlib/` 目录，用纯 TLL 实现常用功能，通过模块系统导入：

```
stdlib/
├── collections/
│   ├── linkedlist.tll    # 链表
│   ├── stack.tll         # 栈
│   ├── queue.tll         # 队列
│   └── set.tll           # 集合（基于map）
├── encoding/
│   ├── base64.tll        # Base64编解码
│   ├── hex.tll           # 十六进制
│   └── url.tll           # URL编解码
├── crypto/
│   ├── sha256.tll        # SHA256（自举验证已用）
│   ├── md5.tll           # MD5
│   └── hmac.tll          # HMAC
├── time/
│   ├── datetime.tll      # 日期时间处理
│   └── timer.tll         # 计时器
├── testing/
│   └── assert.tll        # 测试断言库
└── utils/
    ├── uuid.tll          # UUID生成
    └── validator.tll     # 数据校验
```

### 4.2 包管理器增强

`tll.toml` 格式扩展：

```toml
[package]
name = "my-app"
version = "1.0.0"
description = "My TLL application"
author = "Your Name"
license = "MIT"

[dependencies]
"tllos/std" = "1.2.0"
"tllos/http-server" = "0.1.0"

[dev-dependencies]
"tllos/testing" = "1.0.0"

[scripts]
build = "tll build src/main.tll -o dist/app.tllbc"
test = "tll test"
run = "tll run src/main.tll"
```

包管理命令：
```
tll pkg install <name>    # 安装依赖
tll pkg update            # 更新所有依赖
tll pkg list              # 列出已安装包
tll pkg publish           # 发布包到 registry
tll pkg init              # 初始化 tll.toml
```

---

## 五、测试体系设计

### 5.1 测试分层

| 层级 | 目录 | 工具 | 覆盖目标 |
|------|------|------|----------|
| 单元测试 | `tests/unit/` | tll test | 单个函数/模块 |
| 集成测试 | `tests/integration/` | tll test | 多模块协作 |
| 语言验收 | `tests/acceptance/` | run-tests.sh | 语言特性 |
| 闭包测试 | `tests/closure/` | run-tests.sh | 闭包语义 |
| 异常测试 | `tests/exception/` | run-tests.sh | 异常处理 |
| 模块测试 | `tests/module-system/` | run-tests.sh | 模块/包 |
| VM一致性 | `tests/runtime-equivalence/` | 双VM对比 | C VM vs TLL VM |
| 回归测试 | `tests/regression/` | run-tests.sh | Bug修复验证 |
| 自举测试 | `compiler/` | 手动 | 编译器自编译 |
| ABI一致性 | `scripts/check-abi` | check-abi.bat | spec vs builtin.c |

### 5.2 测试断言库（stdlib/testing/assert.tll）

```tll
from "tllos/testing" import assert, test, describe

describe("math operations", fn() {
  test("addition", fn() {
    assert.equals(1 + 1, 2)
    assert.notEquals(1 + 1, 3)
  })
  test("division by zero", fn() {
    assert.throws(fn() { 1 / 0 })
  })
})
```

### 5.3 CI 流水线

`.github/workflows/ci.yml` 扩展：
1. 构建 tllvm (Windows/Linux/macOS)
2. 引导 tllc
3. 编译所有测试
4. 运行全部测试
5. ABI一致性检查
6. 自举确定性验证 (A==B==C)
7. VM一致性对比
8. 代码覆盖率统计

---

## 六、文档体系设计

### 6.1 文档结构

```
docs/
├── getting-started/
│   ├── quickstart.md          # 快速开始
│   ├── installation.md        # 安装指南
│   └── first-program.md       # 第一个程序
├── language/
│   ├── syntax.md              # 语法参考
│   ├── types.md               # 类型系统
│   ├── control-flow.md        # 控制流
│   ├── functions.md           # 函数与闭包
│   ├── modules.md             # 模块与包
│   ├── error-handling.md      # 异常处理
│   └── structs.md             # 结构体(v1.2)
├── stdlib/
│   ├── io.md                  # IO模块
│   ├── fs.md                  # 文件系统
│   ├── http.md                # HTTP模块
│   ├── math.md                # 数学
│   ├── strings.md             # 字符串
│   ├── arrays.md              # 数组
│   ├── json.md                # JSON
│   ├── process.md             # 进程
│   └── agent.md               # Agent Layer(v1.2)
├── tools/
│   ├── tll-cli.md             # CLI参考
│   ├── tllc.md                # 编译器
│   └── debugging.md           # 调试技巧
├── advanced/
│   ├── bytecode-format.md     # 字节码格式
│   ├── vm-internals.md        # VM内部
│   ├── self-hosting.md        # 自举原理
│   └── embedding.md           # 嵌入TLL到其他程序
├── architecture/
│   ├── overview.md            # 架构总览
│   ├── adr-001.md             # 生产执行器决策
│   └── design-philosophy.md   # 设计哲学
└── development/
    ├── contributing.md        # 贡献指南
    ├── coding-standards.md    # 编码规范
    ├── release-process.md     # 发布流程
    └── P0-*.md                # 开发日志
```

### 6.2 官网设计（规划）

- 域名：tllos.dev（待注册）
- 技术栈：纯静态HTML + TLL编译生成
- 功能：文档浏览、在线Playground、包搜索
- Playground：WebAssembly版tllvm，浏览器内运行TLL代码

---

## 七、生态系统规划

### 7.1 核心包（官方维护）

| 包名 | 功能 | 状态 |
|------|------|------|
| `tllos/std` | 标准库扩展 | 规划 |
| `tllos/http-server` | Web框架（路由/中间件） | 规划 |
| `tllos/json-schema` | JSON Schema校验 | 规划 |
| `tllos/testing` | 测试框架 | 规划 |
| `tllos/logger` | 日志库 | 规划 |
| `tllos/cli` | CLI工具构建库 | 规划 |
| `tllos/database` | 数据库抽象层 | 规划 |
| `tllos/agent` | Agent开发框架 | v1.2 |

### 7.2 应用场景

1. **AI Agent 开发**: 原生 Agent Layer，快速构建智能体
2. **Web 后端**: http.serve + 路由，构建API服务
3. **脚本工具**: 替代Python/Shell，跨平台自动化
4. **嵌入式语言**: tllvm可嵌入C/C++/Rust程序
5. **教育**: 简洁语法，适合编程入门
6. **区块链智能合约**: 确定性执行 + 沙箱

---

## 八、立即行动项（按优先级）

### P0 - 阻塞修复（立即）

1. **修复 fs.writeFile Windows路径问题**
   - 定位：`host/c/builtin.c` 中 fs_writeFile 实现
   - 验证：编译 hello.tll 后确认 .tllbc 落盘
   - 测试：新增跨平台路径测试

2. **确认 ADR-001 方案B**
   - 更新 README/ARCHITECTURE 中 "100%纯TLL VM" 表述
   - 明确 vm.tll 参考实现定位
   - 标记 ADR 状态为 "已确认"

### P1 - 工具链（本周）

3. **实现统一 `tll` CLI**
   - `tll run/build/check/info/test/version`
   - Windows .bat + Linux/macOS .sh 包装器
   - 安装脚本

4. **修复并完善测试运行器**
   - `scripts/run-tests.bat` 全量测试通过
   - 测试结果汇总报告
   - 失败测试详细输出

### P2 - 核心能力（本月）

5. **实现 HTTP 模块（P0-2.8）**
   - Windows: WinHTTP 实现
   - http.get/post/request/serve
   - 示例：HTTP服务器 demo

6. **实现 Struct 结构体（P0-2.9）**
   - 语法：struct 定义 + 实例化
   - 激活 opcode 27
   - 类型检查器扩展

### P3 - v1.2 里程碑（下月）

7. **Agent Native Layer**
   - 22个 builtin (idx 98-119)
   - Provider 抽象（OpenAI/DeepSeek/Ollama）
   - Tool Calling 机制
   - 工作流原语（sequential/parallel/retry/loop）
   - 记忆系统

8. **v1.2.0 发布**
   - 全量测试通过
   - 文档完整
   - 三平台预编译二进制
   - Release Notes

---

## 九、风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| C VM fs.writeFile bug 难以定位 | 阻塞编译工作流 | 高 | 优先修复，添加调试日志，对比TLL VM行为 |
| HTTP模块跨平台实现复杂 | 延迟P0-2.8 | 中 | 先用最小实现（http.get），逐步扩展 |
| Agent Layer 依赖外部API | 测试不稳定 | 中 | 提供 Mock Provider，测试不依赖网络 |
| 双VM语义分叉 | 长期维护成本 | 中 | 严格规范驱动，自动化一致性测试 |
| 社区采用率低 | 生态发展慢 | 高 | 优秀文档 + 示例 + 与AI场景深度绑定 |

---

## 十、成功指标

| 指标 | v1.1 现状 | v1.2 目标 |
|------|-----------|-----------|
| 内置函数数量 | 101 | 123 (含Agent 22) |
| 测试用例数 | ~120 | 200+ |
| 测试通过率 | 待验证 | 100% |
| 支持平台 | Windows (已验证) | Win/Linux/macOS |
| 文档页数 | ~15 | 50+ |
| 示例程序 | 6 | 20+ |
| GitHub Stars | - | 100+ (社区目标) |
| 自举确定性 | A==B==C 已验证 | 持续保持 |

---

**报告结束**

下一步：确认 P0 修复项后立即执行 fs.writeFile 修复和 ADR-001 确认。
