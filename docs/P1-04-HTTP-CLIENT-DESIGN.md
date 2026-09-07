# P1-04 HTTP Client — 最小闭环设计文档

**Status**: DESIGN (pending总指挥 review)
**Date**: 2026-09-07
**Phase**: P1-04
**Predecessor**: P1-03 HMAC-SHA256 🔒 SEALED

---

## 1. 现状评估

### 1.1 已有前期工作

main 分支上已有前施工队留下的 P1-04 实现：

| 组件 | 文件 | 大小 | 状态 |
|------|------|------|------|
| C 原生实现 | `host/c/http_client_builtin.c` | 35KB | 跨三平台（WinHTTP / POSIX+OpenSSL / Secure Transport） |
| TLL Codegen 绑定 | `compiler/codegen.tll` (L1772-1782) | — | httpc 模块 idx 200-208 |
| TLL Linker 注册 | `compiler/linker.tll` (L146) | — | "httpc" 已加入 stdlibs |
| Builtin dispatch | `host/c/builtin.c` (L491-492) | — | idx 200-209 → httpc_builtin_invoke |
| 本地 Gate 测试 | `tests/net/gate_http_client_local.tll` | 6KB / 14 tests | 依赖本地 test_server.py:18080 |
| 公网 Gate 测试 | `tests/net/gate_http_client.tll` | 5KB | 依赖 httpbin.org |
| macOS HTTPS 测试 | `tests/net/test_macos_https.tll` | 1.6KB | — |

### 1.2 已有 API（超出最小闭环范围）

```
httpc.get(url, headers?)          -> Response
httpc.post(url, body, headers?)   -> Response
httpc.put(url, body, headers?)    -> Response
httpc.delete(url, headers?)       -> Response
httpc.head(url, headers?)         -> Response
httpc.patch(url, body, headers?)  -> Response
httpc.request(map)                -> Response (full control)
httpc.getJson(url, headers?)      -> parsed JSON
httpc.postJson(url, body, headers?) -> parsed JSON
```

### 1.3 已知问题（从 git log 推断）

- P1-04-r2 阶段大量 fix commit：SO_LINGER、graceful delay、快速请求梯度测试（20/30 requests）、binary search 定位污染源
- 说明**快速连续请求**存在资源泄漏/连接污染问题
- macOS 曾排除 http_client_builtin.c 和 OpenSSL 构建（498cab0），后改用 Secure Transport（d19967c）
- **现有实现未经过总指挥正式验收，不能直接视为可用**

---

## 2. 最小闭环定义

### 2.1 闭环路径

```
TLL 源码
  ↓
httpc.get(url)
  ↓
HTTP GET 请求（HTTP，非 HTTPS）
  ↓
HTTP Response
  ↓
status / headers / body
  ↓
TLL map 返回值
  ↓
断言验证
  ↓
EVIDENCE
  ↓
CI (三平台)
```

### 2.2 最小闭环范围（Phase 1 — MUST）

| 能力 | 包含 | 说明 |
|------|------|------|
| HTTP GET | ✅ | 仅 HTTP（端口 80 / 自定义端口），不做 HTTPS |
| Response.status | ✅ | int 类型，HTTP 状态码 |
| Response.headers | ✅ | map 类型，key 小写 |
| Response.body | ✅ | string 类型 |
| Response.ok | ✅ | bool，status 200-299 |
| 自定义 request headers | ❌ | Phase 2 |
| POST / PUT / DELETE | ❌ | Phase 2 |
| HTTPS / TLS | ❌ | Phase 3 |
| timeout | ❌ | Phase 2 |
| 错误处理（连接拒绝等） | ❌ | Phase 2（最小闭环只测成功路径） |
| 连接复用 / 并发 | ❌ | Phase 4 |
| getJson / postJson | ❌ | Phase 2 |

### 2.3 最小 API（Phase 1）

```tll
// 仅保留一个函数
let resp = httpc.get(url)

// 返回 map
resp.status    // int: HTTP 状态码
resp.ok        // bool: status >= 200 && status < 300
resp.headers   // map: 响应头，key 小写
resp.body      // string: 响应体
resp.statusText // string: 状态文本
resp.url       // string: 最终 URL
resp.error     // string: 错误信息（成功时为空）
```

**设计决策**：现有实现已包含完整 Response map（含 statusText/url/error），最小闭环不删减返回字段，只限制**调用方式**为 `httpc.get(url)` 单参数。

---

## 3. 测试设计

### 3.1 测试策略

**不依赖公网**（CI 环境可能无公网或不稳定），使用本地 HTTP 测试服务器。

**两种方案**：
1. **Python 测试服务器**（现有方案）：`test_server.py` 监听 127.0.0.1:18080，提供 /status、/headers、/echo、/json 等端点
2. **TLL 自身 HTTP 服务器**（如果 http.serve 已可用）：用 TLL 写一个最小服务器

**Phase 1 选择方案 1**（Python test_server.py），因为：
- 现有测试已使用此方案
- Python 在三平台 CI 均可用
- 不引入额外依赖

### 3.2 最小闭环测试（Phase 1 — 仅 3 个断言）

```tll
// tests/net/gate_http_client_minimal.tll
io.println("=== P1-04 HTTP Client Minimal Gate ===")

let base = "http://127.0.0.1:18080"
let passed = 0
let failed = 0

fn test(name, cond) {
    if cond { io.println("  PASS: " + name); passed = passed + 1 }
    else { io.println("  FAIL: " + name); failed = failed + 1 }
}

// 最小闭环：GET -> status / headers / body
let resp = httpc.get(base + "/status")

test("GET returns status 200", resp.status == 200)
test("GET response body is non-empty", strings.length(resp.body) > 0)
test("GET response headers contain content-type", strings.length(resp.headers["content-type"]) > 0)

io.println("")
io.println("Passed: " + passed + " / Failed: " + failed)
if failed == 0 { io.println("ALL TESTS PASSED") } else { io.println("SOME TESTS FAILED") }
```

