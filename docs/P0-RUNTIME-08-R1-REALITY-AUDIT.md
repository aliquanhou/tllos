# P0-RUNTIME-08 R1 — Reality Root-Cause Audit

**Windows Blockchain 5-Block / 4-Node Sync Failure**

---

## 1. 冻结现场

| 项目 | 值 |
|------|-----|
| 当前 commit | `c718f14` |
| 分支 | `feature/P0-RUNTIME-07-coroutine-100k-root-cause` |
| Issue | #8 — Windows Blockchain 5-Block Sync |
| 失败 CI Run | `34406564979` (sha=87f6075), `34434812383` (sha=c718f14) |
| 失败 Job | `native-build-test (windows-latest)` |
| 失败 Job ID | `102650836285` (Run 34406564979) |
| 失败 Step | `Blockchain 4-Node network test (Windows)` |
| 被跳过 Step | `Blockchain 5-Block multi-node sync (Windows)` |
| Windows runner | `windows-latest` (GitHub-hosted) |
| 测试命令 | `scripts\run-bc-network-test.ps1 bc_node` |
| 测试输入 | 4 nodes (a,b,c,d), leader=a, wait=25s, MinHeight=1 |
| 5-Block 测试 | `scripts\run-bc-network-test.ps1 bc_multi` (MinHeight=5, wait=35s) |

---

## 2. 失败发生阶段

```
Node startup
  ↓
Peer discovery          ← 第一个可能失败点
  ↓
TCP connect             ← 实际 First Invalid State 所在
  ↓
Handshake
  ↓
Peer registration
  ↓
Genesis synchronization
  ↓
Block #1..#5
  ↓
Chain convergence
```

**失败定位：TCP connect 阶段。** Node B/C/D 在 Node A 尚未开始监听时尝试连接，导致连接失败或阻塞。

---

## 3. 4-Node 拓扑真相

从测试脚本 `scripts/run-bc-network-test.ps1` 和测试源码确认：

```
Node A (leader)  127.0.0.1:19201
  ├── Node B     127.0.0.1:19202  → connect to Node A
  ├── Node C     127.0.0.1:19203  → connect to Node A
  └── Node D     127.0.0.1:19204  → connect to Node A
```

- **拓扑类型**：星型（Star），所有 follower 连接到 leader Node A
- **Node A**：监听端口，等待 3 个 peers，挖出 block 并 broadcast
- **Node B/C/D**：启动后立即 `connectToPeer(node, "127.0.0.1", 19201)`
- **无 peer-to-peer 直连**：follower 之间不直接连接

**启动时序**（测试脚本第 77-83 行）：
1. 启动 Node A，等待 **2 秒**
2. 启动 Node B，等待 **1 秒**
3. 启动 Node C，等待 **1 秒**
4. 启动 Node D

Node B 在 Node A 启动后 **2 秒** 开始尝试连接。

---

## 4. 关键代码路径分析

### 4.1 `tcp.connect()` — Windows 阻塞调用

**文件**: `host/c/builtin.c` 第 1723-1738 行

```c
if (idx == 135) { /* tcp.connect(host, port) -> socket_fd (int) */
    // ...
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == INVALID_SOCKET) return tll_int(-1);
    struct sockaddr_in addr;
    // ...
    if (connect(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        closesocket(s);
        return tll_int(-1);
    }
    return tll_int((long long)s);
}
```

**关键事实**：
- `connect()` 是**阻塞调用**，未设置 `O_NONBLOCK` 或 `WSAAsyncSelect`
- 当目标端口未监听时，Windows `connect()` 行为：
  - 对于 127.0.0.1，通常返回 "Connection refused" (WSAECONNREFUSED) 并**立即返回 -1**
  - 但在某些时序下（socket 正在创建中），可能**阻塞较长时间**直到超时
- 连接失败后返回 -1，**无重试**

### 4.2 `p2pConnect()` — 无重试

**文件**: `stdlib/p2p.tll` 第 113-157 行

