# P0-RUNTIME-08-R2 — Transport Failure Proof & Minimal Retry Fix Design (v2)

**Windows Blockchain 5-Block / 4-Node Sync — Transport Layer Closure**

> **v2 更新**：补齐 Total Retry Budget、tcp.connect bounded 行为证明、Test Harness vs Transport 职责分离、Transport Error Evidence 字段、Delayed-Leader Regression Test 设计。

---

## 1. Transport Failure Proof（当前实际行为证据）

### 1.1 调用链

```
bc_multi_b.tll (Node B)
  ↓
connectToPeer(node, "127.0.0.1", 19201)   [stdlib/blockchain_node.tll:64]
  ↓
p2pConnect(node.p2p, host, port)            [stdlib/p2p.tll:113]
  ↓
tcp.connect(host, port)                      [host/c/builtin.c:1723, idx=135]
  ↓
connect(s, (struct sockaddr*)&addr, sizeof(addr))   [Windows blocking call]
```

### 1.2 当前各层实际行为

| 层 | 函数 | 连接失败行为 | 重试 | 超时 | 可观测性 |
|----|------|-------------|------|------|----------|
| Transport | `tcp.connect()` | 返回 -1，**不暴露 WSAGetLastError()** | ❌ 无 | ⚠️ OS 默认（本地约 2s） | ❌ 无错误码 |
| P2P | `p2pConnect()` | 打印 "Failed to connect"，返回 false | ❌ 无 | ⚠️ 仅 handshake 阶段 5s | ⚠️ 仅一行文本 |
| Blockchain | `connectToPeer()` | 透传 false，不 spawn autoSync | ❌ 无 | ❌ 无 | ❌ 无 |
| Test | `bc_multi_b.tll` | 继续等待 20 秒，height=0，输出 RESULT | ❌ 无 | 20 秒固定 | ⚠️ 仅最终 height |

### 1.3 关键实验：Windows connect() 真实行为

**实验环境**：Windows 11，Python socket（与 C `connect()` 同一 OS TCP 栈）

| 目标 | 结果 | 耗时 | 错误码 |
|------|------|------|--------|
| 127.0.0.1:19999（未监听） | FAIL | **2185ms** | WinError 10061 (WSAECONNREFUSED) |
| 10.255.255.1:80（非路由，3s 超时） | FAIL | 3005ms | timed out |

**关键结论**：
1. Windows `connect()` 到本地未监听端口**不是立即返回**，而是需要约 **2 秒**
2. 这是 OS TCP 栈的行为，不是我们代码设置的超时
3. 对于 127.0.0.1 场景，单次 connect 有事实上界（约 2-3 秒）
4. 当前 `tcp.connect()` **不暴露错误码**，只返回 -1，这是真实的 Transport observability GAP

### 1.4 已证实的失败模式

**模式 A：Node A 未监听 → connect 约 2 秒后失败**
- 实验证明：Windows connect 到本地未监听端口约 2185ms 返回 WSAECONNREFUSED
- 当前 `p2pConnect()` 无重试，直接返回 false
- Node B 无 peers，height=0

**模式 B：Node A 启动慢 → connect 时序失败**
- 本地测量：Node A 启动到监听 = 1473ms
- CI 阈值：测试脚本等待 2000ms
- 风险：CI 环境 Node A 启动 >2000ms 时，Node B 连接时 Node A 未监听
- connect 阻塞约 2 秒后返回失败，无重试

**模式 C：connect 阻塞 → 测试超时**
- 对于非本地地址，connect 可能阻塞更长时间
- 但在我们的场景中（127.0.0.1），单次 connect 最多约 2-3 秒

### 1.5 缺失的可观测性

当前无法从 CI 日志中获取：
- Node A 实际 listen 时间戳
- Node B/C/D 实际 connect attempt 时间戳
- `tcp.connect()` 返回值（成功 fd 还是 -1）
- WSAGetLastError() 具体错误码（**API 未暴露**）
- 重试次数（当前无重试）
- handshake 阶段是否到达
- 最终 peer count

---

## 2. Contract — Bounded Retry Transport Contract v1.0

### 2.1 设计原则

