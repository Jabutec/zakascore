from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from validation.models import (
    DataSource,
    FinancialSnapshot,
    Merchant,
    MerchantUser,
    Offering,
    Store,
    Transaction,
    TransactionCreate,
)


def now():
    return datetime.now(timezone.utc)


# ---------- payload factories (override one field per test) ----------

def transaction_data(**overrides):
    data = {
        "transaction_id": uuid4(),
        "store_id": uuid4(),
        "source_id": uuid4(),
        "client_txn_id": uuid4(),
        "input_type": "pos_tap",
        "amount_zar": Decimal("100.00"),
        "payment_method": "digital",
        "transaction_date": now(),
    }
    data.update(overrides)
    return data


def snapshot_data(**overrides):
    data = {
        "snapshot_id": uuid4(),
        "store_id": uuid4(),
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 1, 31),
        "total_revenue_zar": 1000,
        "transaction_count": 50,
        "average_transaction_zar": 20,
        "cash_revenue_zar": 500,
        "digital_revenue_zar": 500,
        "created_at": now(),
    }
    data.update(overrides)
    return data


def data_source_data(**overrides):
    data = {
        "source_id": uuid4(),
        "store_id": uuid4(),
        "source_name": "Vertical",
        "source_type": "pos",
        "created_at": now(),
    }
    data.update(overrides)
    return data


# ---------- Transaction: amount ----------

@pytest.mark.parametrize("amount", ["-100", "-450", "-0.01", "0"])
def test_invalid_transaction_amount(amount):
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(amount_zar=Decimal(amount)))


@pytest.mark.parametrize("amount", ["0.01", "1", "450", "1000", "9999999999.99"])
def test_valid_transaction_amount(amount):
    transaction = Transaction(**transaction_data(amount_zar=Decimal(amount)))

    assert transaction.amount_zar == Decimal(amount)


@pytest.mark.parametrize("amount", ["10.001", "0.005", "10000000000.00"])
def test_amount_rejects_extra_precision_or_too_many_digits(amount):
    # NUMERIC(12,2): more than 2 decimals or more than 12 digits total
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(amount_zar=Decimal(amount)))


# ---------- Transaction: enums ----------

@pytest.mark.parametrize("payment_method", ["banana", "cheque", "Crypto"])
def test_invalid_payment_method(payment_method):
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(payment_method=payment_method))


@pytest.mark.parametrize("payment_method", ["cash", "digital"])
def test_valid_payment_method(payment_method):
    transaction = Transaction(**transaction_data(payment_method=payment_method))

    assert transaction.payment_method == payment_method


@pytest.mark.parametrize("input_type", ["banana", "cheque", "inventory"])
def test_invalid_input_type(input_type):
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(input_type=input_type))


@pytest.mark.parametrize("input_type", ["pos_tap", "voice", "manual", "pwa", "csv", "api"])
def test_valid_input_type(input_type):
    transaction = Transaction(**transaction_data(input_type=input_type))

    assert transaction.input_type == input_type


# ---------- Transaction: structure ----------

def test_transaction_rejects_non_uuid_ids():
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(transaction_id="T001"))

    with pytest.raises(ValidationError):
        Transaction(**transaction_data(store_id="S001"))


def test_transaction_rejects_unknown_fields():
    # merchant is derived via the store, so merchant_id is not a transaction field
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(merchant_id=uuid4()))


def test_transaction_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(transaction_date=datetime.now()))


@pytest.mark.parametrize("quantity", [0, -1])
def test_transaction_quantity_must_be_positive(quantity):
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(offering_id=uuid4(), quantity=quantity))


def test_payment_method_is_required():
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(payment_method=None))


def test_quantity_requires_offering_id():
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(quantity=2))


# ---------- Transaction: void state ----------

def test_voided_transaction_requires_voided_at():
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(is_voided=True))


def test_voided_at_requires_is_voided():
    with pytest.raises(ValidationError):
        Transaction(**transaction_data(is_voided=False, voided_at=now()))


def test_valid_voided_transaction():
    transaction = Transaction(
        **transaction_data(is_voided=True, voided_at=now(), void_reason="duplicate")
    )

    assert transaction.is_voided is True


# ---------- TransactionCreate ----------

def test_transaction_create_defaults_date_to_now_utc():
    data = transaction_data()
    del data["transaction_id"]
    del data["transaction_date"]

    transaction = TransactionCreate(**data)

    assert transaction.transaction_date.tzinfo is not None


def test_transaction_create_rejects_transaction_id():
    # Postgres generates transaction_id
    with pytest.raises(ValidationError):
        TransactionCreate(**{**transaction_data(), "transaction_id": uuid4()})


