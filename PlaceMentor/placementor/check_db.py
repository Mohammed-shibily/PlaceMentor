import sqlite3

try:
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT id, cgpa FROM home_studentprofile")
    rows = cur.fetchall()
    with open('output_py.txt', 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(f"id {row[0]}: {repr(row[1])} type: {type(row[1])}\n")
    conn.close()
except Exception as e:
    print(e)
