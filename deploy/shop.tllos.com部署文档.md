# TLLOS Mall - shop.tllos.com 部署文档

## 概述

TLLOS 商城已部署完成，使用 Nginx 作为反向代理，TLLOS 高帧率编程语言作为后端服务。

### 访问地址

| 环境 | 地址 | 说明 |
|------|------|------|
| 本地测试 | http://127.0.0.1:8090 | TLLOS 商城直接访问 |
| Nginx 代理 | http://127.0.0.1:80 | Nginx 反向代理 |
| 域名访问 | http://shop.tllos.com | 需配置 DNS 解析 |
| 管理后台 | http://shop.tllos.com/admin | 管理员登录 |

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

---

## 一、DNS 域名解析配置

### 1.1 添加 A 记录

在域名服务商（如阿里云、腾讯云、Cloudflare）的 DNS 管理面板中添加：

| 记录类型 | 主机记录 | 记录值 | TTL |
|----------|----------|--------|-----|
| A | shop | 1.161.48.32 | 600 |

> **注意**：将 `1.161.48.32` 替换为您服务器的实际公网 IP。

### 1.2 验证 DNS 解析

```bash
# Windows
nslookup shop.tllos.com

# Linux/Mac
dig shop.tllos.com
```

预期结果：返回服务器公网 IP 地址。

---

## 二、防火墙配置

### 2.1 Windows 防火墙

以管理员身份运行 PowerShell：

```powershell
# 允许 HTTP (80)
New-NetFirewallRule -DisplayName "TLLOS Mall HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow

# 允许 HTTPS (443)
New-NetFirewallRule -DisplayName "TLLOS Mall HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# 查看规则
Get-NetFirewallRule -DisplayName "TLLOS Mall*"
```

### 2.2 云服务器安全组

如果使用云服务器（阿里云、腾讯云、AWS 等），还需要在云控制台的安全组中开放：
- 80 端口（HTTP）
- 443 端口（HTTPS）

---

## 三、服务管理

### 3.1 启动服务

```batch
# 方式一：使用启动脚本（推荐）
start_mall.bat

# 方式二：手动启动
# 1. 启动 TLLOS 商城
cd C:\path\to\tllos
start /B host\c\tllvm.exe mall\main.tllbc

# 2. 启动 Nginx
cd nginx-1.24.0
start /B nginx.exe
```

### 3.2 停止服务

```batch
# 方式一：使用停止脚本（推荐）
stop_mall.bat

# 方式二：手动停止
# 停止 Nginx
cd nginx-1.24.0
nginx.exe -s stop

# 停止 TLLOS 商城
taskkill /F /IM tllvm.exe
```

### 3.3 重启服务

```batch
stop_mall.bat
timeout /t 3
start_mall.bat
```

### 3.4 查看服务状态

```powershell
# 查看 TLLOS 进程
Get-Process -Name tllvm

# 查看 Nginx 进程
Get-Process -Name nginx

# 查看端口监听
netstat -ano | findstr ":80 :443 :8090"
```

---

## 四、Nginx 配置说明

### 4.1 配置文件位置

```
nginx-1.24.0/
├── conf/
│   ├── nginx.conf          # 主配置文件
│   └── conf.d/
│       └── shop.tllos.com.conf  # 商城站点配置
├── logs/
│   ├── access.log           # 访问日志
│   ├── error.log            # 错误日志
│   ├── shop.tllos.com_access.log
│   └── shop.tllos.com_error.log
└── nginx.exe
```

### 4.2 核心配置

- **反向代理**：将所有请求转发到 `http://127.0.0.1:8090`
- **Gzip 压缩**：启用文本资源压缩
- **安全响应头**：X-Frame-Options、X-Content-Type-Options 等
- **静态资源缓存**：图片、CSS、JS 缓存 7 天
- **文件上传限制**：最大 50MB

### 4.3 重载配置

修改 Nginx 配置后，无需重启，使用重载：

```batch
cd nginx-1.24.0
nginx.exe -t          # 测试配置
nginx.exe -s reload   # 重载配置
```

---

## 五、SSL/HTTPS 配置（可选但推荐）

### 5.1 获取 SSL 证书

推荐使用免费的 Let's Encrypt 证书：