def test_client_transaction_id_is_required():
    transaction = transaction_data()
    del transaction["client_txn_id"]
    with pytest.raises(ValidationError):
        Transaction(**transaction)

    transaction_create = transaction_data()
    del transaction_create["transaction_id"]
    del transaction_create["client_txn_id"]
    with pytest.raises(ValidationError):
        TransactionCreate(**transaction_create)


def test_transaction_create_rejects_dates_outside_allowed_window():
    base = transaction_data()
    del base["transaction_id"]
    with pytest.raises(ValidationError):
        TransactionCreate(
            **{**base, "transaction_date": now() + timedelta(minutes=6)}
        )
    with pytest.raises(ValidationError):
        TransactionCreate(
            **{**base, "transaction_date": now() - timedelta(days=31)}
        )


def test_transaction_create_accepts_dates_inside_allowed_window():
    base = transaction_data()
    del base["transaction_id"]
    assert TransactionCreate(
        **{**base, "transaction_date": now() + timedelta(minutes=4)}
    )
    assert TransactionCreate(
        **{**base, "transaction_date": now() - timedelta(days=29)}
    )


# ---------- Merchant / MerchantUser / Store / Offering ----------

def test_merchant():
    merchant_id = uuid4()

    merchant = Merchant(
        merchant_id=merchant_id,
        business_name="vertical",
        location="Joburg",
        created_at=now(),
    )

    assert merchant.merchant_id == merchant_id
    assert merchant.tier == "insights"


def test_merchant_rejects_invalid_tier():
    with pytest.raises(ValidationError):
        Merchant(merchant_id=uuid4(), business_name="vertical", tier="platinum")


def test_merchant_user_defaults_to_owner_and_rejects_bad_role():
    user = MerchantUser(user_id=uuid4(), merchant_id=uuid4())

    assert user.role == "owner"

    with pytest.raises(ValidationError):
        MerchantUser(user_id=uuid4(), merchant_id=uuid4(), role="god")


def test_store_and_offering():
    store = Store(store_id=uuid4(), merchant_id=uuid4(), store_name="Main")
    offering = Offering(offering_id=uuid4(), store_id=store.store_id, offering_name="Shirt")

    assert store.store_name == "Main"
    assert offering.offering_name == "Shirt"


# ---------- DataSource ----------

@pytest.mark.parametrize("source_type", ["cash", "object", "banana", "car"])
def test_invalid_source_type(source_type):
    with pytest.raises(ValidationError):
        DataSource(**data_source_data(source_type=source_type))


@pytest.mark.parametrize(
    "source_type",
    ["pos", "bank_statement", "accounting_software", "online_store", "pwa", "csv", "manual"],
)
def test_valid_source_type(source_type):
    source = DataSource(**data_source_data(source_type=source_type))

    assert source.source_type == source_type
    assert source.is_active is True


# ---------- FinancialSnapshot ----------

NON_NEGATIVE_FIELDS = [
    "total_revenue_zar",
    "cash_revenue_zar",
    "digital_revenue_zar",
    "transaction_count",
    "average_transaction_zar",
]


@pytest.mark.parametrize("field", NON_NEGATIVE_FIELDS)
def test_non_negative_fields(field):
    with pytest.raises(ValidationError):
        FinancialSnapshot(**snapshot_data(**{field: -1}))


@pytest.mark.parametrize("field", NON_NEGATIVE_FIELDS)
def test_non_negative_accept_valid_fields(field):
    snapshot = FinancialSnapshot(**snapshot_data(**{field: 100}))

    assert getattr(snapshot, field) == 100


@pytest.mark.parametrize("field", NON_NEGATIVE_FIELDS)
def test_non_negative_fields_accept_zero(field):
    snapshot = FinancialSnapshot(**snapshot_data(**{field: 0}))

    assert getattr(snapshot, field) == 0


def test_snapshot_rejects_period_end_before_start():
    with pytest.raises(ValidationError):
        FinancialSnapshot(
            **snapshot_data(period_start=date(2026, 2, 1), period_end=date(2026, 1, 1))
        )


def test_snapshot_allows_single_day_period():
    snapshot = FinancialSnapshot(
        **snapshot_data(period_start=date(2026, 1, 1), period_end=date(2026, 1, 1))
    )

    assert snapshot.period_start == snapshot.period_end


def test_snapshot_growth_and_volatility_are_optional_and_may_be_negative():
    snapshot = FinancialSnapshot(**snapshot_data())

    assert snapshot.revenue_growth_pct is None
    assert snapshot.revenue_volatility is None

    snapshot = FinancialSnapshot(**snapshot_data(revenue_growth_pct=Decimal("-12.5")))

    assert snapshot.revenue_growth_pct == Decimal("-12.5")


def test_snapshot_rejects_merchant_id():
    # snapshots belong to a store, not a merchant
    with pytest.raises(ValidationError):
        FinancialSnapshot(**snapshot_data(merchant_id=uuid4()))