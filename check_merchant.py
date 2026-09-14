import sqlite3

conn = sqlite3.connect("data/zakascore.db")
cursor = conn.execute("""
    SELECT t.transaction_id, t.merchant_id, t.amount_zar, t.quantity, o.offering_name, t.raw_message, t.transaction_date
    FROM transactions t
    LEFT JOIN offerings o ON t.offering_id = o.offering_id
    WHERE t.merchant_id = (SELECT merchant_id FROM merchants WHERE whatsapp_number = '+27821234567')
    ORDER BY t.transaction_date DESC;
""")
for row in cursor.fetchall():
    print(row)
conn.close()