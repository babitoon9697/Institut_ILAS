# -*- coding: utf-8 -*-
import sqlite3
import shutil
import datetime
import os
import sys

db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_rayan_smoui_re-enrollment_{timestamp}.db"

# 1. Sauvegarde préventive
shutil.copy2(db_path, backup_path)
print(f"[OK] Sauvegarde cree : {backup_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    student_id = 407
    course_id = 18
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    today_str = '2026-10-29'
    end_date_str = '2026-11-29'

    # Vérification élève
    c.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu = c.fetchone()
    if not stu:
        raise Exception(f"Eleve avec id {student_id} introuvable !")
    print(f"[OK] Eleve trouve : {stu['first_name']} {stu['last_name']} ({stu['code']})")

    # 1. Nettoyage des anciennes lignes de facture erronées
    c.execute("DELETE FROM invoice_items WHERE invoice_id = 586")
    print(f"[OK] Lignes de facture supprimees : {c.rowcount}")

    # 2. Suppression du paiement fractionné temporaire de transfert #991
    c.execute("DELETE FROM payments WHERE id = 991 AND student_id = ?", (student_id,))
    print(f"[OK] Paiement de transfert temporaire (#991) supprime : {c.rowcount}")

    # 3. Suppression définitive des inscriptions annulées/erronées #844 et #894
    c.execute("DELETE FROM enrollments WHERE id IN (844, 894) AND student_id = ?", (student_id,))
    print(f"[OK] Inscriptions erronées (#844, #894) supprimees definitivement : {c.rowcount}")

    # 4. Nettoyage éventuel des présences résiduelles pour cet élève
    c.execute("DELETE FROM attendances WHERE student_id = ?", (student_id,))
    print(f"[OK] Presences nettoyees : {c.rowcount}")

    # 5. Création de la NOUVELLE inscription propre chez Madame Bouchra (Course 18)
    notes_enrollment = (
        "Réinscription officielle — Cours de Français (GROUPE 2 : Mardi - Jeudi - Vendredi 19:00 - 20:30) "
        "chez Mme BOUCHRA LAHMIDI. Tarif convenu : 350.00 DH/mois. Paiement réglé en totalité par reçu REC-0849."
    )
    c.execute("""
        INSERT INTO enrollments (
            student_id, course_id, enroll_date, payment_plan, status,
            total_sessions_month, attended_sessions_month, monthly_price, calculated_price,
            current_month_earned, deferred_amount, notes, created_at,
            custom_end_date, tariff_id, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
    """, (
        student_id, course_id, today_str, 'monthly', 'active',
        14, 0, 350.0, 350.0,
        350.0, 0.0, notes_enrollment, now_str,
        end_date_str, 33
    ))
    new_enrollment_id = c.lastrowid
    print(f"[OK] Nouvelle inscription creee avec succes : ID #{new_enrollment_id}")

    # 6. Mise à jour de la facture 586 (FA-0698)
    c.execute("""
        UPDATE invoices
        SET enrollment_id = ?,
            subtotal = 350.0,
            tva_rate = 0.0,
            tva_amount = 0.0,
            total = 350.0,
            status = 'paid',
            notes = 'Facture réinscription — GROUPE 2 Mme BOUCHRA LAHMIDI (350 DH/mois)'
        WHERE id = 586 AND student_id = ?
    """, (new_enrollment_id, student_id))
    print(f"[OK] Facture #586 (FA-0698) mise a jour (350.00 DH, payée) : {c.rowcount}")

    # 7. Création de la ligne de facture propre pour Course 18
    item_desc = "GROUPE 2: MARDI-JEUDI-VENDREDI(19:00 - 20:30) ADULT A1-A2 (Scolarité 1 mois)"
    c.execute("""
        INSERT INTO invoice_items (invoice_id, enrollment_id, description, amount)
        VALUES (586, ?, ?, 350.0)
    """, (new_enrollment_id, item_desc))
    print(f"[OK] Ligne de facture creee : ID #{c.lastrowid}")

    # 8. Mise à jour du Paiement 935 (REC-0849) à 350.00 DH rattaché à la nouvelle inscription
    c.execute("""
        UPDATE payments
        SET enrollment_id = ?,
            amount = 350.0,
            note = 'Paiement Réinscription — GROUPE 2 (Mme BOUCHRA LAHMIDI)',
            invoice_id = 586
        WHERE id = 935 AND student_id = ?
    """, (new_enrollment_id, student_id))
    print(f"[OK] Paiement #935 (REC-0849) mis a jour a 350.00 DH : {c.rowcount}")

    # 9. Mise à jour du dossier élève (notes, statut actif, solde 0)
    stu_note = (
        "[Réinscription le 29/10/2026 : Inscription chez Mme Bouchra LAHMIDI "
        "(GROUPE 2: Mardi-Jeudi-Vendredi 19:00-20:30) au tarif de 350 DH/mois réglée par reçu REC-0849 (350 DH). "
        "Anciennes inscriptions erronées annulées définitivement]."
    )
    c.execute("""
        UPDATE students
        SET status = 'active',
            credit_balance = 0.0,
            notes = ?
        WHERE id = ?
    """, (stu_note, student_id))
    print(f"[OK] Fiche eleve mise a jour : {c.rowcount}")

    # 10. Mise à jour test de positionnement si applicable
    c.execute("""
        UPDATE placement_tests
        SET enrolled_student_id = ?,
            enrolled_course_id = ?,
            status = 'completed'
        WHERE id = 52
    """, (student_id, course_id))
    print(f"[OK] Test de positionnement mis a jour : {c.rowcount}")

    # 11. Journalisation dans activity_log
    log_detail = (
        f"Annulation définitive de l'inscription erronée de RAYAN ISMOUI (ILAS526) et réinscription propre "
        f"dans le GROUPE 2 de Mme BOUCHRA LAHMIDI (Mardi-Jeudi-Vendredi 19:00-20:30) à 350 DH/mois. "
        f"Nouvelle inscription #{new_enrollment_id}, Facture FA-0698 et reçu REC-0849 réglés à 350.00 DH."
    )
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (33, 'enrollment_recreate', ?, ?)
    """, (log_detail, now_str))
    print(f"[OK] Journal d'activite insere")

    conn.commit()
    print("\n>>> TOUTES LES MODIFICATIONS ONT ÉTÉ ENREGISTRÉES AVEC SUCCÈS DANS institut.db ! <<<")

except Exception as e:
    conn.rollback()
    print(f"\n[ERREUR] Transaction annulee : {e}")
    raise
finally:
    conn.close()
