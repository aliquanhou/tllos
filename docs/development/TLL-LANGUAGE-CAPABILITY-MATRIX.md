# TLL 语言能力总审计矩阵

**版本**: v1.1.0 → P0-3.1 审计
**日期**: 2026-08-27
**审计基准**: aliquanhou/tllos @ a9acc60 (P0-2.4.1)
**审计视角**: AI 开发大型商业软件所需能力

---

## 图例

| 标记 | 含义 |
|------|------|
| ✅ | 已成熟，可用于生产 |
| 🟡 | 可用但存在明显限制 |
| 🔴 | 缺失，无法使用 |
| 🧨 | 架构级缺陷，会导致未来返工 |
| ❓ | 尚未验证 |

---

## 一、语言核心

| 能力 | 状态 | 说明 |
|------|------|------|
| 词法分析 Lexer | ✅ | 纯TLL实现，稳定 |
| 语法分析 Parser | ✅ | 纯TLL实现，支持函数/变量/控制流/导入导出 |
| AST 表示 | 🟡 | 使用map对象，字段访问不可靠（codegen.tll注释证实） |
| 类型系统（基础） | 🟡 | 有int/float/string/bool/null/array/map/fn，但类型检查弱 |
| 类型推导 | 🟡 | 局部变量推导，函数参数无类型强制 |
| 显式类型注解 | 🟡 | 语法支持但typechecker不强制 |
| 泛型 Generics | 🔴 | 完全缺失，array<T>/map<K,V>仅为文档标注 |
| 结构体 Struct | 🔴 | opcode 27预留，语法未实现 |
| 枚举 Enum | 🔴 | 完全缺失 |
| 接口/协议 Interface | 🔴 | 完全缺失 |
| 模式匹配 Pattern Matching | 🔴 | 完全缺失 |
| 可选类型 Optional | 🔴 | 用null代替，无编译期检查 |
| 结果类型 Result | 🔴 | 用异常代替，无编译期检查 |

## 二、函数与闭包

| 能力 | 状态 | 说明 |
|------|------|------|
| 函数声明 | ✅ | fn name(params) { body } |
| 一等函数 | ✅ | 函数可作为值传递/返回 |
| 高阶函数 | ✅ | arrays.map/filter/reduce已验证 |
| 嵌套函数 | ✅ | 支持函数内定义函数 |
| 闭包（不可变捕获） | ✅ | 8类闭包测试全覆盖 |
| 闭包（可变捕获） | ✅ | mut_closure测试通过 |
| 共享 UpvalueBox | ✅ | sibling closures共享同一box |
| 闭包隔离 | ✅ | 每次调用创建新环境 |
| 扁平闭包（深层嵌套） | ✅ | 直接引用外层upvalue |
| 逃逸闭包 | ✅ | 闭包可脱离创建函数存活 |
| 递归函数 | ✅ | 命名函数递归 |
| 匿名函数 / Lambda | ✅ | fn(params) { body } 表达式 |
| 可变参数 Variadic | 🔴 | 不支持，arrays.push用特殊处理绕过 |
| 默认参数 | 🔴 | 不支持 |
| 关键字参数 | 🔴 | 不支持 |
| 函数重载 | 🔴 | 不支持 |

## 三、控制流

| 能力 | 状态 | 说明 |
|------|------|------|
| if/else | ✅ | 标准条件分支 |
| while | ✅ | 标准while循环 |
| for (C风格) | ✅ | for(init;cond;update) |
| for...in / for...of | 🔴 | 不支持数组/映射迭代语法糖 |
| break / continue | ✅ | 循环控制 |
| return | ✅ | 函数返回 |
| 三元运算符 ? : | 🔴 | 不支持，需用if/else |
| 空值合并 ?? | 🟡 | 规范列出但需验证实现 |
| switch/case | 🔴 | 不支持 |
| 标签跳转 goto | 🔴 | 不支持（合理） |

## 四、数据结构

