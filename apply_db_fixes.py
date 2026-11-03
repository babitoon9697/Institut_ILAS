import sqlite3

conn = sqlite3.connect('institut.db')
c = conn.cursor()

# 1. Delete Payment 892 (REC-0810)
c.execute("DELETE FROM payments WHERE id = 892")
print("Deleted payment 892 (REC-0810), rows affected:", c.rowcount)

# Revert invoice 323 to unpaid
c.execute("UPDATE invoices SET status = 'unpaid' WHERE id = 323")
print("Invoice 323 status updated to unpaid, rows affected:", c.rowcount)

# 2. Restore Payment 894 (REC-0813)
# Check if id 894 exists
c.execute("SELECT id FROM payments WHERE id = 894")
row = c.fetchone()
if not row:
    c.execute("""
        INSERT INTO payments (id, receipt, enrollment_id, student_id, amount, method, date, note, invoice_id, recorded_by, created_at)
        VALUES (894, 'REC-0813', 430, 243, 650.0, 'cash', '2026-10-19', 'Reglement scolarite', NULL, 33, '2026-10-19 19:55:09.853839')
    """)
    print("Restored payment 894 (REC-0813)")
else:
    c.execute("UPDATE payments SET receipt='REC-0813', amount=650.0, method='cash', date='2026-10-19', note='Reglement scolarite' WHERE id=894")
    print("Updated payment 894")

conn.commit()
conn.close()
