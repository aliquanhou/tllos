# TLL Mall - 商业交付级 B2C 商城系统

基于 TLL 高帧率编程语言开发的完整 B2C 电商商城系统，包含前台商城和后台管理。

## 项目概述

TLL Mall 是一个完全使用 TLL 语言实现的商业级电商系统，作为 TLL 语言的 Dogfooding 项目，验证了 TLL 在 Web 开发、数据库操作、并发处理等场景下的能力。

### 核心特性

- **全 TLL 实现**：所有核心业务逻辑均使用 TLL 语言，无其他语言偷渡
- **完整商业闭环**：注册→登录→浏览→SKU→加购→结算→下单→扣库存→订单查询→后台管理
- **数据持久化**：SQLite 数据库，重启后数据不丢失
- **多用户并发**：8 线程 Worker Pool，多用户数据隔离
- **RBAC 权限**：用户/管理员角色分离
- **后台管理**：仪表盘、商品、订单、用户、分类管理

## 架构说明

```
mall/
├── main.tll              # 商城入口（前台路由 + 业务逻辑）
├── core/
│   ├── database.tll      # 数据库封装（连接/查询/事务/迁移）
│   ├── router.tll        # Web 框架（路由/中间件/响应/请求）
│   ├── session.tll       # Session/Cookie/缓存/密码哈希
│   ├── auth.tll          # 认证/权限（注册/登录/RBAC）
│   ├── schema.tll        # 数据库 Schema（20 张表 + 种子数据）
│   └── admin.tll         # 后台管理（仪表盘/商品/订单/用户/分类）
├── data/
│   └── mall.db           # SQLite 数据库文件（运行时生成）
├── start.bat             # 启动脚本
├── backup.bat            # 数据库备份脚本
├── restore.bat           # 数据库恢复脚本
└── README.md             # 本文档
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | TLL (tllvm + tllc) |
| 数据库 | SQLite 3.46.1 (C 绑定) |
| Web 服务器 | TLL 内置 HTTP Server (8 线程 Worker Pool) |
| 模板 | 服务端 HTML 字符串拼接 |
| 会话 | 内存 Session + Cookie |

## 快速开始

### 前置要求

- Windows 10/11
- MSVC 编译环境（Visual Studio Build Tools 2022）
- TLL VM 已编译（`host/c/tllvm.exe`）
- TLL 编译器已引导（`tools/TLLC/tllc.tllbc`）

### 编译商城

```bash
cd mall
..\host\c\tllvm.exe ..\tools\TLLC\tllc.tllbc compile main.tll -o main.tllbc
```

### 启动商城

```bash
# 使用启动脚本（自动编译）
start.bat

# 或手动启动
..\host\c\tllvm.exe main.tllbc
```

服务器启动后监听 `http://0.0.0.0:8090`

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | （自行注册） | （自行设置） |

## 功能模块

### 前台商城

| 模块 | 路由 | 说明 |
|------|------|------|
| 首页 | GET / | 商品列表、Banner、分类导航 |
| 分类 | GET /category | 分类列表 |
| 分类商品 | GET /category/:id | 指定分类下的商品 |
| 商品详情 | GET /product/:id | 商品信息、SKU 选择 |
| 购物车 | GET /cart | 购物车列表 |
| 加入购物车 | POST /cart/add | 添加商品到购物车 |
| 更新购物车 | POST /cart/update | 修改数量 |
| 删除购物车 | POST /cart/remove | 删除商品 |
| 结算 | GET /checkout | 订单确认页 |
| 创建订单 | POST /order/create | 提交订单（事务扣库存） |
| 订单列表 | GET /orders | 我的订单 |
| 订单详情 | GET /order/:id | 订单详情 |
| 模拟支付 | POST /order/pay | 支付订单 |
| 登录 | GET/POST /login | 用户登录 |
| 注册 | GET/POST /register | 用户注册 |
| 登出 | GET /logout | 退出登录 |
| 用户中心 | GET /user | 个人中心 |
| 地址管理 | GET /user/address | 收货地址列表 |
| 添加地址 | POST /user/address/add | 添加收货地址 |
| 删除地址 | POST /user/address/delete | 删除收货地址 |

### 后台管理

| 模块 | 路由 | 说明 |
|------|------|------|
| 仪表盘 | GET /admin | 统计数据、最近订单 |
| 商品管理 | GET /admin/products | 商品列表 |
| 添加商品 | GET/POST /admin/product/add | 添加商品 |
| 编辑商品 | GET /admin/product/edit/:id | 编辑商品 |
| 删除商品 | GET /admin/product/delete/:id | 删除商品 |
| 订单管理 | GET /admin/orders | 订单列表 |
| 订单详情 | GET /admin/order/:id | 订单详情 |
| 订单发货 | GET /admin/order/ship/:id | 标记发货 |
| 用户管理 | GET /admin/users | 用户列表 |
| 分类管理 | GET /admin/categories | 分类列表 |

## 数据库 Schema

共 20 张表：

