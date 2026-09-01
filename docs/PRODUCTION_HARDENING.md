# P0-15.18.7 Production Hardening Report

## 概述

本文档记录 TLL OS 在生产环境部署前需要关注的加固项、已知限制和改进建议。

## 一、已验证能力

### Runtime
- [x] TLL Compiler 自举编译
- [x] TLL VM 执行
- [x] Coroutine 创建/调度/yield/sleep
- [x] 100K Coroutine Stress（三平台 CI）
- [x] TCP Socket 监听/连接/收发
- [x] TCP/FD Boundary（65+ real fds，MSVC/Linux/macOS）
- [x] IO-aware Scheduler
- [x] Channel
- [x] Timer

### Compiler / Language
- [x] 变量作用域正确性（全局/局部/参数/嵌套/闭包/coroutine）
- [x] 10 组 Scope Semantics 测试，95 断言硬门禁
- [x] 函数/闭包/递归
- [x] Struct / Array / Map
- [x] JSON 序列化/反序列化
- [x] SHA-256 / HMAC
- [x] Module / Package / Import

### P2P / Blockchain
- [x] 4 Node 真实 TCP 网络
- [x] 5 Block 连续同步
- [x] Auto Sync on Connect
- [x] Disconnect / Reconnect
- [x] Invalid Block Rejection
- [x] Fork Detection
- [x] 120 Tx High-Message Stress
- [x] Mempool Capacity=50 溢出/驱逐
- [x] Transaction Deduplication
- [x] PoW Mining
- [x] Merkle Root
- [x] Chain Validation

### Fault Injection（5 项，三平台 CI）
- [x] fi_duptx：重复交易风暴（100x broadcast）
- [x] fi_dupblock：重复 Block 风暴（100x broadcast）
- [x] fi_ooo：乱序 Block 交付
- [x] fi_kill9：Kill-9 节点故障 + 重启 + 自动同步
- [x] fi_multi：多节点连续故障

## 二、已知限制（NOT READY for Production）

### 1. 密码学签名
- **状态**：SIMULATED
- **说明**：当前 `signTransaction()` 使用 HMAC-SHA256(publicKey, message)，不是真实的非对称加密签名
- **影响**：不能防止交易伪造，不能证明交易发送者身份
- **计划**：未来阶段引入 Ed25519 / secp256k1
- **风险等级**：HIGH

### 2. 共识机制
- **状态**：PARTIAL
- **说明**：当前只有最长链规则的基础实现，没有完整的共识算法
- **缺失**：
  - Chain Reorg（链重组）
  - Heaviest/Best Chain Selection（最重链选择）
  - Orphan Block Pool（孤块池）
  - Fork Resolution（分叉解决）
  - 难度调整
- **影响**：网络出现分叉时无法自动恢复一致
- **风险等级**：HIGH

### 3. 账户状态 / Nonce
- **状态**：PARTIAL
- **说明**：Mempool 有 nonce 查询，但没有完整的账户状态管理
- **缺失**：
  - 账户余额状态
  - Nonce 连续性验证
  - 双花检测（基于账户状态）
  - Block 执行后状态更新
- **影响**：不能防止双花，不能验证交易发送者有足够余额
- **风险等级**：HIGH

### 4. TCP 并发连接限制
- **状态**：DESIGN LIMIT
- **说明**：`tcp.select()` 使用 `select()` API，`FD_SETSIZE=64`
- **行为**：超过 64 个 fd 的连接被静默忽略（不会崩溃，但不会收到事件通知）
- **影响**：单节点最多支持约 60 个并发连接
- **计划**：未来迁移到 `epoll`（Linux）/ `kqueue`（macOS）/ `IOCP`（Windows）
- **风险等级**：MEDIUM

### 5. Windows TCC 构建
- **状态**：UNVERIFIED
- **说明**：TCC 的 `stddef.h` 在 CI 环境中编译失败（编译器内置宏未定义）
- **当前状态**：CI 使用 MSVC `cl` 编译 Windows Runtime
- **影响**：TCC 编译的 Runtime 未经过 CI 验证
- **风险等级**：LOW（不影响 MSVC 构建）

### 6. 持久化
- **状态**：MISSING
- **说明**：Blockchain 状态完全在内存中，节点重启后从 Genesis 开始
- **影响**：节点重启后需要重新同步整个链，不能持久化状态
- **计划**：未来引入 LevelDB / RocksDB / 文件持久化
- **风险等级**：MEDIUM

