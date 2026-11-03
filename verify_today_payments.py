import sqlite3

conn = sqlite3.connect('institut.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id, receipt, amount, method, date, note, recorded_by FROM payments WHERE date = '2026-10-19' ORDER BY id ASC")
rows = c.fetchall()
print(f"Total payments on 2026-10-19: {len(rows)}")
total_amount = 0
for r in rows:
    print(dict(r))
    total_amount += r['amount']
print("Total Amount:", total_amount)

# Check if REC-0810 exists anywhere
c.execute("SELECT * FROM payments WHERE receipt = 'REC-0810'")
print("REC-0810 exists?:", c.fetchall())

# Check if REC-0813 exists
c.execute("SELECT * FROM payments WHERE receipt = 'REC-0813'")
print("REC-0813 exists?:", c.fetchall())