1. 下载 [Win-ACME](https://www.win-acme.com/)
2. 运行 `wacs.exe`
3. 选择 `M` (Create certificate)
4. 选择 `2` (Manual input)
5. 输入 `shop.tllos.com`
6. 选择验证方式（推荐 HTTP-01）
7. 证书生成后，记录证书路径

### 5.2 配置 Nginx SSL

编辑 `nginx-1.24.0/conf/conf.d/shop.tllos.com.conf`，取消 HTTPS server 块的注释：

```nginx
server {
    listen 443 ssl http2;
    server_name shop.tllos.com;

    ssl_certificate     cert/shop.tllos.com.crt;
    ssl_certificate_key cert/shop.tllos.com.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # ... 其他配置同 HTTP
}
```

同时启用 HTTP 到 HTTPS 的重定向：

```nginx
server {
    listen 80;
    server_name shop.tllos.com;
    return 301 https://$server_name$request_uri;
}
```

### 5.3 重载 Nginx

```batch
cd nginx-1.24.0
nginx.exe -t
nginx.exe -s reload
```

---

## 六、数据库管理

### 6.1 数据库位置

```
mall/data/mall.db
```

### 6.2 数据库备份

```batch
# 创建备份目录
mkdir mall\backup

# 备份数据库（使用 SQLite 命令行）
sqlite3 mall\data\mall.db ".backup mall\backup\mall_%date:~0,4%%date:~5,2%%date:~8,2%.db"

# 或者直接复制文件（需先停止服务）
stop_mall.bat
copy mall\data\mall.db mall\backup\mall_backup.db
start_mall.bat
```

### 6.3 自动备份（任务计划程序）

创建每日自动备份任务：

```powershell
# 创建备份脚本 backup_db.bat
@echo off
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "timestamp=%YYYY%%MM%%DD%"
copy "C:\path\to\tllos\mall\data\mall.db" "C:\path\to\tllos\mall\backup\mall_%timestamp%.db"

# 创建计划任务（每天凌晨 3 点执行）
schtasks /create /tn "TLLOS Mall DB Backup" /tr "C:\path\to\backup_db.bat" /sc daily /st 03:00
```

---

## 七、日志管理

### 7.1 日志位置

| 日志类型 | 位置 |
|----------|------|
| Nginx 访问日志 | `nginx-1.24.0/logs/shop.tllos.com_access.log` |
| Nginx 错误日志 | `nginx-1.24.0/logs/shop.tllos.com_error.log` |
| TLLOS 运行日志 | 控制台输出（如需文件可重定向） |

### 7.2 日志轮转

Nginx 日志会持续增长，建议定期清理或轮转：

```batch
# 清理 7 天前的日志
forfiles /p "nginx-1.24.0\logs" /s /m *.log /d -7 /c "cmd /c del @path"
```

---

## 八、性能优化

### 8.1 Nginx 性能

已启用的优化：
- Gzip 压缩
- 静态资源缓存（7 天）
- 代理缓冲
- HTTP/1.1 长连接

### 8.2 TLLOS 商城性能

- 8 线程 Worker Pool
- SQLite 数据库（带互斥锁）
- 全局数据库连接池

### 8.3 系统优化

```powershell
# 增加文件描述符限制（Windows 注册表）
# 建议服务器至少 2GB 内存，2 核 CPU
```

---

## 九、常见问题排查

### 9.1 无法访问网站

```powershell
# 1. 检查服务是否运行
Get-Process -Name tllvm, nginx

# 2. 检查端口是否监听
netstat -ano | findstr ":80 :8090"

# 3. 检查防火墙
Get-NetFirewallRule -DisplayName "*TLLOS*"

# 4. 查看 Nginx 错误日志
Get-Content nginx-1.24.0\logs\error.log -Tail 20
```

### 9.2 502 Bad Gateway

原因：TLLOS 商城未运行或端口错误。

```powershell
# 检查 TLLOS 是否运行
Get-Process -Name tllvm

# 检查 8090 端口
netstat -ano | findstr ":8090"

# 重启 TLLOS
taskkill /F /IM tllvm.exe
start /B host\c\tllvm.exe mall\main.tllbc
```

### 9.3 数据库锁定

原因：SQLite 数据库被其他进程占用。

```batch
# 停止所有服务
stop_mall.bat

# 等待 5 秒
timeout /t 5

# 重新启动
start_mall.bat
```

### 9.4 域名无法访问

```powershell
# 1. 检查 DNS 解析
nslookup shop.tllos.com

# 2. 检查 hosts 文件（本地测试）
type C:\Windows\System32\drivers\etc\hosts | findstr shop

# 3. 检查公网 IP
curl https://api.ipify.org
```

### 9.5 上传文件失败

检查 Nginx 配置中的 `client_max_body_size`，默认 50MB。

---

## 十、安全建议

### 10.1 修改默认密码

首次部署后，立即修改管理员密码：
- 登录后台 → 用户管理 → 修改密码

### 10.2 启用 HTTPS

配置 SSL 证书，启用 HTTPS，保护用户数据传输安全。

### 10.3 限制后台访问 IP

在 Nginx 配置中添加：

```nginx
location /admin {
    allow 192.168.1.0/24;  # 允许的 IP 段
    allow 您的公网IP;
    deny all;
    proxy_pass http://127.0.0.1:8090;
}
```

### 10.4 定期备份

- 数据库每日备份
- 备份文件保留 30 天
- 定期测试备份恢复

---

## 十一、部署清单

- [x] TLLOS 商城编译完成
- [x] Nginx 下载并配置
- [x] 反向代理配置完成
- [x] 本地测试通过（http://127.0.0.1）
- [x] 域名本地 hosts 测试通过（http://shop.tllos.com）
- [x] 商品数据导入（66 个商品）
- [x] 启动/停止脚本创建
- [ ] DNS 域名解析配置（需用户在域名服务商操作）
- [ ] 防火墙/安全组配置（需用户操作）
- [ ] SSL 证书配置（可选，推荐）
- [ ] 自动备份任务配置（推荐）
- [ ] 修改默认管理员密码（必须）

---

## 十二、技术支持

如遇问题，请检查：
1. 服务是否运行（`Get-Process tllvm, nginx`）
2. 端口是否监听（`netstat -ano | findstr ":80 :8090"`）
3. Nginx 错误日志（`nginx-1.24.0/logs/error.log`）
4. TLLOS 控制台输出

---

**部署完成时间**：2026-09-04
**TLLOS 版本**：高帧率编程语言（含 SQLite 绑定）
**Nginx 版本**：1.24.0
**商品数量**：66 个
**API 端点**：47+ 个
**数据表**：64 张
