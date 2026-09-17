import os
import sqlite3
from fastapi import APIRouter, Form

from settings.onboarding import get_merchant_by_number
from services.auth import create_otp, verify_otp, send_otp_via_whatsapp, create_access_token

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zakascore.db")
DEV_MODE = os.environ.get("ENVIRONMENT") != "production"


def get_db():
    return sqlite3.connect(DB_PATH)


@router.post("/auth/request-otp")
async def request_otp(phone_number: str = Form(...)):
    conn = get_db()
    merchant = get_merchant_by_number(phone_number, conn)

    if merchant is None:
        conn.close()
        return {"error": "No account found for this number"}

    code = create_otp(merchant.merchant_id, conn)
    send_otp_via_whatsapp(phone_number, code)
    conn.close()

    response = {"message": "OTP sent"}
    if DEV_MODE:
        response["dev_otp_code"] = code

    return response


@router.post("/auth/verify-otp")
async def verify_otp_route(phone_number: str = Form(...), code: str = Form(...)):
    conn = get_db()
    merchant = get_merchant_by_number(phone_number, conn)

    if merchant is None:
        conn.close()
        return {"error": "No account found for this number"}

    is_valid = verify_otp(merchant.merchant_id, code, conn)
    conn.close()

    if not is_valid:
        return {"error": "Invalid or expired code"}

    token = create_access_token(merchant.merchant_id)
    return {"access_token": token}