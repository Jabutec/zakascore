import os
import sqlite3
from fastapi import APIRouter, Form, Header, HTTPException, Depends

from services.onboarding import get_merchant_by_number
from services.auth import create_otp, verify_otp, send_otp_via_whatsapp, create_access_token, verify_access_token
from bi.visualization import prepare_revenue_data, prepare_top_offerings_data
from bi.overview import get_business_overview
from bi.visualization import prepare_payment_method_data
from services.credit_scoring import get_merchant_credit_score
from datetime import date, timedelta

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

@router.get("/api/revenue")
async def get_my_revenue(merchant_id: str = Depends(get_current_merchant_id)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT date(transaction_date) as day, SUM(amount_zar) as total
           FROM transactions
           WHERE merchant_id = ? AND is_voided = 0
           GROUP BY date(transaction_date)
           ORDER BY day ASC""",
        (merchant_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    revenue_dict = {row[0]: row[1] for row in rows}
    return prepare_revenue_data(revenue_dict)


@router.get("/api/top-offerings")
async def get_my_top_offerings(merchant_id: str = Depends(get_current_merchant_id)):
    conn = sqlite3.connect(DB_PATH)
    result = prepare_top_offerings_data(merchant_id, conn)
    conn.close()
    return result

@router.get("/api/overview")
async def get_my_overview(merchant_id: str = Depends(get_current_merchant_id)):
    conn = sqlite3.connect(DB_PATH)
    result = get_business_overview(merchant_id, conn)
    conn.close()
    return result

@router.get("/api/payment-methods")
async def get_my_payment_methods(merchant_id: str = Depends(get_current_merchant_id)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT payment_method, SUM(amount_zar) as total
           FROM transactions
           WHERE merchant_id = ? AND is_voided = 0 AND payment_method IS NOT NULL
           GROUP BY payment_method""",
        (merchant_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    payment_dict = {row[0]: row[1] for row in rows}
    return prepare_payment_method_data(payment_dict)

@router.get("/api/credit-score")
async def get_my_credit_score(merchant_id: str = Depends(get_current_merchant_id)):
    conn = sqlite3.connect(DB_PATH)

    today = date.today()
    period_start = (today.replace(day=1)).isoformat()
    period_end = today.isoformat()

    try:
        score = get_merchant_credit_score(merchant_id, period_start, period_end, conn)
    except ValueError:
        score = None

    conn.close()
    return {"credit_score": score}