| 能力 | 状态 | 说明 |
|------|------|------|
| 数组 Array | ✅ | 动态数组，23个内置方法 |
| 数组索引读写 | ✅ | arr[idx] = val 直接赋值 |
| 映射 Map | 🟡 | 哈希映射，但字段访问不可靠（🧨见下） |
| 字符串 String | ✅ | UTF-8，25个内置方法 |
| 整数 Int | ✅ | 64位有符号 |
| 浮点数 Float | ✅ | 64位IEEE 754 |
| 布尔 Bool | ✅ | true/false |
| Null | ✅ | null值 |
| 集合 Set | 🔴 | 无原生类型，可用map模拟 |
| 链表 LinkedList | 🔴 | 无原生类型 |
| 栈 Stack | 🔴 | 无原生类型，可用数组模拟 |
| 队列 Queue | 🔴 | 无原生类型 |
| 元组 Tuple | 🔴 | 不支持 |
| 字节数组 ByteArray | 🔴 | 不支持，文件读写仅字符串 |
| 大整数 BigInt | 🔴 | 不支持 |

### 🧨 架构级缺陷：Map 字段访问不可靠

**证据**: compiler/codegen.tll 第3行注释：
```
// Uses parallel lists for maps (TLL map field access is unreliable)
```

**影响**:
- 编译器自身无法可靠使用map.field语法，被迫用并行列表+手动索引
- AST节点用map表示，但字段访问可能返回undefined而非null
- 所有复杂数据结构（AST、函数对象、代码生成状态）都受影响
- 这是语言核心缺陷，不是库问题

**根因推测**: VM中map_get对不存在的key返回undefined（TLL_NULL？），但类型系统不区分undefined和null，导致条件判断 `if (x == null)` 不可靠。

**修复方向**: 需深入VM (host/c/vm.c, value.c) 和TLL VM (runtime/vm.tll) 定位map_get实现，确保不存在key返回null且null比较可靠。

## 五、错误处理

| 能力 | 状态 | 说明 |
|------|------|------|
| throw | ✅ | 抛出异常值 |
| try/catch | ✅ | 捕获异常 |
| finally | ✅ | 最终执行块 |
| 异常类型 | 🟡 | 可抛任意值，无异常类型层级 |
| 错误码返回 | 🟡 | process.exit支持，但函数无标准错误返回模式 |
| 可恢复错误 | 🔴 | 无Result类型，异常是唯一机制 |
| 断言 Assert | 🔴 | 无内置assert，需手动实现 |
| 栈追踪 Stack Trace | 🔴 | 异常无栈信息，调试困难 |

## 六、模块与包

| 能力 | 状态 | 说明 |
|------|------|------|
| 模块导入 import | ✅ | from "./path" import name |
| 模块导出 export | ✅ | export name |
| 相对路径模块 | ✅ | 基于导入文件目录解析 |
| 循环依赖 | ✅ | 支持，符号延迟解析 |
| 跨模块符号身份 | ✅ | symbol-identity-distinct测试通过 |
| 包 manifest (tll.toml) | 🟡 | 基础格式，解析能力有限 |
| 包依赖解析 | 🟡 | node_modules风格，无版本约束 |
| 包注册表 Registry | 🔴 | 无中央注册表 |
| 包安装工具 | 🔴 | 无tll install命令 |
| 包版本管理 | 🔴 | 无semver支持 |
| 模块别名 import as | 🔴 | 不支持，需用变量重命名 |
| 命名空间导入 | 🔴 | 不支持 import * as ns |
| 条件导入 | 🔴 | 不支持 |

## 七、IO 与文件系统