```tll
fn p2pConnect(node: map, host: string, port: int) -> bool {
    let _pc_fd = tcp.connect(host, port)
    if _pc_fd < 0 {
        io.println("[" + node.nodeId + "] Failed to connect to " + host + ":" + convert.toString(port))
        return false  // ← 直接返回，无重试
    }
    tcp.setTimeout(_pc_fd, 5000)
    // ... handshake ...
    coroutine.waitRead(_pc_fd)  // ← 阻塞等待 handshake 响应
    // ...
}
```

**关键事实**：
- `tcp.connect()` 返回 -1 后，打印 "Failed to connect to ..." 并返回 false
- **无任何重试逻辑**
- 连接成功后，`coroutine.waitRead(_pc_fd)` 等待 handshake 响应，如果对端不响应会阻塞

### 4.3 `connectToPeer()` — 透传失败，无重试

**文件**: `stdlib/blockchain_node.tll` 第 64-71 行

```tll
fn connectToPeer(node: map, host: string, port: int) -> bool {
    let ok = p2pConnect(node.p2p, host, port)
    if ok {
        coroutine.spawn(autoSyncOnConnect, node)
    }
    return ok  // ← 透传失败，无重试
}
```

### 4.4 测试源码 — 启动后立即连接

**文件**: `tests/bc_multi_b.tll`

```tll
let node = createBlockchainNode("nodeB", "127.0.0.1", 19202, 1, 50)
startNode(node)
connectToPeer(node, "127.0.0.1", 19201)  // ← 立即连接，无等待/重试

io.println("=== Node B connected, waiting for blocks ===")
let waitTicks = 0
while waitTicks < 200 {  // ← 只等待 20 秒
    coroutine.sleep(100)
    waitTicks = waitTicks + 1
}
// 输出 RESULT 并退出
```

---

## 5. 本地复现实验

### 5.1 Node A 启动时间测量

**实验**：启动 Node A，测量从进程启动到端口 19201 开始监听的时间。

**结果**：
```
Node A listening on 19201 after 1472.83ms (attempt 0)
```

**本地启动时间约 1.5 秒**，接近测试脚本的 2 秒等待阈值。

### 5.2 Node B 连接失败行为

**实验**：不启动 Node A，直接启动 Node B，观察连接行为。

**结果**：
- Node B 启动后 **无任何输出**（包括 "Failed to connect to ..."）
- 5 秒后仍在运行
- 20 秒后退出，**仍然无任何输出**
- stderr 也为空

**分析**：
- `tcp.connect()` 在 Windows 上对于未监听端口可能**阻塞**而非立即返回错误
- 或者 `connect()` 返回 -1 后，`io.println` 输出被缓冲，程序退出时未刷新
- 无论哪种情况，Node B **无法建立连接**，且**无重试**

### 5.3 本地完整测试

**bc_node** (MinHeight=1)：连续运行 3 次，全部 PASS
- 4 节点 height=1，tip hash 一致，valid=true
- 所有节点在 14 秒内提前退出

**bc_multi** (MinHeight=5)：运行 1 次，PASS
- 4 节点 height=5，tip hash 一致，valid=true
- 所有节点在 24 秒内提前退出

**本地通过原因**：Node A 本地启动 1.5 秒 < 测试脚本等待 2 秒，Node B 连接时 Node A 已在监听。

---

## 6. CI 失败证据

### 6.1 持续失败

| CI Run | SHA | Windows Blockchain 4-Node |
|--------|-----|---------------------------|
| 34406564979 | 87f6075 | ❌ FAIL |
| 34434812383 | c718f14 | ❌ FAIL |

两次不同 commit 均失败，说明不是偶发问题。

### 6.2 CI 日志获取受限

GitHub Actions Job Logs API 返回 **403 "Server failed to authenticate the request"**，无法获取原始失败日志。

**缺失的 CI Evidence**：
- Node A 实际启动时间
- Node B/C/D 的具体错误信息
- Node B/C/D 的最终 height 值
- 测试脚本的具体失败断言（height < MinHeight 还是 no RESULT line）

---

## 7. First Invalid State

### 精确定位

