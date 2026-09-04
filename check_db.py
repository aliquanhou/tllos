import sqlite3
conn = sqlite3.connect('mall/data/mall.db')
c = conn.cursor()
c.execute('SELECT id, username, password, role FROM users')
rows = c.fetchall()
print('=== 用户表 ===')
for row in rows:
    print(f'  id={row[0]}, username={row[1]}, password={row[2][:20]}..., role={row[3]}')

c.execute('SELECT COUNT(*) FROM products')
print(f'\n商品总数: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM orders')
print(f'订单总数: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM orders WHERE status=1')
print(f'待发货订单(status=1): {c.fetchone()[0]}')
c.execute('SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status!=4')
print(f'销售额: {c.fetchone()[0]}')

conn.close()
