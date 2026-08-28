# TLL OS Universal Capability Matrix
# Real Software Driven Language Evolution

## 方法论
不是先猜 TLL 缺什么，而是拿 TLL 开发真正复杂的软件，让真实工程把语言缺陷"逼"出来。

每发现一个缺口，必须判断层级归属：
- **Language Core**：语法/类型系统/语义 → Compiler / VM / Spec
- **Runtime**：调度器/网络/线程/内存/文件/进程 → Runtime
- **Stdlib**：HTTP Client/JSON/Crypto/Collections/DateTime → 标准库
- **Host ABI**：只有真正触碰操作系统时才进入 C

硬规则：禁止"发现缺少 X，临时在 C 里加函数让项目跑起来"。

---

## 压力机 1：区块链 (P0-15)

### 已逼出的能力缺口（7个）

| # | 缺口 | 层级 | 修复方式 | 状态 | Commit |
|---|------|------|----------|------|--------|
| 1 | 位运算 opcode 完全缺失 | Language Core (VM/Compiler) | 新增 OP_BAND..OP_ROTL (46-53) | ✅ 已修复 | 03a9765 |
| 2 | 十六进制字面量全返回0 | Language Core (Codegen) | 实现 cg_parseInt/cg_hexDigit | ✅ 已修复 | 03a9765 |
| 3 | strings.fromCharCode 返回空 | Stdlib/Host | 改用字节数组 API | ✅ 已绕过 | bc9e927 |
| 4 | convert.toInt 不支持十六进制 | Host ABI | charCodeAt 解析 | ✅ 已绕过 | bc9e927 |
| 5 | from/to 是关键字不能作字段名 | Language Core (Parser) | 重命名 struct 字段 | ✅ 已绕过 | 4524a62 |
| 6 | /* */ 块注释不支持 | Language Core (Lexer) | 改用 // 行注释 | ✅ 已绕过 | 03a9765 |
| 7 | list 无真正删除操作（设null不减长度） | Runtime/VM | count变量 + 数组压缩 | 🟡 已绕过，需Runtime修复 | 43a571c |

### 已知 P0 问题

| # | 问题 | 层级 | 状态 |
|---|------|------|------|
| 1 | SHA-256('abc') H[4] 低4位差异 | Stdlib (crypto) | 🔴 已锁定回归测试，待修复 |
| 2 | 自引用闭包引用计数环 | Runtime (GC/refcount) | 🔴 P0-14 已知，待修复 |

### 已验证能力

| 能力 | 层级 | 验证方式 | 状态 |
|------|------|----------|------|
| Struct | Language Core | Transaction/Block/Mempool struct | ✅ |
| Enum | Language Core | (区块链未深度使用) | 🟡 |
| Lambda/Closure | Language Core | EventEmitter once() 自引用 | ✅ P0-14修复 |
| Module/Import | Language Core | stdlib/crypto, blockchain, mempool | ✅ |
| Error Handling | Language Core | validateTransaction 返回bool | 🟡 基础 |
| Map | Runtime | txIndex 哈希表 | ✅ |
| List/Array | Runtime | transactions 列表 | 🟡 无删除 |
| String | Stdlib | 十六进制/字节处理 | ✅ |
| Math | Stdlib | 位运算/哈希 | ✅ |
| Crypto (SHA-256/HMAC) | Stdlib | 交易签名/区块哈希 | 🟡 5/6向量 |
| HTTP Client | Stdlib | (区块链未使用) | ✅ P0-3 |
| HTTP Server | Stdlib | (区块链未使用) | ✅ P0-3 |
| File/FS | Host ABI | (区块链未使用) | ✅ P0-3 |
| Time | Host ABI | transaction timestamp | ✅ |
| Process | Host ABI | (区块链未使用) | ✅ P0-3 |

### 待施工阶段（P0-15.7 ~ P0-15.12）

| 阶段 | 内容 | 预计逼出的能力 |
|------|------|----------------|
| 15.7 | Stream | iterator, map/filter/reduce, buffer, backpressure, producer/consumer |
| 15.8 | Task / Channel | Task, Scheduler, Channel, send/receive, cancellation, timeout |
| 15.9 | P2P 网络 | TCP, Socket, Connection, Binary Buffer, Framing, Handshake, Peer |
| 15.10 | Consensus | 并发, State, Event, Task, Channel, Atomic, timeout |
| 15.11 | Persistence | WAL, Snapshot, Recovery, Database, Batch write, Crash recovery |
| 15.12 | RPC / API | HTTP API, JSON RPC, WebSocket, Metrics, Admin API |

---

## 压力机 2：Web 商业应用 (TLL Commerce) — 待启动

预计逼出能力：ORM, DB Pool, Transaction, Auth, Cookie, JWT, Session, Multipart, Upload, Template, Routing, Middleware, WebSocket, Cache, Search, RBAC

---

## 压力机 3：系统工具 — 待启动

预计逼出能力：CLI, Package Manager, Build Tool, Code Formatter, Linter, Debugger, LSP, Process Manager

---

## 压力机 4：跨平台应用 — 待启动

目标平台：Windows, Linux, Android, iOS, Web, H5, 小程序, Server

架构：TLL Application → TLL Compiler → Intermediate Layer → Native(ABI) / Web(WASM/JS) / Mobile(Platform SDK)

---

## TLL 真正目标

高帧率、AI-Native、可自举、可跨平台的**通用软件开发语言**。

- "高帧率"是运行时特征
- "AI-Native"是开发方式
- "自举"是生命力
- "能够开发任何独立软件"是最终验收标准
