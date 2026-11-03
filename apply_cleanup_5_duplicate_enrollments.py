import sqlite3
import shutil
import datetime
import os

# 1. Create a safe backup first
db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_cleanup_5_duplicates_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"Database backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # -------------------------------------------------------------
    # Case 1: Othman Baz (ILAS363, Student ID 277) - Course 80
    # Delete ghost duplicate enrollment 769 (0 DH paid)
    # Active enrollment 794 (600 DH paid) is preserved
    # -------------------------------------------------------------
    c.execute("DELETE FROM invoice_items WHERE enrollment_id = 769")
    print(f"1. Othman Baz: Deleted {c.rowcount} invoice item(s) for EID 769")
    c.execute("DELETE FROM enrollments WHERE id = 769 AND student_id = 277 AND course_id = 80")
    print(f"   Othman Baz: Deleted {c.rowcount} ghost enrollment (EID 769)")

    # -------------------------------------------------------------
    # Case 2: Ritaj Baz (ILAS364, Student ID 278) - Course 80
    # Delete ghost duplicate enrollment 768 (0 DH paid)
    # Active enrollment 793 (600 DH paid) is preserved
    # -------------------------------------------------------------
    c.execute("DELETE FROM invoice_items WHERE enrollment_id = 768")
    print(f"2. Ritaj Baz: Deleted {c.rowcount} invoice item(s) for EID 768")
    c.execute("DELETE FROM enrollments WHERE id = 768 AND student_id = 278 AND course_id = 80")
    print(f"   Ritaj Baz: Deleted {c.rowcount} ghost enrollment (EID 768)")

    # -------------------------------------------------------------
    # Case 3: Arij Salami (ILAS501, Student ID 385) - Course 26
    # Delete ghost duplicate enrollment 778 (0 DH paid), 0 DH payment 847, and unpaid invoice 530
    # Active enrollment 811 (240 DH paid) is preserved
    # -------------------------------------------------------------
    c.execute("DELETE FROM payments WHERE id = 847 AND enrollment_id = 778 AND amount = 0.0")
    print(f"3. Arij Salami: Deleted {c.rowcount} 0 DH payment(s) (ID 847)")
    c.execute("DELETE FROM invoice_items WHERE invoice_id = 530")
    print(f"   Arij Salami: Deleted {c.rowcount} invoice item(s) for Invoice 530")
    c.execute("DELETE FROM invoices WHERE id = 530 AND student_id = 385")
    print(f"   Arij Salami: Deleted {c.rowcount} invoice (ID 530)")
    c.execute("DELETE FROM enrollments WHERE id = 778 AND student_id = 385 AND course_id = 26")
    print(f"   Arij Salami: Deleted {c.rowcount} ghost enrollment (EID 778)")

    # -------------------------------------------------------------
    # Case 4: Saad Ben Moussa (ILAS500, Student ID 384) - Course 26
    # Delete ghost duplicate enrollment 775 (0 DH paid), 0 DH payment 842
    # Active enrollment 808 (200 DH paid) and Maths enrollment 774 are preserved
    # -------------------------------------------------------------
    c.execute("DELETE FROM payments WHERE id = 842 AND enrollment_id = 775 AND amount = 0.0")
    print(f"4. Saad Ben Moussa: Deleted {c.rowcount} 0 DH payment(s) (ID 842)")
    c.execute("DELETE FROM invoice_items WHERE enrollment_id = 775")
    print(f"   Saad Ben Moussa: Deleted {c.rowcount} invoice item(s) for EID 775")
    c.execute("DELETE FROM enrollments WHERE id = 775 AND student_id = 384 AND course_id = 26")
    print(f"   Saad Ben Moussa: Deleted {c.rowcount} ghost enrollment (EID 775)")

    # Recalculate Invoice 528 for Saad Ben Moussa (now only contains items for Maths EID 774)
    c.execute("""
        SELECT coalesce(sum(amount), 0) FROM invoice_items WHERE invoice_id = 528
    """)
    new_inv_tot = c.fetchone()[0]
    c.execute("UPDATE invoices SET total = ?, subtotal = ? WHERE id = 528", (new_inv_tot, new_inv_tot))
    print(f"   Saad Ben Moussa: Invoice 528 total updated to {new_inv_tot} DH")

    # -------------------------------------------------------------
    # Case 5: Hajar Abassi (ILAS033, Student ID 33) - Course 7
    # Delete ghost duplicate enrollment 131 (0 DH paid) and unpaid invoice 29
    # Paid enrollments 616 (250 DH) and 617 (250 DH) are preserved
    # -------------------------------------------------------------
    c.execute("DELETE FROM invoice_items WHERE invoice_id = 29")
    print(f"5. Hajar Abassi: Deleted {c.rowcount} invoice item(s) for Invoice 29")
    c.execute("DELETE FROM invoices WHERE id = 29 AND student_id = 33")
    print(f"   Hajar Abassi: Deleted {c.rowcount} invoice (ID 29)")
    c.execute("DELETE FROM enrollments WHERE id = 131 AND student_id = 33 AND course_id = 7")
    print(f"   Hajar Abassi: Deleted {c.rowcount} ghost enrollment (EID 131)")

    # -------------------------------------------------------------
    # Activity Log
    # -------------------------------------------------------------
    log_detail = (
        "Nettoyage global des inscriptions en doublon créées par erreur (0 DH réglé) : "
        "Suppression de EID #769 (Othman Baz ILAS363), EID #768 (Ritaj Baz ILAS364), "
        "EID #778 & Facture #530 (Arij Salami ILAS501), EID #775 (Saad Ben Moussa ILAS500), "
        "et EID #131 & Facture #29 (Hajar Abassi ILAS033). Leurs inscriptions légitimes et payées restent intactes."
    )
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'bulk_duplicate_cleanup', ?, ?)
    """, (log_detail, now_str))
    print("6. Activity log recorded")

    conn.commit()
    print("\nALL 5 DUPLICATE ENROLLMENTS CLEANED AND COMMITTED SUCCESSFULLY!")

except Exception as e:
    conn.rollback()
    print("ERROR, transaction rolled back:", e)
    raise
finally:
    conn.close()
