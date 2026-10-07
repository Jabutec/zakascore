"""FastAPI application and authenticated PWA transaction logging endpoint."""
from contextlib import asynccontextmanager
import os
from decimal import Decimal
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AwareDatetime, ValidationError

from api.auth import get_conn, get_current_user_id, router as auth_router
from database.connection import close_pool
from services.authorization import require_store_access
from services.onboarding import get_pwa_source_id
from services.offerings import get_or_create_offering
from services.tiers import has_reached_limit
from validation.models import (
    PaymentMethod,
    StrictModel,
    TransactionCreate,
)

load_dotenv()

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        close_pool()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PwaTransactionRequest(StrictModel):
    store_id: UUID
    client_txn_id: UUID
    amount_zar: Decimal
    payment_method: PaymentMethod
    offering_name: str | None = None
    quantity: int | None = None
    transaction_date: AwareDatetime | None = None


TRANSACTION_COLUMNS = (
    "transaction_id, client_txn_id, store_id, source_id, input_type, amount_zar, "
    "payment_method, offering_id, quantity, transaction_date, is_voided, "
    "voided_at, void_reason, created_at"
)


def _transaction_response(row) -> dict:
    return {
        "transaction_id": str(row[0]),
        "client_txn_id": str(row[1]),
        "store_id": str(row[2]),
        "source_id": str(row[3]),
        "input_type": row[4],
        "amount_zar": round(float(row[5]), 2),
        "payment_method": row[6],
        "offering_id": str(row[7]) if row[7] is not None else None,
        "quantity": row[8],
        "transaction_date": row[9].isoformat(),
        "is_voided": row[10],
        "voided_at": row[11].isoformat() if row[11] is not None else None,
        "void_reason": row[12],
        "created_at": row[13].isoformat() if row[13] is not None else None,
    }


def _select_transaction(conn, store_id: UUID, client_txn_id: UUID):
    return conn.execute(
        f"""SELECT {TRANSACTION_COLUMNS}
            FROM transactions
            WHERE store_id = %s AND client_txn_id = %s""",
        (store_id, client_txn_id),
    ).fetchone()


def _validate_transaction(
    request: PwaTransactionRequest, source_id: UUID, offering_id: UUID | None
) -> TransactionCreate:
    transaction_data = {
        "store_id": request.store_id,
        "source_id": source_id,
        "client_txn_id": request.client_txn_id,
        "offering_id": offering_id,
        "quantity": request.quantity,
        "input_type": "pwa",
        "amount_zar": request.amount_zar,
        "payment_method": request.payment_method,
    }
    if request.transaction_date is not None:
        transaction_data["transaction_date"] = request.transaction_date
    return TransactionCreate(**transaction_data)


@app.post("/transactions")
def create_transaction(
    request: PwaTransactionRequest,
    user_id: str = Depends(get_current_user_id),
    conn=Depends(get_conn),
):
    try:
        store_access = require_store_access(
            user_id, request.store_id, conn, min_role="employee"
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))

    existing = _select_transaction(conn, request.store_id, request.client_txn_id)
    if existing is not None:
        try:
            _validate_transaction(request, existing[3], existing[7])
        except ValidationError as error:
            raise HTTPException(status_code=422, detail=str(error))
        return _transaction_response(existing)

    try:
        source_id = get_pwa_source_id(request.store_id, conn)
    except LookupError as error:
        raise HTTPException(status_code=500, detail=str(error))

    offering_id = None
    if request.offering_name is not None:
        try:
            offering_id = get_or_create_offering(
                request.store_id, request.offering_name, conn
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error))

    try:
        transaction = _validate_transaction(request, source_id, offering_id)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error))

    merchant = conn.execute(
        "SELECT tier, created_at FROM merchants WHERE merchant_id = %s",
        (store_access["merchant_id"],),
    ).fetchone()
    if has_reached_limit(
        store_access["merchant_id"], merchant[0], merchant[1], conn
    ):
        existing = _select_transaction(
            conn, request.store_id, request.client_txn_id
        )
        if existing is not None:
            return _transaction_response(existing)
        raise HTTPException(
            status_code=429,
            detail="Transaction not recorded — you've reached your daily limit.",
        )

    row = conn.execute(
        f"""INSERT INTO transactions (
                store_id, source_id, client_txn_id, input_type, amount_zar,
                payment_method, offering_id, quantity, transaction_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (store_id, client_txn_id) DO NOTHING
            RETURNING {TRANSACTION_COLUMNS}""",
        (
            transaction.store_id,
            transaction.source_id,
            transaction.client_txn_id,
            transaction.input_type.value,
            transaction.amount_zar,
            transaction.payment_method.value,
            transaction.offering_id,
            transaction.quantity,
            transaction.transaction_date,
        ),
    ).fetchone()

    if row is None:
        row = _select_transaction(conn, request.store_id, request.client_txn_id)
    if row is None:
        raise RuntimeError("Transaction insert returned no row for its idempotency key")
    return _transaction_response(row)
