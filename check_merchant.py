import sqlite3

conn = sqlite3.connect("data/zakascore.db")

cursor = conn.execute("""
    SELECT transaction_id, amount_zar, transaction_date, is_voided
    FROM transactions
    WHERE merchant_id = 'M011'
    ORDER BY transaction_date DESC
""")
for row in cursor.fetchall():
    print(row)

print()
cursor = conn.execute("""
    SELECT COALESCE(SUM(amount_zar), 0)
    FROM transactions
    WHERE merchant_id = 'M011' AND date(transaction_date) = date('now') AND is_voided = 0
""")
print(f"Today's total per the actual query: {cursor.fetchone()[0]}")

conn.close()