import sqlite3
import shutil
import datetime
import os

db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_cancel_bouchamah_hakima_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"Database backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 1. Delete invoice items for invoice 552 (Course 5 - Hakima El Brij)
    c.execute("DELETE FROM invoice_items WHERE invoice_id = 552")
    print(f"1. Deleted {c.rowcount} invoice item(s) from invoice 552")

    # 2. Delete invoice 552
    c.execute("DELETE FROM invoices WHERE id = 552 AND student_id = 354")
    print(f"2. Deleted {c.rowcount} invoice (552)")

    # 3. Delete ghost enrollments 803 and 804 for Course 5 (Hakima El Brij)
    c.execute("DELETE FROM enrollments WHERE id IN (803, 804) AND student_id = 354 AND course_id = 5")
    print(f"3. Deleted {c.rowcount} enrollment(s) (803, 804)")

    # 4. Clean up any attendances for student 354 in Course 5 if any
    c.execute("DELETE FROM attendances WHERE student_id = 354 AND course_id = 5")
    print(f"4. Cleaned up {c.rowcount} attendance records for Course 5")

    # 5. Log activity
    log_detail = "Annulation de l'inscription erronée de BOUCHAMAH OUIAME (ILAS467) chez Prof. Hakima EL BRIJ (Course 5 - Français). Suppression des inscriptions #803 et #804 (0 DH payé) et de la facture #552. Maintien de son inscription active en Espagnol (#701 - Prof. Lina Lahsinia)."
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_delete', ?, ?)
    """, (log_detail, now_str))
    print("5. Inserted activity log")

    conn.commit()
    print("\nALL CHANGES COMMITTED SUCCESSFULLY TO institut.db!")

except Exception as e:
    conn.rollback()
    print("ERROR, transaction rolled back:", e)
    raise
finally:
    conn.close()
