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
backup_path = f"{backup_dir}/institut_backup_before_ilas532_koach_fix_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"1. Database successfully backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 1. Update Student 413 (ILAS532)
    student_notes = (
        "Inscrit le 26/10/2026 en Français chez Mme Leila LOUTFI (Mercredi 17h-19h, Vendredi 19h-20h30, Samedi 10h-12h). "
        "Début des cours le 01/11/2026 pour un pack trimestriel de 3 mois (du 01/11/2026 au 31/01/2027). "
        "Règlement complet effectué le 26/10/2026 : 1000 DH (900 DH scolarité 3 mois + 100 DH frais d'inscription - Reçu REC-0858)."
    )
    c.execute("""
        UPDATE students
        SET first_name = 'Koach',
            last_name = 'Abdillah',
            notes = ?,
            credit_balance = 0.0,
            status = 'active'
        WHERE id = 413
    """, (student_notes,))
    print("2. Student 413 (ILAS532 - Koach Abdillah) updated.")

    # 2. Update Enrollment 855
    enroll_notes = (
        "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 100.0 DH. "
        "Début le 01/11/2026 chez Mme LEILA LOUTFI (Mercredi, Vendredi, Samedi). "
        "Période: 01/11/2026 au 31/01/2027 (3 mois). Scolarité: 900.0 DH (300 DH/mois) + Frais d'inscription: 100.0 DH. "
        "Règlement effectué le 26/10/2026 (Reçu REC-0858: 1000 DH)."
    )
    c.execute("""
        UPDATE enrollments
        SET enroll_date = '2026-11-01',
            custom_end_date = '2027-01-31',
            payment_plan = '3months',
            monthly_price = 300.0,
            calculated_price = 1000.0,
            total_sessions_month = 39,
            attended_sessions_month = 39,
            current_month_earned = 276.92,
            deferred_amount = 623.08,
            status = 'active',
            notes = ?
        WHERE id = 855
    """, (enroll_notes,))
    print("3. Enrollment 855 updated: enroll_date=2026-11-01, custom_end_date=2027-01-31, calc_price=1000.0, monthly_price=300.0, earned=276.92, deferred=623.08.")

    # 3. Update Invoice 593 & Invoice Items
    c.execute("""
        UPDATE invoices
        SET subtotal = 1000.0,
            total = 1000.0,
            status = 'paid',
            issue_date = '2026-10-26'
        WHERE id = 593
    """)
    print("4. Invoice 593 updated: total=1000.0, status='paid'.")

    # Update line item 1084 (tuition)
    c.execute("""
        UPDATE invoice_items
        SET amount = 900.0,
            description = 'Français 3S/sem (2h-2h-1h30) G1 MERCREDI (17:00-19:00) VENDREDI (19:00-20:30) SAMEDI (10:00-12:00) (Scolarité (3 mois))'
        WHERE id = 1084
    """)
    print("5. Invoice item 1084 updated to 900.0 DH (Scolarité 3 mois).")

    # Check if registration fee item exists for invoice 593
    c.execute("SELECT id FROM invoice_items WHERE invoice_id = 593 AND description LIKE '%Frais d''inscription%'")
    reg_item = c.fetchone()
    if reg_item:
        c.execute("""
            UPDATE invoice_items
            SET amount = 100.0,
                enrollment_id = 855
            WHERE id = ?
        """, (reg_item[0],))
        print(f"6. Existing registration fee item {reg_item[0]} updated to 100.0 DH.")
    else:
        c.execute("""
            INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
            VALUES (593, 855, 'Frais d''inscription - Français 3S/sem (2h-2h-1h30) G1 MERCREDI (17:00-19:00) VENDREDI (19:00-20:30) SAMEDI (10:00-12:00)', 100.0)
        """)
        print("6. Created registration fee item: 100.0 DH.")

    # 4. Update Payment 948
    c.execute("""
        UPDATE payments
        SET amount = 1000.0,
            date = '2026-10-26',
            note = 'Paiement Inscription Express (Scolarité 3 mois: 900 DH + Frais d''inscription: 100 DH)'
        WHERE id = 948
    """)
    print("7. Payment 948 updated: amount=1000.0, date='2026-10-26'.")

    # 5. Log activity
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_fix', 'Correction inscription ILAS532 (Koach Abdillah): 3 mois 900 DH + 100 DH frais inscription (01/11/2026 - 31/01/2027 chez Mme Leila Loutfi)', datetime('now'))
    """)
    print("8. Activity log entry added.")

    conn.commit()
    print("=== TRANSACTION SUCCESSFULLY COMMITTED ===")

except Exception as ex:
    conn.rollback()
    print(f"ERROR: {ex}")
    sys.exit(1)
finally:
    conn.close()
