import statistics
from collections import namedtuple
from datetime import date, datetime, timedelta

from bi.metrics import (
    MIN_DAYS_FOR_VOLATILITY,
    calculate_total_revenue,
    calculate_transaction_count,
    calculate_average_transaction,
    calculate_revenue_by_date,
    calculate_revenue_growth,
    calculate_revenue_volatility,
    calculate_recency,
)

# Same shape the service layer passes in (naive SAST datetimes, float amounts).
SimpleTransaction = namedtuple(
    "SimpleTransaction", ["amount_zar", "transaction_date", "payment_method"]
)


def tx(amount, when, method="cash"):
    return SimpleTransaction(float(amount), when, method)


def create_transactions():
    return [
        tx(100, datetime(2026, 8, 1, 10, 0), "cash"),
        tx(50, datetime(2026, 8, 1, 12, 0), "digital"),
        tx(200, datetime(2026, 8, 2, 14, 0), "digital"),
    ]


def daily_transactions(amounts):
    """One transaction per day, starting 2026-08-01, one per amount."""
    start = datetime(2026, 8, 1, 10, 0)
    return [tx(amount, start + timedelta(days=i)) for i, amount in enumerate(amounts)]


# ---------- totals ----------

def test_total_revenue():
    assert calculate_total_revenue(create_transactions()) == 350


def test_total_revenue_empty():
    assert calculate_total_revenue([]) == 0


def test_transaction_count():
    assert calculate_transaction_count(create_transactions()) == 3


def test_transaction_count_empty():
    assert calculate_transaction_count([]) == 0


def test_average_transaction():
    assert calculate_average_transaction(create_transactions()) == 350 / 3


def test_average_transaction_empty():
    assert calculate_average_transaction([]) == 0.0


# ---------- revenue by date ----------

def test_revenue_by_date():
    result = calculate_revenue_by_date(create_transactions())

    assert result == {
        date(2026, 8, 1): 150.0,
        date(2026, 8, 2): 200.0,
    }


def test_revenue_by_date_is_sorted():
    transactions = [
        tx(10, datetime(2026, 8, 3, 9, 0)),
        tx(20, datetime(2026, 8, 1, 9, 0)),
        tx(30, datetime(2026, 8, 2, 9, 0)),
    ]

    dates = list(calculate_revenue_by_date(transactions).keys())

    assert dates == sorted(dates)


def test_revenue_by_date_empty():
    assert calculate_revenue_by_date([]) == {}


# ---------- growth ----------

def test_revenue_growth():
    assert calculate_revenue_growth(12000, 10000) == 20


def test_revenue_decline():
    assert calculate_revenue_growth(8000, 10000) == -20


def test_revenue_growth_from_zero():
    assert calculate_revenue_growth(10000, 0) is None


def test_revenue_growth_flat():
    assert calculate_revenue_growth(10000, 10000) == 0


# ---------- volatility ----------

def test_revenue_volatility_matches_stdev_of_daily_revenue():
    amounts = [100, 200, 300, 400, 500, 600, 700]

    result = calculate_revenue_volatility(daily_transactions(amounts))

    assert result == statistics.stdev(amounts)
    assert result > 0


def test_revenue_volatility_for_constant_revenue():
    transactions = daily_transactions([100] * MIN_DAYS_FOR_VOLATILITY)

    assert calculate_revenue_volatility(transactions) == 0.0


def test_revenue_volatility_sums_transactions_within_a_day():
    # Volatility is over daily totals, not individual transactions.
    transactions = daily_transactions([100] * MIN_DAYS_FOR_VOLATILITY)
    transactions.append(tx(100, datetime(2026, 8, 1, 15, 0)))  # day 1 now totals 200

    expected = statistics.stdev([200] + [100] * (MIN_DAYS_FOR_VOLATILITY - 1))

    assert calculate_revenue_volatility(transactions) == expected


def test_revenue_volatility_needs_minimum_days():
    below = daily_transactions([100, 200, 300, 400, 500, 600])  # 6 days

    assert calculate_revenue_volatility(below) is None


def test_revenue_volatility_computed_at_minimum_days():
    amounts = list(range(100, 100 * (MIN_DAYS_FOR_VOLATILITY + 1), 100))

    assert calculate_revenue_volatility(daily_transactions(amounts)) is not None


def test_revenue_volatility_insufficient_data():
    transactions = [tx(100, datetime(2026, 8, 1, 10, 0))]

    assert calculate_revenue_volatility(transactions) is None


def test_revenue_volatility_empty():
    assert calculate_revenue_volatility([]) is None


# ---------- recency ----------

def test_recency():
    result = calculate_recency(create_transactions(), datetime(2026, 8, 5, 10, 0))

    assert result == 2


def test_recency_empty_transactions():
    assert calculate_recency([], datetime(2026, 8, 5, 10, 0)) is None


def test_recency_uses_latest_transaction():
    # Input order shouldn't matter: the most recent transaction wins.
    transactions = list(reversed(create_transactions()))

    result = calculate_recency(transactions, datetime(2026, 8, 10, 10, 0))

    assert result == 7


def test_recency_same_day_is_zero():
    result = calculate_recency(create_transactions(), datetime(2026, 8, 2, 20, 0))

    assert result == 0