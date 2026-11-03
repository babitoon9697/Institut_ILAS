import sqlite3
import shutil
import datetime
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_ilas181_fix_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"1. Database successfully backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 1. Update Enrollment 459 (2nd period: 21/08/2026 -> 20/09/2026)
    notes_459 = "Inscription Express (1 mois). Période: 21/08/2026 au 20/09/2026. Frais d'inscription: 0.0 DH."
    c.execute("""
        UPDATE enrollments
        SET enroll_date = '2026-08-21',
            custom_end_date = '2026-09-20',
            notes = ?
        WHERE id = 459 AND student_id = 112
    """, (notes_459,))
    print(f"2. Enrollment 459 updated: {c.rowcount} row(s) (enroll_date='2026-08-21', custom_end_date='2026-09-20').")

    # 2. Update Invoice 298 (linked to enrollment 459)
    c.execute("""
        UPDATE invoices
        SET issue_date = '2026-08-21',
            due_date = '2026-08-28'
        WHERE id = 298 AND enrollment_id = 459
    """)
    print(f"3. Invoice 298 updated: {c.rowcount} row(s) (issue_date='2026-08-21', due_date='2026-08-28').")

    # 3. Update Payment 484 (linked to enrollment 459)
    c.execute("""
        UPDATE payments
        SET date = '2026-08-21',
            note = 'Paiement Inscription Express (21/08/2026 - 20/09/2026)'
        WHERE id = 484 AND enrollment_id = 459
    """)
    print(f"4. Payment 484 updated: {c.rowcount} row(s) (date='2026-08-21').")

    # 4. Update Enrollment 460 (3rd period: 21/09/2026 -> 20/10/2026)
    notes_460 = "Renouvellement (1 mois) du 21/09/2026 au 20/10/2026 suite à l'inscription Nº 459"
    c.execute("""
        UPDATE enrollments
        SET enroll_date = '2026-09-21',
            custom_end_date = '2026-10-20',
            notes = ?
        WHERE id = 460 AND student_id = 112
    """, (notes_460,))
    print(f"5. Enrollment 460 updated: {c.rowcount} row(s) (enroll_date='2026-09-21', custom_end_date='2026-10-20').")

    # 5. Update Invoice 299 (linked to enrollment 460)
    c.execute("""
        UPDATE invoices
        SET issue_date = '2026-09-21',
            due_date = '2026-09-28'
        WHERE id = 299 AND enrollment_id = 460
    """)
    print(f"6. Invoice 299 updated: {c.rowcount} row(s) (issue_date='2026-09-21', due_date='2026-09-28').")

    # 6. Log activity
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'fix_subscription_ilas181', 
                'Correction abonnement ILAS181 (Mohamed Ouassiri): Inscription 459 ajustee au 21/08/2026 - 20/09/2026, Renouvellement 460 ajuste au 21/09/2026 - 20/10/2026', 
                datetime('now'))
    """)
    print("7. Activity log entry added.")

    conn.commit()
    print("=== TRANSACTION SUCCESSFULLY COMMITTED ===")

except Exception as ex:
    conn.rollback()
    print(f"ERROR: {ex}")
    sys.exit(1)
finally:
    conn.close()
