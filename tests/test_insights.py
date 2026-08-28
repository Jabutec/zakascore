import pytest

from bi.insights import (
    generate_revenue_insight,
    generate_stability_insight,
    generate_activity_insight,
    generate_business_insights,
)


@pytest.mark.parametrize(
    "trend, expected",
    [
        ("growing", "Revenue is growing."),
        ("declining", "Revenue is declining."),
        ("stable", "Revenue is relatively stable."),
        ("insufficient_data", "Revenue insight is unavailable."),
    ],
)
def test_revenue_insight(trend, expected):
    assert generate_revenue_insight(trend) == expected


@pytest.mark.parametrize(
    "stability, expected",
    [
        ("high", "Revenue is highly volatile."),
        ("moderate", "Revenue shows moderate volatility."),
        ("low", "Revenue is relatively stable."),
        ("insufficient_data", "Revenue stability insight is unavailable."),
    ],
)
def test_stability_insight(stability, expected):
    assert generate_stability_insight(stability) == expected


@pytest.mark.parametrize(
    "activity, expected",
    [
        ("active", "The business is actively recording transactions."),
        ("at_risk", "Transaction activity is slowing and may require attention."),
        ("inactive", "The business has not recorded transactions recently."),
        ("insufficient_data", "Transaction activity insight is unavailable."),
    ],
)
def test_activity_insight(activity, expected):
    assert generate_activity_insight(activity) == expected
    
def test_generate_business_insights():
    result = generate_business_insights(
        "growing",
        "low",
        "active"
    )

    assert result == [
        "Revenue is growing.",
        "Revenue is relatively stable.",
        "The business is actively recording transactions.",
    ]