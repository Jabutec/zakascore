import sqlite3
from bi.visualization import prepare_top_offerings_data

conn = sqlite3.connect("data/zakascore.db")
result = prepare_top_offerings_data("M011", conn)
for row in result:
    print(row)
conn.close()