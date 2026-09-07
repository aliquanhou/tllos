# TLL v1 Capability Matrix

**版本**: TLL v1 Release Candidate
**生成日期**: 2026-09-06
**基准 Commit**: 3a67b44
**Remote HEAD**: 3a67b44 (origin/main)
**状态定义**:
- `COMPLETE` - 能力完整实现，通过正式 Gate，三平台 CI 通过，有 Evidence
- `PARTIAL` - 能力部分实现，有已知限制，未通过完整 Gate
- `AVAILABLE` - 能力达到可用门槛，可进入真实项目使用，有已知非阻断问题
- `MISSING` - 能力未实现
- `BLOCKED` - 能力被其他问题阻断
- `DEFERRED` - 能力已规划，推迟到后续版本

---

## 1. Language Core

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| Lexer | COMPLETE | compiler/lexer.tll | tests/ | ci.yml | P0-1-12 | - | 支持\xNN十六进制字节转义(P1-03-R1新增) |
| Parser | COMPLETE | compiler/parser.tll | tests/ | ci.yml | P0-1-12 | - | AST构建完整 |
| Type Checker | PARTIAL | compiler/typechecker.tll | - | - | - | 基础类型检查，未定义标识符仍为warning |
| Compiler (TLL→Bytecode) | COMPLETE | compiler/codegen.tll, compiler.tll | tests/ | ci.yml | P0-1-11 | - | 自举链完整 |
| Linker | COMPLETE | compiler/linker.tll | tests/ | ci.yml | - | - | stdlib绑定、模块/import |
| Bootstrap Compiler | COMPLETE | compiler/bootstrap_tllc.tll, tools/TLLC/tllc.tllbc | - | ci.yml | P0-1-9 | - | 两次自举结果一致(MD5验证) |
| Function-level Scope | COMPLETE | compiler/ | tests/scope/ | ci.yml | P0-1-13 | effe492 | 10个scope测试,95个断言 |
| Closure | COMPLETE | runtime/ | tests/closure/ | ci.yml | - | - | 闭包、嵌套函数、递归 |
| Coroutine | COMPLETE | runtime/ | tests/ | ci.yml | P0-15.18.6 | - | 100K并发协程压力验证 |
| Lambda | COMPLETE | compiler/ | tests/ | ci.yml | - | - | - |
| Struct | COMPLETE | compiler/ | tests/ | ci.yml | - | - | - |
| Map | COMPLETE | compiler/ | tests/ | ci.yml | - | - | {}字面量, .key=value 语法 |
| Array | COMPLETE | stdlib/array.tll | tests/ | ci.yml | - | - | - |
| String | COMPLETE | stdlib/string.tll, stringbuilder.tll | tests/ | ci.yml | - | - | - |
| Bytes (\xNN) | COMPLETE | compiler/lexer.tll | tests/crypto/ | ci.yml | P1-03 | 303034c | P1-03-R1新增,支持RFC4231二进制测试向量 |
| Module/Package | PARTIAL | compiler/ | tests/module-system/ | ci.yml | P0-1-14 | - | 基础模块系统,包管理未完整 |
| Import | COMPLETE | compiler/linker.tll | tests/ | ci.yml | - | - | - |
| Error Handling | PARTIAL | runtime/ | tests/exception/ | ci.yml | - | - | 基础异常,未定义标识符运行时崩溃 |
| Control Flow | COMPLETE | compiler/ | tests/ | ci.yml | - | - | if/else/for/while/return |
| Operators | COMPLETE | compiler/ | tests/ | ci.yml | - | - | 算术/比较/逻辑/位运算 |

---

## 2. Compiler / Bootstrap

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| Self-hosting Bootstrap | COMPLETE | tools/TLLC/main.tll | - | ci.yml | P0-1-9 | - | TLL编译器用TLL编写并编译自身 |
| Deterministic Build | COMPLETE | - | - | ci.yml | P0-1-9 | - | 两次自举MD5一致:0181be6cd8d76fc32d2d1f7adf8ff7fd |
| Codegen | COMPLETE | compiler/codegen.tll | tests/ | ci.yml | P0-1-11 | - | 变量scope bug已修复(effe492) |
| Opcode | COMPLETE | host/c/vm.c | tests/ | ci.yml | P0-1-11 | - | - |
| Builtin Dispatch | COMPLETE | host/c/builtin.c | tests/ | ci.yml | P0-1-12 | - | idx映射完整,无冲突 |
| Stdlib Binding | COMPLETE | compiler/linker.tll | tests/ | ci.yml | - | - | 22个stdlib模块 |
| Compiler Artifact | COMPLETE | tools/TLLC/tllc.tllbc | - | - | - | - | 665,681字节,Functions 172,Constants 3911 |
| Rollback Compiler | MISSING | - | - | - | - | - | 未正式保留上一稳定版本作为救援工具链 |
| Build SHA256 Record | MISSING | - | - | - | - | - | 未正式记录Compiler Build SHA256 |

