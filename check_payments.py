import sqlite3

conn = sqlite3.connect('institut.db')
c = conn.cursor()
c.execute("SELECT id, receipt, amount, date, created_at, recorded_by, note FROM payments WHERE id = 894")
print("id=894:", c.fetchall())

c.execute("SELECT id, receipt, amount, date, created_at, recorded_by, note FROM payments WHERE receipt LIKE '%813%'")
print("receipt 813:", c.fetchall())

c.execute("SELECT id, receipt, amount, date, created_at, recorded_by, note FROM payments ORDER BY id DESC LIMIT 5")
print("last 5:", c.fetchall())
