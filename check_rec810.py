import sqlite3

conn = sqlite3.connect('institut.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM payments WHERE receipt = 'REC-0810'")
p = c.fetchone()
print("REC-0810:", dict(p) if p else "Not found")

if p:
    student_id = p['student_id']
    c.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    print("Student:", dict(c.fetchone()))
    enrollment_id = p['enrollment_id']
    c.execute("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,))
    print("Enrollment:", dict(c.fetchone()))
