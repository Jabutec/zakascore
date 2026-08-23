from datetime import datetime
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


def create_transactions():
    return [
        Transaction(
            transaction_id="T001",
            merchant_id="M001",
            source_id="S001",
            input_type=None,
            amount_zar=100,
            payment_method="cash",
            transaction_date=datetime(2026, 8, 1, 10, 0),
        ),
        Transaction(
            transaction_id="T002",
            merchant_id="M001",
            source_id="S001",
            input_type=None,
            amount_zar=50,
            payment_method="digital",
            transaction_date=datetime(2026, 8, 1, 12, 0),
        ),
        Transaction(
            transaction_id="T003",
            merchant_id="M001",
            source_id="S001",
            input_type=None,
            amount_zar=200,
            payment_method="digital",
            transaction_date=datetime(2026, 8, 2, 14, 0),
        ),
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
        Transaction(
            transaction_id="T001",
            merchant_id="M001",
            source_id="S001",
            input_type=None,
            amount_zar=100,
            payment_method="cash",
            transaction_date=datetime(2026, 8, 1, 10, 0),
        ),
        Transaction(
            transaction_id="T002",
            merchant_id="M001",
            source_id="S001",
            input_type=None,
            amount_zar=100,
            payment_method="cash",
            transaction_date=datetime(2026, 8, 2, 10, 0),
        ),
    ]

    assert calculate_revenue_volatility(transactions) == 0.0
    
def test_revenue_volatility_insufficient_data():
    transactions = [
        Transaction(
            transaction_id="T001",
            merchant_id="M001",
            source_id="S001",
            input_type=None,
            amount_zar=100,
            payment_method="cash",
            transaction_date=datetime(2026, 8, 1, 10, 0),
        )
    ]

    assert calculate_revenue_volatility(transactions) == 0.0
    
def test_recency():
    transactions = create_transactions()

    reference_date = datetime(2026, 8, 5, 10, 0)

    result = calculate_recency(
        transactions,
        reference_date
    )

    assert result == 2

def test_recency_empty_transactions():
    result = calculate_recency(
        [],
        datetime(2026, 8, 5, 10, 0)
    )

    assert result is None

def test_recency_uses_latest_transaction():
    transactions = create_transactions()

    reference_date = datetime(2026, 8, 10, 10, 0)

    result = calculate_recency(
        transactions,
        reference_date
    )

    assert result == 7