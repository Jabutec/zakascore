from database.connection import get_db

conn = get_db()
try:
    cursor = conn.execute(
        """SELECT m.merchant_id
           FROM data_sources ds
           JOIN stores s ON s.store_id = ds.store_id
           JOIN merchants m ON m.merchant_id = s.merchant_id
           WHERE ds.source_type = 'whatsapp'
             AND ds.external_identifier = %s""",
        ("+27735347153",),
    )
    row = cursor.fetchone()

    if row is None:
        print("No merchant found with that number — register one via the webhook first.")
    else:
        print(f"Merchant found: {row[0]}")
finally:
    conn.close()