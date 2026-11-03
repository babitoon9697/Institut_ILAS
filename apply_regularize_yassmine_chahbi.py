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
backup_path = f"{backup_dir}/institut_backup_before_yassmine_chahbi_fix_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"1. Database successfully backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 1. Update Student 274 (YASSMINE CHAHBI)
    student_notes = (
        "Dossier régularisé le 29/10/2026 : Début le 01/10/2026 chez Mme Hakima EL BRIJ, "
        "arrêt pour raisons familiales le 10/10/2026 (105 DH scolarité consommés + 100 DH frais d'inscription). "
        "Reprise le 27/10/2026 chez Mme BOUCHRA LAHMIDI (Mardi-Jeudi-Vendredi 19:00-20:30) "
        "avec report du reliquat payé de 245 DH couvrant jusqu'au 15/11/2026 (9 séances). Tarif mensuel : 350 DH/mois."
    )
    c.execute("""
        UPDATE students
        SET notes = ?,
            credit_balance = 0.0,
            status = 'active'
        WHERE id = 274
    """, (student_notes,))
    print("2. Student 274 (Yassmine Chahbi) updated: notes, credit_balance=0.0, status='active'")

    # 2. Update Enrollment 499 (Mme Hakima EL BRIJ)
    notes_499 = (
        "Inscription 1 mois (350 DH/mois). Frais d'inscription: 100.0 DH. "
        "Présente du 01/10/2026 au 10/10/2026 chez Mme Hakima EL BRIJ (Mardi-Jeudi-Samedi). "
        "Arrêt pour raisons familiales le 10/10/2026 (Part scolarité consommée : 105.00 DH + Inscription 100.00 DH). "
        "Reliquat de 245.00 DH transféré vers le cours de Mme BOUCHRA LAHMIDI."
    )
    c.execute("""
        UPDATE enrollments
        SET enroll_date = '2026-10-01',
            custom_end_date = '2026-10-10',
            status = 'transferred',
            monthly_price = 350.0,
            calculated_price = 205.0,
            current_month_earned = 105.0,
            total_sessions_month = 4,
            attended_sessions_month = 4,
            deferred_amount = 0.0,
            notes = ?
        WHERE id = 499
    """, (notes_499,))
    print("3. Enrollment 499 (Hakima) updated: enroll_date=2026-10-01, end_date=2026-10-10, calc_price=205.0, earned=105.0")

    # 3. Update Enrollment 712 (Intermediate course 78 dropped)
    notes_712 = (
        "Inscription intermédiaire annulée - Arrêt de l'élève pour raisons familiales du 10/10/2026 au 26/10/2026 (aucune séance suivie)."
    )
    c.execute("""
        UPDATE enrollments
        SET status = 'dropped',
            custom_end_date = '2026-10-10',
            monthly_price = 0.0,
            calculated_price = 0.0,
            current_month_earned = 0.0,
            total_sessions_month = 0,
            attended_sessions_month = 0,
            deferred_amount = 0.0,
            notes = ?
        WHERE id = 712
    """, (notes_712,))
    print("4. Enrollment 712 (intermediate) marked as 'dropped': calculated_price=0.0")

    # 4. Update Enrollment 896 (Mme BOUCHRA LAHMIDI)
    notes_896 = (
        "Reprise le 27/10/2026 chez Mme BOUCHRA LAHMIDI - GROUPE 2 (Mardi-Jeudi-Vendredi 19:00-20:30) "
        "suite à interruption temporaire pour raisons familiales. "
        "Report du reliquat payé de 245.00 DH (sur cotisation mensuelle de 350.00 DH). "
        "Période couverte : 27/10/2026 au 15/11/2026 inclus (9 séances). "
        "Prochain renouvellement à partir du 16/11/2026 à 350.00 DH/mois."
    )
    c.execute("""
        UPDATE enrollments
        SET course_id = 18,
            enroll_date = '2026-10-27',
            custom_end_date = '2026-11-15',
            status = 'active',
            monthly_price = 350.0,
            calculated_price = 245.0,
            current_month_earned = 245.0,
            total_sessions_month = 9,
            attended_sessions_month = 0,
            deferred_amount = 0.0,
            notes = ?
        WHERE id = 896
    """, (notes_896,))
    print("5. Enrollment 896 (Bouchra) updated: enroll_date=2026-10-27, end_date=2026-11-15, calc_price=245.0, 9 sessions")

    # 5. Delete intermediate ghost invoice item 861 if exists
    c.execute("DELETE FROM invoice_items WHERE id = 861")
    print("6. Deleted ghost invoice item 861")

    # 6. Update Invoice Items for Invoice 329
    c.execute("""
        UPDATE invoice_items
        SET enrollment_id = 499,
            amount = 205.0,
            description = 'Français 3S/sem (1h30) GROUPE 2 (Prof. Hakima EL BRIJ) - Période du 01/10 au 10/10/2026 (Prorata 105.00 DH + Frais inscription 100.00 DH)'
        WHERE id = 566
    """)
    c.execute("""
        UPDATE invoice_items
        SET enrollment_id = 896,
            amount = 245.0,
            description = 'GROUPE 2: MARDI-JEUDI-VENDREDI (Prof. BOUCHRA LAHMIDI) - Reprise du 27/10 au 15/11/2026 (Report reliquat 245.00 DH - 9 séances)'
        WHERE id = 1135
    """)
    print("7. Invoice items 566 (205.0 DH) and 1135 (245.0 DH) updated")

    # 7. Update Invoice 329 header
    c.execute("""
        UPDATE invoices
        SET subtotal = 450.0,
            total = 450.0,
            status = 'paid'
        WHERE id = 329
    """)
    print("8. Invoice 329 header confirmed: total=450.0, status='paid'")

    # 8. Update Payments for Invoice 329
    c.execute("""
        UPDATE payments
        SET enrollment_id = 499,
            amount = 205.0,
            note = 'Paiement Inscription Express (Frais inscription 100 DH + Scolarité Mme Hakima EL BRIJ 105 DH)'
        WHERE id = 526
    """)
    c.execute("""
        UPDATE payments
        SET enrollment_id = 896,
            amount = 245.0,
            note = 'Report transfert vers GROUPE 2 Mme BOUCHRA LAHMIDI (Part 245.00 DH pour reprise le 27/10/2026)'
        WHERE id = 766
    """)
    print("9. Payments 526 (205.0 DH -> Enr 499) and 766 (245.0 DH -> Enr 896) confirmed")

    # 9. Add audit log
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'regularize_enrollment', ?, ?)
    """, (
        "Régularisation YASSMINE CHAHBI (ILAS360): Cours Hakima EL BRIJ du 01/10 au 10/10 (105 DH scolarité + 100 DH inscription). "
        "Arrêt familial 10/10 au 26/10. Reprise 27/10 chez Mme BOUCHRA LAHMIDI (Mardi-Jeudi-Vendredi) avec report 245 DH jusqu'au 15/11/2026. "
        "Tarif 350 DH/mois préservé. Solde dû: 0.00 DH.",
        now_str
    ))
    print("10. Audit log entry recorded")

    conn.commit()
    print("\n>>> ALL CHANGES SUCCESSFULLY COMMITTED! <<<")

except Exception as err:
    conn.rollback()
    print(f"\n[ERROR] Transaction failed, rolled back: {err}")
    raise
finally:
    conn.close()