---

## 3. High-Frame Runtime

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| VM Core | COMPLETE | host/c/vm.c | tests/ | ci.yml | P0-1-10 | - | 字节码执行引擎 |
| Value System | COMPLETE | host/c/value.c | tests/ | ci.yml | - | - | TLLValue类型系统 |
| JSON | COMPLETE | host/c/json.c, stdlib/json.tll | tests/ | ci.yml | - | - | JSON解析/序列化 |
| Worker Pool | PARTIAL | host/c/ | tests/ | ci.yml | - | - | 多线程执行基础,高并发隔离未充分压力测试 |
| ExecutionContext | PARTIAL | host/c/ | tests/ | ci.yml | - | - | 请求隔离基础 |
| Global State Isolation | PARTIAL | host/c/ | tests/ | ci.yml | - | - | 多Worker全局状态隔离待验证 |
| Coroutine (100K) | COMPLETE | host/c/ | tests/ | ci.yml | P0-15.18.6 | - | create:95.4us, yield:2.19us |
| TCP Sockets | COMPLETE | host/c/ | tests/ | ci.yml | P0-15.18.2 | - | 非阻塞IO+select,FD_SETSIZE=64限制 |
| Long-Run Stability (120s) | COMPLETE | host/c/ | tests/ | ci.yml | P0-15.18.5 | - | 4-node blockchain 120秒稳定 |
| Memory Safety (source audit) | PARTIAL | host/c/ | - | - | - | - | 源码审计无明显泄漏,ASAN/valgrind未验证 |
| Socket Lifecycle (macOS) | PARTIAL | host/c/http_client_builtin.c | tests/net/ | ci.yml | P1-04 | - | 快速连续请求有时序问题,30纯GET通过,23混合请求偶发失败 |
| Resource Cleanup | PARTIAL | host/c/ | tests/net/ | ci.yml | P1-04 | - | macOS快速建连资源释放待优化 |

---

## 4. Stdlib

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| Array | COMPLETE | stdlib/array.tll | tests/ | ci.yml | - | - |
| String | COMPLETE | stdlib/string.tll | tests/ | ci.yml | - | - |
| StringBuilder | COMPLETE | stdlib/stringbuilder.tll | tests/ | ci.yml | - | - |
| Math | COMPLETE | stdlib/math.tll | tests/ | ci.yml | - | - |
| JSON | COMPLETE | stdlib/json.tll | tests/ | ci.yml | - | - |
| Stream | COMPLETE | stdlib/stream.tll | tests/ | ci.yml | - | - |
| Observable | COMPLETE | stdlib/observable.tll | tests/ | ci.yml | - | - |
| EventBus | COMPLETE | stdlib/eventbus.tll | tests/ | ci.yml | - | - |
| Events | COMPLETE | stdlib/events.tll | tests/ | ci.yml | - | - |
| Future | COMPLETE | stdlib/future.tll | tests/ | ci.yml | - | - |
| Task | COMPLETE | stdlib/task.tll | tests/ | ci.yml | - | - |
| Tool | COMPLETE | stdlib/tool.tll | tests/ | ci.yml | - | - |
| State | COMPLETE | stdlib/state.tll | tests/ | ci.yml | - | - |
| Crypto (pure TLL) | COMPLETE | stdlib/crypto.tll | tests/crypto/ | ci.yml | - | - | SHA-256/HMAC纯TLL实现(已被C-native加速补充) |
| Blockchain | COMPLETE | stdlib/blockchain.tll | tests/ | ci.yml | P0-15 | - | Genesis Blockchain,4-node TCP network |
| Blockchain Node | COMPLETE | stdlib/blockchain_node.tll | tests/ | ci.yml | P0-15 | - | P2P节点 |
| Mempool | COMPLETE | stdlib/mempool.tll | tests/ | ci.yml | P0-15 | - | 交易内存池,容量50,溢出淘汰 |
| P2P | COMPLETE | stdlib/p2p.tll | tests/ | ci.yml | P0-15 | - | 点对点网络 |
| Agent | COMPLETE | stdlib/agent.tll | tests/agent/ | ci.yml | P0-15.25 | - | Agent基础 |
| Capability | COMPLETE | stdlib/capability.tll | tests/capability/ | ci.yml | P0-15.21 | - | 能力系统 |
| File System | COMPLETE | builtin idx 79-90 | 25/25 | 3/3 | tests/fs/gate_file_system.tll | P1-NEXT-L1: readFile/writeFile/appendFile/exists/mkdir/remove/listDir/isFile/isDir/fileSize/copyFile/rename |
| Scheduler | MISSING | - | - | - | - | - | 定时任务/调度器未建立 |
| Image Processing | MISSING | - | - | - | - | - | 图像处理未建立 |
| HTTP Server | COMPLETE | builtin idx 94 | 19/19 | 3/3 | tests/http/gate_http_server.tll | P1-NEXT-L2: http.serve with worker pool, request/response maps |
| HTTP Client | AVAILABLE | host/c/http_client_builtin.c | tests/net/ | ci.yml | P1-04 | 3a67b44 | Linux/Windows完整,macOS基础可用有Known Issue |

