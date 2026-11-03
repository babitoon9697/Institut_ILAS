import sqlite3
con = sqlite3.connect('institut.db')
cur = con.cursor()
cur.execute("SELECT id, code, first_name, last_name FROM students WHERE id = 243 OR last_name LIKE '%BAHLOUL%'")
print('Students:', cur.fetchall())

cur.execute("SELECT * FROM payments WHERE student_id = 243")
print('Payments for student 243:', cur.fetchall())

cur.execute("SELECT * FROM enrollments WHERE student_id = 243")
print('Enrollments for student 243:', cur.fetchall())
