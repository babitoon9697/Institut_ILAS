import sqlite3
import shutil
import datetime
import os

db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_cancel_ilas328_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"Database backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    student_id = 244
    course_id = 57
    enrollment_id = 431
    invoice_id = 273

    # 1. Delete attendances for student 244 in course 57
    c.execute("DELETE FROM attendances WHERE student_id = ? AND course_id = ?", (student_id, course_id))
    print(f"1. Deleted {c.rowcount} attendance record(s)")

    # 2. Delete payments for student 244 (Payment 451 of 150 DH and Payment 649 of 650 DH)
    c.execute("DELETE FROM payments WHERE student_id = ? AND id IN (451, 649)", (student_id,))
    print(f"2. Deleted {c.rowcount} payment(s) (IDs 451, 649)")

    # 3. Delete invoice items for invoice 273
    c.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    print(f"3. Deleted {c.rowcount} invoice item(s) from invoice {invoice_id}")

    # 4. Delete invoice 273
    c.execute("DELETE FROM invoices WHERE id = ? AND student_id = ?", (invoice_id, student_id))
    print(f"4. Deleted {c.rowcount} invoice (ID {invoice_id})")

    # 5. Delete enrollment 431
    c.execute("DELETE FROM enrollments WHERE id = ? AND student_id = ? AND course_id = ?", (enrollment_id, student_id, course_id))
    print(f"5. Deleted {c.rowcount} enrollment (ID {enrollment_id})")

    # 6. Update student notes
    now_date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    c.execute("SELECT notes FROM students WHERE id = ?", (student_id,))
    cur_notes = c.fetchone()[0] or ''
    new_note = f"[Annulation totale inscription Allemand (Prof. Rachid SABRI) le {now_date_str} - Inscription #431, Facture #273 et paiements #451 (150 DH) / #649 (650 DH) supprimés]."
    updated_notes = (cur_notes + " | " + new_note).strip(' |')
    c.execute("UPDATE students SET notes = ?, credit_balance = 0.0 WHERE id = ?", (updated_notes, student_id))
    print(f"6. Updated student {student_id} notes and confirmed credit_balance=0.0")

    # 7. Insert audit activity log
    log_detail = "Annulation complète de l'inscription de MOHAMED ZAHRAOUI (ILAS328) chez Prof. Rachid SABRI (Allemand - Course #57). Suppression de l'inscription #431, de la facture #273 (FA-0354), et des paiements #451 (150 DH) et #649 (650 DH)."
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_delete', ?, ?)
    """, (log_detail, now_str))
    print("7. Inserted activity log")

    conn.commit()
    print("\nALL CHANGES COMMITTED SUCCESSFULLY TO institut.db!")

except Exception as e:
    conn.rollback()
    print("ERROR, transaction rolled back:", e)
    raise
finally:
    conn.close()
