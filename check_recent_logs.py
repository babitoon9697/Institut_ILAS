import sqlite3

con = sqlite3.connect('institut.db')
cur = con.cursor()
cur.execute("SELECT id, user_id, action, detail, created_at FROM activity_log WHERE id >= 4080 ORDER BY id ASC")
for row in cur.fetchall():
    print(row)
