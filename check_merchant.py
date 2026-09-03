import sqlite3

conn = sqlite3.connect("data/zakascore.db")
cursor = conn.execute("SELECT * FROM merchants WHERE whatsapp_number = '+27821234567';")
print(cursor.fetchall())
conn.close()