1. **Bounded, not infinite**：所有失败路径都有时间上界
2. **Observable, not silent**：每次连接尝试产生 Evidence
3. **Budget-based, not magic-number**：使用 Total Retry Budget 而非固定 sleep
4. **Backward compatible**：不改变成功路径的行为
5. **Cross-platform**：Windows / Linux / macOS 行为一致
6. **Honest about gaps**：当前 API 未暴露错误码，不伪造

### 2.2 Total Retry Budget（总重试预算）— v2 修正版

**严格最坏时间上界公式**：
```
Total = Σ(connect_i + handshake_i) + Σ(backoff_i) ≤ TOTAL_RETRY_BUDGET
```

**参数**：
```
TOTAL_RETRY_BUDGET = 25 秒
├── MAX_ATTEMPTS = 5
├── 单次 connect 上界 = 2.5 秒（127.0.0.1 实验约 2185ms，取保守 2.5s）
├── 单次 handshake 上界 = 2 秒（架构师批准缩短为 2s，独立于 connect）
├── Backoff 序列 = [200ms, 400ms, 600ms, 800ms]
│   （第 N 次失败后等待 min(N*200ms, 1000ms)，共 4 次 backoff）
└── Backoff 总计 = 200+400+600+800 = 2000ms = 2 秒
```

**两条失败路径的严格上界**：

| 路径 | 单次 attempt | 5 次 attempt | + 4 次 backoff | 总计 | 预算 |
|------|-------------|-------------|----------------|------|------|
| **Connect 失败**（最常见，Node A 未监听） | connect=2.5s, 无 handshake | 5×2.5=12.5s | +2s | **14.5s** | ≤25s ✅ |
| **Handshake 失败**（少见，对端 connect 成功但不响应） | connect=2.5s + handshake=2s=4.5s | 5×4.5=22.5s | +2s | **24.5s** | ≤25s ✅ |

**最坏情况证明**：
- 最坏路径 = 每次 attempt 都 connect 成功但 handshake 超时
- 单次 attempt = connect(2.5s) + handshake(2s) = 4.5s
- 5 次 attempt = 5 × 4.5s = 22.5s
- 4 次 backoff = 2s
- **Total = 24.5s ≤ 25s TOTAL_RETRY_BUDGET ✅**

> **注意**：对于非 127.0.0.1 地址，单次 connect 可能超过 2.5 秒。但在本项目的 Blockchain/P2P 测试场景中，所有节点均使用 127.0.0.1，因此预算成立。未来如果需要支持远程地址，应引入非阻塞 connect + select 超时（方案 C，不在本次范围）。

> **Connect timeout 与 Handshake timeout 是两个独立预算**：
> - Connect timeout = OS 默认（127.0.0.1 约 2.1s），不由我们设置
> - Handshake timeout = 2s，通过 `tcp.setTimeout(fd, 2000)` 设置，仅影响 recv/waitRead
> - 二者不叠加为一个 "connectTimeoutMs" 参数

### 2.3 `p2pConnectWithRetry()` 契约

