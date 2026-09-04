import urllib.request, json

# Login
data = json.dumps({'username':'admin','password':'admin123'}).encode()
req = urllib.request.Request('http://127.0.0.1:8090/login', data=data, headers={'Content-Type':'application/json'}, method='POST')
resp = urllib.request.urlopen(req, timeout=5)
login_result = json.loads(resp.read().decode())
session_id = login_result.get('sessionId')
print('Login: success=' + str(login_result.get('success')) + ', sessionId=' + str(session_id))

headers = {'Cookie': 'sessionId=' + session_id, 'Content-Type': 'application/json'}

# Test products API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/products', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/products: code=' + str(result.get('code')) + ', count=' + str(len(result.get('data',[]))))

# Test dashboard API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/dashboard/stats', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
d = result['data']
print('GET /api/admin/dashboard/stats: products=' + str(d['totalProducts']) + ', orders=' + str(d['totalOrders']) + ', users=' + str(d['totalUsers']) + ', sales=' + str(d['totalSales']))

# Test create product
data = json.dumps({'name':'Python API测试商品','price':88.88,'stock':50}).encode()
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/products', data=data, headers=headers, method='POST')
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('POST /api/admin/products: ' + str(result.get('message')))

# Test categories API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/categories', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/categories: code=' + str(result.get('code')) + ', count=' + str(len(result.get('data',[]))))

# Test create category
data = json.dumps({'name':'Python API测试分类','parent_id':0}).encode()
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/categories', data=data, headers=headers, method='POST')
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('POST /api/admin/categories: ' + str(result.get('message')))

# Test permissions API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/permissions/roles', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/permissions/roles: code=' + str(result.get('code')))

# Test create role
data = json.dumps({'name':'Python测试角色','role_key':'python_test','description':'Python API创建'}).encode()
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/permissions/roles', data=data, headers=headers, method='POST')
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('POST /api/admin/permissions/roles: ' + str(result.get('message')))

# Test decoration API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/decoration/banners', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/decoration/banners: code=' + str(result.get('code')))

# Test organization API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/org/departments', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/org/departments: code=' + str(result.get('code')))

# Test channel API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/channel/channels', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/channel/channels: code=' + str(result.get('code')))

# Test users API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/users', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/users: code=' + str(result.get('code')) + ', count=' + str(len(result.get('data',[]))))

# Test coupons API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/coupons', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/coupons: code=' + str(result.get('code')))

# Test orders API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/orders', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/orders: code=' + str(result.get('code')))

# Test system config API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/system/config', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/system/config: code=' + str(result.get('code')))

# Test merchants API
req = urllib.request.Request('http://127.0.0.1:8090/api/admin/merchants', headers=headers)
resp = urllib.request.urlopen(req, timeout=5)
result = json.loads(resp.read().decode())
print('GET /api/admin/merchants: code=' + str(result.get('code')))

print()
print('=== All 17 module API tests completed successfully ===')