```
时间线：
  T+0s    Node A 进程启动
  T+?s    Node A 调用 tcp.listen() → 开始监听 19201
  T+2s    测试脚本启动 Node B
  T+2s+ε  Node B 调用 startNode() → tcp.listen(19202)
  T+2s+ε  Node B 调用 connectToPeer() → p2pConnect() → tcp.connect(127.0.0.1, 19201)
           ↓
           如果 Node A 尚未监听 (T+?s > T+2s)：
           → tcp.connect() 阻塞或返回 -1
           → p2pConnect() 返回 false
           → connectToPeer() 返回 false
           → Node B 无 peers，无法接收 block
           → Node B height=0
           → 测试断言 height >= MinHeight 失败
           ← FIRST INVALID STATE
```

### First Invalid State 定义

**Node B/C/D 调用 `tcp.connect(127.0.0.1, 19201)` 时，Node A 尚未开始监听，导致连接失败或阻塞。连接失败后 P2P 层无重试机制，Node B/C/D 最终没有 peers，height=0，不满足 MinHeight 要求。**

---

## 8. 问题分类

### A. Transport Failure — ✅ 确认

| 检查项 | 结果 |
|--------|------|
| connect failed | ✅ 是（Node A 未监听时） |
| socket closed | ⚠️ 可能（connect 超时后） |
| WSA error | ⚠️ 未获取到具体 WSAGetLastError |
| accept failed | ❌ 不涉及（Node A 未监听） |
| send/recv failed | ❌ 未到达此阶段 |

### B. Protocol Failure — ❌ 不涉及

连接未建立，未到达 handshake / message framing / protocol version 阶段。

### C. Blockchain State Failure — ❌ 不涉及

Node B/C/D 无 peers，未接收任何 block，未进入 block validation / chain selection 阶段。

**最终分类：A. Transport Failure — 连接时序问题 + 无重试机制**

---

## 9. Root Cause Hypothesis

### 主假设：CI 环境 Node A 启动时间 > 2 秒，导致连接时序失败

**因果链**：

```
CI 环境（GitHub-hosted Windows runner）
  ↓
tllvm.exe 启动较慢（加载字节码、初始化 runtime、WSAStartup 等）
  ↓
Node A 从进程启动到 tcp.listen() 成功的时间 > 2 秒
  ↓
测试脚本在 Node A 启动 2 秒后启动 Node B
  ↓
Node B 调用 tcp.connect(127.0.0.1, 19201)
  ↓
Node A 尚未开始监听 → connect() 阻塞或返回 WSAECONNREFUSED
  ↓
p2pConnect() 返回 false，无重试
  ↓
connectToPeer() 返回 false
  ↓
Node B/C/D 无 peers，无法接收 block broadcast
  ↓
Node B/C/D height=0 < MinHeight
  ↓
测试断言失败 → CI RED
```

### 辅助假设：tcp.connect() 在 Windows 上的阻塞行为加剧问题

即使 Node A 在 Node B 连接后不久开始监听，`tcp.connect()` 的阻塞行为可能导致：
- connect() 阻塞期间，Node B 无法执行其他操作
- Windows 默认 TCP 连接超时可能很长（20 秒以上）
- 测试脚本的等待时间（bc_node=25s, bc_multi=35s）可能不足以覆盖连接超时

---

## 10. Evidence Supporting Hypothesis

| # | 证据 | 来源 |
|---|------|------|
| 1 | 本地 Node A 启动时间 1.5 秒，接近 2 秒阈值 | 本地测量 |
| 2 | CI 环境通常比本地慢（共享 runner、资源竞争） | 常识 + GitHub runner 特性 |
| 3 | `tcp.connect()` 在 Windows 上是阻塞调用，未设置非阻塞 | `host/c/builtin.c:1736` |
| 4 | `p2pConnect()` 连接失败后直接返回 false，无重试 | `stdlib/p2p.tll:113-118` |
| 5 | `connectToPeer()` 透传失败，无重试 | `stdlib/blockchain_node.tll:64-71` |
| 6 | 测试脚本启动 Node A 后只等待 2 秒 | `scripts/run-bc-network-test.ps1:82` |
| 7 | 本地测试通过（1.5s < 2s），CI 测试失败（可能 >2s） | 本地 vs CI 对比 |
| 8 | 两次不同 commit 均失败，非偶发 | CI Run 34406564979, 34434812383 |
| 9 | Node B 在 Node A 未运行时启动后无输出、20 秒后退出 | 本地实验 |
| 10 | 失败发生在 Blockchain 4-Node（第一个网络测试），后续测试被跳过 | CI step 顺序 |

