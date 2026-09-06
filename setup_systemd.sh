#!/bin/bash
echo "=== 1. 重载 systemd ==="
systemctl daemon-reload

echo ""
echo "=== 2. 启用服务 ==="
systemctl enable tllos-mall

echo ""
echo "=== 3. 启动服务 ==="
systemctl start tllos-mall
sleep 5

echo ""
echo "=== 4. 检查服务状态 ==="
systemctl status tllos-mall --no-pager -l | head -20

echo ""
echo "=== 5. 检查进程 ==="
ps aux | grep tllvm | grep -v grep || echo "进程未找到"

echo ""
echo "=== 6. 检查端口 ==="
netstat -tlnp | grep 8090 || echo "8090 端口未监听"

echo ""
echo "=== 7. 测试访问 ==="
curl -s -o /dev/null -w "HTTP状态: %{http_code}\n" http://127.0.0.1:8090/

echo ""
echo "=== 8. 测试商品 API ==="
curl -s "http://127.0.0.1:8090/search/products?page=1&page_size=2" | head -100

echo ""
echo "=== 9. 测试 Nginx 代理 ==="
curl -s -o /dev/null -w "HTTP状态: %{http_code}\n" -H "Host: shop.tllos.com" http://127.0.0.1/

echo ""
echo "=== 10. 查看日志 ==="
tail -20 /var/log/tllos-mall.log
