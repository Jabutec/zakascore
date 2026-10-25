"""Run with: pytest test_credit_profile.py
Uses a small fake connection, so no database is needed."""
from datetime import date, datetime, timedelta

import pytest


from services.credit_scoring import credit_scoring as cs

from services.credit_profile import credit_profile as cp


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0]

    def fetchall(self):
        return self._rows


class FakeConn:
    """Answers the two queries credit_scoring.py makes, from a list of (date, amount)."""

    def __init__(self, sales):
        self.sales = sales

    def execute(self, sql, params):
        if "MIN(" in sql:
            return FakeCursor([(min((d for d, _ in self.sales), default=None),)])
        start, end = params[1].date(), params[2].date()
        by_week = {}
        for day, amount in self.sales:
            if start <= day < end:
                monday = day - timedelta(days=day.weekday())
                revenue, days = by_week.get(monday, (0.0, set()))
                by_week[monday] = (revenue + amount, days | {day})
        return FakeCursor([(m, r, len(d)) for m, (r, d) in sorted(by_week.items())])


def weekly_sales(first_monday, weekly_amounts, days_per_week=4):
    """One sale per trading day, for each given week, starting on first_monday."""
    sales = []
    for i, total in enumerate(weekly_amounts):
        if total <= 0:
            continue
        for d in range(days_per_week):
            sales.append((first_monday + timedelta(weeks=i, days=d), total / days_per_week))
    return sales


MONDAY = date(2026, 9, 7)  # a Monday


def test_partial_first_week_is_skipped():
    assert cs.first_complete_week_start(date(2026, 9, 7)) == date(2026, 9, 7)
    assert cs.first_complete_week_start(date(2026, 9, 10)) == date(2026, 9, 14)


def test_window_is_capped_at_12_weeks_and_never_reaches_before_first_week():
    as_of = date(2027, 1, 20)
    start, end, weeks = cs.scoring_window(as_of, date(2026, 1, 5))
    assert weeks == 12 and end == date(2027, 1, 18) and start == end - timedelta(weeks=12)
    start, end, weeks = cs.scoring_window(as_of, date(2026, 12, 21))
    assert start == date(2026, 12, 21) and weeks == 4


def test_no_transactions_is_no_data():
    profile = cp.get_credit_profile("m1", FakeConn([]), as_of=date(2026, 10, 25), premium=True)
    assert profile["state"] == "no_data" and profile["score"] is None


def test_under_four_weeks_is_building_not_a_low_score():
    conn = FakeConn(weekly_sales(MONDAY, [2000, 2100, 1900]))
    profile = cp.get_credit_profile("m1", conn, as_of=date(2026, 9, 30), premium=True)  # Wed, 3 weeks later
    assert profile["state"] == "building"
    assert profile["score"] is None
    assert profile["progress"]["weeks_of_history"] == 3
    assert profile["progress"]["weeks_remaining"] == 1
    assert profile["progress"]["available_from"] == "2026-10-05"
    assert profile["forecast"] is None


def test_four_complete_weeks_scores_and_is_marked_early():
    conn = FakeConn(weekly_sales(MONDAY, [2400, 2500, 2300, 2600]))
    profile = cp.get_credit_profile("m1", conn, as_of=date(2026, 10, 7), premium=True)  # Wed of week 5
    assert profile["state"] == "scored"
    assert profile["weeks_scored"] == 4 and profile["maturity"] == "early"
    assert 0 <= profile["score"] <= 100
    assert profile["forecast"]["based_on_weeks"] == 4 and profile["forecast"]["confidence"] == "low"


def test_current_week_is_not_scored_but_shows_in_this_week():
    sales = weekly_sales(MONDAY, [2400, 2500, 2300, 2600])
    sales.append((date(2026, 10, 5), 700.0))  # Monday of the week in progress
    profile = cp.get_credit_profile("m1", FakeConn(sales), as_of=date(2026, 10, 7), premium=True)
    assert profile["metrics"]["total_revenue_zar"] == 9800.0  # the 700 is not in the score
    assert profile["this_week"]["revenue_zar"] == 700.0
    assert profile["this_week"]["active_days"] == 1
    assert profile["this_week"]["days_left"] == 4  # Wed: Thu, Fri, Sat, Sun