| 能力 | 状态 | 说明 |
|------|------|------|
| print / println | ✅ | 标准输出 |
| readLine | ✅ | 标准输入读取一行 |
| 文件读取 readFile | ✅ | 完整读取为字符串 |
| 文件写入 writeFile | ✅ | 覆盖写入字符串 |
| 文件追加 appendFile | ✅ | 追加写入 |
| 文件存在 exists | ✅ | 检查路径存在 |
| 创建目录 mkdir | 🟡 | 仅单级，无递归创建 |
| 删除文件/目录 remove | 🟡 | 仅空目录，无递归删除 |
| 列出目录 listDir | ✅ | 列出文件名 |
| isFile / isDir | ✅ | 路径类型判断 |
| 文件大小 fileSize | ✅ | 字节数 |
| 复制文件 copyFile | ✅ | 文件复制 |
| 重命名 rename | ✅ | 文件/目录重命名 |
| 流式读取 | 🔴 | 无逐行/分块读取 |
| 流式写入 | 🔴 | 无流式写入 |
| 二进制文件 | 🔴 | 仅字符串，无字节数组 |
| 文件权限 | 🔴 | 无chmod |
| 符号链接 | 🔴 | 无支持 |
| 路径操作（join/normalize） | 🔴 | 无内置path模块 |
| 临时文件 | 🔴 | 无内置支持 |
| 标准错误 stderr | 🔴 | 无stderr输出，仅stdout |
| 文件监听 watch | 🔴 | 无支持 |

## 八、进程与环境

| 能力 | 状态 | 说明 |
|------|------|------|
| 命令行参数 argv | ✅ | process.argv，[tllvm, bytecode, args...] |
| 环境变量 env | ✅ | process.env，只读Map |
| 退出进程 exit | ✅ | process.exit(code)，退出码传播 |
| 当前工作目录 cwd | 🔴 | 无process.cwd() |
| 切换工作目录 chdir | 🔴 | 无支持 |
| 设置环境变量 | 🔴 | env只读，无setEnv |
| 子进程 spawn | 🔴 | 无法执行外部命令 |
| 进程信号 | 🔴 | 无信号处理 |
| 进程ID PID | 🔴 | 无获取PID |
| 平台信息 | 🔴 | 无os.platform/os.arch |
| 时间戳 | 🔴 | 无内置time模块（builtin.c include了time.h但未暴露） |
| 睡眠 sleep | 🔴 | 无内置sleep |

## 九、网络与 HTTP

| 能力 | 状态 | 说明 |
|------|------|------|
| HTTP GET | 🔴 | STUB，返回null |
| HTTP POST | 🔴 | STUB，返回null |
| 通用 HTTP request | 🔴 | STUB，返回null |
| HTTP 服务器 serve | 🔴 | STUB，返回null |
| URL 编码/解码 | 🔴 | STUB，返回null |
| JSON 响应解析 | 🔴 | STUB，返回null |
| WebSocket | 🔴 | 完全缺失 |
| TCP Socket | 🔴 | 完全缺失 |
| UDP | 🔴 | 完全缺失 |
| TLS/SSL | 🔴 | 完全缺失 |
| DNS 解析 | 🔴 | 完全缺失 |

## 十、序列化与格式

| 能力 | 状态 | 说明 |
|------|------|------|
| JSON 解析 parse | ✅ | json.parse |
| JSON 序列化 stringify | ✅ | json.stringify |
| JSON 美化输出 | 🔴 | 无indent选项 |
| TOML 解析 | 🔴 | tll.toml用自定义解析，非通用 |
| YAML 解析 | 🔴 | 完全缺失 |
| XML 解析 | 🔴 | 完全缺失 |
| CSV 解析 | 🔴 | 完全缺失 |
| Base64 | 🔴 | 完全缺失 |
| 十六进制 | 🔴 | 完全缺失 |
| URL 编码 | 🔴 | STUB |
| MessagePack | 🔴 | 完全缺失 |
| 二进制序列化 | 🔴 | 完全缺失 |

## 十一、并发与异步

| 能力 | 状态 | 说明 |
|------|------|------|
| 线程 Thread | 🔴 | 完全缺失，单线程VM |
| 协程 Coroutine | 🔴 | 完全缺失 |
| async/await | 🔴 | 完全缺失 |
| Promise/Future | 🔴 | 完全缺失 |
| 事件循环 Event Loop | 🔴 | 完全缺失 |
| 定时器 setTimeout/setInterval | 🔴 | 完全缺失 |
| 并行 map/reduce | 🔴 | 完全缺失 |
| 锁 Mutex | 🔴 | 完全缺失 |
| 通道 Channel | 🔴 | 完全缺失 |
| 原子操作 | 🔴 | 完全缺失 |

