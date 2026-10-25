"""Credit profile: everything the credit page needs, built on top of credit_scoring.py.

The score itself is unchanged. This module adds the parts around it: a band, the four
factors, tips ranked by how many points they could add, a plain range for next week's
takings, a "this week so far" view that reacts live, and the free / premium split.

The plan split happens HERE, on the server. The route decides whether the merchant's tier includes
the full credit profile (Feature.CREDIT_PREVIEW) and passes `premium`; merchants on the Insights
tier never receive the full fields, so hiding them in the page is not what protects them.
"""
import statistics
import os
from datetime import date, datetime, timedelta

try:  # works whether this file sits in a package or next to credit_scoring.py
    from .credit_scoring import (
        MIN_TRADING_DAYS_PER_WEEK,
        MIN_WEEKS_TO_SCORE,
        SAST,
        WEIGHTS,
        InsufficientHistoryError,
        _to_date,
        first_complete_week_start,
        get_first_transaction_date,
        get_merchant_credit_assessment,
        get_week_to_date,
    )
except ImportError:  # pragma: no cover
    from credit_scoring import (
        MIN_TRADING_DAYS_PER_WEEK,
        MIN_WEEKS_TO_SCORE,
        SAST,
        WEIGHTS,
        InsufficientHistoryError,
        _to_date,
        first_complete_week_start,
        get_first_transaction_date,
        get_merchant_credit_assessment,
        get_week_to_date,
    )

# Placeholders, like the weights: descriptive labels, not risk levels.
SCORE_BANDS = ((75, "Strong"), (60, "Steady"), (40, "Developing"), (0, "Getting started"))

FACTOR_INFO = {
    "stability": ("Weekly stability", "How evenly your takings hold from week to week."),
    "growth": ("Growth", "Your recent weeks compared with your earlier weeks."),
    "revenue_level": ("Revenue level", "Your typical weekly takings."),
    "consistency": (
        "Trading consistency",
        f"Weeks in which you traded on at least {MIN_TRADING_DAYS_PER_WEEK} days.",
    ),
}

TREND_THRESHOLD_PCT = 10
MAX_TIPS = 3
DISCLAIMER = (
    "This score reflects the sales recorded in ZakaScore. It describes your business activity. "
    "It is not a credit decision and it does not predict whether a loan would be repaid."
)

FREE_LOCKED = ["factors", "metrics", "forecast", "score_change", "more_tips", "report"]


# ---------------------------------------------------------------------------
# Pure builders (no database access, easy to test)
# ---------------------------------------------------------------------------
def _rand(value: float) -> str:
    return "R" + f"{round(value):,}".replace(",", " ")


def band_for(score: float) -> str:
    for floor, name in SCORE_BANDS:
        if score >= floor:
            return name
    return SCORE_BANDS[-1][1]


def build_factors(components: dict) -> list[dict]:
    factors = []
    for name, weight in WEIGHTS.items():
        value = components[name]
        label, description = FACTOR_INFO[name]
        factors.append(
            {
                "key": name,
                "label": label,
                "description": description,
                "score": round(value, 1),
                "weight_pct": round(weight * 100),
                "points_available": round(weight * (100 - value), 1),
                "status": "strong" if value >= 75 else "ok" if value >= 50 else "focus",
            }
        )
    return factors


def _tip_text(name: str, metrics: dict) -> str:
    weeks = metrics["weeks_scored"]
    if name == "consistency":
        short = weeks - metrics["trading_weeks"]
        return (
            f"{short} of your last {weeks} weeks had fewer than {MIN_TRADING_DAYS_PER_WEEK} trading days "
            "logged. If you traded on more days, log those sales so your weeks show what really happened."
        )
    if name == "stability":
        empty = metrics["weeks_without_sales"]
        if empty:
            return (
                f"{empty} week{'s' if empty != 1 else ''} had no sales logged, and those count as zero. "
                "If you were open, log those sales."
            )
        return (
            "Your weekly takings swing quite a bit. Log every sale, including small ones, so busy and "
            "quiet weeks show what really happened."
        )
    if name == "growth":
        growth = metrics["revenue_growth_pct"]
        if growth is None:
            return (
                "Growth compares your recent weeks with your earlier weeks. Keep logging and it will "
                "appear once your earlier weeks have sales."
            )
        if growth < 0:
            return (
                f"Your recent weeks are {abs(growth):.0f}% below your earlier weeks. Steady weeks from "
                "here lift this part of your score."
            )
        return "Your growth is holding steady. Sustained increases lift this part of your score."
    return (
        f"Your typical week is about {_rand(metrics['typical_weekly_revenue_zar'])}. This part of your "
        "score rises as your usual weekly takings grow."
    )


