import sqlite3

conn = sqlite3.connect('institut.db')
c = conn.cursor()
c.execute("UPDATE payments SET note = 'Reglement scolarite' WHERE id = 894")
conn.commit()
print("Updated payment 894, rows affected:", c.rowcount)

# Also let's check any other payment today with NULL note
c.execute("UPDATE payments SET note = 'Paiement' WHERE created_at LIKE '2026-10-19%' AND note IS NULL")
conn.commit()
print("Updated other payments with NULL note today, rows affected:", c.rowcount)
