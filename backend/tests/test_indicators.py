import pytest
from bi.indicators import (
    calculate_transaction_activity,
    determine_activity_status,
    determine_digital_payment_adoption,
    determine_revenue_stability,
    determine_revenue_trend,
)


@pytest.mark.parametrize(
    "revenue_growth, expected",
    [
        (20, "growing"),
        (-20, "declining"),
        (3, "stable"),
        (5, "stable"),
        (-5, "stable"),
        (None, "insufficient_data"),
    ],
)
def test_determine_revenue_trend(revenue_growth, expected):
    assert determine_revenue_trend(revenue_growth) == expected


@pytest.mark.parametrize(
    "transaction_count, active_days, expected",
    [
        (60, 5, "high"),
        (30, 5, "moderate"),
        (10, 5, "low"),
        (10, 0, "insufficient_data"),
        (25, 5, "moderate"),
        (50, 5, "moderate"),
        (55, 5, "high"),
    ],
)
def test_calculate_transaction_activity(transaction_count, active_days, expected):
    assert calculate_transaction_activity(transaction_count, active_days) == expected


@pytest.mark.parametrize(
    "revenue_volatility, expected",
    [
        (None, "insufficient_data"),
        (0.05, "high"),
        (0.10, "high"),
        (0.11, "moderate"),
        (0.15, "moderate"),
        (0.25, "moderate"),
        (0.30, "low"),
    ],
)
def test_determine_revenue_stability(revenue_volatility, expected):
    assert determine_revenue_stability(revenue_volatility) == expected


@pytest.mark.parametrize(
    "days_since_transaction, expected",
    [
        (6, "active"),
        (7, "active"),
        (8, "at_risk"),
        (10, "at_risk"),
        (30, "at_risk"),
        (31, "inactive"),
        (None, "insufficient_data"),
    ],
)
def test_determine_activity_status(days_since_transaction, expected):
    assert determine_activity_status(days_since_transaction) == expected


@pytest.mark.parametrize(
    "cash_revenue, digital_revenue, expected",
    [
        (20, 80, "high"),
        (50, 50, "moderate"),
        (90, 10, "low"),
        (0, 0, "insufficient_data"),
        (70, 30, "moderate"),
        (30, 70, "high"),
        (71, 29, "low"),
    ],
)
def test_determine_digital_payment_adoption(cash_revenue, digital_revenue, expected):
    assert determine_digital_payment_adoption(cash_revenue, digital_revenue) == expected