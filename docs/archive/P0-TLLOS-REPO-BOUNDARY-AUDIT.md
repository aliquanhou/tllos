# P0-TLLOS-REPO-BOUNDARY-AUDIT
## TLL OS 主仓商城代码彻底清理审计

**施工令**: P0-TLLOS-REPO-BOUNDARY-PURGE-FINAL
**审计时间**: 2026-09-06
**审计分支**: feature/P0-tll-language-fundamentals
**审计 HEAD**: 43a8237

---

## 一、架构决定

从本施工令开始，正式执行以下仓库边界：

- **aliquanhou/tllos** = TLL OS 核心底座
- **aliquanhou/tll-shop** = TLL OS 第一商业 Dogfooding 商城

两者不得混淆。tllos 不再保留任何商城项目代码。

---

## 二、审计方法

搜索关键词：
`mall`, `shop`, `commerce`, `product`, `products`, `cart`, `checkout`, `order`, `payment`, `invoice`, `coupon`, `marketing`, `user center`, `user_center`, `admin`, `SKU`, `inventory`, `商城`, `购物车`, `订单`, `支付`, `商品`

分类标准：
- **A. TLL OS 核心能力** - KEEP
- **B. TLL OS 测试/示例** - KEEP
- **C. 明确商城业务代码** - DELETE
- **D. 商城专用文档/CI/部署** - DELETE
- **E. 不确定** - UNKNOWN (STOP，不允许自行删除)

---

## 三、审计结果清单

### 3.1 明确商城业务代码（C - DELETE）

| 路径 | 类型 | 文件数 | 大小 | 判断 | 处理 |
|------|------|--------|------|------|------|
| `mall/` | 商城源码 | 50 | 0.6 MB | 完整商城实现，含 core/ 模块（database, router, session, auth, payment, marketing, invoice, icp, agreement, admin, search, schema 等） | DELETE |
| `shop/` | 商城源码 | 15 | 0.04 MB | 完整商城实现（cart, product, user, session, storage, templates 等） | DELETE |

### 3.2 商城专用部署配置（D - DELETE）

| 路径 | 类型 | 文件数 | 判断 | 处理 |
|------|------|--------|------|------|
| `deploy/` | 商城部署 | 12 | 含 shop.tllos.com.conf、deploy-shop.sh、tll-shop.service、商城部署文档等 | DELETE |
| `nginx-1.24.0/` | 商城专用 Nginx | 34 | 4.6 MB，完整 Nginx 安装目录，商城专用 | DELETE |

### 3.3 商城专用 CI（D - DELETE）

| 路径 | 类型 | 判断 | 处理 |
|------|------|------|------|
| `.github/workflows/product-dogfood.yml` | 商城 CI | Product Vertical Slice 测试，商城专用 | DELETE |

### 3.4 商城专用文档（D - DELETE）

| 路径 | 类型 | 判断 | 处理 |
|------|------|------|------|
| `docs/FUDUODUO_CAPABILITY_MATRIX.md` | 商城文档 | 福多多商城能力矩阵 | DELETE |
| `docs/FUDUODUO_REFERENCE_MALL_SPEC.md` | 商城文档 | 福多多参考商城规范 | DELETE |
| `docs/language/TLL-COMMERCE-MINIMUM-COMPILER-SET.md` | 商城文档 | 商城最小编译器集审计 | DELETE |
| `docs/language/TLL-COMMERCE-VERTICAL-SLICE-AUDIT.md` | 商城文档 | 商城垂直切片审计 | DELETE |

### 3.5 根目录商城脚本和文件（C/D - DELETE）

| 路径 | 类型 | 判断 | 处理 |
|------|------|------|------|
| `setup_mall.sh` | 商城脚本 | 商城安装脚本 | DELETE |
| `setup_systemd.sh` | 商城脚本 | systemd 安装脚本（商城专用） | DELETE |
| `start_mall.bat` | 商城脚本 | 商城启动脚本 | DELETE |
| `stop_mall.bat` | 商城脚本 | 商城停止脚本 | DELETE |
| `tllos-mall.service` | 商城配置 | 商城 systemd 服务 | DELETE |
| `import_1688_products.py` | 商城脚本 | 1688 商品导入脚本 | DELETE |
| `test_imported_products.py` | 商城脚本 | 导入商品测试脚本 | DELETE |
| `test_api.py` | 商城脚本 | API 测试脚本（商城专用） | DELETE |
| `test_*.db`, `test_*.db-shm`, `test_*.db-wal` | 商城数据库 | 商城测试数据库文件 | DELETE |
| `debug_*.tll`, `debug_*.tllbc` | 临时文件 | 调试文件 | DELETE |
| `fix_*.py`, `get_artifacts.py` | 临时脚本 | 临时调试脚本 | DELETE |
| `phase4_artifact.zip` | 临时文件 | 临时 artifact | DELETE |
| `debug_out.log` | 临时文件 | 调试日志 | DELETE |
| `test_output_relative.txt` | 临时文件 | 测试输出 | DELETE |

