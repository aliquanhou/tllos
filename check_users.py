import sqlite3
conn = sqlite3.connect('mall/data/mall.db')
c = conn.cursor()
c.execute('PRAGMA table_info(users)')
print('=== users 表结构 ===')
for row in c.fetchall():
    print(f'  {row[1]} ({row[2]})')

c.execute('SELECT * FROM users LIMIT 1')
print('\n=== users 表数据(第一条) ===')
cols = [d[0] for d in c.description]
row = c.fetchone()
for i, col in enumerate(cols):
    val = str(row[i])[:50] if row[i] else 'NULL'
    print(f'  {col}: {val}')

conn.close()
