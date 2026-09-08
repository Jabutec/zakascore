import sqlite3

conn = sqlite3.connect("data/zakascore.db")
cursor = conn.execute("SELECT * FROM transactions WHERE merchant_id = 'M011';")
print(cursor.fetchall())
conn.close()