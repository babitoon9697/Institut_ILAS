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
backup_path = f"{backup_dir}/institut_backup_before_marwa_bitar_fix_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"1. Database successfully backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 1. Update Enrollment 498 (Hamza El Motaki - transferred)
    notes_498 = (
        "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 100.0 DH. | "
        "Transféré vers 'Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE LUNDI-MERCREDI-VENDREDI 19:00/20:30' "
        "le 03/11/2026 (Part Hamza: 450.00 DH + Frais inscription: 100.00 DH = 550.00 DH)"
    )
    c.execute("""
        UPDATE enrollments
        SET calculated_price = 550.0,
            monthly_price = 383.33,
            current_month_earned = 450.0,
            deferred_amount = 0.0,
            custom_end_date = '2026-11-03',
            notes = ?
        WHERE id = 498
    """, (notes_498,))
    print("2. Enrollment #498 updated: calculated_price=550.0 DH, current_month_earned=450.0 DH")

    # 2. Update Enrollment 1003 (Nordine Bougrir - active)
    notes_1003 = (
        "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 100.0 DH. | "
        "Transféré depuis 'Anglais 3S/sem (1h30) groupe1 /lundi-mercredi-19:00-20:30jeudi-18:30-20:00' "
        "le 03/11/2026 (Part Nordine: 700.00 DH)"
    )
    c.execute("""
        UPDATE enrollments
        SET calculated_price = 700.0,
            monthly_price = 383.33,
            current_month_earned = 383.33,
            deferred_amount = 316.67,
            custom_end_date = '2026-12-29',
            notes = ?
        WHERE id = 1003
    """, (notes_1003,))
    print("3. Enrollment #1003 updated: calculated_price=700.0 DH, custom_end_date='2026-12-29'")

    # 3. Update Payment 525 (REC-0480) for Enrollment 498
    c.execute("""
        UPDATE payments
        SET amount = 550.0,
            note = 'Paiement Inscription Express (Part Hamza 450 DH + Inscription 100 DH)'
        WHERE id = 525
    """)
    print("4. Payment #525 updated: amount=550.0 DH")

    # 4. Check if split payment REC-0480-TR already exists, if not insert it
    c.execute("SELECT id FROM payments WHERE receipt = 'REC-0480-TR'")
    existing_tr = c.fetchone()
    if existing_tr:
        c.execute("""
            UPDATE payments
            SET amount = 700.0,
                enrollment_id = 1003,
                student_id = 254,
                invoice_id = 328
            WHERE id = ?
        """, (existing_tr[0],))
        print(f"5. Existing split payment #{existing_tr[0]} updated to 700.0 DH")
    else:
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("""
            INSERT INTO payments (receipt, enrollment_id, student_id, amount, method, date, note, invoice_id, recorded_by, created_at)
            VALUES ('REC-0480-TR', 1003, 254, 700.0, 'cash', '2026-09-29', 'Report transfert (Part 700.00 DH suite transfert vers Anglais GROUPE 2 PROF NORDINE)', 328, 1, ?)
        """, (now_str,))
        print("5. Created split payment REC-0480-TR: 700.0 DH for Enrollment #1003")

    # 5. Update Invoice Items for Invoice 328
    c.execute("""
        UPDATE invoice_items
        SET amount = 550.0,
            description = "Anglais 3S/sem (1h30) groupe1 /lundi-mercredi-19:00-20:30jeudi-18:30-20:00 (Scolarité au prorata jusqu'au 03/11 + Frais d'inscription)"
        WHERE id = 564
    """)
    c.execute("""
        UPDATE invoice_items
        SET amount = 700.0,
            description = "Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE LUNDI-MERCREDI-VENDREDI 19:00/20:30 (Scolarité au prorata à partir du 03/11)"
        WHERE id = 1270
    """)
    print("6. Invoice items updated: #564=550.0 DH, #1270=700.0 DH (Total=1250.0 DH)")

    # 6. Log the fix in activity_log
    log_detail = "Régularisation financière Marwa Bitar (ILAS338) suite transfert: 550.0 DH sur #498 (Hamza + frais) et 700.0 DH sur #1003 (Nordine), solde = 0.0 DH, fin au 29/12/2026"
    now_log = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_fix', ?, ?)
    """, (log_detail, now_log))
    print("7. Action logged in activity_log")

    conn.commit()
    print("\n>>> TOUTES LES MODIFICATIONS ONT ÉTÉ APPLIQUÉES AVEC SUCCÈS ! <<<")

except Exception as err:
    conn.rollback()
    print(f"\n[ERREUR] Rollback effectué : {err}")
    sys.exit(1)
finally:
    conn.close()