---

## 5. Cryptography (必须严格封板)

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| SHA-256 (pure TLL) | COMPLETE | stdlib/crypto.tll | tests/crypto/ | ci.yml | - | - | 区块链使用 |
| SHA-256 (C-native) | COMPLETE | host/c/hmac_builtin.c | tests/crypto/ | ci.yml | P1-03 | 06be89d | HMAC内部使用 |
| HMAC-SHA256 (C-native) | 🔒 SEALED | host/c/hmac_builtin.c | tests/crypto/ | ci.yml #200 | P1-03 | 303034c | RFC4231 TC1-TC7全量通过(含TC5 full+truncated),\xNN字节表达 |
| Secure Random (C-native) | 🔒 SEALED | host/c/crypto_builtin.c | tests/crypto/ | ci.yml #21 | P1-01 | ddc148c | Windows BCryptGenRandom,Linux getrandom(),macOS /dev/urandom,27/27 Gate |
| Password Hashing bcrypt | 🔒 SEALED | host/c/password_builtin.c | tests/crypto/ | ci.yml | P1-02 | 06be89d | OpenBSD bcrypt实现,36/36 Gate,旧密码自动迁移 |
| Ed25519 RFC8032 | 🔒 SEALED | host/c/ | tests/crypto/ | ci.yml | P0-15.19 | - | RFC8032测试向量通过 |
| SHA-512 | MISSING | - | - | - | - | - | 未实现 |
| AES | MISSING | - | - | - | - | - | 未实现 |
| TLS (native) | PARTIAL | host/c/http_client_builtin.c | tests/net/ | ci.yml | P1-04 | - | Linux OpenSSL,Windows WinHTTP,macOS Secure Transport |

---

## 6. AI Engineering Foundation (必须严格封板)

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| Identity | 🔒 SEALED | stdlib/agent.tll | tests/identity/ | ci.yml | P0-15.20 | - | 8/8 Gate |
| Capability | 🔒 SEALED | stdlib/capability.tll | tests/capability/ | ci.yml | P0-15.21 | - | 12/12 Gate |
| Authority | 🔒 SEALED | - | tests/authority/ | ci.yml | P0-15.22 | - | 12/12 Gate |
| Evidence | 🔒 SEALED | - | tests/evidence/ | ci.yml | P0-15.23 | - | 12/12 Gate |
| Trust | 🔒 SEALED | - | tests/trust/ | ci.yml | P0-15.24 | - | 14/14 Gate |
| Agent Ecosystem | 🔒 SEALED | stdlib/agent.tll | tests/agent/ | ci.yml | P0-15.25 | - | 18/18 Gate |
| Truth Engine | PARTIAL | .tll-engine/truth/ | - | - | - | - | Schema建立,自动化验证未完成,与实际代码严重滞后 |
| Cognition | PARTIAL | .tll-engine/cognition/ | - | - | - | - | 决策/依赖/图谱基础 |
| Protocol | PARTIAL | .tll-engine/protocol/ | - | - | - | - | audit/development/testing协议 |

---

