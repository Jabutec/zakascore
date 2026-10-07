"""Dashboard API.

Every route is protected the same way:
    1. get_current_user_id   verifies the Neon Auth token (services/auth.py) -> user id
    2. get_current_merchant  checks that user belongs to the merchant (services/authorization.py)
Routes are plain `def` (not `async def`) because the database calls block; FastAPI runs
them in a thread pool instead of freezing the event loop.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from bi.overview import get_business_overview
from bi.visualization import (
    prepare_payment_method_data,
    prepare_revenue_data,
    prepare_top_offerings_data,
)
from database.connection import get_db
from services.auth import verify_access_token
from services.authorization import get_user_merchants, require_merchant_access
from services.credit_scoring import InsufficientHistoryError, get_merchant_credit_assessment
from services.onboarding import (
    create_dashboard_merchant,
    redeem_connect_code_for_user,
)
from services.tiers import get_entitlements

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)

NO_MERCHANT_DETAIL = "User does not belong to any merchant"  # the dashboard may match on this text


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
def get_conn():
    """One pooled connection per request, shared by every dependency and the route.
    Commits when the request succeeds and rolls back if it raises."""
    with get_db() as conn:
        yield conn


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    unauthorized = {"WWW-Authenticate": "Bearer"}
    if credentials is None:
        raise HTTPException(status_code=401, detail="Invalid authorization header", headers=unauthorized)

    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers=unauthorized)
    return user_id


@dataclass
class CurrentMerchant:
    user_id: str
    merchant_id: UUID
    role: str
    tier: str
    created_at: datetime


def get_current_merchant(
    user_id: str = Depends(get_current_user_id),
    x_merchant_id: str | None = Header(default=None),
    conn=Depends(get_conn),
) -> CurrentMerchant:
    """The merchant this request is for.

    Users with one business need nothing extra. Users with several send an
    `X-Merchant-Id` header, which is checked against their memberships. Without it they
    get their oldest business. There is no fallback that treats a user id as a merchant id.
    """
    if x_merchant_id:
        try:
            access = require_merchant_access(user_id, x_merchant_id, conn)
        except PermissionError:
            raise HTTPException(status_code=403, detail="No access to this business")
    else:
        merchants = get_user_merchants(user_id, conn)
        if not merchants:
            raise HTTPException(status_code=403, detail=NO_MERCHANT_DETAIL)
        access = merchants[0]

    row = conn.execute(
        "SELECT tier, created_at FROM merchants WHERE merchant_id = %s",
        (access["merchant_id"],),
    ).fetchone()

    return CurrentMerchant(
        user_id=user_id,
        merchant_id=access["merchant_id"],
        role=access["role"],
        tier=row[0],
        created_at=row[1],
    )


def get_current_merchant_id(merchant: CurrentMerchant = Depends(get_current_merchant)) -> UUID:
    """Kept for anything that still imports it."""
    return merchant.merchant_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
class DashboardOnboardingRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=100)
    store_name: str | None = Field(default=None, min_length=1, max_length=100)


class ConnectCodeRedemption(BaseModel):
    code: str = Field(min_length=1, max_length=32)


@router.post("/api/onboarding/dashboard", status_code=201)
def create_dashboard_onboarding(
    request: DashboardOnboardingRequest,
    user_id: str = Depends(get_current_user_id),
    conn=Depends(get_conn),
):
    try:
        return create_dashboard_merchant(
            user_id,
            request.business_name.strip(),
            conn,
            store_name=request.store_name.strip() if request.store_name else None,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/api/connect-codes/redeem")
def redeem_dashboard_connect_code(
    request: ConnectCodeRedemption,
    user_id: str = Depends(get_current_user_id),
    conn=Depends(get_conn),
):
    try:
        return redeem_connect_code_for_user(request.code, user_id, conn)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired connect code",
        ) from error


@router.get("/api/transactions")
def get_my_transactions(
    limit: int = Query(20, ge=1, le=100),
    merchant: CurrentMerchant = Depends(get_current_merchant),
    conn=Depends(get_conn),
):
    rows = conn.execute(
        """SELECT t.transaction_id, t.amount_zar, t.quantity,
                  t.payment_method, t.transaction_date
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE
           ORDER BY t.transaction_date DESC
           LIMIT %s""",
        (merchant.merchant_id, limit),
    ).fetchall()

    return [
        {
            "transaction_id": row[0],
            "amount_zar": round(float(row[1]), 2),
            "quantity": row[2],
            "payment_method": row[3],
            "transaction_date": row[4].isoformat(),
        }
        for row in rows
    ]


@router.get("/api/revenue")
def get_my_revenue(
    days: int | None = Query(None, ge=1, le=3650),
    merchant: CurrentMerchant = Depends(get_current_merchant),
    conn=Depends(get_conn),
):
    """Daily revenue in South African time. Pass `days` to limit how far back it goes."""
    sql = """SELECT (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date AS day,
                    SUM(t.amount_zar) AS total
             FROM transactions t
             JOIN stores s ON s.store_id = t.store_id
             WHERE s.merchant_id = %s AND t.is_voided = FALSE"""
    params: list = [merchant.merchant_id]
    if days is not None:
        sql += " AND t.transaction_date >= now() - make_interval(days => %s)"
        params.append(days)
    sql += " GROUP BY 1 ORDER BY 1 ASC"

    rows = conn.execute(sql, params).fetchall()
    return prepare_revenue_data({row[0]: row[1] for row in rows})


@router.get("/api/top-offerings")
def get_my_top_offerings(
    limit: int = Query(10, ge=1, le=100),
    merchant: CurrentMerchant = Depends(get_current_merchant),
    conn=Depends(get_conn),
):
    return prepare_top_offerings_data(merchant.merchant_id, conn, limit=limit)


@router.get("/api/overview")
def get_my_overview(
    merchant: CurrentMerchant = Depends(get_current_merchant),
    conn=Depends(get_conn),
):
    return get_business_overview(merchant.merchant_id, conn)


@router.get("/api/payment-methods")
def get_my_payment_methods(
    merchant: CurrentMerchant = Depends(get_current_merchant),
    conn=Depends(get_conn),
):
    """Historical sales without a payment method show as "unknown" so the chart adds up."""
    rows = conn.execute(
        """SELECT COALESCE(t.payment_method, 'unknown') AS payment_method,
                  SUM(t.amount_zar) AS total
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE
           GROUP BY 1""",
        (merchant.merchant_id,),
    ).fetchall()
    return prepare_payment_method_data({row[0]: row[1] for row in rows})


@router.get("/api/credit-score")
def get_my_credit_score(
    merchant: CurrentMerchant = Depends(get_current_merchant),
    conn=Depends(get_conn),
):
    """`credit_score` is null while the profile is still being built. `status` says why."""
    try:
        assessment = get_merchant_credit_assessment(merchant.merchant_id, conn)
    except InsufficientHistoryError as error:
        return {
            "status": "building",
            "credit_score": None,
            "message": str(error),
            "weeks_of_history": error.weeks_of_history,
            "weeks_required": error.weeks_required,
        }

    return {
        "status": "scored",
        "credit_score": assessment["score"],
        "components": assessment["components"],
        "metrics": assessment["metrics"],
        "window": assessment["window"],
    }


@router.get("/api/entitlements")
def get_my_entitlements(merchant: CurrentMerchant = Depends(get_current_merchant)):
    """Which features this merchant's plan includes, so the dashboard can draw the locks.
    Routes for premium features must still check on the server (require_feature)."""
    return {"role": merchant.role, **get_entitlements(merchant.tier, merchant.created_at)}