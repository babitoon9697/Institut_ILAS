import sqlite3
import os

db_path = 'institut.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=====================================================================")
print("1. PAYMENTS IN OCTOBER 2026")
print("=====================================================================")
c.execute("SELECT COUNT(*) as cnt, SUM(amount) as tot FROM payments WHERE date LIKE '2026-10%'")
row = c.fetchone()
print(f"Total payments in 2026-10: {row['cnt']} transactions, Total amount: {row['tot']} DH")

print("\n=====================================================================")
print("2. PAYMENTS WITH NULL ENROLLMENT_ID IN OCTOBER 2026")
print("=====================================================================")
c.execute("SELECT id, receipt, student_id, amount, date, note FROM payments WHERE enrollment_id IS NULL AND date LIKE '2026-10%'")
null_en = c.fetchall()
print(f"Payments without enrollment_id in 2026-10: {len(null_en)}")
for r in null_en:
    print(dict(r))

print("\n=====================================================================")
print("3. ALL PAYMENTS WITH NULL ENROLLMENT_ID (EVER)")
print("=====================================================================")
c.execute("SELECT id, receipt, student_id, amount, date, note FROM payments WHERE enrollment_id IS NULL")
all_null_en = c.fetchall()
print(f"Total payments without enrollment_id (ever): {len(all_null_en)}")
for r in all_null_en:
    print(dict(r))

print("\n=====================================================================")
print("4. STUDENTS WITH MULTIPLE ENROLLMENTS IN OCTOBER 2026")
print("=====================================================================")
c.execute("""
    SELECT s.id, s.first_name, s.last_name, COUNT(e.id) as enroll_count
    FROM students s
    JOIN enrollments e ON e.student_id = s.id
    WHERE e.status != 'dropped'
    GROUP BY s.id
    HAVING COUNT(e.id) > 1
    ORDER BY enroll_count DESC
""")
multi_students = c.fetchall()
print(f"Students with > 1 enrollment: {len(multi_students)}")
for s in multi_students[:15]:
    print(f"Student ID: {s['id']}, Name: {s['first_name']} {s['last_name']}, Enrollments: {s['enroll_count']}")
    c.execute("""
        SELECT e.id, e.course_id, c.name as course_name, e.monthly_price, e.calculated_price, e.status, e.enroll_date
        FROM enrollments e
        LEFT JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ? AND e.status != 'dropped'
    """, (s['id'],))
    for en in c.fetchall():
        # Get payments for this enrollment
        c.execute("SELECT id, receipt, amount, date FROM payments WHERE enrollment_id = ?", (en['id'],))
        pays = c.fetchall()
        pay_str = ", ".join([f"{p['receipt']}:{p['amount']}DH ({p['date']})" for p in pays]) or "NO DIRECT PAYMENT"
        print(f"   -> Enroll {en['id']} | Course {en['course_id']} ({en['course_name']}) | Monthly: {en['monthly_price']} | Calc: {en['calculated_price']} | Status: {en['status']} | Payments: [{pay_str}]")

print("\n=====================================================================")
print("5. PAYMENTS WITH MULTI-COURSE OR PACK MENTIONS IN NOTES OR INVOICES")
print("=====================================================================")
c.execute("""
    SELECT id, receipt, student_id, enrollment_id, amount, date, note 
    FROM payments 
    WHERE (note LIKE '%pack%' OR note LIKE '%multi%' OR note LIKE '%2 mat%' OR note LIKE '%3 mat%' OR note LIKE '%remise%' OR note LIKE '%famille%')
    AND date >= '2026-09-01'
""")
pack_pays = c.fetchall()
print(f"Pack/Multi payments: {len(pack_pays)}")
for p in pack_pays:
    print(dict(p))

conn.close()
