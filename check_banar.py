import sqlite3
con = sqlite3.connect('institut.db')
cur = con.cursor()
cur.execute("SELECT * FROM activity_log WHERE detail LIKE '%EL BANAR%' OR detail LIKE '%REC-0810%' OR detail LIKE '%REC-0811%'")
for r in cur.fetchall():
    print(r)
