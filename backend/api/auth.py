import os
import sqlite3
from fastapi import APIRouter, Form, Header, HTTPException, Depends

from services.onboarding import get_merchant_by_number
from services.auth import create_otp, verify_otp, send_otp_via_whatsapp, create_access_token, verify_access_token

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


def get_current_merchant_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    merchant_id = verify_access_token(token)

    if merchant_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return merchant_id


@router.get("/api/transactions")
async def get_my_transactions(merchant_id: str = Depends(get_current_merchant_id)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT transaction_id, amount_zar, quantity, raw_message, transaction_date
           FROM transactions
           WHERE merchant_id = ? AND is_voided = 0
           ORDER BY transaction_date DESC
           LIMIT 20""",
        (merchant_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "transaction_id": row[0],
            "amount_zar": row[1],
            "quantity": row[2],
            "raw_message": row[3],
            "transaction_date": row[4],
        }
        for row in rows
    ]