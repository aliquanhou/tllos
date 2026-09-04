#!/bin/bash
# ============================================================
# TLLOS 商城一键部署脚本
# 用法: sudo bash deploy-shop.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SHOP_DIR="/var/www/tllos.com/shop"
NGINX_CONF="/etc/nginx/sites-available/tllos.com"
SERVICE_NAME="tll-shop"
DOMAIN="tllos.com"
PORT=8090

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  TLLOS 商城一键部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 检查当前目录是否有商城文件
if [ ! -f "main.tllbc" ]; then
    echo -e "${YELLOW}警告: 当前目录未找到 main.tllbc${NC}"
    echo -e "${YELLOW}请确保在 deploy/shop 目录下运行此脚本${NC}"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[1/8] 检查系统环境...${NC}"

# 检查 Nginx
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}  安装 Nginx...${NC}"
    apt update -qq
    apt install -y -qq nginx
fi
echo -e "  ✓ Nginx 已安装: $(nginx -v 2>&1)"

# 检查 gcc（用于编译 TLL VM）
if ! command -v gcc &> /dev/null; then
    echo -e "${YELLOW}  安装 gcc...${NC}"
    apt install -y -qq gcc make
fi
echo -e "  ✓ gcc 已安装"

# 检查 sqlite3
if ! command -v sqlite3 &> /dev/null; then
    echo -e "${YELLOW}  安装 sqlite3...${NC}"
    apt install -y -qq sqlite3
fi
echo -e "  ✓ sqlite3 已安装"

echo ""
echo -e "${GREEN}[2/8] 创建目录结构...${NC}"
mkdir -p "$SHOP_DIR"
mkdir -p "$SHOP_DIR/data"
mkdir -p "/var/log"
mkdir -p "/backup"
echo -e "  ✓ 商城目录: $SHOP_DIR"
echo -e "  ✓ 数据目录: $SHOP_DIR/data"
echo -e "  ✓ 备份目录: /backup"

echo ""
echo -e "${GREEN}[3/8] 复制商城文件...${NC}"

# 复制文件
if [ -f "main.tllbc" ]; then
    cp main.tllbc "$SHOP_DIR/"
    echo -e "  ✓ main.tllbc"
fi

if [ -f "tllvm" ]; then
    cp tllvm "$SHOP_DIR/"
    chmod +x "$SHOP_DIR/tllvm"
    echo -e "  ✓ tllvm (Linux)"
elif [ -f "tllvm.exe" ]; then
    echo -e "${YELLOW}  ⚠ 检测到 Windows 版本 tllvm.exe，需要在 Linux 上重新编译${NC}"
fi

# 复制脚本
if [ -f "backup.bat" ]; then
    cp backup.bat "$SHOP_DIR/"
fi
if [ -f "restore.bat" ]; then
    cp restore.bat "$SHOP_DIR/"
fi

# 创建 Linux 启动脚本
cat > "$SHOP_DIR/start.sh" << 'STARTEOF'
#!/bin/bash
cd /var/www/tllos.com/shop
if pgrep -f "tllvm main.tllbc" > /dev/null; then
    echo "商城服务器已在运行"
    exit 0
fi
nohup ./tllvm main.tllbc > /var/log/tll-shop.log 2>&1 &
echo $! > /var/run/tll-shop.pid
echo "商城服务器已启动，PID: $(cat /var/run/tll-shop.pid)"
STARTEOF
chmod +x "$SHOP_DIR/start.sh"
echo -e "  ✓ start.sh"

# 创建备份脚本
cat > "$SHOP_DIR/backup.sh" << 'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/var/www/tllos.com/shop/data/mall.db"

if [ -f "$DB_PATH" ]; then
    sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/mall-$DATE.db"
    echo "备份完成: $BACKUP_DIR/mall-$DATE.db"
    # 保留最近 30 天
    find "$BACKUP_DIR" -name "mall-*.db" -mtime +30 -delete
else
    echo "数据库文件不存在: $DB_PATH"
fi
BACKUPEOF
chmod +x "$SHOP_DIR/backup.sh"
echo -e "  ✓ backup.sh"

# 设置权限
chown -R www-data:www-data "$SHOP_DIR"
chmod -R 755 "$SHOP_DIR"
chmod -R 775 "$SHOP_DIR/data"
echo -e "  ✓ 权限设置完成"

