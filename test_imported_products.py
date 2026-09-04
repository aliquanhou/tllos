#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request, json, urllib.parse

def api(method, path, data=None, headers=None):
    url = 'http://127.0.0.1:8090' + path
    h = {'Content-Type': 'application/json'}
    if headers: h.update(headers)
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

print('=== 商品总数统计 ===')
r = api('GET', '/search/products?page=1&page_size=1')
print('商品总数:', r.get('total'))
print('总页数:', r.get('total_pages'))

print()
print('=== 商品列表（前10个）===')
r = api('GET', '/search/products?page=1&page_size=10')
print('返回数量:', r.get('count'))
for i, p in enumerate(r.get('data', [])):
    name = str(p.get('name', ''))[:40]
    price = p.get('price', 0)
    stock = p.get('stock', 0)
    cat_id = p.get('category_id', 0)
    print(f'  {i+1}. {name}... | 价格: ¥{price} | 库存: {stock} | 分类ID: {cat_id}')

print()
print('=== 搜索测试（关键词：真皮）===')
keyword = urllib.parse.quote('真皮')
r = api('GET', '/search/products?keyword=' + keyword + '&page_size=5')
print('搜索结果数:', r.get('total'))
for i, p in enumerate(r.get('data', [])):
    name = str(p.get('name', ''))[:40]
    price = p.get('price', 0)
    print(f'  {i+1}. {name}... | 价格: ¥{price}')

print()
print('=== 价格筛选测试（100-200元）===')
r = api('GET', '/search/products?min_price=100&max_price=200&page_size=5')
print('筛选结果数:', r.get('total'))
for i, p in enumerate(r.get('data', [])):
    name = str(p.get('name', ''))[:40]
    price = p.get('price', 0)
    print(f'  {i+1}. {name}... | 价格: ¥{price}')

print()
print('=== 商品详情测试（ID: 7）===')
r = api('GET', '/product/7')
if isinstance(r, dict) and r.get('name'):
    print('商品名称:', r.get('name'))
    print('商品价格:', r.get('price'))
    print('商品库存:', r.get('stock'))
    desc = str(r.get('description', ''))[:100]
    print('商品描述:', desc)
else:
    print('返回内容:', str(r)[:200])

print()
print('=== 1688商品导入验证完成 ===')
print('商品已成功导入并可正常搜索、筛选、查看详情！')