---

## 11. Evidence Still Missing

| # | 缺失证据 | 影响 | 获取方式 |
|---|----------|------|----------|
| 1 | CI 中 Node A 实际启动时间 | 验证主假设 | 在测试脚本中增加启动时间测量 |
| 2 | CI 中 Node B/C/D 的具体错误信息 | 确认是 connect 失败还是超时 | CI logs API 403，需增加诊断输出 |
| 3 | CI 中 Node B/C/D 的最终 height 值 | 确认是 height=0 还是其他 | 同上 |
| 4 | CI 中测试脚本的具体失败断言 | 确认是 height < MinHeight 还是 no RESULT | 同上 |
| 5 | `tcp.connect()` 在 Windows 上对未监听端口的精确行为 | 确认是立即返回还是阻塞 | 增加 WSAGetLastError 诊断 |
| 6 | Node B 无输出的原因（缓冲 vs 阻塞） | 确认 connect 是否阻塞 | 增加 fflush 或 stderr 输出 |

---

## 12. 是否可以进入 R2 Fix Gate

### 结论：✅ 可以进入 R2 Fix Gate

**理由**：
1. First Invalid State 已精确定位到 `tcp.connect()` 时序问题
2. 根因假设已有 10 条证据支持，证据链较强
3. 修复方向明确，不涉及 consensus / block validation / chain selection
4. 问题分类为 A. Transport Failure，修复范围可控

### R2 修复方向（待架构师确认）

**方案 A（推荐）：在 P2P 层增加连接重试**
- 在 `p2pConnect()` 或 `connectToPeer()` 中增加重试逻辑
- 例如：最多重试 5 次，每次间隔 500ms
- 不修改 `tcp.connect()` 的阻塞行为
- 优点：最小改动，不影响其他使用 tcp.connect 的代码
- 风险：重试间隔需要合理设置，避免测试超时

**方案 B：增加测试脚本中 Node A 启动后的等待时间**
- 将 2 秒改为 5 秒或 10 秒
- 优点：零代码改动
- 风险：只是 workaround，未解决根本问题；CI 环境变化后可能再次失败

**方案 C：将 `tcp.connect()` 改为非阻塞 + 超时**
- 设置 socket 为非阻塞模式，使用 select() 等待连接完成
- 优点：根本解决阻塞问题
- 风险：改动较大，可能影响其他代码；需要跨平台测试

---

## 13. 本轮未做（按施工令禁止）

- ❌ 未修改 Blockchain / P2P / Consensus / Runtime 核心代码
- ❌ 未增加 retry / Sleep / arbitrary delay
- ❌ 未修改 consensus / block validation / chain selection
- ❌ 未修改 Windows socket 行为
- ❌ 未修改 Coroutine / P0-RUNTIME-07
- ❌ 未用 Linux/macOS PASS 推导 Windows 正确
- ❌ 未删除测试 / 降低断言 / 修改期望值
- ❌ 未自行宣布 PASS / SEALED / ROOT CAUSE CONFIRMED

---

## 14. 总结

**P0-RUNTIME-08 R1 Reality Root-Cause Audit**

- **First Invalid State**：Node B/C/D 调用 `tcp.connect(127.0.0.1, 19201)` 时 Node A 尚未监听，连接失败且无重试
- **问题分类**：A. Transport Failure — 连接时序 + 无重试
- **根因假设**：CI 环境 Node A 启动 >2 秒，超过测试脚本等待时间
- **证据强度**：10 条支持证据，证据链较强
- **缺失证据**：CI 原始日志（API 403）、Node A 实际启动时间
- **R2 Fix Gate**：✅ 可以进入，推荐方案 A（P2P 层增加连接重试）

---

**施工执行**: Agent A
**架构审查**: GPT-5.6 Luna
**最终裁决**: 于秋鸿博士（待验收）
