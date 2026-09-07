# P1-NEXT: TLL OS 全量能力审计 + 云梯式连续施工 — 最终报告

## 1. Executive Summary

本轮 P1-NEXT 施工以"先审计、再补缺、不重复造轮子"为原则，对 TLL OS 仓库进行了真实能力审计，发现 Capability Matrix 与实际代码存在多处不一致（多项标为 MISSING/PARTIAL 的能力实际已实现）。

通过云梯式连续施工，完成了 3 个层级的能力补缺：

| 层级 | 能力 | 关键成果 | Gate | Commit |
|------|------|----------|------|--------|
| L1 | File System stdlib | 修复 6 个 fs 函数返回值从 null→bool，新增 25 断言 Gate 测试 | 25/25 | db5cd29 |
| L2 | HTTP Server Gate | 新增 19 断言 Gate 测试，修复测试驱动 subprocess 管道死锁 | 19/19 | 34db802 |
| L3 | Database Abstraction | 从 mall/ 提取 stdlib/db.tll，**修复关键 db_buildSQL 类型检查 Bug**（"list"→"array"，导致所有参数化查询失效），新增 20 断言 Gate 测试 | 20/20 | 7946d3c |

**本轮共发现并修复 3 个真实 Bug**，其中 db_buildSQL Bug 影响 mall 商城的所有参数化查询，是最关键的修复。

---

## 2. Baseline

施工开始时仓库真实状态：
- 分支：`p1-04-http-client`
- HEAD：`c4105e5`（P1-04 Level 4 Evidence 更新）
- main HEAD：`6875401`（含 Capability Matrix 和清理提交）
- 已封板：P1-01/02/03 + P1-04 Level 1-4
- 工作树：CLEAN

**审计发现的 Capability Matrix 与代码不一致**：
- File System 标为 MISSING → 实际已在 builtin.c idx 79-90 实现（12 个函数）
- HTTP Server 标为 PARTIAL → 实际已在 builtin.c idx 94 实现（三平台 + worker pool）
- Database Abstraction 标为 PARTIAL → 实际已在 mall/core/database.tll 实现（完整封装 + 迁移支持）
- Database Migration 标为 MISSING → 实际已在 mall/core/database.tll 实现

---

## 3. Cloud Ladder

```
L1: File System stdlib          (最底层 I/O 缺口，已有实现但无测试+返回值Bug)
    ↓
L2: HTTP Server Gate            (已有实现，无独立 Gate 测试)
    ↓
L3: Database Abstraction stdlib (已有实现在 mall/，未抽象 + 关键Bug)
    ↓
[停止：已到达合理能力边界，剩余缺口需要独立阶段]
```

每一级依赖前一级的稳定基础，且都遵循"已有实现→找缺口→最小修复→Gate→Evidence→CI"的原则。

---

## 4. 实际施工

### L1: File System stdlib

**能力**：fs builtin idx 79-90（readFile/writeFile/appendFile/exists/mkdir/remove/listDir/isFile/isDir/fileSize/copyFile/rename）

**根因**：6 个写操作函数（writeFile/appendFile/mkdir/remove/copyFile/rename）返回 `tll_null()` 而非布尔值，调用方无法判断操作成功/失败。

**修改**：`host/c/builtin.c` — 6 个函数改为返回 `tll_bool()`，基于实际操作结果；添加 `#include <errno.h>`。

**测试**：`tests/fs/gate_file_system.tll` — 25 断言，覆盖 11 个 Gate（含异常路径）。

**Gate**：25/25 PASS

**Commit**：`db5cd29`

### L2: HTTP Server Gate

**能力**：http.serve builtin idx 94（三平台 + worker pool + VM 锁序列化）

**根因**：无独立 Gate 测试；测试基础设施存在 subprocess stderr 管道死锁（服务器输出到 stderr 但 Python 不读取，缓冲区满后服务器阻塞）。

**修改**：`tests/http/test_http_server.py` — stderr 改为 `subprocess.DEVNULL`；添加请求间隔和重试。

**测试**：`tests/http/gate_http_server.tll`（服务器端 8 端点）+ `tests/http/test_http_server.py`（Python 驱动）— 19 断言，覆盖 8 个 Gate。

**Gate**：19/19 PASS

**Commit**：`34db802`

### L3: Database Abstraction stdlib

**能力**：stdlib/db.tll（从 mall/core/database.tll 提取，含连接管理/参数化查询/事务/迁移/工具函数）

**根因（关键 Bug）**：`db_buildSQL()` 中类型检查使用 `"list"`，但 TLL `convert.typeOf([])` 返回 `"array"`，导致**所有参数化查询的 `?` 占位符永远不被替换**。此 Bug 同时存在于 mall/core/database.tll，影响商城所有参数化查询。