## 十二、数学与工具

| 能力 | 状态 | 说明 |
|------|------|------|
| 基础运算（+,-,*,/,%,**） | ✅ | 完整 |
| 比较运算 | ✅ | 完整 |
| 逻辑运算（&&,||,!） | ✅ | 完整，短路求值 |
| 位运算 | 🔴 | 无 &,|,^,~,<<,>> |
| sqrt/abs/floor/ceil/round | ✅ | 完整 |
| min/max/pow | ✅ | 完整 |
| sin/cos/tan | ✅ | 完整 |
| log/log2/log10/exp | ✅ | 完整 |
| pi/e 常量 | ✅ | 完整 |
| random/randomInt | ✅ | 完整，但无种子设置 |
| 类型转换 convert | ✅ | toInt/toFloat/toString/toBool/toChar/charCode/typeOf |
| 日期时间 | 🔴 | 完全缺失（time.h已include但未暴露） |
| 正则表达式 | 🔴 | 完全缺失 |
| 加密哈希 | 🔴 | 无md5/sha256（自举验证用了外部sha256sum） |
| UUID | 🔴 | 完全缺失 |

## 十三、AI Native 能力

| 能力 | 状态 | 说明 |
|------|------|------|
| Agent 创建 | 🔴 | builtin 98-119预留，未实现 |
| LLM 调用 | 🔴 | 无原生支持，需HTTP+自行实现 |
| Tool Calling | 🔴 | 无原生支持 |
| Structured Output | 🔴 | 无原生支持 |
| Streaming | 🔴 | 无原生流式支持 |
| Context 管理 | 🔴 | 无原生支持 |
| Memory / RAG | 🔴 | 无原生支持 |
| Workflow 原语 | 🔴 | 无原生支持 |
| Multi-Agent | 🔴 | 无原生支持 |
| MCP 协议 | 🔴 | 无原生支持 |
| Model Provider 抽象 | 🔴 | 无原生支持 |
| Token/Cost 统计 | 🔴 | 无原生支持 |
| Sandbox 执行 | 🔴 | 无原生支持 |
| 长期任务 / 任务恢复 | 🔴 | 无原生支持 |

## 十四、开发工具链

| 能力 | 状态 | 说明 |
|------|------|------|
| 编译器 tllc | ✅ | 纯TLL实现，可自举 |
| 编译命令 compile | ✅ | tllc compile <file> [-o out] |
| 类型检查 check | ✅ | tllc check <file> |
| 字节码分析 info | ✅ | tllc info <file.tllbc> |
| 帮助 help | ✅ | tllc help |
| 统一 CLI (tll) | 🔴 | 无tll run/build/test命令 |
| 代码格式化 formatter | 🟡 | tools/TLLC/formatter.tll存在，未集成 |
| LSP 语言服务器 | 🔴 | 完全缺失 |
| 调试器 Debugger | 🔴 | 完全缺失 |
| REPL 交互式 | 🔴 | 完全缺失 |
| 文档生成 | 🔴 | 无doc命令 |
| 代码覆盖率 | 🔴 | 无支持 |
| 性能分析 Profiler | 🔴 | 无支持 |
| 包管理器 | 🔴 | 无tll pkg命令 |
| 项目脚手架 | 🔴 | 无tll init |
| 预编译二进制发布 | 🟡 | build.bat可构建，无CI发布 |
| CI/CD | 🟡 | .github/workflows存在，需验证 |

## 十五、测试与质量