1. **users** - 用户表
2. **user_addresses** - 用户收货地址
3. **categories** - 商品分类
4. **brands** - 品牌
5. **products** - 商品
6. **product_skus** - 商品 SKU
7. **product_images** - 商品图片
8. **cart_items** - 购物车
9. **orders** - 订单
10. **order_items** - 订单项
11. **after_sales** - 售后
12. **coupons** - 优惠券
13. **user_coupons** - 用户优惠券
14. **banners** - Banner
15. **system_configs** - 系统配置
16. **admin_logs** - 管理员日志
17. **product_specs** - 商品规格
18. **product_spec_values** - 规格值
19. **order_logs** - 订单操作日志
20. **payments** - 支付记录

## 部署说明

### 生产环境部署

1. 编译 TLL VM（含 SQLite 绑定）
2. 引导 TLL 编译器
3. 编译商城字节码
4. 使用 `start.bat` 启动
5. 配置 Nginx 反向代理（可选）
6. 设置定时任务执行 `backup.bat`

### 环境变量

无特殊环境变量要求。数据库文件默认存储在 `mall/data/mall.db`。

### 端口配置

默认端口 8090，可通过 `start.bat [port]` 修改。

## 备份与恢复

### 备份

```bash
# 备份到默认目录（mall/backups/）
backup.bat

# 备份到指定目录
backup.bat D:\backups\tllmall
```

自动保留最近 10 份备份。

### 恢复

```bash
restore.bat backups\mall_20260904_120000.db
```

恢复前会自动备份当前数据库为 `mall.db.bak`。

## TLL 语言限制与 Workaround

在开发过程中发现的 TLL 语言限制及解决方案：

| 限制 | 影响 | Workaround |
|------|------|------------|
| 不支持三元运算符 `? :` | 条件表达式 | 使用 if/else 赋值 |
| 字符串拼接中不能插 let | 内联变量声明 | 变量声明移到拼接前 |
| `process.pid()` Windows 返回 -1 | 唯一 ID 生成 | 使用计数器 |
| 闭包捕获变量多线程下被清空 | Router 崩溃 | 使用全局变量 + 全局函数 |
| 编译器对未定义标识符只警告 | 运行时崩溃 | 代码审查确保所有标识符已定义 |
| PowerShell UTF8 BOM 导致词法错误 | 编译失败 | 使用 .NET UTF8Encoding(false) 保存 |
| import 路径不能带 .tll 扩展名 | 模块加载失败 | 使用不带扩展名的路径 |

### 关键 Bug 修复记录

1. **SQLite 多线程互斥锁**：在 `sqlite_builtin.c` 中添加全局 CRITICAL_SECTION，确保 SQLite 操作线程安全
2. **Router 多线程崩溃**：根因是 TLL 闭包捕获变量在 Worker Pool 多线程环境下被清空，解决方案是使用全局变量和全局函数

## 交付门验证状态

| 级别 | 项目 | 状态 |
|------|------|------|
| P0 | 语言正确性 | ✅ |
| P1 | Runtime 正确性 | ✅ |
| P2 | HTTP/Web Framework | ✅ |
| P3 | 数据库与事务 | ✅ |
| P4 | Session/Auth | ✅ |
| P5 | 商品/SKU/库存 | ✅ |
| P6 | Cart | ✅ |
| P7 | Order | ✅ |
| P8 | 后台管理 | ✅ |
| P9 | 安全/权限 | ✅ |
| P10 | 并发/压力 | ✅ (8 线程 Worker Pool) |
| P11 | 数据持久化 | ✅ (重启验证通过) |
| P12 | 部署/备份/恢复 | ✅ (脚本已提供) |
| P13 | CI/CD | ⏳ (待配置) |
| P14 | 完整商业流程 | ✅ (端到端验证通过) |
| P15 | 交付文档 | ✅ (本文档) |

## 完整商业流程验证

已验证的端到端流程：

1. ✅ 用户注册
2. ✅ 用户登录
3. ✅ 浏览商品（首页/分类/搜索）
4. ✅ 查看商品详情 + SKU 选择
5. ✅ 加入购物车
6. ✅ 修改购物车数量
7. ✅ 结算（选择地址）
8. ✅ 创建订单（事务扣库存）
9. ✅ 查询订单列表/详情
10. ✅ 模拟支付
11. ✅ 后台管理（仪表盘/商品/订单/用户）
12. ✅ 重启服务器后数据仍然存在
13. ✅ 多用户数据隔离

## 后续扩展方向

- MySQL/MariaDB 数据库支持（当前 SQLite）
- Redis 缓存层
- 文件上传/图片管理
- 营销模块（优惠券、满减、秒杀）
- 售后完整流程
- 数据统计报表
- WebSocket 实时通知
- 移动端适配
- 支付接口集成（支付宝/微信）

## 许可证

TLL Mall 是 TLL OS 项目的一部分，遵循 TLL OS 的开源协议。

## 联系方式

- 项目仓库：https://github.com/aliquanhou/tllos
- 官网：https://tllos.com/
