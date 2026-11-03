import sqlite3

con = sqlite3.connect('institut.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

print("--- Payments for Student 77 ---")
cur.execute("SELECT * FROM payments WHERE student_id = 77")
for p in cur.fetchall():
    print(dict(p))

print("\n--- Enrollments for Student 77 ---")
cur.execute("SELECT * FROM enrollments WHERE student_id = 77")
for e in cur.fetchall():
    print(dict(e))

print("\n--- Invoices for Student 77 ---")
cur.execute("SELECT * FROM invoices WHERE student_id = 77")
for inv in cur.fetchall():
    print(dict(inv))
