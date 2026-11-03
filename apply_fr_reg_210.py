# -*- coding: utf-8 -*-
"""
Ajustement du tarif et paiement de Français Régional pour RAIHANA LAAZIZI (ILAS263, ID 184).
- Inscription #858 : tarif ajusté à 210 DH (au lieu de 170 DH).
- Facture #595 (FA-0707) : montant ajusté à 210 DH.
- Item de facture #1087 : montant ajusté à 210 DH.
- Paiement #950 (REC-0860) : montant ajusté à 210 DH.
"""

import shutil
import sqlite3
import datetime
import os

DB_PATH = 'institut.db'
BACKUP_DIR = 'backups'

os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_filename = os.path.join(BACKUP_DIR, f"institut_backup_before_fr_reg_210_{timestamp}.db")

shutil.copy2(DB_PATH, backup_filename)
print(f"[OK] Sauvegarde créée : {backup_filename}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

STUDENT_ID = 184
ENROLLMENT_ID = 858
INVOICE_ID = 595
PAYMENT_ID = 950

# 1. Mettre à jour l'inscription 858
cursor.execute("""
    UPDATE enrollments
    SET monthly_price = 210.0,
        calculated_price = 210.0,
        current_month_earned = 210.0,
        deferred_amount = 0.0
    WHERE id = ? AND student_id = ?
""", (ENROLLMENT_ID, STUDENT_ID))
print(f"[OK] Inscription #{ENROLLMENT_ID} mise à jour à 210.0 DH : {cursor.rowcount} ligne(s)")

# 2. Mettre à jour la facture 595
cursor.execute("""
    UPDATE invoices
    SET subtotal = 210.0,
        total = 210.0,
        status = 'paid'
    WHERE id = ? AND student_id = ?
""", (INVOICE_ID, STUDENT_ID))
print(f"[OK] Facture #{INVOICE_ID} mise à jour à 210.0 DH : {cursor.rowcount} ligne(s)")

# 3. Mettre à jour l'item de facture 1087
cursor.execute("""
    UPDATE invoice_items
    SET amount = 210.0
    WHERE invoice_id = ? AND enrollment_id = ?
""", (INVOICE_ID, ENROLLMENT_ID))
print(f"[OK] Item de facture mis à jour à 210.0 DH : {cursor.rowcount} ligne(s)")

# 4. Mettre à jour le paiement 950
cursor.execute("""
    UPDATE payments
    SET amount = 210.0
    WHERE id = ? AND student_id = ?
""", (PAYMENT_ID, STUDENT_ID))
print(f"[OK] Paiement #{PAYMENT_ID} (REC-0860) mis à jour à 210.0 DH : {cursor.rowcount} ligne(s)")

# 5. Ajouter un log d'activité
cursor.execute("""
    INSERT INTO activity_log (user_id, action, detail, created_at)
    VALUES (1, 'enrollment_edit', 'Ajustement montant renouvellement Français Régional à 210 DH pour RAIHANA LAAZIZI', datetime('now'))
""")
print(f"[OK] Log d'activité ajouté")

conn.commit()
conn.close()

print("\n--- MODIFICATIONS APPLIQUÉES AVEC SUCCÈS ---")
