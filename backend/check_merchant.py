import sqlite3
from services.auth import create_otp, verify_otp

conn = sqlite3.connect("data/zakascore.db")

merchant_id = "M001"

code = create_otp(merchant_id, conn)
print(f"Generated code: {code}")

result = verify_otp(merchant_id, code, conn)
print(f"Verify with correct code: {result}")

result_again = verify_otp(merchant_id, code, conn)
print(f"Verify same code again (should be False): {result_again}")

new_code = create_otp(merchant_id, conn)
wrong_result = verify_otp(merchant_id, "000000", conn)
print(f"Verify with wrong code (should be False): {wrong_result}")

conn.close()