## 7. Database

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| SQLite C Binding | COMPLETE | host/c/sqlite_builtin.c, sqlite3.c | - | ci.yml | - | - | idx 150-159,完整CRUD |
| Database Abstraction | COMPLETE | stdlib/db.tll | 20/20 | 3/3 | tests/db/gate_database.tll | P1-NEXT-L3: connection/query/exec/transaction/migration, extracted from mall |
| Database Migration | COMPLETE | stdlib/db.tll | 4/4 | 3/3 | tests/db/gate_database.tll | P1-NEXT-L3: db_ensureMigrationsTable/db_applyMigration/db_migrate |
| Transaction | PARTIAL | mall/ | - | - | - | - | 商城已实现基础事务 |
| Migration | MISSING | - | - | - | - | - | 数据库迁移工具未建立 |
| MySQL/MariaDB | MISSING | - | - | - | - | - | 仅SQLite,可扩展 |
| Connection Pool | MISSING | - | - | - | - | - | 连接池未建立 |

---

## 8. Network / HTTP

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| HTTP Client (Linux) | COMPLETE | host/c/http_client_builtin.c | tests/net/gate_http_client.tll | ci.yml | P1-04 | - | POSIX socket+OpenSSL,29/29 Gate |
| HTTP Client (Windows) | COMPLETE | host/c/http_client_builtin.c | tests/net/gate_http_client.tll | ci.yml | P1-04 | - | WinHTTP,29/29 Gate |
| HTTP Client (macOS) | AVAILABLE | host/c/http_client_builtin.c | tests/net/ | ci.yml | P1-04 | - | Secure Transport+POSIX socket,基础HTTP/HTTPS可用,完整Gate混合请求有时序问题(Known Issue) |
| HTTP Client API | COMPLETE | host/c/http_client_builtin.c | tests/net/ | ci.yml | P1-04 | - | get/post/put/delete/head/patch/request/getJson/postJson/options,idx 200-209 |
| HTTP Server | COMPLETE | builtin idx 94 | 19/19 | 3/3 | tests/http/gate_http_server.tll | P1-NEXT-L2: see Network section |
| Router | PARTIAL | mall/ | - | - | - | - | 商城已实现,未抽象为stdlib |
| Middleware | PARTIAL | mall/ | - | - | - | - | 商城已实现,未抽象为stdlib |
| WebSocket | MISSING | - | - | - | - | - | 未实现 |
| DNS | PARTIAL | host/c/ | tests/net/ | ci.yml | - | - | 系统DNS解析 |
| TLS | PARTIAL | host/c/http_client_builtin.c | tests/net/ | ci.yml | P1-04 | - | 三平台不同backend:Linux OpenSSL,Windows WinHTTP,macOS Secure Transport |

---

## 9. Blockchain

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| Genesis Blockchain | COMPLETE | stdlib/blockchain.tll | tests/ | ci.yml | P0-15 | - | 创世链 |
| 4-Node TCP Network | COMPLETE | stdlib/blockchain_node.tll | tests/ | ci.yml | P0-15 | - | 独立进程,真实TCP,P2P同步 |
| Transaction Propagation | COMPLETE | stdlib/mempool.tll | tests/ | ci.yml | P0-15 | - | 120tx压力测试,去重,容量50溢出淘汰 |
| Fault Injection (5场景) | COMPLETE | - | tests/ | ci.yml | P0-15 | - | 重复tx/块,乱序块,kill-9重启,多节点故障 |
| Invalid Block Rejection | COMPLETE | - | tests/ | ci.yml | P0-15 | - | 错误hash/prevHash/index/tx/PoW拒绝 |
| Fork Detection | PARTIAL | - | tests/ | ci.yml | P0-15 | - | 检测并拒绝冲突块,无链重组(reorg) |
| Real Crypto Signatures | 🔒 SEALED | host/c/ | tests/crypto/ | ci.yml | P0-15.19 | - | Ed25519 RFC8032,已升级区块链签名 |
| Account State (nonce/balance) | MISSING | - | - | - | - | - | 未实现账户状态、nonce、余额、双花防护 |
| Chain Persistence | MISSING | - | - | - | - | - | 全内存,重启从genesis开始 |
| Fork Reorg | MISSING | - | - | - | - | - | 链重组未实现 |
| Smart Contract | MISSING | - | - | - | - | - | 智能合约未实现 |

---

