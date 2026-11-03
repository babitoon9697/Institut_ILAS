import sqlite3
import shutil
import datetime
import os

# 1. Create a safe backup first
db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_ilas334_transfer_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"Database backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 2. Update Student: level to 'Tronc Commun' and credit_balance to 50.0 DH
    c.execute("""
        UPDATE students
        SET school_level = 'Tronc Commun',
            credit_balance = 50.0
        WHERE id = 250
    """)
    print("1. Student 250 updated: school_level='Tronc Commun', credit_balance=50.0")

    # 3. Cancel / Drop Enrollment 578 (Anglais - Nordine Bougrir)
    c.execute("""
        UPDATE enrollments
        SET status = 'dropped',
            calculated_price = 0.0,
            monthly_price = 0.0,
            custom_end_date = '2026-10-01',
            notes = coalesce(notes, '') || ' | Inscription annulée le 22/10/2026. Paiement de 350.0 DH transféré vers TC Maths (150 DH), TC PC (150 DH) et 50 DH solde créditeur.'
        WHERE id = 578
    """)
    print("2. Enrollment 578 marked as 'dropped'")

    # 4. Update Enrollment 439 (Soutien TC - Maths - Hamza Boubtana) to 2 months (300.0 DH)
    notes_439 = "Inscription Express (2 mois). Durée: 2 mois. Frais: 150 DH/mois. Frais d'inscription: 0.0 DH. Transfert paiement Anglais (150 DH) vers TC Maths (Prof. HAMZA BOUBTANA)."
    c.execute("""
        UPDATE enrollments
        SET custom_end_date = '2026-11-30',
            monthly_price = 150.0,
            calculated_price = 300.0,
            total_sessions_month = 18,
            attended_sessions_month = 18,
            current_month_earned = 150.0,
            deferred_amount = 150.0,
            notes = ?
        WHERE id = 439
    """, (notes_439,))
    print("3. Enrollment 439 updated to 2 months (300 DH, ending 2026-11-30)")

    # 5. Update Enrollment 440 (Soutien TC - Physique Chimie - Tarik Radid) to 2 months (300.0 DH)
    notes_440 = "Inscription Express (2 mois). Durée: 2 mois. Frais: 150 DH/mois. Frais d'inscription: 0.0 DH. Transfert paiement Anglais (150 DH) vers TC PC (Prof. TARIK RADID)."
    c.execute("""
        UPDATE enrollments
        SET custom_end_date = '2026-11-30',
            monthly_price = 150.0,
            calculated_price = 300.0,
            total_sessions_month = 18,
            attended_sessions_month = 18,
            current_month_earned = 150.0,
            deferred_amount = 150.0,
            notes = ?
        WHERE id = 440
    """, (notes_440,))
    print("4. Enrollment 440 updated to 2 months (300 DH, ending 2026-11-30)")

    # 6. Reassign Payment 464 to Enrollment 439 (Maths - 150 DH)
    c.execute("""
        UPDATE payments
        SET enrollment_id = 439,
            amount = 150.0,
            note = 'Paiement transféré d''Anglais vers Soutien TC - Maths (Mois 2 / Novembre - Prof. HAMZA BOUBTANA)'
        WHERE id = 464
    """)
    print("5. Payment 464 reassigned to Enrollment 439 (amount=150 DH)")

    # 7. Insert new payment row for Enrollment 440 (PC - 150 DH)
    c.execute("""
        INSERT INTO payments (receipt, enrollment_id, student_id, amount, method, date, note, invoice_id, recorded_by, created_at)
        VALUES ('REC-0424-TR', 440, 250, 150.0, 'cash', '2026-09-28', 'Paiement transféré d''Anglais vers Soutien TC - PC (Mois 2 / Novembre - Prof. TARIK RADID)', 283, 5, '2026-09-28 18:29:54.377470')
    """)
    new_payment_id = c.lastrowid
    print(f"6. Inserted Payment {new_payment_id} for Enrollment 440 (amount=150 DH)")

    # 8. Update Invoice 283 and its items
    c.execute("""
        UPDATE invoice_items
        SET enrollment_id = 439,
            amount = 150.0,
            description = 'Soutien TC - Maths (Mois 2 Novembre - Transféré d''Anglais - Prof. HAMZA BOUBTANA)'
        WHERE id = 673
    """)
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (283, 440, 'Soutien TC - Physique Chimie (Mois 2 Novembre - Transféré d''Anglais - Prof. TARIK RADID)', 150.0)
    """)
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (283, NULL, 'Solde créditeur conservé sur compte élève suite transfert d''Anglais', 50.0)
    """)
    c.execute("""
        UPDATE invoices
        SET notes = 'Transfert de paiement: 150 DH vers TC Maths, 150 DH vers TC PC, 50 DH solde créditeur élève'
        WHERE id = 283
    """)
    print("7. Invoice 283 items and notes updated")

    # 9. Record student credit
    c.execute("""
        INSERT INTO student_credits (student_id, enrollment_id, amount, type, note, created_at)
        VALUES (250, NULL, 50.0, 'credit', 'Reliquat transfert paiement Anglais (350 DH) vers TC Maths (150 DH) et TC PC (150 DH)', datetime('now'))
    """)
    print("8. Recorded student credit in student_credits")

    # 10. Clean up attendances in dropped English course
    c.execute("DELETE FROM attendances WHERE student_id = 250 AND course_id IN (10, 45)")
    print(f"9. Cleaned up {c.rowcount} attendance record(s) in dropped English classes")

    # 11. Log activity in activity_log
    log_detail = "Annulation inscription RABIA ALAA (ILAS334) en Anglais (Nordine Bougrir). Paiement de 350 DH transféré vers TC Maths (Hamza Boubtana: 150 DH) et TC PC (Tarik Radid: 150 DH) pour solder 2 mois (Octobre et Novembre jusqu'au 30/11/2026). Reliquat de 50 DH crédité sur le compte élève. Total payé TC: 600 DH (300 DH Maths + 300 DH PC)."
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_transfer', ?, ?)
    """, (log_detail, now_str))
    print("10. Inserted activity log")

    conn.commit()
    print("\nALL CHANGES SUCCESSFULLY COMMITTED TO institut.db!")

except Exception as e:
    conn.rollback()
    print("ERROR, rolled back:", e)
    raise
finally:
    conn.close()
