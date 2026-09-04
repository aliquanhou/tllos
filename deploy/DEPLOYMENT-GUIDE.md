# TLLOS 商城部署到 tllos.com 完整指南

## 概述

将 TLLOS 商城部署到官方网站 `tllos.com`，通过 `tllos.com/shop` 路径访问商城全部功能。

**架构图：**
```
用户浏览器
    │
    ▼
tllos.com (Nginx :80/:443)
    ├── /          → 官网静态页面 (/var/www/tllos.com/)
    ├── /docs      → 文档静态页面
    └── /shop/*    → 反向代理 → 127.0.0.1:8090 (TLL 商城服务器)
                           │
                           ▼
                    TLL VM + SQLite
                    (mall/data/mall.db)
```

---

## 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+ | Ubuntu 22.04 LTS |
| CPU | 1 核 | 2 核以上 |
| 内存 | 512 MB | 2 GB 以上 |
| 磁盘 | 1 GB | 10 GB 以上（含数据库和备份） |
| 软件 | Nginx 1.18+ | Nginx 1.24+ |
| 端口 | 80, 443, 8090（内部） | 80, 443 |

---

## 部署步骤

### 第一步：上传商城文件到服务器

```bash
# 在服务器上创建目录
sudo mkdir -p /var/www/tllos.com/shop
sudo mkdir -p /var/www/tllos.com/shop/data

# 上传商城文件（从本地 deploy/shop/ 目录）
# 方式一：scp
scp -r deploy/shop/* user@tllos.com:/var/www/tllos.com/shop/

# 方式二：rsync
rsync -avz deploy/shop/ user@tllos.com:/var/www/tllos.com/shop/

# 设置权限
sudo chown -R www-data:www-data /var/www/tllos.com/shop
sudo chmod -R 755 /var/www/tllos.com/shop
sudo chmod -R 775 /var/www/tllos.com/shop/data
```

**商城文件清单：**
```
/var/www/tllos.com/shop/
├── tllvm.exe          # TLL 虚拟机（Linux 版本需重新编译）
├── main.tllbc         # 商城编译产物
├── start.bat          # Windows 启动脚本
├── start.sh           # Linux 启动脚本（需创建）
├── backup.bat         # 备份脚本
├── restore.bat        # 恢复脚本
├── tll-shop.service   # Systemd 服务配置
└── data/
    └── mall.db        # SQLite 数据库（首次运行自动创建）
```

### 第二步：编译 Linux 版本的 TLL 虚拟机

如果服务器是 Linux，需要重新编译 `tllvm`：

```bash
# 安装编译工具
sudo apt update
sudo apt install -y gcc make

# 从 GitHub 克隆源码
git clone https://github.com/aliquanhou/tllos.git
cd tllos/host/c

# 编译（含 SQLite 支持）
gcc -O2 -std=c99 -D_POSIX_C_SOURCE=200809L -DSQLITE_THREADSAFE=1 \
    -o tllvm main.c vm.c value.c json.c builtin.c sqlite_builtin.c sqlite3.c \
    -lm -lpthread

# 复制到商城目录
sudo cp tllvm /var/www/tllos.com/shop/
sudo chmod +x /var/www/tllos.com/shop/tllvm
```

### 第三步：创建 Linux 启动脚本

```bash
sudo tee /var/www/tllos.com/shop/start.sh << 'EOF'
#!/bin/bash
# TLLOS 商城启动脚本

cd /var/www/tllos.com/shop

# 检查是否已运行
if pgrep -f "tllvm main.tllbc" > /dev/null; then
    echo "商城服务器已在运行"
    exit 0
fi

# 启动商城
nohup ./tllvm main.tllbc > /var/log/tll-shop.log 2>&1 &
echo $! > /var/run/tll-shop.pid
echo "商城服务器已启动，PID: $(cat /var/run/tll-shop.pid)"
echo "访问地址: http://127.0.0.1:8090"
EOF

sudo chmod +x /var/www/tllos.com/shop/start.sh
```

### 第四步：配置 Systemd 服务（推荐）

```bash
# 复制服务文件
sudo cp /var/www/tllos.com/shop/tll-shop.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start tll-shop

# 设置开机自启动
sudo systemctl enable tll-shop

# 查看状态
sudo systemctl status tll-shop
```

