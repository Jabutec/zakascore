import os
import random
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.rest import Client
import jwt


load_dotenv()


OTP_EXPIRY_MINUTES = 5
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")  # e.g. "whatsapp:+14155238886" for sandbox

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

def create_access_token(merchant_id: str) -> str:
    payload = {
        "merchant_id": merchant_id,
        "exp": datetime.now() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["merchant_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


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


def send_otp_via_whatsapp(whatsapp_number: str, code: str) -> None:
    # TEMPORARY: real WhatsApp sending deferred until Twilio vs Meta 
    # is decided and an approved Authentication Template exists.
    print(f"[DEV MODE] OTP for {whatsapp_number}: {code}")