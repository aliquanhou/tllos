#!/bin/bash
# TLLOS Mall - Setup and Test Script

echo "=== 1. 检查 TLLOS 商城进程 ==="
ps aux | grep tllvm | grep -v grep || echo "进程未找到"

echo ""
echo "=== 2. 检查 8090 端口 ==="
netstat -tlnp | grep 8090 || echo "8090 端口未监听"

echo ""
echo "=== 3. 直接测试 TLLOS 商城 ==="
curl -s -o /dev/null -w "HTTP状态: %{http_code}\n" http://127.0.0.1:8090/
curl -s http://127.0.0.1:8090/ | head -5

echo ""
echo "=== 4. 测试商品 API ==="
curl -s "http://127.0.0.1:8090/search/products?page=1&page_size=3" | head -100

echo ""
echo "=== 5. 检查 Nginx 配置 ==="
cat /etc/nginx/sites-available/shop.tllos.com

echo ""
echo "=== 6. 测试 Nginx 代理 ==="
curl -s -o /dev/null -w "HTTP状态: %{http_code}\n" -H "Host: shop.tllos.com" http://127.0.0.1/