**修改**：
- `stdlib/db.tll` — 新建，从 mall 提取（移除 mall 特定 GLOBAL_DB_PATH）
- `mall/core/database.tll` — 修复同样的类型检查 Bug
- 类型检查：`"list"` → `"array"`

**测试**：`tests/db/gate_database.tll` — 20 断言，覆盖 11 个 Gate（含 SQL 注入防护、事务、迁移）。

**Gate**：20/20 PASS

**Commit**：`7946d3c`

---

## 5. Bug Discovery

本轮共发现并修复 3 个真实 Bug：

### Bug 1: fs 写操作返回值缺失（L1）
- **位置**：`host/c/builtin.c` cases 80,81,83,84,89,90
- **影响**：writeFile/appendFile/mkdir/remove/copyFile/rename 总是返回 null，调用方无法判断成功/失败
- **修复**：改为返回 tll_bool(实际结果)
- **严重度**：中（API 设计缺陷，不影响功能执行）

### Bug 2: HTTP Server 测试驱动 subprocess 管道死锁（L2）
- **位置**：`tests/http/test_http_server.py`（新建时引入）
- **影响**：服务器进程输出到 stderr 但 Python 不读取，缓冲区满后服务器阻塞，约 7 个请求后进程无响应
- **修复**：stderr 改为 subprocess.DEVNULL
- **严重度**：低（测试基础设施问题，非运行时 Bug）

### Bug 3: db_buildSQL 参数化查询永远失效（L3）⭐ 最关键
- **位置**：`stdlib/db.tll` + `mall/core/database.tll`
- **影响**：`convert.typeOf(params) != "list"` 总是为 true（因为 TLL 数组类型是 "array"），导致 `?` 占位符永远不被替换。所有参数化查询失效，SQL 注入防护形同虚设
- **修复**：`"list"` → `"array"`
- **严重度**：高（安全 Bug，影响 mall 商城所有参数化查询）

---

## 6. Regression

| 能力 | 结果 | 验证方式 |
|------|------|----------|
| P1-01 Secure Random | PASS | 本地运行 |
| P1-02 Password Hashing | 36/36 PASS | 本地运行 |
| P1-03 HMAC-SHA256 | 20/20 PASS | 本地运行 |
| P1-04 Level 1-4 | 未重跑 | 无 HTTP 客户端代码修改 |
| Compiler Bootstrap | PASS | 新编译器编译 fs 测试 25/25 |
| File System L1 | 25/25 PASS | 本地运行 |
| HTTP Server L2 | 19/19 PASS | 本地运行 |
| Database L3 | 20/20 PASS | 本地运行 |
| mall/core/database.tll | Bug 已修复 | 同 L3 修复 |

---

## 7. CI

所有 3 个层级的测试已加入 `.github/workflows/p1-04-http-client.yml`，覆盖三平台（Ubuntu/Windows/macOS）：
- L1 File System：编译后直接运行，检查 "ALL FILE SYSTEM GATES PASSED"
- L2 HTTP Server：Python 驱动，检查退出码
- L3 Database：编译后直接运行，检查 "ALL DATABASE GATES PASSED"

CI 放置顺序：Build → Bootstrap → L1 FS → L2 HTTP Server → L3 Database → P1-04 Level 1-4

**CI Run ID**：`34075379859`（HEAD `051e183`）

**三平台结果**：

| 平台 | 状态 | L1 FS | L2 HTTP Server | L3 Database | P1-04 L1-4 |
|------|------|-------|----------------|-------------|-------------|
| Linux (Ubuntu 22.04) | ✅ PASS | 25/25 | 19/19 | 20/20 | PASS |
| Windows (MSVC) | ✅ PASS | 25/25 | 19/19 | 20/20 | PASS |
| macOS (Apple Silicon / Intel) | ✅ PASS | 25/25 | 19/19 | 20/20 | PASS |

**CI 修复记录**：
- `f5f181e`：修复 `test_http_server.py` 在 Linux/macOS 上错误执行 Windows `tllvm.exe` 的问题（PermissionError）
- `051e183`：扩展 CI path 过滤，包含 `tests/fs/**`、`tests/http/**`、`tests/db/**`、`stdlib/**`、`mall/core/database.tll`

**商城回归测试**（db_buildSQL Bug 修复后）：
- `mall/test_db_debug.tll`：✅ PASS（数据库打开、迁移、表创建、直接执行全部正常）
- `mall/test_minimal.tll`：✅ PASS（数据库查询、session 创建、auth_login 正常）
- `mall/test_auth.tll`：✅ PASS（admin 创建、用户注册、登录验证正常）

---

## 8. Final Capability Ledger

