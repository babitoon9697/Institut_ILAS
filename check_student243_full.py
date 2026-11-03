import sqlite3

con = sqlite3.connect('institut.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

print("--- Student 243 ---")
cur.execute("SELECT * FROM students WHERE id = 243")
print(dict(cur.fetchone()))

print("\n--- Enrollments 243 ---")
cur.execute("SELECT * FROM enrollments WHERE student_id = 243")
for e in cur.fetchall():
    print(dict(e))

print("\n--- Invoices 243 ---")
cur.execute("SELECT * FROM invoices WHERE student_id = 243")
for inv in cur.fetchall():
    print(dict(inv))

print("\n--- Payments 243 ---")
cur.execute("SELECT * FROM payments WHERE student_id = 243")
for p in cur.fetchall():
    print(dict(p))
