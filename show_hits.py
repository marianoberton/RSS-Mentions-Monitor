import sqlite3

conn = sqlite3.connect('data/mentions.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM hits')
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()