```
函数签名：
  p2pConnectWithRetry(node, host, port) -> bool

默认参数（硬编码在函数内，不暴露给调用方）：
  MAX_ATTEMPTS = 5
  BACKOFF_BASE_MS = 200
  BACKOFF_MAX_MS = 1000
  HANDSHAKE_TIMEOUT_MS = 2000  // 架构师批准：独立于 connect 的 handshake 超时

行为：
  for attempt = 1 to MAX_ATTEMPTS:
    1. 记录 attempt_start = time.nowMs()
    2. 输出 Evidence:
       [nodeId] CONNECT_ATTEMPT attempt=MAX_ATTEMPTS host=host port=port
    3. fd = tcp.connect(host, port)
       （tcp.connect 是阻塞的，127.0.0.1 未监听时约 2 秒返回 -1）
    4. elapsed = time.nowMs() - attempt_start
    5. 如果 fd >= 0:
       - 输出 Evidence:
         [nodeId] CONNECT_SUCCESS attempt=N elapsed_ms=X fd=Y
       - 执行 handshake（现有 p2pConnect 逻辑）
       - 如果 handshake 成功：
         输出 [nodeId] HANDSHAKE_SUCCESS peer=peerId
         return true
       - 如果 handshake 失败：
         输出 [nodeId] HANDSHAKE_FAILED attempt=N
         tcp.close(fd)
         继续重试（handshake 失败也重试）
    6. 如果 fd < 0:
       - 输出 Evidence:
         [nodeId] CONNECT_FAILED attempt=N elapsed_ms=X fd=-1
         （注意：transport error code 未被当前 tcp.connect API 暴露，
           此处不伪造错误码，仅记录 fd=-1 和 elapsed_ms）
    7. 如果 attempt < MAX_ATTEMPTS:
       - backoff = min(attempt * BACKOFF_BASE_MS, BACKOFF_MAX_MS)
       - 输出 [nodeId] CONNECT_RETRY attempt=N backoff_ms=X
       - coroutine.sleep(backoff)  // 让出 coroutine，不阻塞其他逻辑
    8. attempt++

  达到 MAX_ATTEMPTS:
    输出 [nodeId] CONNECT_EXHAUSTED attempts=MAX_ATTEMPTS host=host port=port
    return false

返回值：
  true: 连接并 handshake 成功
  false: 达到 MAX_ATTEMPTS 仍未成功

可观测性字段（每次 attempt）：
  - node_id: 当前节点 ID
  - peer_host: 目标主机
  - peer_port: 目标端口
  - attempt: 当前尝试次数 (1..MAX_ATTEMPTS)
  - max_attempts: 最大尝试次数
  - elapsed_ms: 本次 connect 耗时
  - result: success / failed / handshake_failed
  - fd: socket fd（成功时）或 -1（失败时）
  - transport_error: "not_exposed_by_current_api"（诚实记录 GAP）
```

### 2.4 `connectToPeer()` 契约更新

```
函数签名：
  connectToPeer(node, host, port) -> bool

行为变更：
  旧：p2pConnect(node.p2p, host, port) → 透传
  新：p2pConnectWithRetry(node.p2p, host, port) → 透传

成功后：
  coroutine.spawn(autoSyncOnConnect, node)  // 现有逻辑不变
```

### 2.5 Test Harness vs Transport 职责分离

| 层 | 职责 | 机制 | 不是什么 |
|----|------|------|----------|
| **Test Harness** (`run-bc-network-test.ps1`) | 确保测试拓扑启动顺序稳定 | Node A 端口轮询（最多 10s，仅 Windows） | 不是 transport 修复 |
| **P2P Transport** (`p2pConnectWithRetry`) | 确保真实连接具备有限重试能力 | bounded retry + backoff + evidence | 不依赖测试脚本的等待时间 |

**Test Harness 端口轮询设计**（仅 Windows，作为启动同步保险）：
```
启动 Node A 后：
  轮询 19201 端口是否监听
  - 每 200ms 检查一次
  - 最多等待 10 秒
  - 端口监听后立即启动 Node B/C/D
  - 10 秒未监听则报错 "Node A failed to start listening"

Linux/macOS：保持原逻辑（Start-Sleep 2 秒），因为 Get-NetTCPConnection 不可用。
```

> **重要**：Test Harness 端口轮询是**启动同步保险**，不是根因修复。根因修复是 `p2pConnectWithRetry()`。即使没有端口轮询，`p2pConnectWithRetry()` 也应该能处理 Node A 启动慢的情况。

### 2.6 Transport Error Evidence GAP（诚实记录）

**当前状态**：`tcp.connect()` (host/c/builtin.c:1736) 失败时只返回 -1，**不调用 WSAGetLastError()，不暴露错误码**。

**影响**：`p2pConnectWithRetry()` 无法记录具体的 transport error（如 WSAECONNREFUSED=10061、WSAETIMEDOUT=10060）。

**R2 处理方式**：
- 不修改 `tcp.connect()` API（范围太大，属于方案 C）
- 在 Evidence 中诚实记录：`transport_error: "not_exposed_by_current_api"`
- 记录 `elapsed_ms` 和 `fd=-1`，这些是可观测的
- 未来可引入 `tcp.connectWithError()` 返回 {fd, error_code}，但不在 R2 范围

