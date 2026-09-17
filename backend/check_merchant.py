import sqlite3
from services.auth import create_otp, send_otp_via_whatsapp

conn = sqlite3.connect("data/zakascore.db")

cursor = conn.execute(
    "SELECT merchant_id FROM merchants WHERE whatsapp_number = ?",
    ("+27735347153",)
)
row = cursor.fetchone()

if row is None:
    print("No merchant found with that number — register one via the webhook first.")
else:
    merchant_id = row[0]
    code = create_otp(merchant_id, conn)
    send_otp_via_whatsapp("+27735347153", code)
    print(f"OTP sent! Code was: {code}")

conn.close()