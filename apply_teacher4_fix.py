import sqlite3
import shutil
from datetime import datetime

db_path = 'institut.db'
backup_path = f"backups/institut_backup_before_teacher4_comp50_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

print(f"Creating backup: {backup_path}")
shutil.copyfile(db_path, backup_path)
print("Backup created successfully.")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    # 1. State before update
    t4 = cursor.execute("SELECT id, first_name, last_name, specialty, salary_type, salary_amount FROM teachers WHERE id = 4").fetchone()
    print("\n[BEFORE] Teacher 4:", dict(t4))

    cts = cursor.execute("SELECT id, course_id, teacher_id, compensation_type, compensation_value, is_active FROM course_teachers WHERE teacher_id = 4").fetchall()
    print("[BEFORE] CourseTeacher records for Teacher 4:")
    for ct in cts:
        print("  ", dict(ct))

    # 2. Update teachers table
    cursor.execute("""
        UPDATE teachers 
        SET salary_amount = 50.0 
        WHERE id = 4
    """)
    print("\nUpdated teachers table: salary_amount = 50.0 for teacher 4")

    # 3. Update course_teachers table
    cursor.execute("""
        UPDATE course_teachers 
        SET compensation_value = 50.0 
        WHERE teacher_id = 4
    """)
    print(f"Updated course_teachers table: compensation_value = 50.0 for teacher 4 ({cursor.rowcount} rows)")

    # 4. Insert Activity Log
    cursor.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (33, 'teacher_compensation_update', 'Mise  jour rmunration enseignante Hakima EL BRIJ (ID 4): passage de 55%  50% pour octobre 2026 et suivants.', datetime('now', 'localtime'))
    """)
    print("Added activity_log entry")

    conn.commit()
    print("\nTransaction committed successfully!")

    # 5. State after update
    t4_after = cursor.execute("SELECT id, first_name, last_name, specialty, salary_type, salary_amount FROM teachers WHERE id = 4").fetchone()
    print("\n[AFTER] Teacher 4:", dict(t4_after))

    cts_after = cursor.execute("SELECT id, course_id, teacher_id, compensation_type, compensation_value, is_active FROM course_teachers WHERE teacher_id = 4").fetchall()
    print("[AFTER] CourseTeacher records for Teacher 4:")
    for ct in cts_after:
        print("  ", dict(ct))

except Exception as ex:
    conn.rollback()
    print(f"ERROR: {ex}, transaction rolled back.")
    raise
finally:
    conn.close()
