from fastapi import APIRouter, Header, HTTPException, Depends
from services.auth import verify_access_token
from services.authorization import get_user_merchants
from bi.visualization import prepare_revenue_data, prepare_top_offerings_data
from bi.overview import get_business_overview
from bi.visualization import prepare_payment_method_data
from services.credit_scoring import get_merchant_credit_score
from datetime import date
from database.connection import get_db as get_connection

router = APIRouter()

def get_db():
    return get_connection()


def get_current_merchant_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_db()
    try:
        merchants = get_user_merchants(user_id, conn)
        if merchants:
            return merchants[0]["merchant_id"]

        with conn.cursor() as cursor:
            cursor.execute("SELECT merchant_id FROM merchants WHERE merchant_id = %s", (user_id,))
            row = cursor.fetchone()

        if row is not None:
            return row[0]

        raise HTTPException(status_code=403, detail="User does not belong to any merchant")
    finally:
        conn.close()


@router.get("/api/transactions")
async def get_my_transactions(merchant_id: str = Depends(get_current_merchant_id)):
    conn = get_db()
    cursor = conn.execute(
        """SELECT t.transaction_id, t.amount_zar, t.quantity, t.raw_message, t.transaction_date
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE
           ORDER BY t.transaction_date DESC
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
    conn = get_db()
    cursor = conn.execute(
        """SELECT (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date AS day,
                  SUM(t.amount_zar) AS total
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE
           GROUP BY (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date
           ORDER BY day ASC""",
        (merchant_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    revenue_dict = {row[0]: row[1] for row in rows}
    return prepare_revenue_data(revenue_dict)


@router.get("/api/top-offerings")
async def get_my_top_offerings(merchant_id: str = Depends(get_current_merchant_id)):
    conn = get_db()
    result = prepare_top_offerings_data(merchant_id, conn)
    conn.close()
    return result

@router.get("/api/overview")
async def get_my_overview(merchant_id: str = Depends(get_current_merchant_id)):
    conn = get_db()
    result = get_business_overview(merchant_id, conn)
    conn.close()
    return result

@router.get("/api/payment-methods")
async def get_my_payment_methods(merchant_id: str = Depends(get_current_merchant_id)):
    conn = get_db()
    cursor = conn.execute(
        """SELECT payment_method, SUM(amount_zar) as total
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE AND t.payment_method IS NOT NULL
           GROUP BY t.payment_method""",
        (merchant_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    payment_dict = {row[0]: row[1] for row in rows}
    return prepare_payment_method_data(payment_dict)

@router.get("/api/credit-score")
async def get_my_credit_score(merchant_id: str = Depends(get_current_merchant_id)):
    conn = get_db()

    today = date.today()
    period_start = (today.replace(day=1)).isoformat()
    period_end = today.isoformat()

    try:
        score = get_merchant_credit_score(merchant_id, period_start, period_end, conn)
    except ValueError:
        score = None

    conn.close()
    return {"credit_score": score}