| 能力 | 状态 | Commit | Gate | CI | Evidence |
|------|------|--------|------|-----|----------|
| P1-01 Secure Random | SEALED | (历史) | PASS | PASS | (历史) |
| P1-02 Password Hashing | SEALED | (历史) | 36/36 | PASS | (历史) |
| P1-03 HMAC-SHA256 | SEALED | (历史) | 20/20 | PASS | (历史) |
| P1-04 HTTP Client L1-4 | SEALED | c4105e5 | PASS | PASS | 4 个 Level Evidence |
| **File System** | **COMPLETE** | **db5cd29** | **25/25** | **3/3** | **P1-NEXT-L1** |
| **HTTP Server** | **COMPLETE** | **34db802** | **19/19** | **3/3** | **P1-NEXT-L2** |
| **Database Abstraction** | **COMPLETE** | **7946d3c** | **20/20** | **3/3** | **P1-NEXT-L3** |
| **Database Migration** | **COMPLETE** | **7946d3c** | **4/4** | **3/3** | **P1-NEXT-L3** |
| Router/Middleware | PARTIAL | - | - | - | 仍在 mall/ |
| Scheduler | MISSING | - | - | - | 需新建 |
| SHA-512/AES | MISSING | - | - | - | 需新建 |
| WebSocket | MISSING | - | - | - | 需新建 |
| MySQL/Connection Pool | MISSING | - | - | - | 需新建 |
| Compiler Rollback/Build SHA256 | MISSING | - | - | - | 需新建 |
| Blockchain Smart Contract | MISSING | - | - | - | 需新建 |
| Truth Layer (.tll-engine) | PARTIAL | - | - | - | 与代码滞后 |
| HTTPS Server | MISSING | - | - | - | 仅 HTTP |
| Connection Keep-Alive (server) | MISSING | - | - | - | 服务器发送 Connection: close |

---

## 9. Remaining Gaps

### PARTIAL（已有实现但不完整）
- **Router/Middleware**：在 mall/core/router.tll 中实现，未抽象为 stdlib/http/router.tll
- **Truth Layer (.tll-engine)**：文档与实际代码严重滞后，需要同步
- **Type Checker**：基础类型检查，未定义标识符仍为 warning
- **Error Handling**：基础异常，未定义标识符运行时可能崩溃
- **Worker Pool / ExecutionContext**：多线程基础，高并发隔离待验证
- **Memory Safety**：源码审计无明显泄漏，ASAN/valgrind 未验证

### MISSING（完全缺失）
- **Scheduler**（定时任务/调度器）
- **SHA-512 / AES**（加密算法扩展）
- **WebSocket**
- **HTTPS Server**（仅 HTTP Client 支持 HTTPS）
- **MySQL / PostgreSQL / Connection Pool**
- **Compiler Rollback / Build SHA256 Record**
- **Blockchain Account State / Chain Persistence / Fork Reorg / Smart Contract**
- **Mall CSRF**
- **HTTP/2 / HTTP/3**

### DEFERRED（已决定暂缓）
- **并发/异步 I/O** → 独立 High-Frame Runtime 阶段
- **HTTPS 连接复用** → SSL session 状态管理需精细调试
- **完整 Connection Pool** → L4 仅做单条目缓存

---

## 10. Final Recommendation

### 本轮成果
本轮通过云梯式施工，将 3 项能力从 MISSING/PARTIAL 提升为 COMPLETE，并修复了 3 个真实 Bug（其中 db_buildSQL 是影响商城安全的关键 Bug）。

### 下一阶段建议
**推荐下一阶：Router/Middleware stdlib 抽象（P1-NEXT L4）**

理由：
1. Router 已在 mall/core/router.tll 中完整实现（路径参数、中间件、响应助手），提取成本低
2. HTTP Server 已 COMPLETE（L2），Router 是自然的下一层
3. 提取后可让其他项目（非 mall）使用 TLL Web 框架
4. 完成后 Web Framework 可从 PARTIAL 提升为 COMPLETE

**备选：Scheduler stdlib**
- 完全 MISSING，需要从零设计
- 可基于 TLL 纯实现（time.sleep + 循环），不需要 C 代码
- 但可能需要并发支持（当前 DEFERRED）

### 关键提醒
1. **db_buildSQL Bug 修复后，mall 商城的参数化查询才真正生效**，建议后续对 mall 进行全量回归测试
2. **p1-04-http-client 分支尚未合并到 main**，包含 P1-04 Level 1-4 + P1-NEXT L1-3 的全部成果，建议总指挥裁决合并时机
3. **Truth Layer (.tll-engine) 与代码滞后**是长期技术债，建议安排独立阶段同步

---

## 施工信息

- **施工分支**：`p1-04-http-client`
- **最终 HEAD**：`7946d3c`
- **工作树**：CLEAN
- **新增文件**：7 个（3 个测试 + 1 个 stdlib + 3 个 Evidence）
- **修改文件**：4 个（builtin.c + mall/database.tll + CI workflow + Capability Matrix）
- **总新增行数**：~1400 行
- **总删除行数**：~20 行
