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
backup_path = f"{backup_dir}/institut_backup_before_marwa_bitar_re-enrollment_{timestamp}.db"

# 1. Sauvegarde préventive
shutil.copy2(db_path, backup_path)
print(f"[OK] Sauvegarde créée : {backup_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    student_id = 254
    course_id = 45 # Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE LUNDI-MERCREDI-VENDREDI 19:00/20:30
    start_date_str = '2026-09-29'
    end_date_str = '2026-12-29'
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # 1. Vérification de l'élève
    c.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu = c.fetchone()
    if not stu:
        raise Exception(f"Élève avec id {student_id} introuvable !")
    print(f"[OK] Élève trouvé : {stu['first_name']} {stu['last_name']} ({stu['code']})")

    # 2. Suppression du paiement fractionné de transfert #1108 (REC-0480-TR)
    c.execute("DELETE FROM payments WHERE receipt = 'REC-0480-TR' AND student_id = ?", (student_id,))
    print(f"[OK] Paiement de transfert temporaire REC-0480-TR supprimé : {c.rowcount}")

    # 3. Nettoyage des anciennes lignes de la facture #328
    c.execute("DELETE FROM invoice_items WHERE invoice_id = 328")
    print(f"[OK] Anciennes lignes de facture supprimées : {c.rowcount}")

    # 4. Suppression des anciennes inscriptions fragmentées (#498 et #1003)
    c.execute("DELETE FROM enrollments WHERE id IN (498, 1003) AND student_id = ?", (student_id,))
    print(f"[OK] Anciennes inscriptions fragmentées (#498, #1003) supprimées : {c.rowcount}")

    # 5. Création de la NOUVELLE inscription propre (Course 45 - Prof Nordine Bougrir)
    notes_enrollment = (
        "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 100.0 DH. Scolarité: 1150.0 DH. "
        "Affectée à GROUPE 2 (Prof. NORDINE BOUGRIR) avec maintien de la date de début au 29/09/2026."
    )
    c.execute("""
        INSERT INTO enrollments (
            student_id, course_id, enroll_date, payment_plan, status,
            total_sessions_month, attended_sessions_month, monthly_price, calculated_price,
            current_month_earned, deferred_amount, notes, created_at,
            custom_end_date, tariff_id, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
    """, (
        student_id, course_id, start_date_str, '3months', 'active',
        39, 2, 383.33, 1250.0,
        383.33, 766.67, notes_enrollment, now_str,
        end_date_str, 1
    ))
    new_enrollment_id = c.lastrowid
    print(f"[OK] Nouvelle inscription propre créée : ID #{new_enrollment_id}")

    # 6. Mise à jour de la Facture #328 (FA-0413) rattachée à la nouvelle inscription
    c.execute("""
        UPDATE invoices
        SET enrollment_id = ?,
            subtotal = 1250.0,
            tva_rate = 0.0,
            tva_amount = 0.0,
            total = 1250.0,
            status = 'paid',
            notes = 'Facture Inscription Trimestrielle — Anglais GROUPE 2 (Prof. NORDINE BOUGRIR)'
        WHERE id = 328 AND student_id = ?
    """, (new_enrollment_id, student_id))
    print(f"[OK] Facture #328 (FA-0413) mise à jour : {c.rowcount}")

    # 7. Création des lignes de facture propres pour FA-0413
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (328, ?, 'Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE (Scolarité 3 mois du 29/09/2026 au 29/12/2026)', 1150.0)
    """, (new_enrollment_id,))
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (328, ?, "Frais d'inscription", 100.0)
    """, (new_enrollment_id,))
    print(f"[OK] 2 lignes de facture propres insérées (Total: 1250.00 DH)")

    # 8. Mise à jour du Paiement #525 (REC-0480) à 1 250.00 DH rattaché à la nouvelle inscription
    c.execute("""
        UPDATE payments
        SET enrollment_id = ?,
            amount = 1250.0,
            date = '2026-09-29',
            method = 'cash',
            note = 'Paiement Inscription Express (1150 DH scolarité 3 mois + 100 DH frais d''inscription)',
            invoice_id = 328
        WHERE id = 525 AND student_id = ?
    """, (new_enrollment_id, student_id))
    print(f"[OK] Paiement unique #525 (REC-0480) rétabli à 1250.00 DH : {c.rowcount}")

    # 9. Mise à jour du dossier élève (notes, statut actif, solde 0)
    stu_note = (
        "Inscrite le 29/09/2026 en Anglais (GROUPE 2 Prof. Nordine BOUGRIR) pour 3 mois jusqu'au 29/12/2026. "
        "Forfait 1250 DH réglé en totalité par reçu REC-0480 (1150 DH scolarité + 100 DH frais d'inscription)."
    )
    c.execute("""
        UPDATE students
        SET status = 'active',
            credit_balance = 0.0,
            notes = ?
        WHERE id = ?
    """, (stu_note, student_id))
    print(f"[OK] Fiche élève mise à jour : {c.rowcount}")

    # 10. Journalisation dans activity_log
    log_detail = (
        f"Réinscription propre de MARWA BITAR (ILAS338) dans le GROUPE 2 de M. NORDINE BOUGRIR "
        f"(Lundi-Mercredi-Vendredi 19:00-20:30) pour 3 mois (du 29/09/2026 au 29/12/2026). "
        f"Nouvelle inscription #{new_enrollment_id}, Facture FA-0413 et reçu REC-0480 réglés à 1250.00 DH."
    )
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'enrollment_recreate', ?, ?)
    """, (log_detail, now_str))
    print(f"[OK] Journal d'activité inséré")

    conn.commit()
    print("\n>>> TOUTES LES MODIFICATIONS ONT ÉTÉ ENREGISTRÉES AVEC SUCCÈS DANS institut.db ! <<<")

except Exception as e:
    conn.rollback()
    print(f"\n[ERREUR] Transaction annulée : {e}")
    sys.exit(1)
finally:
    conn.close()