### 第五步：配置 Nginx 反向代理

```bash
# 复制 Nginx 配置
sudo cp deploy/nginx/tllos.com.conf /etc/nginx/sites-available/tllos.com

# 创建软链接
sudo ln -s /etc/nginx/sites-available/tllos.com /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

**Nginx 配置要点：**
- `location /shop/` 将 `/shop/` 开头的请求转发到 `127.0.0.1:8090`
- `rewrite ^/shop/(.*)$ /$1 break;` 移除 `/shop` 前缀
- 设置 `X-Forwarded-*` 头，让商城知道真实的客户端 IP 和协议
- 静态资源缓存 30 天
- 启用 Gzip 压缩

### 第六步：修改官网顶部导航栏

1. 找到官网的导航栏文件（通常是 `header.html`、`nav.html` 或 `index.html`）
2. 在导航菜单中添加 "Shop" 链接：

```html
<!-- 简单文本链接 -->
<li><a href="/shop">商城</a></li>

<!-- 或者带样式的按钮 -->
<a href="/shop" class="nav-shop-btn">商城</a>
```

3. 参考 `deploy/website/navbar-shop-integration.html` 中的三种方案
4. 添加配套的 CSS 样式

### 第七步：配置 SSL/HTTPS（推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d tllos.com -d www.tllos.com

# 自动续期（Certbot 会自动配置）
sudo certbot renew --dry-run
```

---

## 验证测试

### 1. 商城服务器测试

```bash
# 测试商城服务器是否运行
curl http://127.0.0.1:8090/

# 测试登录 API
curl -X POST http://127.0.0.1:8090/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 2. Nginx 反向代理测试

```bash
# 测试通过域名访问商城
curl http://tllos.com/shop/

# 测试商城 API
curl -X POST http://tllos.com/shop/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 3. 浏览器访问测试

| 测试项 | URL | 预期结果 |
|--------|-----|---------|
| 商城首页 | https://tllos.com/shop/ | 显示商城首页，商品列表 |
| 商品列表 | https://tllos.com/shop/products | 显示所有商品 |
| 商品详情 | https://tllos.com/shop/product/1 | 显示商品详情和 SKU |
| 购物车 | https://tllos.com/shop/cart | 显示购物车 |
| 登录 | https://tllos.com/shop/login | 登录页面 |
| 管理后台 | https://tllos.com/shop/admin | 后台登录页面 |
| 官网首页 | https://tllos.com/ | 官网正常显示 |
| 导航栏 | 任意页面 | 顶部有 "商城" 链接 |

### 4. 功能完整测试

```
注册 → 登录 → 浏览商品 → 查看 SKU → 加入购物车 → 修改数量
→ 结算 → 创建订单 → 扣库存 → 查询订单 → 后台管理
→ 重启服务器 → 数据仍然存在
```

---

## 默认账号

| 角色 | 用户名 | 密码 | 访问地址 |
|------|--------|------|---------|
| 管理员 | admin | admin123 | https://tllos.com/shop/admin |
| 测试用户 | testuser | test123 | https://tllos.com/shop/login |

**⚠️ 安全提醒：** 上线前务必修改默认密码！

---

## 维护和备份

### 数据库备份

```bash
# 手动备份
sqlite3 /var/www/tllos.com/shop/data/mall.db ".backup /backup/mall-$(date +%Y%m%d).db"

# 自动备份（添加到 crontab）
# 每天凌晨 3 点备份
0 3 * * * sqlite3 /var/www/tllos.com/shop/data/mall.db ".backup /backup/mall-$(date +\%Y\%m\%d).db"

# 保留最近 30 天的备份
0 4 * * * find /backup -name "mall-*.db" -mtime +30 -delete
```

### 日志查看

```bash
# 查看商城日志
sudo journalctl -u tll-shop -f

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 服务管理

```bash
# 重启商城
sudo systemctl restart tll-shop

# 停止商城
sudo systemctl stop tll-shop

# 查看状态
sudo systemctl status tll-shop
```

---

## 故障排查

### 问题 1：访问 tllos.com/shop 显示 502 Bad Gateway

**原因：** 商城服务器没有运行或端口不对。

**解决：**
```bash
# 检查商城进程
ps aux | grep tllvm

