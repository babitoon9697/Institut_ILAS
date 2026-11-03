# -*- coding: utf-8 -*-
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
backup_path = f"{backup_dir}/institut_backup_before_marwa_bitar_transfer_exact_{timestamp}.db"

# 1. Sauvegarde préventive
shutil.copy2(db_path, backup_path)
print(f"[OK] Sauvegarde créée : {backup_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    student_id = 254
    course_hamza_id = 8   # Anglais 3S/sem (1h30) groupe1 /lundi-mercredi-19:00-20:30jeudi-18:30-20:00 (Prof. HAMZA EL MOTAKI)
    course_nordine_id = 45 # Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE LUNDI-MERCREDI-VENDREDI 19:00/20:30 (Prof. NORDINE BOUGRIR)

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # 1. Vérification de l'élève
    c.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu = c.fetchone()
    if not stu:
        raise Exception(f"Élève avec id {student_id} introuvable !")
    print(f"[OK] Élève trouvé : {stu['first_name']} {stu['last_name']} ({stu['code']})")

    # 2. Nettoyage des anciennes inscriptions de Marwa Bitar pour repartir sur une base propre
    c.execute("DELETE FROM enrollments WHERE student_id = ?", (student_id,))
    print(f"[OK] Anciennes inscriptions nettoyées : {c.rowcount}")

    # 3. Inscription 1 : Chez Prof. HAMZA EL MOTAKI (du 29/09/2026 au 31/10/2026 - Transféré)
    notes_hamza = (
        "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 100.0 DH. "
        "A étudié chez Prof. HAMZA EL MOTAKI du 29/09/2026 au 31/10/2026 (Part Octobre: 383.33 DH + Inscription: 100.00 DH = 483.33 DH). | "
        "Transféré vers 'Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE LUNDI-MERCREDI-VENDREDI 19:00/20:30' le 01/11/2026."
    )
    c.execute("""
        INSERT INTO enrollments (
            student_id, course_id, enroll_date, payment_plan, status,
            total_sessions_month, attended_sessions_month, monthly_price, calculated_price,
            current_month_earned, deferred_amount, notes, created_at,
            custom_end_date, tariff_id, created_by
        ) VALUES (?, ?, '2026-09-29', 'monthly', 'transferred',
                  14, 2, 383.33, 483.33,
                  383.33, 0.0, ?, ?,
                  '2026-10-31', NULL, 1)
    """, (student_id, course_hamza_id, notes_hamza, now_str))
    eid_hamza = c.lastrowid
    print(f"[OK] Inscription 1 créée (Prof. Hamza, 29/09 -> 31/10, transféré) : ID #{eid_hamza}")

    # 4. Inscription 2 : Chez Prof. NORDINE BOUGRIR (du 01/11/2026 au 29/12/2026 - Actif)
    notes_nordine = (
        "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 100.0 DH. "
        "Transféré depuis 'Anglais 3S/sem (1h30) groupe1' le 01/11/2026. "
        "Période active chez Prof. NORDINE BOUGRIR du 01/11/2026 au 29/12/2026 (Part restante: 766.67 DH pour 2 mois)."
    )
    c.execute("""
        INSERT INTO enrollments (
            student_id, course_id, enroll_date, payment_plan, status,
            total_sessions_month, attended_sessions_month, monthly_price, calculated_price,
            current_month_earned, deferred_amount, notes, created_at,
            custom_end_date, tariff_id, created_by
        ) VALUES (?, ?, '2026-11-01', 'monthly', 'active',
                  25, 0, 383.33, 766.67,
                  383.33, 383.34, ?, ?,
                  '2026-12-29', NULL, 1)
    """, (student_id, course_nordine_id, notes_nordine, now_str))
    eid_nordine = c.lastrowid
    print(f"[OK] Inscription 2 créée (Prof. Nordine, 01/11 -> 29/12, actif) : ID #{eid_nordine}")

    # 5. Nettoyage des paiements existants pour Marwa Bitar
    c.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
    print(f"[OK] Anciens paiements nettoyés : {c.rowcount}")

    # 6. Création des 2 lignes de paiement partageant le même reçu REC-0480 (1250 DH au total)
    # Ligne 1 : rattachée à l'inscription de Hamza (483.33 DH)
    c.execute("""
        INSERT INTO payments (
            receipt, enrollment_id, student_id, amount, method, date, note, invoice_id, recorded_by, created_at
        ) VALUES ('REC-0480', ?, ?, 483.33, 'cash', '2026-09-29', 'Paiement Inscription Express (Part Hamza 383.33 DH + Inscription 100 DH)', 328, 1, ?)
    """, (eid_hamza, student_id, now_str))
    pay_id_1 = c.lastrowid

    # Ligne 2 : rattachée à l'inscription de Nordine (766.67 DH)
    c.execute("""
        INSERT INTO payments (
            receipt, enrollment_id, student_id, amount, method, date, note, invoice_id, recorded_by, created_at
        ) VALUES ('REC-0480', ?, ?, 766.67, 'cash', '2026-09-29', 'Report transfert (Part Nordine 766.67 DH du 01/11 au 29/12)', 328, 1, ?)
    """, (eid_nordine, student_id, now_str))
    pay_id_2 = c.lastrowid
    print(f"[OK] 2 lignes de paiement unifiées sous REC-0480 créées : #{pay_id_1} (483.33 DH) et #{pay_id_2} (766.67 DH) -> Total: 1250.00 DH")

    # 7. Mise à jour de la Facture #328 (FA-0413)
    c.execute("""
        UPDATE invoices
        SET enrollment_id = ?,
            subtotal = 1250.0,
            tva_rate = 0.0,
            tva_amount = 0.0,
            total = 1250.0,
            status = 'paid',
            notes = 'Facture Inscription Trimestrielle avec transfert au 01/11/2026'
        WHERE id = 328 AND student_id = ?
    """, (eid_nordine, student_id))
    print(f"[OK] Facture #328 mise à jour rattachée à l'inscription active #{eid_nordine}")

    # 8. Mise à jour des lignes de facture (Invoice Items)
    c.execute("DELETE FROM invoice_items WHERE invoice_id = 328")
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (328, ?, 'Anglais 3S/sem (1h30) Groupe 1 Prof. HAMZA EL MOTAKI (Scolarité du 29/09 au 31/10)', 383.33)
    """, (eid_hamza,))
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (328, ?, 'Anglais 3S/sem (1h30) GROUPE 2 Prof. NORDINE BOUGRIR (Scolarité du 01/11 au 29/12)', 766.67)
    """, (eid_nordine,))
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (328, ?, "Frais d'inscription", 100.0)
    """, (eid_hamza,))
    print(f"[OK] Lignes de facture créées : 383.33 DH + 766.67 DH + 100.00 DH = 1250.00 DH")

    # 9. Rétablissement du cours des présences d'octobre vers Course 8 (Hamza)
    c.execute("""
        UPDATE attendances
        SET course_id = ?
        WHERE student_id = ? AND date <= '2026-10-31'
    """, (course_hamza_id, student_id))
    print(f"[OK] Présences d'octobre vérifiées et associées au cours de Prof. Hamza : {c.rowcount}")

    # 10. Mise à jour de la fiche élève
    stu_note = (
        "Inscrite le 29/09/2026 (forfait trimestriel 1250 DH réglé par reçu REC-0480). "
        "A suivi ses cours chez Prof. HAMZA EL MOTAKI du 29/09/2026 au 31/10/2026. "
        "Transférée le 01/11/2026 chez Prof. NORDINE BOUGRIR (Lundi-Mercredi-Vendredi 19:00-20:30) jusqu'au 29/12/2026."
    )
    c.execute("""
        UPDATE students
        SET status = 'active',
            credit_balance = 0.0,
            notes = ?
        WHERE id = ?
    """, (stu_note, student_id))
    print(f"[OK] Fiche élève mise à jour")

    # 11. Journalisation dans activity_log
    log_detail = (
        f"Configuration exacte transfert MARWA BITAR (ILAS338) : "
        f"Prof. Hamza (du 29/09 au 31/10 - transféré, part 483.33 DH) -> "
        f"Prof. Nordine (du 01/11 au 29/12 - actif, part 766.67 DH). "
        f"Reçu REC-0480 et Facture FA-0413 réglés à 1250.00 DH (Solde: 0 DH)."
    )
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_transfer_exact', ?, ?)
    """, (log_detail, now_str))
    print(f"[OK] Journal d'activité inséré")

    conn.commit()
    print("\n>>> CONFIGURATION EXACTE DU TRANSFERT ENREGISTRÉE AVEC SUCCÈS ! <<<")

except Exception as e:
    conn.rollback()
    print(f"\n[ERREUR] Transaction annulée : {e}")
    sys.exit(1)
finally:
    conn.close()
