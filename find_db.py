import os
import sqlite3

desktop_dir = r"C:\Users\INSTITUT ILAS\Desktop"

for root, dirs, files in os.walk(desktop_dir):
    for f in files:
        if f.endswith('.db'):
            path = os.path.join(root, f)
            try:
                con = sqlite3.connect(path)
                cur = con.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
                if cur.fetchone():
                    cur.execute("SELECT id, receipt, amount, date, created_at, recorded_by, note FROM payments WHERE id = 894 OR receipt LIKE '%813%'")
                    res = cur.fetchall()
                    if res:
                        print(f"FOUND IN {path}:", res)
                    else:
                        cur.execute("SELECT MAX(id), count(*) FROM payments")
                        print(f"In {path}: max_id={cur.fetchone()}")
                con.close()
            except Exception as e:
                pass
