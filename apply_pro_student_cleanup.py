import sqlite3
import shutil
import datetime
import os
import sys

db_path = 'institut.db'
backup_dir = 'backups'
os.makedirs(backup_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"{backup_dir}/institut_backup_before_pro_student_cleanup_{timestamp}.db"

# 1. Create a safe backup first
shutil.copy2(db_path, backup_path)
print(f"[OK] Database backed up to: {backup_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Capture baseline statistics
initial_student_count = c.execute("SELECT count(*) FROM students").fetchone()[0]
initial_payment_sum = c.execute("SELECT coalesce(sum(amount), 0) FROM payments").fetchone()[0]
initial_enrollment_count = c.execute("SELECT count(*) FROM enrollments").fetchone()[0]

print(f"\n[BASELINE]")
print(f"  Students: {initial_student_count}")
print(f"  Payments: {initial_payment_sum:.2f} DH")
print(f"  Enrollments: {initial_enrollment_count}")

# -------------------------------------------------------------
# Configuration of Cleanup
# -------------------------------------------------------------

# Step 1: Test accounts to completely delete
test_ids = [213, 214, 215, 216, 217, 218, 219, 177, 178, 220]

# Step 2: Pure empty duplicate IDs (0 payments, 0 enrollments, 0 attendances)
empty_duplicate_ids = [
    246, 247,  # Kawtar Lahbiri (Keep ID 248)
    154, 155,  # Ilyas El Hdydi (Keep ID 165)
    233,       # Romayssaa Sarour (Keep ID 234)
    179,       # Naima Bouoyoun (Keep ID 58)
    7,         # Roaya Lamhmdi (Keep ID 91)
]

# Step 3: Merges: (source_old_ids, target_latest_id, label)
merges = [
    ([44], 234, "SAROUR ROMAYSSA"),
    ([64], 113, "KHADIJA EL MASRAR"),
    ([83], 193, "SIHAM RASMI"),
    ([201], 225, "SAAD ENNACHADI"),
    ([238], 358, "RIHAB REGGUI"),
    ([263], 286, "JIHAN CHAIKH"),
    ([10], 74, "ABDE EL SAMAD DAOUDI / DAOUDI ABDESMAD"),
    ([26], 121, "MARIAM MOHSSIN / meriem mohcine"),
    ([42], 242, "HAFSA BOUCHTANEA / HAFSA BOUCHTANE"),
    ([228], 271, "LINA BOUTNAYA / BOUTNYA LINA"),
    ([241], 395, "GHITA NOURRY / Ghita Noury"),
    ([297], 318, "FATIMA ZAHRA EL HEJJAJI"),
    ([295], 339, "JIDAE BELAFDA / jaidae belfdal"),
    ([299], 321, "BADR BOURHFIR / Badr Boughfir"),
    ([3], 210, "AYOUB MOKRIM / AYOUB MOUKRIM"),
    ([273], 251, "RIHANA ZARIOUH"),
    ([62], 111, "OUMAIMA JOULAL (AL 628 -> ILAS180)"),
    ([63], 112, "MED OUASSIRI (AL 640 -> ILAS181)"),
    ([71], 109, "ABDELBASSET KAFI (ALL 746 -> ILAS178)"),
]

fk_tables = [
    'enrollments',
    'attendances',
    'grades',
    'badge_records',
    'invoices',
    'payments',
    'student_credits',
    'certificates',
    'book_sales',
    'vacation_student_dispatches'
]

all_deleted_ids = test_ids + empty_duplicate_ids + [old_id for m in merges for old_id in m[0]]

try:
    c.execute("BEGIN TRANSACTION")

    # =========================================================
    # STEP 1: Delete Test Accounts
    # =========================================================
    print(f"\n[STEP 1] Removing Test Accounts: {test_ids}")
    placeholders = ",".join("?" for _ in test_ids)
    
    # 1.1 Delete invoice items of test invoices or test enrollments
    c.execute(f"""
        DELETE FROM invoice_items 
        WHERE invoice_id IN (SELECT id FROM invoices WHERE student_id IN ({placeholders}))
           OR enrollment_id IN (SELECT id FROM enrollments WHERE student_id IN ({placeholders}))
    """, test_ids + test_ids)
    print(f"  - Deleted {c.rowcount} test invoice item(s)")

    # 1.2 Delete from all child tables
    for tbl in fk_tables:
        c.execute(f"DELETE FROM {tbl} WHERE student_id IN ({placeholders})", test_ids)
        if c.rowcount > 0:
            print(f"  - Deleted {c.rowcount} row(s) from {tbl}")

    # 1.3 Delete test students
    c.execute(f"DELETE FROM students WHERE id IN ({placeholders})", test_ids)
    print(f"  - Deleted {c.rowcount} test student record(s)")

    # =========================================================
    # STEP 2: Delete Pure Empty Duplicates
    # =========================================================
    print(f"\n[STEP 2] Removing Pure Empty Duplicate IDs: {empty_duplicate_ids}")
    for eid in empty_duplicate_ids:
        for tbl in fk_tables:
            cnt = c.execute(f"SELECT count(*) FROM {tbl} WHERE student_id = ?", (eid,)).fetchone()[0]
            if cnt > 0:
                raise ValueError(f"Safety check failed: Empty ID {eid} has {cnt} rows in {tbl}!")
        
        c.execute("DELETE FROM students WHERE id = ?", (eid,))
        print(f"  - Deleted empty student ID {eid}")

    # =========================================================
    # STEP 3: Merge Multi-ID Students into their Target Latest ID
    # =========================================================
    print(f"\n[STEP 3] Merging Active Duplicate Profiles into Target Latest IDs")
    
    for old_ids, target_id, label in merges:
        target_student = dict(c.execute("SELECT * FROM students WHERE id = ?", (target_id,)).fetchone())
        print(f"\n  Merging {label} -> Target ID {target_id} ({target_student['code']}):")
        
        for old_id in old_ids:
            old_student = dict(c.execute("SELECT * FROM students WHERE id = ?", (old_id,)).fetchone())
            
            # 1. Handle potential unique constraint conflicts before transferring:
            # 1.1 attendances (course_id, student_id, date)
            c.execute("""
                DELETE FROM attendances 
                WHERE student_id = ? 
                  AND (course_id, date) IN (
                      SELECT course_id, date FROM attendances WHERE student_id = ?
                  )
            """, (old_id, target_id))
            if c.rowcount > 0:
                print(f"    * Deduplicated {c.rowcount} overlapping attendance record(s)")

            # 1.2 vacation_student_dispatches (student_id, course_id)
            c.execute("""
                DELETE FROM vacation_student_dispatches 
                WHERE student_id = ? 
                  AND course_id IN (
                      SELECT course_id FROM vacation_student_dispatches WHERE student_id = ?
                  )
            """, (old_id, target_id))
            if c.rowcount > 0:
                print(f"    * Deduplicated {c.rowcount} overlapping vacation dispatch record(s)")

            # 2. Reassign all child tables
            for tbl in fk_tables:
                c.execute(f"UPDATE {tbl} SET student_id = ? WHERE student_id = ?", (target_id, old_id))
                if c.rowcount > 0:
                    print(f"    * Transferred {c.rowcount} row(s) in {tbl} from ID {old_id} to ID {target_id}")

            # 3. Backfill any missing contact fields on target student from old student
            update_fields = {}
            for col in ['phone', 'parent_phone', 'parent_name', 'birth_date', 'gender', 'cin', 'school_level', 'school_name', 'address', 'city']:
                target_val = (target_student.get(col) or '').strip()
                old_val = (old_student.get(col) or '').strip()
                if not target_val and old_val and old_val.lower() != 'none':
                    update_fields[col] = old_val

            if update_fields:
                set_clause = ", ".join(f"{col} = ?" for col in update_fields.keys())
                values = list(update_fields.values()) + [target_id]
                c.execute(f"UPDATE students SET {set_clause} WHERE id = ?", values)
                print(f"    * Backfilled missing fields on target ID {target_id}: {list(update_fields.keys())}")
                target_student = dict(c.execute("SELECT * FROM students WHERE id = ?", (target_id,)).fetchone())

            # 4. Delete old student record
            c.execute("DELETE FROM students WHERE id = ?", (old_id,))
            print(f"    * Deleted source student ID {old_id} ({old_student['code']})")

    # =========================================================
    # STEP 4: Verification & Integrity Checks
    # =========================================================
    print(f"\n[STEP 4] Running Verification & Integrity Checks")
    
    final_student_count = c.execute("SELECT count(*) FROM students").fetchone()[0]
    final_payment_sum = c.execute("SELECT coalesce(sum(amount), 0) FROM payments").fetchone()[0]
    final_enrollment_count = c.execute("SELECT count(*) FROM enrollments").fetchone()[0]

    print(f"  Final Students: {final_student_count} (Expected: {initial_student_count - 36})")
    print(f"  Final Payments: {final_payment_sum:.2f} DH (Initial: {initial_payment_sum:.2f} DH)")
    print(f"  Final Enrollments: {final_enrollment_count}")

    # Check 1: Payments must match 100%
    diff_pay = abs(final_payment_sum - initial_payment_sum)
    if diff_pay > 0.001:
        raise ValueError(f"PAYMENT INTEGRITY FAILED! Difference: {diff_pay} DH")
    print("  [PASS] 100% Financial Integrity: Zero payment loss!")

    # Check 2: Student count exact match
    expected_students = initial_student_count - 36
    if final_student_count != expected_students:
        raise ValueError(f"STUDENT COUNT MISMATCH! Found {final_student_count}, expected {expected_students}")
    print("  [PASS] Exact Student Count: 36 redundant IDs cleanly removed.")

    # Check 3: Check that NO deleted student ID is referenced in ANY child table
    del_placeholders = ",".join("?" for _ in all_deleted_ids)
    for tbl in fk_tables:
        cnt = c.execute(f"SELECT count(*) FROM {tbl} WHERE student_id IN ({del_placeholders})", all_deleted_ids).fetchone()[0]
        if cnt > 0:
            raise ValueError(f"Safety violation: Found {cnt} row(s) in {tbl} still referencing deleted IDs!")
    print("  [PASS] Zero Residual References: None of the deleted IDs remain in any table!")

    # =========================================================
    # STEP 5: Log to Activity Log
    # =========================================================
    log_detail = (
        f"Nettoyage professionnel des doublons d'élèves (Total 36 IDs supprimés) : "
        f"10 comptes de test supprimés ({test_ids}), "
        f"7 doublons vides sans activité supprimés ({empty_duplicate_ids}), "
        f"et 19 profils fusionnés vers leurs IDs récents légitimes avec transfert complet "
        f"des inscriptions, paiements ({initial_payment_sum:.2f} DH préservés), factures et présences. "
        f"Backup créé sous {backup_path}."
    )
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'pro_duplicate_student_cleanup', ?, ?)
    """, (log_detail, now_str))
    print(f"\n[STEP 5] Activity log recorded.")

    # Commit Transaction
    conn.commit()
    print("\n" + "=" * 60)
    print(">>> TRANSACTION COMMITTED SUCCESSFULLY! CLEANUP COMPLETE! <<<")
    print("=" * 60)

except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] Transaction aborted and rolled back: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    conn.close()