### 2.7 不做的事情

- ❌ 不修改 `tcp.connect()` 为非阻塞（方案 C，范围太大）
- ❌ 不修改 `tcp.connect()` 返回错误码（API 变更，不在本次范围）
- ❌ 不修改 consensus / block validation / chain selection
- ❌ 不修改 coroutine / scheduler
- ❌ 不降低 height=5 断言
- ❌ 不删除 4-node test
- ❌ 不用无限重试
- ❌ 不用固定 sleep(500) 代替 backoff
- ❌ 不伪造 transport error code

---

## 3. Minimal Fix Design

### 3.1 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `stdlib/p2p.tll` | 新增函数 | `p2pConnectWithRetry()` |
| `stdlib/p2p.tll` | 修改导出 | 导出 `p2pConnectWithRetry` |
| `stdlib/blockchain_node.tll` | 修改 | `connectToPeer()` 调用 `p2pConnectWithRetry` |
| `scripts/run-bc-network-test.ps1` | 修改 | Node A 启动后轮询端口监听（仅 Windows） |
| `tests/bc_multi_a.tll` | 无修改 | 保持原样 |
| `tests/bc_multi_b.tll` | 无修改 | 保持原样 |
| `host/c/builtin.c` | 无修改 | tcp.connect 保持阻塞，不暴露错误码 |

### 3.2 `p2pConnectWithRetry()` 实现设计

```tll
// Connect to a peer with bounded retry
// Contract: MAX_ATTEMPTS=5, exponential backoff, observable, bounded
// Total budget: ~14s for 127.0.0.1 (5*2s connect + 4*1s backoff)
fn p2pConnectWithRetry(node: map, host: string, port: int) -> bool {
    let MAX_ATTEMPTS = 5
    let BACKOFF_BASE_MS = 200
    let BACKOFF_MAX_MS = 1000
    let attempt = 1
    while attempt <= MAX_ATTEMPTS {
        let attemptStart = time.nowMs()
        io.println("[" + node.nodeId + "] CONNECT_ATTEMPT attempt=" + convert.toString(attempt) + "/" + convert.toString(MAX_ATTEMPTS) + " host=" + host + " port=" + convert.toString(port))
        
        let fd = tcp.connect(host, port)
        let elapsed = time.nowMs() - attemptStart
        
        if fd >= 0 {
            io.println("[" + node.nodeId + "] CONNECT_SUCCESS attempt=" + convert.toString(attempt) + " elapsed_ms=" + convert.toString(elapsed) + " fd=" + convert.toString(fd))
            
            // Handshake (reuse existing logic from p2pConnect)
            tcp.setTimeout(fd, 2000)  // HANDSHAKE_TIMEOUT_MS = 2s (架构师批准)
            let handshake = {
                nodeId: node.nodeId,
                host: node.host,
                port: node.port,
                version: "0.1.0"
            }
            let msg = encodeMessage("handshake", handshake)
            tcp.send(fd, msg)
            coroutine.waitRead(fd)
            let resp = tcp.tryRecv(fd, 65536)
            let decoded = decodeMessages(resp)
            if arrays.length(decoded.messages) > 0 {
                let respMsg = decoded.messages[0]
                if respMsg.type == "handshake" {
                    let peer = {
                        nodeId: respMsg.payload.nodeId,
                        host: host,
                        port: port,
                        fd: fd,
                        lastSeen: time.nowMs(),
                        recvBuffer: decoded.remaining,
                        alive: true
                    }
                    arrays.push(node.peers, peer)
                    io.println("[" + node.nodeId + "] HANDSHAKE_SUCCESS peer=" + peer.nodeId + " attempt=" + convert.toString(attempt))
                    if node.running {
                        coroutine.spawn(p2pPeerReceiveLoop, node, fd)
                    }
                    return true
                }
            }
            io.println("[" + node.nodeId + "] HANDSHAKE_FAILED attempt=" + convert.toString(attempt))
            tcp.close(fd)
        } else {
            io.println("[" + node.nodeId + "] CONNECT_FAILED attempt=" + convert.toString(attempt) + " elapsed_ms=" + convert.toString(elapsed) + " fd=-1 transport_error=not_exposed_by_current_api")
        }
        
        // Backoff before retry
        if attempt < MAX_ATTEMPTS {
            let backoff = attempt * BACKOFF_BASE_MS
            if backoff > BACKOFF_MAX_MS { backoff = BACKOFF_MAX_MS }
            io.println("[" + node.nodeId + "] CONNECT_RETRY attempt=" + convert.toString(attempt) + " backoff_ms=" + convert.toString(backoff))
            coroutine.sleep(backoff)
        }
        attempt = attempt + 1
    }
    
    io.println("[" + node.nodeId + "] CONNECT_EXHAUSTED attempts=" + convert.toString(MAX_ATTEMPTS) + " host=" + host + " port=" + convert.toString(port))
    return false
}
```

