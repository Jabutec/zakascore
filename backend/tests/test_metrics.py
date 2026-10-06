from datetime import datetime, timezone
from uuid import uuid4
from validation.models import Transaction
from bi.metrics import (
    calculate_total_revenue,
    calculate_transaction_count,
    calculate_average_transaction,
    calculate_revenue_by_date,
    calculate_revenue_growth,
    calculate_revenue_volatility,
    calculate_recency
)

def make_transaction(amount, transaction_date, payment_method="cash"):
    return Transaction(
        transaction_id=uuid4(),
        store_id=uuid4(),
        source_id=uuid4(),
        client_txn_id=uuid4(),
        input_type="manual",
        amount_zar=amount,
        payment_method=payment_method,
        transaction_date=transaction_date.replace(tzinfo=timezone.utc),
    )


def create_transactions():
    return [
        make_transaction(100, datetime(2026, 8, 1, 10, 0)),
        make_transaction(50, datetime(2026, 8, 1, 12, 0), "digital"),
        make_transaction(200, datetime(2026, 8, 2, 14, 0), "digital"),
    ]

def test_total_revenue():
    transactions = create_transactions()

    result = calculate_total_revenue(transactions)

    assert result == 350


def test_transaction_count():
    transactions = create_transactions()

    result = calculate_transaction_count(transactions)

    assert result == 3


def test_average_transaction():
    transactions = create_transactions()

    result = calculate_average_transaction(transactions)

    assert result == 350 / 3


def test_average_transaction_empty():
    result = calculate_average_transaction([])

    assert result == 0.0


def test_revenue_by_date():
    transactions = create_transactions()

    result = calculate_revenue_by_date(transactions)

    assert result == {
        transactions[0].transaction_date.date(): 150.0,
        transactions[2].transaction_date.date(): 200.0,
    }


def test_revenue_by_date_is_sorted():
    transactions = create_transactions()

    result = calculate_revenue_by_date(transactions)

    dates = list(result.keys())

    assert dates == sorted(dates)


def test_revenue_growth():
    result = calculate_revenue_growth(12000, 10000)

    assert result == 20


def test_revenue_decline():
    result = calculate_revenue_growth(8000, 10000)

    assert result == -20


def test_revenue_growth_from_zero():
    result = calculate_revenue_growth(10000, 0)

    assert result is None
    
def test_revenue_volatility():
    transactions = create_transactions()

    result = calculate_revenue_volatility(transactions)

    assert result > 0

def test_revenue_volatility_for_constant_revenue():
    transactions = [
        make_transaction(100, datetime(2026, 8, 1, 10, 0)),
        make_transaction(100, datetime(2026, 8, 2, 10, 0)),
    ]

    assert calculate_revenue_volatility(transactions) == 0.0
    
def test_revenue_volatility_insufficient_data():
    transactions = [
        make_transaction(100, datetime(2026, 8, 1, 10, 0))
    ]

    assert calculate_revenue_volatility(transactions) == 0.0
    
def test_recency():
    transactions = create_transactions()

    reference_date = datetime(2026, 8, 5, 10, 0)

    result = calculate_recency(
        transactions,
        reference_date.replace(tzinfo=timezone.utc)
    )

    assert result == 2

def test_recency_empty_transactions():
    result = calculate_recency(
        [],
        datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc)
    )

    assert result is None

def test_recency_uses_latest_transaction():
    transactions = create_transactions()

    reference_date = datetime(2026, 8, 10, 10, 0)

    result = calculate_recency(
        transactions,
        reference_date.replace(tzinfo=timezone.utc)
    )

    assert result == 7