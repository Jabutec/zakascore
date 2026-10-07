from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from services.auth import verify_access_token
from services.authorization import get_user_merchants
from services.onboarding import create_dashboard_merchant, redeem_connect_code
from bi.visualization import prepare_revenue_data, prepare_top_offerings_data
from bi.overview import get_business_overview
from bi.visualization import prepare_payment_method_data
from services.credit_scoring import get_merchant_credit_score
from datetime import date
from database.connection import get_db as get_connection

router = APIRouter()

def get_db():
    return get_connection()


def get_current_user_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


def get_current_merchant_id(authorization: str = Header(...)) -> str:
    user_id = get_current_user_id(authorization)
    conn = get_db()
    try:
        merchants = get_user_merchants(user_id, conn)
        if merchants:
            return merchants[0]["merchant_id"]
        raise HTTPException(status_code=403, detail="User does not belong to any merchant")
    finally:
        conn.close()


class ConnectCodeRedemption(BaseModel):
    code: str = Field(min_length=1, max_length=32)


class DashboardOnboardingRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=160)
    store_name: str | None = Field(default=None, min_length=1, max_length=160)


@router.post("/api/onboarding/dashboard", status_code=201)
async def create_dashboard_onboarding(
    request: DashboardOnboardingRequest,
    user_id: str = Depends(get_current_user_id),
):
    conn = get_db()
    try:
        return create_dashboard_merchant(
            user_id,
            request.business_name.strip(),
            conn,
            store_name=request.store_name.strip() if request.store_name else None,
        )
    finally:
        conn.close()


@router.post("/api/connect-codes/redeem")
async def redeem_dashboard_connect_code(
    request: ConnectCodeRedemption,
    user_id: str = Depends(get_current_user_id),
):
    conn = get_db()
    try:
        redeemed = redeem_connect_code(request.code.strip().upper(), conn, user_id=user_id)
        return {
            "store_id": redeemed.store_id,
            "merchant_id": redeemed.merchant_id,
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid or expired connect code") from error
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