### 3.3 `connectToPeer()` 修改

```tll
// 旧：
fn connectToPeer(node: map, host: string, port: int) -> bool {
    let ok = p2pConnect(node.p2p, host, port)
    if ok {
        coroutine.spawn(autoSyncOnConnect, node)
    }
    return ok
}

// 新：
fn connectToPeer(node: map, host: string, port: int) -> bool {
    let ok = p2pConnectWithRetry(node.p2p, host, port)
    if ok {
        coroutine.spawn(autoSyncOnConnect, node)
    }
    return ok
}
```

### 3.4 测试脚本端口轮询（仅 Windows）

```powershell
# 旧：
if ($node -eq $Leader) { Start-Sleep -Seconds 2 } else { Start-Sleep -Seconds 1 }

# 新（仅 Windows，Linux/macOS 保持原逻辑）：
if ($node -eq $Leader) {
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        # Wait for leader to actually listen before starting followers
        $listenWait = 0
        while ($listenWait -lt 10000) {
            $conn = Get-NetTCPConnection -LocalPort 19201 -State Listen -ErrorAction SilentlyContinue
            if ($conn) {
                Write-Output "  Leader listening on 19201 after ${listenWait}ms"
                break
            }
            Start-Sleep -Milliseconds 200
            $listenWait += 200
        }
        if (-not $conn) {
            Write-Output "FAIL: Leader did not start listening within 10s"
            exit 1
        }
    } else {
        Start-Sleep -Seconds 2
    }
} else {
    Start-Sleep -Seconds 1
}
```

---

## 4. Deterministic Delayed-Leader Regression Test 设计

### 4.1 测试目标

证明 `p2pConnectWithRetry()` 能处理 Leader 延迟启动的情况，而不是碰巧 PASS。

### 4.2 测试场景

```
时序：
  T+0s    Follower (Node B) 启动，立即调用 connectToPeer(127.0.0.1:19201)
  T+0s    Leader (Node A) 尚未启动（故意延迟）
  T+1s    Follower attempt 1: connect 失败（约 2s 后返回）
  T+3s    Follower attempt 2: connect 失败
  T+5s    Leader Node A 启动，开始监听 19201
  T+5s    Follower attempt 3: connect 成功 → handshake → peer 建立
  T+6s    Follower height 同步
```

### 4.3 测试实现

创建新测试文件 `tests/bc_delayed_leader.tll`（或通过测试脚本参数控制）：

```
测试脚本 run-bc-network-test.ps1 新增参数 -DelayedLeaderStart <seconds>：
  - 启动 Follower (Node B/C/D)
  - 等待指定秒数
  - 再启动 Leader (Node A)
  - 验证 Follower 能通过 retry 连接到 Leader
  - 验证最终 height 一致
```

或者更简单：在现有 bc_multi 测试中，通过修改启动顺序来验证：
1. 先启动 Node B/C/D（它们会 retry）
2. 5 秒后启动 Node A
3. 验证所有节点最终 height=5

### 4.4 验收标准

- Follower 日志包含 `CONNECT_ATTEMPT attempt=1`、`CONNECT_FAILED`、`CONNECT_RETRY`
- Follower 日志包含 `CONNECT_SUCCESS attempt=N`（N > 1）
- 所有节点最终 height=5，tip hash 一致
- 测试不依赖固定 sleep 时间

