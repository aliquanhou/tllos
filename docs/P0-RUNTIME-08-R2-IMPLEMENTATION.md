# P0-RUNTIME-08-R2-IMPLEMENTATION — Bounded Transport Retry

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）

**设计基线**: `41bfa3a` (R2 Design v2.1)
**实现提交**: 待提交

---

## 1. 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `stdlib/p2p.tll` | 新增函数 | `p2pConnectWithRetry()` — bounded retry with observable evidence |
| `stdlib/blockchain_node.tll` | 修改 | `connectToPeer()` 从 `p2pConnect` 改为 `p2pConnectWithRetry`；import 添加新函数 |
| `scripts/run-bc-network-test.ps1` | 修改 | Windows 端口轮询（动态读取 leader 端口）+ `bc_delayed` delayed-leader regression 配置 |

**未修改**（符合施工令禁止范围）：
- ❌ `tcp.connect()` — 保持 blocking，未修改
- ❌ Consensus / Block validation / Chain selection
- ❌ Coroutine / Scheduler
- ❌ `height=5` 原测试断言
- ❌ 无限 retry / 大 sleep 掩盖问题

---

## 2. p2pConnectWithRetry() 实现细节

### 参数（架构师批准）

| 参数 | 值 | 说明 |
|------|-----|------|
| `MAX_ATTEMPTS` | 5 | 最大尝试次数 |
| `BACKOFF_BASE_MS` | 200 | 初始 backoff |
| `BACKOFF_MAX_MS` | 1000 | 最大 backoff |
| `HANDSHAKE_TIMEOUT_MS` | 2000 | handshake 超时（独立于 connect） |

### 可观测 Evidence 事件

每次 attempt 输出以下事件之一：
- `CONNECT_ATTEMPT` — attempt=N/5, host, port
- `CONNECT_SUCCESS` — attempt, elapsed_ms, fd
- `CONNECT_FAILED` — attempt, elapsed_ms, fd=-1, **transport_error=not_exposed_by_current_api**
- `HANDSHAKE_SUCCESS` — peer, attempt
- `HANDSHAKE_FAILED` — attempt, elapsed_ms
- `CONNECT_RETRY` — attempt, backoff_ms
- `CONNECT_EXHAUSTED` — attempts=5, host, port

### 诚实性保证

- **不伪造 WSA error code**：`tcp.connect()` 当前 API 不暴露 `WSAGetLastError()`，因此 `transport_error` 诚实记录为 `not_exposed_by_current_api`
- **不包装成 tcp.connect() 具有 2.5s timeout**：2.5s 是 Windows 127.0.0.1 工程上界假设，不是 TCP API 绝对保证
- **所有失败路径 fail-closed**：5 次 attempt 全部失败后返回 `false`，不无限重试

---

## 3. 时间预算验证

**严格公式**：`Total = Σ(connect_i + handshake_i) + Σ(backoff_i) ≤ 25s`

| 路径 | 单次 attempt | 5 次 attempt | + backoff | 总计 | 预算 |
|------|-------------|-------------|-----------|------|------|
| Connect 失败（常见） | 2.5s | 12.5s | +2.0s | **14.5s** | ≤25s ✅ |
| Leader delayed（典型） | 2.5s（前2次） | ~5.0s | +0.6s | **~5.6s** | ≤25s ✅ |
| Handshake 失败（最坏） | 4.5s | 22.5s | +2.0s | **24.5s** | ≤25s ✅ |

**结论**：所有失败路径的严格最坏时间上界 = 24.5s ≤ 25s TOTAL_RETRY_BUDGET ✅

---

## 4. 本地测试结果

### 4.1 bc_node（原有 4-node / height=1）

**结果**: ✅ PASS

```
Leader listening on port 19101 after 0ms
Node a : height=1 tip=09324d40... valid=true
Node b : height=1 tip=09324d40... valid=true
Node c : height=1 tip=09324d40... valid=true
Node d : height=1 tip=09324d40... valid=true
All nodes tip hash match
PASS: bc_node - all assertions passed
```

