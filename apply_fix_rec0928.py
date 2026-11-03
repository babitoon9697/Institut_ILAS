import sqlite3
import shutil
from datetime import datetime, date

db_path = 'institut.db'
backup_path = f"backups/institut_backup_before_fix_rec0928_ilas549_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

print(f"Creating backup: {backup_path}")
shutil.copyfile(db_path, backup_path)
print("Backup created successfully.")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    # 1. Verification before update
    p1046 = cursor.execute("SELECT * FROM payments WHERE id = 1046").fetchone()
    p1028 = cursor.execute("SELECT * FROM payments WHERE id = 1028").fetchone()
    e927 = cursor.execute("SELECT * FROM enrollments WHERE id = 927").fetchone()
    e944 = cursor.execute("SELECT * FROM enrollments WHERE id = 944").fetchone()
    inv639 = cursor.execute("SELECT * FROM invoices WHERE id = 639").fetchone()
    inv651 = cursor.execute("SELECT * FROM invoices WHERE id = 651").fetchone()

    print("\n[BEFORE] Payment 1046:", dict(p1046))
    print("[BEFORE] Payment 1028:", dict(p1028))
    print("[BEFORE] Enrollment 927:", dict(e927))
    print("[BEFORE] Enrollment 944:", dict(e944))
    print("[BEFORE] Invoice 639:", dict(inv639))
    print("[BEFORE] Invoice 651:", dict(inv651))

    # 2. Update Payment 1046 (REC-0928)
    cursor.execute("""
        UPDATE payments 
        SET amount = 1400.0,
            enrollment_id = 927,
            invoice_id = 639,
            note = 'Paiement solde Cours Particulier - Yakout melloul (Anglais)'
        WHERE id = 1046
    """)
    print("\nUpdated payment 1046: amount=1400.0, enrollment_id=927, invoice_id=639")

    # 3. Update Invoice 639 status to 'paid'
    cursor.execute("""
        UPDATE invoices 
        SET status = 'paid'
        WHERE id = 639
    """)
    print("Updated invoice 639: status='paid'")

    # 4. Update Enrollment 927: status='active', custom_end_date='2026-11-27'
    cursor.execute("""
        UPDATE enrollments 
        SET status = 'active',
            custom_end_date = '2026-11-27',
            rest_promise_date = NULL,
            rest_promise_note = NULL
        WHERE id = 927
    """)
    print("Updated enrollment 927: status='active', custom_end_date='2026-11-27'")

    # 5. Delete Invoice 651 and items
    cursor.execute("DELETE FROM invoice_items WHERE invoice_id = 651")
    cursor.execute("DELETE FROM invoices WHERE id = 651")
    print("Deleted invoice 651 and its invoice items")

    # 6. Delete Enrollment 944
    cursor.execute("DELETE FROM enrollments WHERE id = 944")
    print("Deleted enrollment 944")

    # 7. Reset next_invoice_number in settings if it is 765
    curr_inv_num = cursor.execute("SELECT value FROM settings WHERE key = 'next_invoice_number'").fetchone()
    if curr_inv_num and curr_inv_num['value'] == '765':
        cursor.execute("UPDATE settings SET value = '764' WHERE key = 'next_invoice_number'")
        print("Reset next_invoice_number in settings to 764")

    # 8. Insert Activity Log
    cursor.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (33, 'fix_payment_receipt', 'Correction REC-0928 Yakout melloul (ILAS549): montant 2400->1400 DH li  FA-0752 (cours 2400 DH sold). Suppression renouvellement erron 944 et FA-0764.', datetime('now', 'localtime'))
    """)
    print("Added activity_log entry")

    conn.commit()
    print("\nTransaction committed successfully!")

    # 9. Verify state after update
    print("\n[AFTER] Verifying updated state:")
    p1046_after = cursor.execute("SELECT * FROM payments WHERE id = 1046").fetchone()
    e927_after = cursor.execute("SELECT * FROM enrollments WHERE id = 927").fetchone()
    inv639_after = cursor.execute("SELECT * FROM invoices WHERE id = 639").fetchone()
    e944_check = cursor.execute("SELECT * FROM enrollments WHERE id = 944").fetchone()
    inv651_check = cursor.execute("SELECT * FROM invoices WHERE id = 651").fetchone()
    inv_setting = cursor.execute("SELECT * FROM settings WHERE key = 'next_invoice_number'").fetchone()

    print("[AFTER] Payment 1046:", dict(p1046_after))
    print("[AFTER] Enrollment 927:", dict(e927_after))
    print("[AFTER] Invoice 639:", dict(inv639_after))
    print("[AFTER] Enrollment 944 exists:", e944_check is not None)
    print("[AFTER] Invoice 651 exists:", inv651_check is not None)
    print("[AFTER] next_invoice_number:", dict(inv_setting))

    # Total payments for invoice 639
    total_paid = cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = 639").fetchone()[0]
    print(f"[AFTER] Total paid for invoice 639: {total_paid} DH (Expected: 2400.0 DH)")

    # Total payments for student 429
    total_stu_paid = cursor.execute("SELECT SUM(amount) FROM payments WHERE student_id = 429").fetchone()[0]
    print(f"[AFTER] Total paid by Yakout Melloul: {total_stu_paid} DH (Expected: 2400.0 DH)")

except Exception as ex:
    conn.rollback()
    print(f"ERROR: {ex}, rolled back transaction.")
    raise
finally:
    conn.close()
