import shutil
import sqlite3
import datetime

# 1. Create a safe backup first
backup_filename = f"backups/institut_backup_before_math_hamza_fix_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2('institut.db', backup_filename)
print(f"Database backed up to {backup_filename}")

conn = sqlite3.connect('institut.db')
cursor = conn.cursor()

# 2. Delete temporary transfer payment 910
cursor.execute("DELETE FROM payments WHERE id = 910 AND student_id = 298")
print(f"Deleted payment 910: {cursor.rowcount} row(s)")

# 3. Delete temporary transfer enrollment 822
cursor.execute("DELETE FROM enrollments WHERE id = 822 AND student_id = 298")
print(f"Deleted enrollment 822: {cursor.rowcount} row(s)")

# 4. Restore Payment 600 to full 500.0 DH for enrollment 567
cursor.execute("""
    UPDATE payments
    SET amount = 500.0,
        enrollment_id = 567,
        note = 'Paiement Inscription Express'
    WHERE id = 600 AND student_id = 298
""")
print(f"Restored payment 600 to 500.0 DH: {cursor.rowcount} row(s)")

# 5. Update Enrollment 567 to Course 24 (Hamza Boubtana) starting 14/10/2026 for 3 months
cursor.execute("""
    UPDATE enrollments
    SET course_id = 24,
        enroll_date = '2026-10-14',
        status = 'active',
        custom_end_date = '2027-01-14',
        total_sessions_month = 27,
        attended_sessions_month = 27,
        monthly_price = 166.67,
        calculated_price = 500.0,
        current_month_earned = 111.11,
        deferred_amount = 388.89,
        payment_plan = '3months',
        notes = "Inscription Express (3 mois). Durée: 3 mois. Frais d'inscription: 0.0 DH. Début le 14/10/2026 chez Prof. HAMZA BOUBTANA."
    WHERE id = 567 AND student_id = 298
""")
print(f"Updated enrollment 567 to Hamza Boubtana Course 24: {cursor.rowcount} row(s)")

# 6. Update invoice item 657
cursor.execute("""
    UPDATE invoice_items
    SET enrollment_id = 567,
        amount = 500.0,
        description = 'Soutien 1 BAC SX - Maths  mercredi  et 20:30-22:00 vendredi 19:00-20:30 (Scolarité)'
    WHERE id = 657
""")
print(f"Updated invoice item 657: {cursor.rowcount} row(s)")

# 7. Insert activity log
cursor.execute("""
    INSERT INTO activity_log (user_id, action, detail, created_at)
    VALUES (1, 'fix_subscription_ilas384_math_hamza', 'Basculement abonnement Maths ILAS384 vers Prof. Hamza Boubtana (Course #24) début 14/10/2026 3 mois 500 DH et annulation chez Mr Matouk', datetime('now'))
""")
print("Inserted activity log")

conn.commit()
conn.close()
print("All changes committed successfully!")