### 4.2 bc_multi（原有 4-node / 5-block）

**结果**: ✅ PASS

```
Leader listening on 19201 after 0ms
Node a : height=5 tip=05a5c8cb... valid=true
Node b : height=5 tip=05a5c8cb... valid=true
Node c : height=5 tip=05a5c8cb... valid=true
Node d : height=5 tip=05a5c8cb... valid=true
All nodes tip hash match
PASS: bc_multi - all assertions passed
```

### 4.3 bc_delayed（新增 delayed-leader regression）

**结果**: ✅ PASS

**配置**: Nodes=b,c,d,a（follower 先启动），leader 延迟 5 秒启动，Wait=45s, MinHeight=5

```
Node b : height=5 tip=06ec3348... valid=true
Node c : height=5 tip=06ec3348... valid=true
Node d : height=5 tip=06ec3348... valid=true
Node a : height=5 tip=06ec3348... valid=true
All nodes tip hash match
PASS: bc_delayed - all assertions passed
```

---

## 5. Transport Evidence — Retry 真实证据

### Node B（follower，经历 retry）

```
[nodeB] CONNECT_ATTEMPT attempt=1/5 host=127.0.0.1 port=19201
[nodeB] CONNECT_FAILED attempt=1 elapsed_ms=2081 fd=-1 transport_error=not_exposed_by_current_api
[nodeB] CONNECT_RETRY attempt=1 backoff_ms=200
[nodeB] CONNECT_ATTEMPT attempt=2/5 host=127.0.0.1 port=19201
[nodeB] CONNECT_SUCCESS attempt=2 elapsed_ms=1012 fd=244
[nodeB] HANDSHAKE_SUCCESS peer=nodeA attempt=2
```

### Node C（follower，经历 retry）

```
[nodeC] CONNECT_ATTEMPT attempt=1/5 host=127.0.0.1 port=19201
[nodeC] CONNECT_FAILED attempt=1 elapsed_ms=2030 fd=-1 transport_error=not_exposed_by_current_api
[nodeC] CONNECT_RETRY attempt=1 backoff_ms=200
[nodeC] CONNECT_ATTEMPT attempt=2/5 host=127.0.0.1 port=19201
[nodeC] CONNECT_SUCCESS attempt=2 elapsed_ms=0 fd=248
[nodeC] HANDSHAKE_SUCCESS peer=nodeA attempt=2
```

### Node D（follower，启动时 leader 已监听）

```
[nodeD] CONNECT_ATTEMPT attempt=1/5 host=127.0.0.1 port=19201
[nodeD] CONNECT_SUCCESS attempt=1 elapsed_ms=1020 fd=252
[nodeD] HANDSHAKE_SUCCESS peer=nodeA attempt=1
```

### Evidence 验证要点

- ✅ **Transport failure 可观测**: `CONNECT_FAILED` with `elapsed_ms=2081` and `transport_error=not_exposed_by_current_api`
- ✅ **Bounded retry 有效**: attempt 1 失败 → backoff 200ms → attempt 2 成功
- ✅ **不伪造 WSA error code**: `transport_error=not_exposed_by_current_api` 诚实记录
- ✅ **Handshake 成功**: `HANDSHAKE_SUCCESS peer=nodeA`
- ✅ **4 节点最终同步**: height=5, same tip

---

## 6. Windows 端口轮询（Test Harness Startup Sync）

### 设计原则

- **明确标注为 TEST HARNESS startup sync，NOT transport bug fix**
- 真正的 transport retry 在 `p2pConnectWithRetry()` 中
- 动态读取 leader 端口（从测试源文件 `createBlockchainNode()` 调用中解析）
- 支持不同测试使用不同端口（bc_node=19101, bc_multi=19201）

### 实现

```powershell
# 动态读取 leader 端口
$leaderSrc = "tests\${TestPrefix}_${Leader}.tll"
$portMatch = Select-String -Path $leaderSrc -Pattern 'createBlockchainNode\("[^"]+",\s*"[^"]+",\s*(\d+)'
$leaderPort = [int]$portMatch.Matches[0].Groups[1].Value

# 轮询端口，最多 10 秒
while ($listenWait -lt 10000) {
    $conn = Get-NetTCPConnection -LocalPort $leaderPort -State Listen
    if ($conn) { break }
    Start-Sleep -Milliseconds 200
    $listenWait += 200
}
```

