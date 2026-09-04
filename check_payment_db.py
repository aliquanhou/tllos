import sqlite3
conn = sqlite3.connect('mall/data/mall.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print('数据库表总数:', len(tables))
print()
payment_tables = [t for t in tables if 'payment' in t[0] or 'refund' in t[0] or 'account' in t[0]]
print('支付相关表:')
for t in payment_tables:
    print('  -', t[0])
print()
try:
    cursor.execute('SELECT * FROM payment_configs')
    rows = cursor.fetchall()
    print('payment_configs 记录数:', len(rows))
    for r in rows[:5]:
        print('  ', r)
except Exception as e:
    print('payment_configs 查询失败:', e)
conn.close()