def build_tips(components: dict, metrics: dict, limit: int = MAX_TIPS) -> list[dict]:
    """Tips for the factors with the most room to improve, biggest first."""
    tips = []
    for name, weight in WEIGHTS.items():
        value = components[name]
        if value >= 90:
            continue
        tips.append(
            {
                "factor": name,
                "impact_points": round(weight * (100 - value), 1),
                "text": _tip_text(name, metrics),
            }
        )
    tips.sort(key=lambda tip: tip["impact_points"], reverse=True)
    return tips[:limit]


def build_forecast(weekly_revenues: list[float]) -> dict | None:
    """A plain range for next week, from the merchant's own recent weeks.

    Deliberately simple: the middle of recent weeks and the range most weeks fall in. It is
    not a statistical prediction interval, and the page should not present it as one.
    """
    if len(weekly_revenues) < MIN_WEEKS_TO_SCORE:
        return None
    low, _, high = statistics.quantiles(weekly_revenues, n=4, method="inclusive")
    direction = None
    if len(weekly_revenues) >= 8:
        recent = statistics.mean(weekly_revenues[-4:])
        earlier = statistics.mean(weekly_revenues[:-4])
        if earlier > 0:
            change = (recent - earlier) / earlier * 100
            direction = "up" if change > TREND_THRESHOLD_PCT else "down" if change < -TREND_THRESHOLD_PCT else "steady"
    return {
        "expected_zar": round(statistics.median(weekly_revenues), 2),
        "low_zar": round(low, 2),
        "high_zar": round(high, 2),
        "direction": direction,
        "based_on_weeks": len(weekly_revenues),
        "confidence": "low" if len(weekly_revenues) < 8 else "medium",
    }


def build_this_week(revenue: float, active_days: int, as_of: date, typical_week: float | None) -> dict:
    """The week in progress. It is not scored, but it moves as sales come in."""
    week_start = as_of - timedelta(days=as_of.weekday())
    return {
        "week_start": week_start.isoformat(),
        "revenue_zar": round(revenue, 2),
        "active_days": active_days,
        "days_left": 6 - as_of.weekday(),
        "share_of_typical_week_pct": (
            round(revenue / typical_week * 100) if typical_week and typical_week > 0 else None
        ),
    }


def build_scored_profile(assessment: dict, this_week: tuple[float, int], as_of: date, previous_score=None) -> dict:
    metrics = assessment["metrics"]
    revenue, active_days = this_week
    return {
        "state": "scored",
        "as_of": as_of.isoformat(),
        "score": assessment["score"],
        "band": band_for(assessment["score"]),
        "maturity": assessment["maturity"],
        "score_change": round(assessment["score"] - previous_score, 1) if previous_score is not None else None,
        "window": assessment["window"],
        "weeks_scored": metrics["weeks_scored"],
        "factors": build_factors(assessment["components"]),
        "tips": build_tips(assessment["components"], metrics),
        "metrics": metrics,
        "forecast": build_forecast(assessment["weekly_revenues_zar"]),
        "this_week": build_this_week(revenue, active_days, as_of, metrics["typical_weekly_revenue_zar"]),
        "progress": None,
        "disclaimer": DISCLAIMER,
    }