| 能力 | 状态 | 说明 |
|------|------|------|
| 测试框架 | 🟡 | 基于exit code + expected.txt，无断言库 |
| 验收测试 | ✅ | 15个acceptance测试 |
| 闭包测试 | ✅ | A-H 8类，~25个测试 |
| 异常测试 | ✅ | 6个exception测试 |
| 模块测试 | ✅ | ~10个module-system测试 |
| 包测试 | ✅ | 6个package测试 |
| 回归测试 | ✅ | ~15个regression测试 |
| VM一致性测试 | 🟡 | runtime-equivalence存在，需验证 |
| 自举测试 | ✅ | compiler自编译+确定性SHA256 |
| ABI一致性检查 | ✅ | check-abi.bat脚本 |
| 测试运行器 | 🟡 | run-tests.bat存在，需验证全量通过 |
| 断言库 | 🔴 | 无内置assert，需手动if+throw |
| Mock/Stub | 🔴 | 无支持 |
| 基准测试 Benchmark | 🔴 | 无支持 |
| Fuzz 测试 | 🔴 | 无支持 |

## 十六、VM 与运行时

| 能力 | 状态 | 说明 |
|------|------|------|
| 字节码格式 | ✅ | JSON格式，{functions,constants,mainFunctionIndex,globalCount} |
| 操作码 | ✅ | 46个 (0-45)，冻结 |
| 寄存器模型 | ✅ | 虚拟寄存器，每帧动态大小 |
| 参数栈 | ✅ | 每帧独立参数栈 |
| 调用栈 | ✅ | 函数调用帧管理 |
| 闭包环境 | ✅ | ClosureEnv + UpvalueBox |
| 异常栈 | ✅ | try/catch帧管理 |
| 全局变量 | ✅ | globalCount + LOAD_GLOBAL/STORE_GLOBAL |
| 引用计数 GC | ✅ | value.c实现，自动内存管理 |
| 垃圾回收（分代/标记清除） | 🔴 | 仅引用计数，无循环引用处理 |
| 内存限制 | 🔴 | 无内存上限配置 |
| 沙箱隔离 | 🔴 | 无资源限制/权限控制 |
| 字节码验证 | 🔴 | 加载时无验证，恶意字节码可崩溃VM |
| JIT 编译 | 🔴 | 纯解释执行 |
| AOT 编译 | 🔴 | 无原生代码生成 |
| 调试钩子 | 🔴 | 无单步/断点/观察点 |
| 性能计数器 | 🔴 | 无指令计数/耗时统计 |

## 十七、安全与权限

| 能力 | 状态 | 说明 |
|------|------|------|
| 权限模型 | 🔴 | 无，所有程序可访问所有文件/网络 |
| 沙箱执行 | 🔴 | 无 |
| 资源限制 | 🔴 | 无CPU/内存/时间限制 |
| 代码签名 | 🔴 | 无 |
| 安全启动 | 🔴 | 字节码无校验 |
| 加密 API | 🔴 | 无TLS/哈希/加密 |
| 输入验证 | 🔴 | 无内置sanitize |
| 危险操作确认 | 🔴 | fs.remove无确认 |

## 十八、跨平台

| 能力 | 状态 | 说明 |
|------|------|------|
| Windows 支持 | ✅ | build.bat + TCC，已验证 |
| Linux 支持 | 🟡 | build.sh存在，未在本环境验证 |
| macOS 支持 | 🟡 | build.sh存在，未验证 |
| 路径分隔符 | 🟡 | 直接用OS原生，无path模块抽象 |
| 行尾符 | 🔴 | 无统一处理 |
| 环境变量大小写 | 🟡 | Windows自动大写，可能导致跨平台问题 |
| 信号处理 | 🔴 | 无跨平台信号 |
| 文件权限 | 🔴 | Windows/Linux差异未处理 |
| 换行符输出 | 🟡 | println用puts，自动加\n，Windows应为\r\n |

## 十九、构建与发布