# 检查端口
netstat -tlnp | grep 8090

# 重启服务
sudo systemctl restart tll-shop

# 查看日志
sudo journalctl -u tll-shop -n 50
```

### 问题 2：商城页面样式错乱

**原因：** Nginx 反向代理没有正确转发静态资源。

**解决：** 检查 Nginx 配置中的 `location /shop/` 是否正确，确保 `rewrite` 规则移除了 `/shop` 前缀。

### 问题 3：登录后 Session 丢失

**原因：** Cookie 路径问题。

**解决：** 确保商城设置的 Cookie 路径为 `/`，或者在 Nginx 中配置 `proxy_cookie_path`：
```nginx
proxy_cookie_path / /shop;
```

### 问题 4：数据库锁定（SQLite database is locked）

**原因：** 并发写入冲突。

**解决：**
- 确保 SQLite 开启了 WAL 模式
- 检查是否有多个进程同时写入数据库
- 考虑升级到 MySQL/MariaDB（高并发场景）

### 问题 5：内存占用过高

**原因：** TLL VM 内存泄漏或请求堆积。

**解决：**
```bash
# 查看内存占用
ps aux --sort=-%mem | head -10

# 重启服务释放内存
sudo systemctl restart tll-shop

# 配置 Systemd 内存限制（已在 tll-shop.service 中设置）
# MemoryMax=512M
```

---

## 性能优化

### 1. 启用 SQLite WAL 模式

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

### 2. Nginx 缓存

```nginx
# 缓存商城静态页面（可选）
proxy_cache_path /var/cache/nginx/tll-shop levels=1:2 keys_zone=tll_shop:10m max_size=1g inactive=60m;

location /shop/ {
    proxy_cache tll_shop;
    proxy_cache_valid 200 5m;
    proxy_cache_key $scheme$request_method$host$request_uri;
    # ... 其余配置
}
```

### 3. 数据库索引优化

确保常用查询字段都有索引：
- `products(category_id, status)`
- `orders(user_id, status)`
- `order_items(order_id)`
- `users(username, email)`

---

## 安全加固

### 1. 修改默认密码

登录后台后立即修改 admin 密码。

### 2. 限制管理后台访问

```nginx
# 只允许特定 IP 访问管理后台
location /shop/admin {
    allow 192.168.1.0/24;  # 你的 IP 段
    deny all;
    # ... 反向代理配置
}
```

### 3. 启用 HTTPS

所有流量强制 HTTPS，配置 HSTS：
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 4. 定期更新

```bash
# 更新 TLL OS 源码
cd /opt/tllos
git pull

# 重新编译商城
./host/c/tllvm tools/TLLC/tllc.tllbc compile mall/main.tll -o mall/main.tllbc

# 复制到生产目录
cp mall/main.tllbc /var/www/tllos.com/shop/

# 重启服务
sudo systemctl restart tll-shop
```

---

## 部署文件清单

```
deploy/
├── shop/                          # 商城服务器文件
│   ├── tllvm.exe                  # TLL 虚拟机（Windows）
│   ├── main.tllbc                 # 商城编译产物
│   ├── start.bat                  # Windows 启动脚本
│   ├── start.sh                   # Linux 启动脚本（需创建）
│   ├── backup.bat                 # 备份脚本
│   ├── restore.bat                # 恢复脚本
│   ├── tll-shop.service           # Systemd 服务配置
│   └── data/                      # 数据库目录
│       └── mall.db                # SQLite 数据库
├── nginx/
│   └── tllos.com.conf             # Nginx 反向代理配置
└── website/
    └── navbar-shop-integration.html  # 官网导航栏修改示例
```

---

## 联系与支持

- GitHub: https://github.com/aliquanhou/tllos
- 官网: https://tllos.com
- 商城: https://tllos.com/shop

---

**部署完成后，请验证：**
- [ ] tllos.com/shop 能正常访问商城首页
- [ ] 官网顶部导航栏有 "商城" 链接
- [ ] 商城所有功能正常（商品/购物车/下单/后台）
- [ ] 数据持久化正常（重启服务器后数据不丢失）
- [ ] HTTPS 正常工作
- [ ] 默认密码已修改
