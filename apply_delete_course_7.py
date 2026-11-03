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
backup_path = f"{backup_dir}/institut_backup_before_delete_course_7_{timestamp}.db"

# 1. Sauvegarde préventive
shutil.copy2(db_path, backup_path)
print(f"[OK] Sauvegarde créée : {backup_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    c.execute("BEGIN TRANSACTION")

    cid = 7
    # Vérification du cours
    c.execute("SELECT c.*, t.first_name, t.last_name FROM courses c JOIN teachers t ON c.teacher_id=t.id WHERE c.id = ?", (cid,))
    course = c.fetchone()
    if not course:
        raise Exception(f"Cours ID #{cid} introuvable !")
    print(f"[OK] Cours trouvé : '{course['name']}' (Prof. {course['first_name']} {course['last_name']})")

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # 1. Clôture de l'inscription échue d'octobre (Enrollment #617 Hajar Abassi finie le 31/10/2026)
    c.execute("""
        UPDATE enrollments
        SET status = 'completed'
        WHERE course_id = ? AND status = 'active' AND custom_end_date <= '2026-10-31'
    """, (cid,))
    print(f"[OK] Inscriptions échues passées à 'completed' : {c.rowcount}")

    # 2. Suppression des créneaux d'emploi du temps (Mardi & Vendredi 19:00 - 20:30)
    c.execute("DELETE FROM schedule_slots WHERE course_id = ?", (cid,))
    print(f"[OK] Créneaux de planning supprimés de l'emploi du temps : {c.rowcount}")

    # 3. Suppression des assignations enseignants pour ce cours
    c.execute("DELETE FROM course_teachers WHERE course_id = ?", (cid,))
    print(f"[OK] Assignations course_teachers supprimées : {c.rowcount}")

    # 4. Suppression des dispatches vacances éventuels
    c.execute("DELETE FROM vacation_student_dispatches WHERE course_id = ?", (cid,))
    print(f"[OK] Entrées vacation_student_dispatches nettoyées : {c.rowcount}")

    # 5. Désactivation et suppression du cours de la liste des cours actifs
    c.execute("""
        UPDATE courses
        SET active = 0,
            notes = coalesce(notes, '') || ' | Cours clôturé et supprimé de l''emploi du temps le 03/11/2026'
        WHERE id = ?
    """, (cid,))
    print(f"[OK] Cours ID #{cid} désactivé (active = 0) et retiré de l'affichage")

    # 6. Journalisation dans activity_log
    log_detail = f"Suppression du Groupe 2 Prof. HAMZA EL MOTAKI (Mardi et Vendredi 19:00-20:30) - Course #{cid} retiré de l'emploi du temps et archivé"
    c.execute("""
        INSERT INTO activity_log (user_id, action, detail, created_at)
        VALUES (1, 'course_delete', ?, ?)
    """, (log_detail, now_str))
    print(f"[OK] Action enregistrée dans activity_log")

    conn.commit()
    print("\n>>> GROUPE 2 DU PROF MOTAKI SUPPRIMÉ AVEC SUCCÈS ! <<<")

except Exception as e:
    conn.rollback()
    print(f"\n[ERREUR] Transaction annulée : {e}")
    sys.exit(1)
finally:
    conn.close()