---

## 7. 未覆盖平台 / Outstanding GAP

### Linux / macOS

- 本地 Windows 环境无法直接运行 Linux/macOS 测试
- 需要通过 GitHub CI 验证三平台行为
- `p2pConnectWithRetry()` 是纯 TLL 实现，不依赖平台特定 API，理论上跨平台兼容

### Outstanding GAP

1. **`tcp.connect()` 不暴露错误码**：`transport_error=not_exposed_by_current_api`，未来可考虑扩展 API 暴露 `WSAGetLastError()` / `errno`
2. **ASan 100K**：P0-RUNTIME-07 遗留的资源限制问题，不阻塞本单
3. **全量 CI P2P/Blockchain**：全量 CI 中可能仍有其他独立问题，需在 CI 中验证

---

## 8. 验收标准对照

| 架构师要求 | 状态 | 证据 |
|-----------|------|------|
| `p2pConnectWithRetry()` bounded retry | ✅ | MAX_ATTEMPTS=5, backoff=200/400/600/800ms |
| 每次 attempt 可观测 | ✅ | CONNECT_ATTEMPT/SUCCESS/FAILED/RETRY/EXHAUSTED |
| 不修改 `tcp.connect()` | ✅ | 保持 blocking，未修改 |
| `connectToPeer()` 接入 bounded retry | ✅ | blockchain_node.tll 已修改 |
| Handshake timeout = 2s | ✅ | `tcp.setTimeout(fd, 2000)` |
| 所有路径 fail-closed | ✅ | 5 次失败后返回 false |
| Windows 端口轮询（startup sync） | ✅ | 动态读取端口，最多 10s |
| 明确标注为 startup sync，不是 transport fix | ✅ | 代码注释明确说明 |
| Delayed-leader regression test | ✅ | bc_delayed，follower 先启动，leader 延迟 5s |
| 前若干次连接失败，后续 retry 成功 | ✅ | Node B/C attempt 1 失败，attempt 2 成功 |
| 4 节点最终同步到 height=5 | ✅ | bc_delayed PASS, tip 一致 |
| Evidence: node_id, peer, host, port, attempt, max_attempts, elapsed_ms, result, fd, backoff_ms | ✅ | 日志包含所有字段 |
| transport_error = not_exposed_by_current_api | ✅ | 诚实记录，不伪造 WSA error code |
| 禁止碰 tcp.connect / Consensus / Coroutine / height=5 | ✅ | 均未修改 |
| 原有 4-node / 5-block 测试通过 | ✅ | bc_multi PASS |
| p2p 相关测试通过 | ✅ | p2p 层通过 blockchain 测试间接覆盖 |

---

## 9. 提交信息（待提交）

```
feat(p2p): P0-RUNTIME-08-R2 bounded transport retry + delayed-leader regression

- stdlib/p2p.tll: add p2pConnectWithRetry() (MAX_ATTEMPTS=5, bounded backoff,
  handshake timeout=2s, observable evidence, fail-closed)
- stdlib/blockchain_node.tll: connectToPeer() uses p2pConnectWithRetry()
- scripts/run-bc-network-test.ps1: Windows port polling (dynamic leader port,
  startup sync NOT transport fix) + bc_delayed delayed-leader regression test
- Transport evidence: CONNECT_ATTEMPT/SUCCESS/FAILED/RETRY/EXHAUSTED
- transport_error=not_exposed_by_current_api (honest, no fabricated WSA code)
- Time budget: worst case 24.5s <= 25s TOTAL_RETRY_BUDGET
- Tests: bc_node PASS, bc_multi PASS, bc_delayed PASS (retry evidence verified)
- NOT modified: tcp.connect, Consensus, Coroutine, height=5 assertions
```

---

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）

*Implementation complete. Waiting for independent architecture audit.*