echo ""
echo -e "${GREEN}[4/8] 编译 Linux 版本 TLL VM（如需要）...${NC}"
if [ ! -f "$SHOP_DIR/tllvm" ]; then
    echo -e "${YELLOW}  从 GitHub 克隆源码并编译...${NC}"
    cd /opt
    if [ ! -d "tllos" ]; then
        git clone https://github.com/aliquanhou/tllos.git --depth 1
    fi
    cd tllos/host/c
    gcc -O2 -std=c99 -D_POSIX_C_SOURCE=200809L -DSQLITE_THREADSAFE=1 \
        -o tllvm main.c vm.c value.c json.c builtin.c sqlite_builtin.c sqlite3.c \
        -lm -lpthread 2>/dev/null || {
            echo -e "${YELLOW}  编译失败，尝试简化版本...${NC}"
            gcc -O2 -std=c99 -D_POSIX_C_SOURCE=200809L \
                -o tllvm main.c vm.c value.c json.c builtin.c -lm
        }
    cp tllvm "$SHOP_DIR/"
    chmod +x "$SHOP_DIR/tllvm"
    echo -e "  ✓ TLL VM 编译完成"
else
    echo -e "  ✓ TLL VM 已存在，跳过编译"
fi

echo ""
echo -e "${GREEN}[5/8] 配置 Systemd 服务...${NC}"
cat > "/etc/systemd/system/$SERVICE_NAME.service" << 'SERVICEEOF'
[Unit]
Description=TLLOS Shop - High Performance E-Commerce Platform
After=network.target nginx.service
Wants=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/tllos.com/shop
ExecStart=/var/www/tllos.com/shop/tllvm /var/www/tllos.com/shop/main.tllbc
Restart=always
RestartSec=5
Environment=TLL_SHOP_PORT=8090
NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tll-shop

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "  ✓ Systemd 服务已启动"
    echo -e "  ✓ 状态: $(systemctl is-active $SERVICE_NAME)"
else
    echo -e "${RED}  ✗ 服务启动失败，查看日志:${NC}"
    journalctl -u "$SERVICE_NAME" -n 20
    exit 1
fi

echo ""
echo -e "${GREEN}[6/8] 配置 Nginx 反向代理...${NC}"

# 检查是否已有配置
if [ -f "$NGINX_CONF" ]; then
    echo -e "${YELLOW}  已存在 Nginx 配置，备份后更新...${NC}"
    cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%Y%m%d)"
fi

cat > "$NGINX_CONF" << 'NGINXEOF'
upstream tll_shop_backend {
    server 127.0.0.1:8090;
    keepalive 32;
}

server {
    listen 80;
    server_name tllos.com www.tllos.com;
    root /var/www/tllos.com;
    index index.html;

    # 商城反向代理
    location /shop/ {
        rewrite ^/shop/(.*)$ /$1 break;
        proxy_pass http://tll_shop_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
NGINXEOF

# 创建软链接
ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/tllos.com"

# 测试并重载
if nginx -t 2>&1 | grep -q "test is successful"; then
    systemctl reload nginx
    echo -e "  ✓ Nginx 配置已生效"
else
    echo -e "${RED}  ✗ Nginx 配置测试失败${NC}"
    nginx -t
    exit 1
fi

echo ""
echo -e "${GREEN}[7/8] 配置自动备份...${NC}"

# 添加 crontab
(crontab -l 2>/dev/null | grep -v "tll-shop-backup"; \
 echo "0 3 * * * /var/www/tllos.com/shop/backup.sh # tll-shop-backup") | crontab -
echo -e "  ✓ 每天凌晨 3 点自动备份"
echo -e "  ✓ 备份保留 30 天"

echo ""
echo -e "${GREEN}[8/8] 验证部署...${NC}"

# 等待服务启动
sleep 3

# 测试商城服务器
if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/" | grep -q "200\|302"; then
    echo -e "  ✓ 商城服务器运行正常 (端口 $PORT)"
else
    echo -e "${YELLOW}  ⚠ 商城服务器响应异常，可能需要检查${NC}"
fi

# 测试 Nginx 反向代理
if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/shop/" | grep -q "200\|302"; then
    echo -e "  ✓ Nginx 反向代理正常"
else
    echo -e "${YELLOW}  ⚠ Nginx 反向代理响应异常，可能需要检查${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "商城访问地址:"
echo -e "  ${GREEN}http://$DOMAIN/shop/${NC}"
echo -e "  ${GREEN}http://www.$DOMAIN/shop/${NC}"
echo ""
echo -e "管理后台:"
echo -e "  ${GREEN}http://$DOMAIN/shop/admin${NC}"
echo -e "  用户名: admin"
echo -e "  密码: admin123 ${RED}(请立即修改!)${NC}"
echo ""
echo -e "常用命令:"
echo -e "  查看状态: sudo systemctl status $SERVICE_NAME"
echo -e "  重启服务: sudo systemctl restart $SERVICE_NAME"
echo -e "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo -e "  手动备份: sudo $SHOP_DIR/backup.sh"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo -e "  1. 在官网导航栏添加 '商城' 链接，指向 /shop"
echo -e "  2. 修改管理员默认密码"
echo -e "  3. 配置 SSL/HTTPS (sudo certbot --nginx)"
echo -e "  4. 测试完整购物流程"
echo ""
