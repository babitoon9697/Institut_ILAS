import shutil
import sqlite3
import datetime

# 1. Create a safe backup first
backup_filename = f"backups/institut_backup_before_ilas384_fix_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2('institut.db', backup_filename)
print(f"Database backed up to {backup_filename}")

conn = sqlite3.connect('institut.db')
cursor = conn.cursor()

# 2. Delete 0 DH trial enrollments and linked records
# Payments 576, 577
cursor.execute("DELETE FROM payments WHERE id IN (576, 577) AND amount = 0.0 AND student_id = 298")
print(f"Deleted {cursor.rowcount} trial payment(s)")

# Invoice items 637, 638
cursor.execute("DELETE FROM invoice_items WHERE id IN (637, 638) AND amount = 0.0")
print(f"Deleted {cursor.rowcount} trial invoice item(s)")

# Invoice 368
cursor.execute("DELETE FROM invoices WHERE id = 368 AND total = 0.0 AND student_id = 298")
print(f"Deleted {cursor.rowcount} trial invoice(s)")

# Enrollments 549, 550
cursor.execute("DELETE FROM enrollments WHERE id IN (549, 550) AND student_id = 298 AND calculated_price = 0.0")
print(f"Deleted {cursor.rowcount} trial enrollment(s)")

# 3. Update Math (Enrollment 567): 500 DH for 3 months
cursor.execute("""
    UPDATE enrollments
    SET monthly_price = 166.67,
        calculated_price = 500.0,
        custom_end_date = '2026-12-31',
        total_sessions_month = 13,
        attended_sessions_month = 13,
        current_month_earned = 153.85,
        deferred_amount = 346.15,
        notes = "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 0.0 DH. "
    WHERE id = 567 AND student_id = 298
""")
print(f"Updated Math enrollment 567: {cursor.rowcount} row(s)")

# 4. Update Français (Enrollment 568): 300 DH for 2 months (150 DH / month)
cursor.execute("""
    UPDATE enrollments
    SET monthly_price = 150.0,
        calculated_price = 300.0,
        custom_end_date = '2026-11-30',
        total_sessions_month = 16,
        attended_sessions_month = 16,
        current_month_earned = 150.0,
        deferred_amount = 150.0,
        notes = "Inscription Express (2 mois). Durée: 2 mois. Frais d'inscription: 0.0 DH. "
    WHERE id = 568 AND student_id = 298
""")
print(f"Updated Français enrollment 568: {cursor.rowcount} row(s)")

# 5. Log the fix in activity_log
cursor.execute("""
    INSERT INTO activity_log (user_id, action, detail, created_at)
    VALUES (1, 'fix_subscription_ilas384', 'Correction abonnement ILAS384 (Math 3 mois 500 DH, Français 2 mois 150 DH/m, suppression 2 séances essai 0 DH)', datetime('now'))
""")
print("Activity log inserted")

conn.commit()
conn.close()
print("All changes successfully committed to institut.db!")
