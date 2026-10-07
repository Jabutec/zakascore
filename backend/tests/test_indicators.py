import pytest
from bi.indicators import (
    MIN_PAYMENT_COVERAGE,
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


@pytest.mark.parametrize(
    "cash_revenue, digital_revenue, total_revenue, expected",
    [
        # Full coverage: judged normally
        (20, 80, 100, "high"),
        (90, 10, 100, "low"),
        # Partial coverage above the threshold: still judged on known revenue only
        (30, 70, 150, "high"),
        # Exactly at the coverage threshold: judged (check is strictly "<")
        (20, 80, 200, "high"),
        # Just below the threshold: insufficient
        (20, 79, 200, "insufficient_data"),
        # Mostly legacy sales with no recorded payment method: insufficient
        (10, 10, 1000, "insufficient_data"),
        # No known revenue at all
        (0, 0, 100, "insufficient_data"),
        # total_revenue None or 0 skips the coverage check
        (50, 50, None, "moderate"),
        (50, 50, 0, "moderate"),
    ],
)
def test_determine_digital_payment_adoption_with_coverage(
    cash_revenue, digital_revenue, total_revenue, expected
):
    result = determine_digital_payment_adoption(
        cash_revenue, digital_revenue, total_revenue
    )
    assert result == expected


def test_min_payment_coverage_threshold():
    assert MIN_PAYMENT_COVERAGE == 0.5