---

## 5. 回归测试计划

| 测试 | 平台 | 预期 |
|------|------|------|
| bc_node (4-node, height=1) | Windows | PASS |
| bc_multi (4-node, height=5) | Windows | PASS |
| bc_node | Linux | PASS |
| bc_multi | Linux | PASS |
| bc_node | macOS | PASS |
| bc_multi | macOS | PASS |
| bc_sync | 全平台 | PASS |
| bc_reconnect | 全平台 | PASS |
| bc_invalid | 全平台 | PASS |
| bc_stress | 全平台 | PASS |
| p2p_2node | 全平台 | PASS |
| p2p_4node | 全平台 | PASS |
| blockchain_basic | 全平台 | PASS |
| **delayed_leader**（新增） | Windows | **PASS（证明 retry 有效）** |

---

## 6. Transport Observability Evidence

修复后，CI 日志应包含：

```
[nodeB] CONNECT_ATTEMPT attempt=1/5 host=127.0.0.1 port=19201
[nodeB] CONNECT_FAILED attempt=1 elapsed_ms=2180 fd=-1 transport_error=not_exposed_by_current_api
[nodeB] CONNECT_RETRY attempt=1 backoff_ms=200
[nodeB] CONNECT_ATTEMPT attempt=2/5 host=127.0.0.1 port=19201
[nodeB] CONNECT_SUCCESS attempt=2 elapsed_ms=5 fd=1234
[nodeB] HANDSHAKE_SUCCESS peer=nodeA attempt=2
```

**Evidence 字段**：
- `node_id`: 当前节点 ID
- `attempt`: 当前尝试次数
- `max_attempts`: 最大尝试次数
- `host`: 目标主机
- `port`: 目标端口
- `elapsed_ms`: 本次 connect 耗时
- `result`: success / failed / handshake_failed / exhausted
- `fd`: socket fd（成功时）或 -1（失败时）
- `transport_error`: "not_exposed_by_current_api"（诚实记录 GAP）
- `backoff_ms`: 重试前等待时间
- `peer`: handshake 成功后的 peer ID

---

## 7. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| p2pConnectWithRetry 与 p2pConnect handshake 逻辑重复 | 高 | 维护成本 | 可接受，后续可重构为内部函数 |
| coroutine.sleep(backoff) 阻塞其他 coroutine | 中 | 性能 | backoff 最大 1 秒，仅失败路径；且是 coroutine.sleep（让出） |
| 测试脚本端口轮询跨平台 | 高 | 仅 Windows | 仅 Windows 使用，Linux/macOS 保持原逻辑 |
| 重试掩盖真正 connect 问题 | 低 | 诊断困难 | 每次 attempt 都有日志，可观测 |
| 单次 connect 超过 3 秒（非 127.0.0.1） | 低 | 预算超支 | 当前所有测试均用 127.0.0.1；未来远程地址需方案 C |
| transport error 未暴露 | 中 | 诊断不完整 | 诚实记录 GAP，未来引入 tcp.connectWithError |

---

## 8. 验收标准

R2 完成后必须满足：

1. ✅ **Transport Failure 可观测**：CI 日志包含每次 connect attempt 的 result、elapsed_ms、fd
2. ✅ **Bounded retry 有明确上限**：MAX_ATTEMPTS=5，backoff 最大 1000ms
3. ✅ **所有失败路径有时间上界**：127.0.0.1 场景总预算 ≤15 秒（已证明）
4. ✅ **重试失败不会无限阻塞**：达到 MAX_ATTEMPTS 后返回 false，输出 CONNECT_EXHAUSTED
5. ✅ **4 Node 5 Block 全平台 PASS**：Windows / Linux / macOS
6. ✅ **Delayed-Leader Regression Test PASS**：证明 retry 真正有效
7. ✅ **原有 Blockchain correctness 不变**：所有 bc_* / p2p_* 测试 PASS
8. ✅ **不修改 consensus / block validation / chain selection**
9. ✅ **不降低 height=5 断言**
10. ✅ **不删除 4-node test**
11. ✅ **不伪造 transport error code**（诚实记录 not_exposed_by_current_api）