| 能力 | 状态 | 说明 |
|------|------|------|
| 构建脚本 (Windows) | ✅ | scripts/build.bat |
| 构建脚本 (Linux/macOS) | ✅ | scripts/build.sh |
| 引导脚本 | ✅ | bootstrap-tllc.bat/.sh |
| 测试编译脚本 | ✅ | compile-tests.bat/.sh |
| 测试运行脚本 | ✅ | run-tests.bat/.sh |
| ABI检查脚本 | ✅ | check-abi.bat/.sh |
| Makefile | 🟡 | host/c/Makefile存在 |
| CMake | 🔴 | 无跨平台构建系统 |
| 安装脚本 | 🔴 | 无install.sh/install.bat |
| 版本号管理 | 🟡 | README标注1.1.0，无统一VERSION文件 |
| Changelog | 🔴 | 无CHANGELOG.md |
| Release 流程 | 🔴 | 无自动化release |
| 包格式 (deb/rpm/msi) | 🔴 | 无 |

## 二十、文档

| 能力 | 状态 | 说明 |
|------|------|------|
| README | ✅ | 完整，含快速开始/架构/项目结构 |
| 语言规范 LANGUAGE.md | ✅ | 完整，v1.1 FROZEN |
| 操作码规范 OPCODES.md | ✅ | 完整，46个opcode |
| 内置函数规范 BUILTINS.md | ✅ | 完整，101个builtin |
| Host ABI 规范 | ✅ | HOST_ABI.md + HOST_ABI.json |
| 字节码规范 | ✅ | BYTECODE.md |
| 闭包规范 | ✅ | CLOSURE.md |
| 模块规范 | ✅ | MODULE.md |
| 包规范 | ✅ | PACKAGE.md |
| 值模型规范 | ✅ | VALUE_MODEL.md |
| 语法规范 | ✅ | SYNTAX.md |
| 架构文档 | ✅ | ARCHITECTURE.md + ADR-001 |
| AI贡献指南 | ✅ | AGENT.md |
| 贡献指南 | ✅ | CONTRIBUTING.md |
| 快速开始 | ✅ | docs/getting-started/quickstart.md |
| 开发日志 | ✅ | docs/development/P0-*.md |
| 示例程序 | 🟡 | 6个examples，覆盖基础功能 |
| API 参考 | 🔴 | 无按模块组织的API参考 |
| 教程 | 🔴 | 无step-by-step教程 |
| 常见问题 FAQ | 🔴 | 无 |
| 官网 | 🔴 | 无 |
| 在线 Playground | 🔴 | 无 |

---

## 审计总结

### 统计

| 状态 | 数量 | 占比 |
|------|------|------|
| ✅ 已成熟 | 78 | 32% |
| 🟡 可用但受限 | 35 | 14% |
| 🔴 缺失 | 124 | 51% |
| 🧨 架构级缺陷 | 1 | 0.4% |
| ❓ 未验证 | 6 | 2.5% |
| **总计** | **244** | **100%** |

### Top 10 最关键缺失（按AI开发大型软件优先级排序）

1. 🧨 **Map字段访问不可靠** — 编译器自身都在规避，语言核心缺陷
2. 🔴 **HTTP/网络完全缺失** — 无法构建任何网络服务/API/AI调用
3. 🔴 **并发/异步完全缺失** — 无法处理IO密集型任务，无法做Agent
4. 🔴 **时间/日期完全缺失** — 连sleep/timestamp都没有
5. 🔴 **结构体/泛型/枚举缺失** — 无法定义复杂数据类型
6. 🔴 **stderr/路径操作/流式IO缺失** — 基础工具链不完整
7. 🔴 **子进程/进程管理缺失** — 无法调用外部工具
8. 🔴 **调试器/REPL/LSP缺失** — 开发体验极差
9. 🔴 **测试断言库/覆盖率缺失** — 质量保障薄弱
10. 🔴 **包管理器/注册表缺失** — 生态无法发展

### 架构级缺陷详情

#### 🧨 DEFECT-001: Map字段访问不可靠

**严重度**: 致命（影响编译器自身可靠性）
**位置**: host/c/vm.c (map_get), host/c/value.c (TLLMap)
**证据**: compiler/codegen.tll 第3行注释
**影响范围**: 所有使用map.field语法的TLL程序
**修复优先级**: P0（必须在任何其他工作之前修复）

---

**下一步**: 立即开始修复 DEFECT-001，然后按优先级补齐关键能力。