def build_building_profile(
    first_transaction: date | None,
    weeks_of_history: int,
    this_week: tuple[float, int],
    as_of: date,
    no_recent_sales: bool = False,
) -> dict:
    """Not scored yet. Shows how far along the merchant is, not a low score."""
    revenue, active_days = this_week
    remaining = max(0, MIN_WEEKS_TO_SCORE - weeks_of_history)
    available_from = None
    if first_transaction is not None:
        available_from = (first_complete_week_start(first_transaction) + timedelta(weeks=MIN_WEEKS_TO_SCORE)).isoformat()

    if first_transaction is None:
        tips = [{"factor": None, "impact_points": None, "text": "Log your first sale to start building your score."}]
        state = "no_data"
    elif no_recent_sales:
        tips = [{"factor": None, "impact_points": None, "text": "No sales were logged in your recent weeks. Log your sales to get scored."}]
        state = "building"
    else:
        tips = [
            {
                "factor": None,
                "impact_points": None,
                "text": (
                    f"Log every sale, every day you trade. Your first score needs {MIN_WEEKS_TO_SCORE} complete "
                    "weeks, and weeks run Monday to Sunday."
                ),
            },
            {
                "factor": None,
                "impact_points": None,
                "text": "The week you started in doesn't count if it began part-way through, so your history starts on the next Monday.",
            },
        ]
        state = "building"

    return {
        "state": state,
        "as_of": as_of.isoformat(),
        "score": None,
        "band": None,
        "maturity": None,
        "score_change": None,
        "window": None,
        "weeks_scored": 0,
        "factors": None,
        "tips": tips,
        "metrics": None,
        "forecast": None,
        "this_week": build_this_week(revenue, active_days, as_of, None),
        "progress": {
            "weeks_of_history": weeks_of_history,
            "weeks_required": MIN_WEEKS_TO_SCORE,
            "weeks_remaining": remaining,
            "available_from": available_from,
        },
        "disclaimer": DISCLAIMER,
    }


def apply_plan(profile: dict, premium: bool) -> dict:
    """Insights tier: the score, its band, one tip and the week in progress. Everything else is withheld."""
    profile = dict(profile)
    profile["plan"] = "full" if premium else "free"
    if premium:
        profile["locked"] = []
        return profile
    profile["factors"] = None
    profile["metrics"] = None
    profile["forecast"] = None
    profile["score_change"] = None
    profile["tips"] = profile["tips"][:1]
    if profile["this_week"]:
        profile["this_week"] = {**profile["this_week"], "share_of_typical_week_pct": None}
    profile["locked"] = list(FREE_LOCKED) if profile["state"] == "scored" else []
    return profile


# ---------------------------------------------------------------------------
# Database-backed entry point
# ---------------------------------------------------------------------------
def get_credit_profile(merchant_id, conn, as_of=None, premium: bool = False) -> dict:
    as_of_date = _to_date(as_of) if as_of is not None else datetime.now(SAST).date()

    week_start = as_of_date - timedelta(days=as_of_date.weekday())
    this_week = get_week_to_date(merchant_id, week_start, conn)
    first_transaction = get_first_transaction_date(merchant_id, conn)

    if first_transaction is None:
        return apply_plan(build_building_profile(None, 0, this_week, as_of_date), premium)

    try:
        assessment = get_merchant_credit_assessment(merchant_id, conn, as_of=as_of_date)
    except InsufficientHistoryError as error:
        no_recent_sales = error.weeks_of_history >= MIN_WEEKS_TO_SCORE
        return apply_plan(
            build_building_profile(first_transaction, error.weeks_of_history, this_week, as_of_date, no_recent_sales),
            premium,
        )

    previous_score = None
    if premium:  # only the full plan sees the change, so don't spend a query otherwise
        try:
            previous_score = get_merchant_credit_assessment(
                merchant_id, conn, as_of=as_of_date - timedelta(weeks=4)
            )["score"]
        except InsufficientHistoryError:
            previous_score = None

    return apply_plan(build_scored_profile(assessment, this_week, as_of_date, previous_score), premium)

def is_premium_merchant(merchant_id) -> bool:
    """Return True when the merchant ID is in the premium allowlist."""
    raw_ids = os.getenv("PREMIUM_MERCHANT_IDS", "")

    premium_ids = {
        merchant_id.strip()
        for merchant_id in raw_ids.split(",")
        if merchant_id.strip()
    }

    return str(merchant_id).strip() in premium_ids