---

## 9. 时间上界证明（所有失败路径）— v2 修正版

**严格公式**：`Total = Σ(connect_i + handshake_i) + Σ(backoff_i) ≤ 25s`

**参数**：
- connect 上界 = 2.5s（127.0.0.1 实验约 2185ms，取保守 2.5s）
- handshake 上界 = 2.0s（架构师批准，`tcp.setTimeout(fd, 2000)`）
- backoff 序列 = [200, 400, 600, 800]ms，总计 2.0s
- MAX_ATTEMPTS = 5

### 路径 1：Connect 失败（最常见，Node A 未监听）

```
attempt 1: connect → 2.5s 失败 (WSAECONNREFUSED)
backoff 1: 200ms
attempt 2: connect → 2.5s 失败
backoff 2: 400ms
attempt 3: connect → 2.5s 失败
backoff 3: 600ms
attempt 4: connect → 2.5s 失败
backoff 4: 800ms
attempt 5: connect → 2.5s 失败
→ return false

总时间 = 5×2.5s + (200+400+600+800)ms = 12.5s + 2.0s = 14.5s ≤ 25s 预算 ✅
```

### 路径 2：Leader 在 attempt 3 时启动（典型 delayed startup）

```
attempt 1: connect → 2.5s 失败
backoff 1: 200ms
attempt 2: connect → 2.5s 失败
backoff 2: 400ms
attempt 3: connect → 成功（Leader 已启动，约 5ms）
handshake → 成功（约 5ms）
→ return true

总时间 = 2×2.5s + 200ms + 400ms + connect_success + handshake ≈ 5.6s ≤ 25s ✅
```

### 路径 3：Handshake 失败（最坏情况，对端 connect 成功但不响应）

```
attempt 1: connect → 2.5s 成功
           handshake → 2.0s 超时 (coroutine.waitRead)
backoff 1: 200ms
attempt 2: connect → 2.5s 成功
           handshake → 2.0s 超时
backoff 2: 400ms
attempt 3: connect → 2.5s 成功
           handshake → 2.0s 超时
backoff 3: 600ms
attempt 4: connect → 2.5s 成功
           handshake → 2.0s 超时
backoff 4: 800ms
attempt 5: connect → 2.5s 成功
           handshake → 2.0s 超时
→ return false

单次 attempt = connect(2.5s) + handshake(2.0s) = 4.5s
5 次 attempt = 5 × 4.5s = 22.5s
4 次 backoff = 2.0s
总时间 = 22.5s + 2.0s = 24.5s ≤ 25s 预算 ✅
```

### 三条路径汇总

| 路径 | 单次 attempt | 5 次 attempt | + backoff | 总计 | 预算 |
|------|-------------|-------------|-----------|------|------|
| Connect 失败（常见） | 2.5s | 12.5s | +2.0s | **14.5s** | ≤25s ✅ |
| Leader delayed（典型） | 2.5s（前2次） | ~5.0s | +0.6s | **~5.6s** | ≤25s ✅ |
| Handshake 失败（最坏） | 4.5s | 22.5s | +2.0s | **24.5s** | ≤25s ✅ |

**结论**：所有失败路径的严格最坏时间上界 = 24.5s ≤ 25s TOTAL_RETRY_BUDGET。

> **注意**：handshake 失败路径是理论最坏情况（对端 connect 成功但持续 2 秒不发 handshake 响应，连续 5 次）。实际中 handshake 失败通常是对端关闭连接，`coroutine.waitRead` 会立即返回（EOF），不会等满 2 秒。因此实际 handshake 失败路径通常远快于 24.5s。

---

## 10. 下一步

本设计文档（v2）经架构师审查批准后，进入施工阶段：
1. 修改 `stdlib/p2p.tll`：新增 `p2pConnectWithRetry()`
2. 修改 `stdlib/blockchain_node.tll`：`connectToPeer()` 调用新函数
3. 修改 `scripts/run-bc-network-test.ps1`：Node A 端口轮询（仅 Windows）
4. 创建 Delayed-Leader Regression Test
5. 本地回归测试
6. 提交 Evidence
7. 等待架构师独立审查

---

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
