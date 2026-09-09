import sqlite3
from services.credit_scoring import get_merchant_credit_score

conn = sqlite3.connect("data/zakascore.db")


cursor = conn.execute(
    "SELECT merchant_id, period_start, period_end FROM financial_snapshots LIMIT 1"
)
merchant_id, period_start, period_end = cursor.fetchone()

print(f"Testing merchant {merchant_id}, period {period_start} to {period_end}")

score = get_merchant_credit_score(merchant_id, period_start, period_end, conn)
print(f"Credit score: {score}")

conn.close()