import random
import string
from datetime import datetime, timedelta


OTP_EXPIRY_MINUTES = 5


def generate_otp_id(conn) -> str:
    cursor = conn.execute(
        "SELECT otp_id FROM otp_codes ORDER BY otp_id DESC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        return "OTP001"

    last_number = int(row[0][3:])
    return f"OTP{last_number + 1:03d}"


def generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def create_otp(merchant_id: str, conn) -> str:
    code = generate_code()
    otp_id = generate_otp_id(conn)
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    conn.execute(
        """INSERT INTO otp_codes (otp_id, merchant_id, code, expires_at)
           VALUES (?, ?, ?, ?)""",
        (otp_id, merchant_id, code, expires_at.isoformat())
    )
    conn.commit()

    return code


def verify_otp(merchant_id: str, submitted_code: str, conn) -> bool:
    cursor = conn.execute(
        """SELECT otp_id, code, expires_at, used FROM otp_codes
           WHERE merchant_id = ?
           ORDER BY created_at DESC
           LIMIT 1""",
        (merchant_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return False

    otp_id, stored_code, expires_at, used = row

    if used == 1:
        return False

    if datetime.fromisoformat(expires_at) < datetime.now():
        return False

    if stored_code != submitted_code:
        return False

    conn.execute("UPDATE otp_codes SET used = 1 WHERE otp_id = ?", (otp_id,))
    conn.commit()

    return True