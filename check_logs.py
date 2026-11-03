import sqlite3
con = sqlite3.connect('institut.db')
cur = con.cursor()
cur.execute("PRAGMA table_info(activity_log)")
print("activity_log cols:", [col[1] for col in cur.fetchall()])

cur.execute("SELECT * FROM activity_log WHERE detail LIKE '%894%' OR detail LIKE '%813%'")
print('logs for 894/813:', cur.fetchall())

cur.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 5")
print('latest 5 logs:', cur.fetchall())