### 3.6 TLL OS 核心能力（A - KEEP）

| 路径 | 类型 | 判断 | 处理 |
|------|------|------|------|
| `compiler/` | TLL 编译器 | TLL OS 核心 | KEEP |
| `runtime/` | TLL Runtime | TLL OS 核心 | KEEP |
| `stdlib/` | TLL 标准库 | TLL OS 核心 | KEEP |
| `host/` | TLL Native Host | TLL OS 核心 | KEEP |
| `scripts/` | TLL 构建脚本 | bootstrap、build、test、abi 检查等 | KEEP |
| `tests/` | TLL 测试 | blockchain、coroutine、crypto、closure、ternary 等核心测试 | KEEP |
| `examples/` | TLL 示例 | blockchain、closure、hello 等核心示例 | KEEP |
| `docs/architecture/` | TLL 架构文档 | TLL OS 核心架构 | KEEP |
| `docs/development/` | TLL 开发文档 | TLL OS 开发指南 | KEEP |
| `docs/getting-started/` | TLL 入门文档 | TLL OS 入门指南 | KEEP |
| `docs/language/TLL-LANGUAGE-*` | TLL 语言文档 | TLL 语言基础能力审计（非商城） | KEEP |
| `docs/P0-*`, `docs/P1-*` | TLL 工程文档 | TLL OS 工程审计报告 | KEEP |
| `docs/TLL-*` | TLL 能力文档 | TLL OS 能力矩阵 | KEEP |
| `audit/` | TLL 审计脚本 | Exact Count 校验等 | KEEP |
| `phase4/` | TLL Phase 4 证据 | Phase 4 Evidence Validator | KEEP |
| `benchmarks/` | TLL 基准测试 | TLL OS 性能基准 | KEEP |
| `spec/` | TLL 规范 | TLL OS 规范 | KEEP |
| `tools/` | TLL 工具 | TLL OS 工具 | KEEP |
| `.tll-engine/` | TLL 引擎 | TLL OS 引擎 | KEEP |

### 3.7 不确定（E - UNKNOWN）

| 路径 | 类型 | 判断 | 处理 |
|------|------|------|------|
| `package/package.tll` | 包管理 | 需要检查内容是否为商城相关 | UNKNOWN - 需进一步检查 |
| 根目录 `README.md` | 项目文档 | 需要检查是否有商城引用 | UNKNOWN - 需进一步检查 |
| 根目录 `ARCHITECTURE.md` | 架构文档 | 需要检查是否有商城引用 | UNKNOWN - 需进一步检查 |
| 根目录 `AGENT.md` | Agent 指南 | 需要检查是否有商城引用 | UNKNOWN - 需进一步检查 |
| `.github/workflows/ci.yml` | 主 CI | 需要检查是否有商城引用 | UNKNOWN - 需进一步检查 |
| `.github/workflows/release.yml` | Release CI | 需要检查是否有商城引用 | UNKNOWN - 需进一步检查 |
| `.github/workflows/p1-crypto-tests.yml` | 加密测试 CI | 应该是 TLL OS 核心 | KEEP（初步判断） |
| 根目录 `P0-15.17-REPORT.md`, `P0-15.17.1-REPORT.md` | 工程报告 | 需要检查是否为商城相关 | UNKNOWN - 需进一步检查 |

---

## 四、下一步

1. 检查 3.7 中的 UNKNOWN 项，确认是否为商城相关
2. 确认后删除所有明确属于商城的内容
3. 全仓库引用审计，确保没有残留商城路径引用
4. CI 清理，确保 TLL OS CI 不再依赖商城代码
5. 验证 TLL OS 本身没有被破坏（编译、测试、Bootstrap、CI）
6. 提交并推送

---

## 五、审计原则

- **Audit first** - 先审计，不立即删除
- **Delete only confirmed mall** - 只删除明确属于商城的内容
- **UNKNOWN = STOP** - 不确定就停，不猜，不误删，不扩 scope
- **禁止借机修改 TLL** - 本施工令只处理 Repository Boundary / Mall Purge，严禁重构 Compiler、Parser、TypeChecker、VM、Runtime、Stdlib、Crypto、Agent Foundation
- **禁止"搬回来"** - 不要把任何商城代码重新复制、迁移、同步回 tllos