### 7. 自动重连
- **状态**：PARTIAL
- **说明**：有 `p2pReconnect()` API，但没有后台自动重连机制
- **行为**：节点断线后需要外部触发重连，不会自动重连
- **影响**：网络临时故障后节点不会自动恢复连接
- **风险等级**：MEDIUM

### 8. 消息协议版本化
- **状态**：MISSING
- **说明**：P2P 消息协议没有版本号，不支持协议协商
- **影响**：不同版本节点之间可能不兼容
- **风险等级**：LOW

## 三、生产加固建议

### 3.1 错误处理加固
- [ ] P2P 连接失败时的重试策略
- [ ] JSON 解析失败时的错误恢复
- [ ] Coroutine 异常捕获和隔离
- [ ] TCP 发送失败时的连接清理

### 3.2 资源清理保证
- [ ] 确保所有 TCP socket 在节点停止时关闭
- [ ] 确保所有 Coroutine 在节点停止时取消
- [ ] 确保 Mempool 交易过期后被清理
- [ ] 确保 Peer 断开后相关资源被释放

### 3.3 边界条件处理
- [ ] 空交易列表的 Merkle Root 计算
- [ ] 超大消息的 framing 处理
- [ ] 非法端口号的验证
- [ ] 负数/溢出数值的验证

### 3.4 可观测性
- [ ] 结构化日志（JSON 格式）
- [ ] 节点状态指标（height/tip/mempool size/peer count）
- [ ] P2P 消息统计（发送/接收/失败）
- [ ] Runtime 指标（coroutine count/fd count/memory usage）

### 3.5 配置化
- [ ] 节点配置文件（端口/peer list/difficulty）
- [ ] Mempool 容量可配置
- [ ] 连接超时可配置
- [ ] 日志级别可配置

## 四、性能基准（本地 Windows MSVC）

| 指标 | 数值 | 备注 |
|------|------|------|
| Coroutine 创建 | 95.4 us/个 | 10000 个 |
| Coroutine Yield | 2.19 us/次 | 100000 次 |
| Sleep 调度 | 0.111 ms/个 | 1000 个 sleep(50ms) |
| JSON 简单对象 | 5 us/次 | 1000 次 round-trip |
| JSON 嵌套对象 | 10 us/次 | 100 次 round-trip |
| JSON 大数组 | 420 us/次 | 100 次（100 元素） |
| Transaction 创建+签名 | 2.6 ms/个 | 1000 个（HMAC-SHA256） |
| Merkle Root | 0.01 ms/个 | 100 个（10 tx） |
| Block Hash | 0.001 ms/个 | 1000 个 |
| Full Mining | 143 ms/块 | 10 块（5 tx，diff=1） |

## 五、Production Readiness 判定

| 维度 | 状态 | 说明 |
|------|------|------|
| Runtime 稳定性 | ✅ READY | 100K coroutine + 故障注入验证 |
| 网络稳定性 | ✅ READY | 4 Node + disconnect/reconnect 验证 |
| 区块链功能 | ⚠️ PARTIAL | 基础功能完整，但缺共识/账户状态 |
| 密码学安全 | ❌ NOT READY | HMAC 模拟签名，非真实加密 |
| 持久化 | ❌ NOT READY | 纯内存，节点重启丢失状态 |
| 可观测性 | ⚠️ PARTIAL | 有基本日志，缺结构化指标 |
| 配置化 | ❌ NOT READY | 硬编码参数 |

**总体判定：NOT READY for Production**

TLL OS 当前适合作为：
- 编程语言/Runtime 能力验证
- 区块链技术原型
- Agent 开发框架实验
- 教育和研究用途

不适合作为：
- 生产级区块链节点
- 金融交易系统
- 高并发生产服务

## 六、后续路线

### P0-15.19：密码学增强
- Ed25519 签名
- 公钥/地址体系
- 交易签名验证

### P0-15.20：账户状态与共识
- 账户状态树
- Nonce 连续性
- 双花检测
- 最长链选择
- Chain Reorg

### P0-15.21：持久化与运维
- LevelDB 持久化
- 节点配置文件
- 结构化日志
- 指标导出

### P0-15.22：生产级网络
- epoll/kqueue/IOCP
- 自动重连
- 消息协议版本化
- 节点发现
