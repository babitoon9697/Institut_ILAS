import sqlite3
import shutil
import datetime
import os

db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_cancel_credit_ilas334_{timestamp}.db"
shutil.copy2(db_path, backup_path)
print(f"Database backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    # 1. Reset credit_balance to 0.0
    c.execute("""
        UPDATE students
        SET credit_balance = 0.0
        WHERE id = 250
    """)
    print("1. Student 250 credit_balance set to 0.0")

    # 2. Remove the 50 DH record from student_credits
    c.execute("""
        DELETE FROM student_credits
        WHERE student_id = 250 AND amount = 50.0
    """)
    print(f"2. Deleted {c.rowcount} row(s) from student_credits")

    # 3. Remove the 50 DH item from Invoice 283
    c.execute("""
        DELETE FROM invoice_items
        WHERE id = 1031 AND invoice_id = 283
    """)
    print(f"3. Deleted {c.rowcount} row(s) from invoice_items")

    # 4. Update Invoice 283 total to 300.0 DH
    c.execute("""
        UPDATE invoices
        SET subtotal = 300.0,
            total = 300.0,
            notes = 'Transfert de paiement: 150 DH vers TC Maths, 150 DH vers TC PC (Total: 300 DH pour Novembre)'
        WHERE id = 283
    """)
    print("4. Invoice 283 updated: total=300.0 DH")

    # 5. Update notes on dropped enrollment 578
    c.execute("""
        UPDATE enrollments
        SET notes = 'Transféré depuis ''Anglais 3S/sem (1h30)GROUPE 1: MARDI-JEUDI-VENDREDI (19:00 - 20:30)'' le 01/10/2026 (Part: 350.00 DH) | Inscription annulée le 22/10/2026. Paiement de 300.0 DH transféré vers TC Maths (150 DH) et TC PC (150 DH) pour Novembre.'
        WHERE id = 578
    """)
    print("5. Enrollment 578 notes updated")

    # 6. Log activity
    log_detail = "Annulation du solde créditeur de 50 DH pour RABIA ALAA (ILAS334). Seuls 300 DH sont conservés et imputés sur Novembre 2026 (150 DH TC Maths Hamza Boubtana + 150 DH TC PC Tarik Radid). Solde créditeur élève ramené à 0.0 DH."
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'credit_adjustment', ?, ?)
    """, (log_detail, now_str))
    print("6. Inserted activity log")

    conn.commit()
    print("\nALL CHANGES SUCCESSFULLY COMMITTED TO institut.db!")

except Exception as e:
    conn.rollback()
    print("ERROR, rolled back:", e)
    raise
finally:
    conn.close()