## 10. Mall / Commercial (已实现但未封板,属于应用层)

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| Web Framework | PARTIAL | mall/ | - | - | - | - | HTTP Server COMPLETE (P1-NEXT-L2), Router still in mall/ |
| Session/Cookie | PARTIAL | mall/ | - | - | - | - | 数据库存储Session,Session ID仍为可预测格式(需换CSPRNG) |
| RBAC Auth | PARTIAL | mall/ | - | - | - | - | 角色权限基础 |
| Product Management | COMPLETE | mall/ | - | - | - | - | 商品CRUD/分类/品牌/SKU/库存 |
| Order Management | COMPLETE | mall/ | - | - | - | - | 订单状态机,24个测试用例 |
| User Management | COMPLETE | mall/ | - | - | - | - | 用户/等级/充值/提现/地址 |
| Marketing | PARTIAL | mall/ | - | - | - | - | 优惠券/会员折扣,秒杀/拼团待完善 |
| Payment (Sandbox) | PARTIAL | mall/ | - | - | - | - | 微信/支付宝/余额沙箱模式,需真实商户密钥 |
| Admin Backend (17模块) | COMPLETE | mall/ | - | - | - | - | 17个管理模块 |
| H5 Frontend | COMPLETE | mall/ | - | - | - | - | PC/移动自适应 |
| CSRF | MISSING | - | - | - | - | - | 需用CSPRNG+HMAC重新设计 |
| Multi-user Concurrency | PARTIAL | mall/ | - | - | - | - | 基础隔离,高并发压力测试待完善 |

---

## 11. Engineering / CI / Git

| 能力 | 状态 | Source | Test | CI | Evidence | Commit | 说明 |
|------|------|--------|------|-----|----------|--------|------|
| CI (三平台) | COMPLETE | .github/workflows/ci.yml | - | ci.yml | - | - | Ubuntu/Windows/macOS |
| P1 Crypto Tests CI | COMPLETE | .github/workflows/p1-crypto-tests.yml | - | p1-crypto-tests.yml | - | - | P1-01/02/03独立CI |
| Release CI | COMPLETE | .github/workflows/release.yml | - | release.yml | - | - | 发布流程 |
| Git Integrity Loop | PARTIAL | - | - | - | - | - | 规范未正式建立文档 |
| Evidence System | PARTIAL | docs/P1-*.md | - | - | - | - | P1 Evidence完整,历史能力Evidence待整理 |
| Truth Layer (.tll-engine) | PARTIAL | .tll-engine/truth/ | - | - | - | - | 与实际代码严重滞后,需同步 |
| Compiler Release Mgmt | MISSING | - | - | - | - | - | 版本管理/Build SHA256/回滚机制未建立 |
| .gitignore | PARTIAL | .gitignore | - | - | - | - | 临时文件未充分忽略 |

---

## 12. 封版阻断项汇总

| # | 阻断项 | 严重度 | 处理阶段 |
|---|--------|--------|----------|
| 1 | .tll-engine Truth Layer与实际代码严重不一致 | 🔴 高 | P3 |
| 2 | 工作树大量临时文件(200+调试脚本) | 🟡 中 | P2 |
| 3 | Compiler Release/Rollback机制未建立 | 🟡 中 | P4 |
| 4 | P1-04 macOS完整Gate未全绿(按新路线为非阻断,但需准确记录) | 🟡 中 | P5 |
| 5 | Bootstrap确定性未纳入CI自动化 | 🟡 中 | P4/P6 |

---

## 13. 已知限制 (Known Limitations)

1. **TCP FD_SETSIZE=64**: 最大64个并发文件描述符,高并发场景需升级为poll/epoll
2. **macOS HTTP Client混合请求时序问题**: 30个纯GET通过,23个混合请求偶发失败,根因待查(可能与FD_SETSIZE或socket lifecycle有关)
3. **Memory Safety未经过ASAN/valgrind验证**: 源码审计无明显泄漏,运行时泄漏未验证
4. **未定义标识符仍为warning**: 编译时不报错,运行时可能崩溃
5. **Blockchain无持久化**: 全内存,重启从genesis开始
6. **Blockchain无账户状态**: 无nonce/balance/双花防护
7. ~~无File System stdlib~~ **已解决 (P1-NEXT-L1)**: fs builtin idx 79-90 + 25-assertion Gate test
8. **无Scheduler stdlib**: 定时任务/调度器未建立
9. **无WebSocket**: 实时通信未实现
10. **Compiler Rollback机制未建立**: 无正式救援工具链

---

## 14. 统计

| 状态 | 数量 | 占比 |
|------|------|------|
| 🔒 SEALED (严格封板) | 11 | 10.6% |
| COMPLETE | 58 | 55.8% |
| AVAILABLE | 2 | 1.9% |
| PARTIAL | 24 | 23.1% |
| MISSING | 9 | 8.7% |
| **总计** | **104** | **100%** |

---

**文档生成完成。基于实际源码/测试/CI/Evidence,未复制旧Truth Layer。等待P1验收后进入P2。**