**仅 3 个断言**，对应总指挥要求的最小闭环：status / headers / body。

### 3.3 测试服务器端点要求

`/status` 端点需返回：
- HTTP 200
- Content-Type header
- 非空 body

---

## 4. CI 设计

### 4.1 新增 Workflow 或复用现有 CI

**方案**：在现有 `ci.yml` 中新增 P1-04 步骤，或新建 `p1-04-http-client.yml`。

**Phase 1 选择**：新建 `p1-04-http-client.yml`，与 P1-01/P1-03 保持一致的独立 workflow 模式。

### 4.2 CI 步骤（三平台）

```yaml
# .github/workflows/p1-04-http-client.yml
name: P1-04 HTTP Client Tests

on: [push, pull_request]

jobs:
  linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build tllvm
        run: gcc ... -o tllvm main.c ... http_client_builtin.c ... -lm -lpthread -ldl
      - name: Build TLL compiler
        run: ./tllvm tools/TLLC/tllc.tllbc compile tools/TLLC/main.tll -o tllc.tllbc
      - name: Start test server
        run: python3 tests/net/test_server.py &
      - name: Wait for server
        run: sleep 2
      - name: Compile minimal gate test
        run: ./tllvm tllc.tllbc compile tests/net/gate_http_client_minimal.tll -o test.tllbc
      - name: Run minimal gate test
        run: ./tllvm test.tllbc

  macos:
    runs-on: macos-latest
    # 同上，使用 clang，注意 macOS 用 Secure Transport（但 Phase 1 只测 HTTP，不需要 TLS）

  windows:
    runs-on: windows-latest
    # 同上，使用 MSVC
```

### 4.3 编译命令（必须包含 http_client_builtin.c）

**Linux/macOS**:
```bash
gcc -O2 -std=gnu99 -D_POSIX_C_SOURCE=200809L -D_GNU_SOURCE -D_DARWIN_C_SOURCE -o tllvm \
  main.c vm.c value.c json.c builtin.c sqlite_builtin.c crypto_builtin.c password_builtin.c \
  hmac_builtin.c http_client_builtin.c sqlite3.c \
  -lm -lpthread -ldl
```

**Windows (MSVC)**:
```cmd
cl /O2 /D_CRT_SECURE_NO_WARNINGS /Fe:tllvm.exe main.c vm.c value.c json.c builtin.c \
  sqlite_builtin.c crypto_builtin.c password_builtin.c hmac_builtin.c http_client_builtin.c \
  sqlite3.c ws2_32.lib winhttp.lib bcrypt.lib advapi32.lib
```

---

## 5. 实现策略

### 5.1 不重新开发

现有 `http_client_builtin.c` 已包含最小闭环所需的 `httpc.get()` 实现。**Phase 1 不修改 C 代码**，只：
1. 验证现有实现能编译通过
2. 验证现有 `httpc.get()` 能完成最小闭环
3. 编写最小闭环测试
4. 配置 CI
5. 记录 Evidence

### 5.2 如果现有实现不能完成最小闭环

按以下优先级修复：
1. **编译错误** → 只修编译错误，不重构
2. **GET 请求失败** → 定位平台特定问题，最小修复
3. **Response 字段缺失** → 补齐 status/headers/body 三个字段

**禁止**：在 Phase 1 重构整个 http_client_builtin.c、添加新 API、优化性能。

---

## 6. 后续迭代路线

| Phase | 内容 | 依赖 |
|-------|------|------|
| **Phase 1 (本次)** | GET → status/headers/body，HTTP only，三平台 CI | — |
| Phase 2 | POST + request headers + timeout + 错误处理 | Phase 1 |
| Phase 3 | HTTPS / TLS（WinHTTP / Secure Transport / OpenSSL） | Phase 2 |
| Phase 4 | 连接复用 + 并发 + 资源泄漏修复 | Phase 3 |
| Phase 5 | getJson / postJson + 完整 REST 支持 | Phase 4 |

---

## 7. 验收标准（Phase 1）

| Gate | 描述 | 标准 |
|------|------|------|
| Gate 1 | 编译通过 | 三平台（Linux/macOS/Windows）编译 http_client_builtin.c 无错误 |
| Gate 2 | 最小 GET 闭环 | `httpc.get(url)` 返回 status=200、body 非空、headers 含 content-type |
| Gate 3 | Compiler Bootstrap | 新编译器能编译 httpc 测试 |
| Gate 4 | 三平台 CI | Ubuntu/macOS/Windows 3/3 PASS |
| Gate 5 | 历史回归 | P1-01/P1-02/P1-03 封板能力不被破坏 |
| Gate 6 | Evidence | 完整记录实现、测试、CI 结果 |

---

## 8. 风险与注意事项

1. **现有实现可能有 bug**：从 git log 看 P1-04-r2 阶段有大量修复，说明实现不稳定。Phase 1 只测最小 GET，如果最小 GET 都失败，需要定位修复。
2. **macOS 构建**：之前曾因 OpenSSL 问题排除 http_client_builtin.c，后改用 Secure Transport。Phase 1 只测 HTTP，理论上不需要 TLS，但编译时可能仍链接 Secure Transport 框架。
3. **本地测试服务器**：依赖 Python test_server.py，需确认该文件存在且能在三平台运行。
4. **不做大而全**：Phase 1 严格限制在 GET → status/headers/body，不扩展到 POST/HTTPS/并发。

---

**下一步**：等待总指挥 review 本设计文档，确认最小闭环范围后，进入实现验证阶段。
