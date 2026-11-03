# -*- coding: utf-8 -*-
"""
Script de correction du renouvellement pour RAIHANA LAAZIZI (ILAS263, ID 184).
- Français Régional (Course 27) : Déjà renouvelé sous l'inscription #858 (170 DH, payé REC-0860, fin 24/11/2026).
- Maths (Course 24) : Correction de l'inscription erronée #861 (qui avait été saisie en doublon sur le français)
  vers le cours de Maths #24, prix 170 DH, payé (REC-0863 / FA-0710), fin d'abonnement au 24/11/2026.
- Physique-Chimie (Course 28) : Création du renouvellement pour PC #28, prix 170 DH, payé (REC-0869 / FA-0716),
  fin d'abonnement au 24/11/2026.
- Les inscriptions initiales (#319 Maths et #320 PC) sont passées à l'état 'completed'.
"""

import shutil
import sqlite3
import datetime
import os

DB_PATH = 'institut.db'
BACKUP_DIR = 'backups'

os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_filename = os.path.join(BACKUP_DIR, f"institut_backup_before_raihana_laazizi_renew_{timestamp}.db")

# 1. Sauvegarde préventive de la base de données
shutil.copy2(DB_PATH, backup_filename)
print(f"[OK] Sauvegarde créée : {backup_filename}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ID de l'élève
STUDENT_ID = 184

# ID des cours
COURSE_MATHS = 24
COURSE_FR = 27
COURSE_PC = 28

MATHS_NAME = "Soutien 1 BAC SX - Maths  mercredi  et 20:30-22:00 vendredi 19:00-20:30"
PC_NAME = "Soutien 1 BAC SX - Physique Chimie (PC)MARDI 20:30/22:00 - SAMEDI- 20:30/22:00"

# 2. Clôturer les anciennes inscriptions initiales Maths (319) et PC (320)
cursor.execute("UPDATE enrollments SET status = 'completed' WHERE id = 319 AND student_id = ?", (STUDENT_ID,))
print(f"[OK] Inscription #319 (Maths précédente) marquée 'completed': {cursor.rowcount} ligne(s)")

cursor.execute("UPDATE enrollments SET status = 'completed' WHERE id = 320 AND student_id = ?", (STUDENT_ID,))
print(f"[OK] Inscription #320 (PC précédente) marquée 'completed': {cursor.rowcount} ligne(s)")

# 3. Corriger l'inscription #861 (était Français en doublon) -> MATHS (Course 24)
cursor.execute("""
    UPDATE enrollments
    SET course_id = ?,
        enroll_date = '2026-10-22',
        custom_end_date = '2026-11-24',
        payment_plan = 'monthly',
        status = 'active',
        total_sessions_month = 9,
        attended_sessions_month = 3,
        monthly_price = 170.0,
        calculated_price = 170.0,
        current_month_earned = 170.0,
        deferred_amount = 0.0,
        notes = "Renouvellement (1 mois) suite à l'inscription N° 319"
    WHERE id = 861 AND student_id = ?
""", (COURSE_MATHS, STUDENT_ID))
print(f"[OK] Inscription #861 corrigée vers Maths Course #24 (fin 24/11/2026, 170 DH): {cursor.rowcount} ligne(s)")

# Corriger la facture #598 (FA-0710) et son item #1092
cursor.execute("UPDATE invoices SET due_date = '2026-10-29' WHERE id = 598")
cursor.execute("""
    UPDATE invoice_items
    SET description = ?
    WHERE invoice_id = 598 AND id = 1092
""", (f"Renouvellement {MATHS_NAME}",))
print(f"[OK] Facture #598 / Item #1092 mis à jour pour Maths: {cursor.rowcount} ligne(s)")

# Corriger le paiement #953 (REC-0863)
cursor.execute("""
    UPDATE payments
    SET note = ?
    WHERE id = 953 AND student_id = ?
""", (f"Paiement renouvellement {MATHS_NAME}", STUDENT_ID))
print(f"[OK] Paiement #953 (REC-0863) mis à jour pour Maths: {cursor.rowcount} ligne(s)")

# Corriger le journal d'activité #4470
cursor.execute("""
    UPDATE activity_log
    SET detail = ?
    WHERE id = 4470
""", (f"Student RAIHANA LAAZIZI renewed {MATHS_NAME}",))
print(f"[OK] Log d'activité #4470 mis à jour: {cursor.rowcount} ligne(s)")

# 4. Créer le renouvellement pour PHYSIQUE-CHIMIE (Course 28)
cursor.execute("""
    INSERT INTO enrollments (
        student_id, course_id, tariff_id, enroll_date, payment_plan,
        status, total_sessions_month, attended_sessions_month,
        monthly_price, calculated_price, current_month_earned, deferred_amount,
        notes, created_at, custom_end_date, created_by
    ) VALUES (
        ?, ?, NULL, '2026-10-22', 'monthly',
        'active', 9, 3,
        170.0, 170.0, 170.0, 0.0,
        "Renouvellement (1 mois) suite à l'inscription N° 320",
        '2026-10-27 19:55:00', '2026-11-24', 1
    )
""", (STUDENT_ID, COURSE_PC))
new_pc_enrollment_id = cursor.lastrowid
print(f"[OK] Nouveau renouvellement PC créé sous l'ID #{new_pc_enrollment_id} (fin 24/11/2026, 170 DH)")

# Récupérer et incrémenter le numéro de facture
cursor.execute("SELECT value FROM settings WHERE key = 'next_invoice_number'")
row = cursor.fetchone()
next_inv_num = int(row[0]) if row and row[0] else 1
inv_prefix = 'FA-'
invoice_number_str = f"{inv_prefix}{next_inv_num:04d}"
cursor.execute("UPDATE settings SET value = ? WHERE key = 'next_invoice_number'", (str(next_inv_num + 1),))

# Créer la facture pour PC
cursor.execute("""
    INSERT INTO invoices (
        number, type, student_id, enrollment_id, issue_date, due_date,
        subtotal, tva_rate, tva_amount, total, status, created_at
    ) VALUES (
        ?, 'facture', ?, ?, '2026-10-27', '2026-10-29',
        170.0, 0.0, 0.0, 170.0, 'paid', '2026-10-27 19:55:00'
    )
""", (invoice_number_str, STUDENT_ID, new_pc_enrollment_id))
new_pc_invoice_id = cursor.lastrowid
print(f"[OK] Facture PC créée #{new_pc_invoice_id} ({invoice_number_str})")

# Créer l'item de facture
cursor.execute("""
    INSERT INTO invoice_items (
        invoice_id, enrollment_id, description, amount
    ) VALUES (
        ?, ?, ?, 170.0
    )
""", (new_pc_invoice_id, new_pc_enrollment_id, f"Renouvellement {PC_NAME}"))
print(f"[OK] Item de facture créé pour PC")

# Récupérer et incrémenter le numéro de reçu
cursor.execute("SELECT value FROM settings WHERE key = 'next_receipt_number'")
row = cursor.fetchone()
next_rec_num = int(row[0]) if row and row[0] else 1
rec_prefix = 'REC-'
receipt_number_str = f"{rec_prefix}{next_rec_num:04d}"
cursor.execute("UPDATE settings SET value = ? WHERE key = 'next_receipt_number'", (str(next_rec_num + 1),))

# Créer le paiement pour PC
cursor.execute("""
    INSERT INTO payments (
        receipt, enrollment_id, student_id, amount, method, date,
        note, invoice_id, recorded_by, created_at
    ) VALUES (
        ?, ?, ?, 170.0, 'cash', '2026-10-27',
        ?, ?, 1, '2026-10-27 19:55:00'
    )
""", (receipt_number_str, new_pc_enrollment_id, STUDENT_ID, f"Paiement renouvellement {PC_NAME}", new_pc_invoice_id))
new_pc_payment_id = cursor.lastrowid
print(f"[OK] Paiement PC créé #{new_pc_payment_id} ({receipt_number_str}) de 170.0 DH")

# Ajouter l'action au journal d'activité
cursor.execute("""
    INSERT INTO activity_log (user_id, action, detail, created_at)
    VALUES (1, 'enrollment_renew', ?, '2026-10-27 19:55:00')
""", (f"Student RAIHANA LAAZIZI renewed {PC_NAME}",))
print(f"[OK] Log d'activité ajouté pour PC")

# 5. Vérifier et synchroniser l'inscription FR REG (#858)
cursor.execute("""
    UPDATE enrollments
    SET custom_end_date = '2026-11-24',
        monthly_price = 170.0,
        calculated_price = 170.0,
        status = 'active'
    WHERE id = 858 AND student_id = ?
""", (STUDENT_ID,))
print(f"[OK] Inscription #858 (Français Régional) vérifiée au 24/11/2026 (170 DH): {cursor.rowcount} ligne(s)")

conn.commit()
conn.close()

print("\n--- MODIFICATIONS APPLIQUÉES AVEC SUCCÈS DANS INSTITUT.DB ---")