def test_more_history_raises_maturity():
    conn = FakeConn(weekly_sales(MONDAY, [2500] * 14))
    profile = cp.get_credit_profile("m1", conn, as_of=date(2026, 12, 20), premium=True)
    assert profile["weeks_scored"] == 12 and profile["maturity"] == "established"


def test_free_plan_withholds_premium_fields():
    conn = FakeConn(weekly_sales(MONDAY, [2400, 2500, 2300, 2600]))
    free = cp.get_credit_profile("m1", conn, as_of=date(2026, 10, 7), premium=False)
    assert free["plan"] == "free" and free["score"] is not None and free["band"]
    for key in ("factors", "metrics", "forecast", "score_change"):
        assert free[key] is None
    assert len(free["tips"]) <= 1
    assert free["this_week"]["share_of_typical_week_pct"] is None
    assert "factors" in free["locked"]
    premium = cp.get_credit_profile("m1", conn, as_of=date(2026, 10, 7), premium=True)
    assert premium["factors"] and premium["metrics"] and premium["locked"] == []


def test_building_state_is_not_locked_for_free_users():
    conn = FakeConn(weekly_sales(MONDAY, [2000, 2100]))
    free = cp.get_credit_profile("m1", conn, as_of=date(2026, 9, 24), premium=False)
    assert free["state"] == "building" and free["locked"] == [] and free["progress"]


def test_tips_are_ranked_by_points_available():
    components = {"stability": 90.0, "growth": 50.0, "revenue_level": 20.0, "consistency": 100.0}
    metrics = {
        "weeks_scored": 8, "trading_weeks": 8, "weeks_without_sales": 0,
        "revenue_growth_pct": -10.0, "typical_weekly_revenue_zar": 800.0,
    }
    tips = cp.build_tips(components, metrics)
    assert [t["factor"] for t in tips] == ["revenue_level", "growth"]  # 20.0 > 12.5; stability and consistency are >= 90
    assert tips[0]["impact_points"] == pytest.approx(20.0)


def test_weeks_with_no_sales_count_as_zero_and_trigger_the_tip():
    amounts = [2500, 0, 2500, 2500, 2500]
    conn = FakeConn(weekly_sales(MONDAY, amounts))
    profile = cp.get_credit_profile("m1", conn, as_of=date(2026, 10, 14), premium=True)
    assert profile["metrics"]["weeks_without_sales"] == 1
    assert any("no sales logged" in t["text"] for t in profile["tips"])


def test_forecast_direction_needs_eight_weeks():
    assert cp.build_forecast([100, 100, 100]) is None
    assert cp.build_forecast([100, 100, 100, 100])["direction"] is None
    up = cp.build_forecast([100] * 4 + [150] * 4)
    assert up["direction"] == "up" and up["confidence"] == "medium"


def test_score_change_compares_with_four_weeks_earlier():
    conn = FakeConn(weekly_sales(MONDAY, [2000] * 6 + [3000] * 4))
    profile = cp.get_credit_profile("m1", conn, as_of=date(2026, 11, 18), premium=True)
    assert profile["score_change"] is not None


def test_premium_allowlist(monkeypatch):
    monkeypatch.setenv("PREMIUM_MERCHANT_IDS", "abc, def")
    assert cp.is_premium_merchant("abc") and cp.is_premium_merchant("def")
    assert not cp.is_premium_merchant("xyz")


def test_old_route_helper_still_works():
    conn = FakeConn(weekly_sales(MONDAY, [2400, 2500, 2300, 2600]))
    assert isinstance(cs.get_merchant_credit_score("m1", None, date(2026, 10, 7), conn), float)
    with pytest.raises(ValueError):
        cs.get_merchant_credit_score("m1", None, date(2026, 9, 20), conn)