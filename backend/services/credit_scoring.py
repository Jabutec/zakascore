import statistics
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SAST = ZoneInfo("Africa/Johannesburg")

# ---------------------------------------------------------------------------
# Tunable assumptions. These are placeholders: nothing here has been calibrated
# against repayment outcomes yet, so treat the score as a measure of business
# activity and health, not a probability of default.
# ---------------------------------------------------------------------------
MIN_WEEKS_TO_SCORE = 4             # complete Mon-Sun weeks of history needed before a score is shown
MAX_WINDOW_WEEKS = 12              # the score uses at most this many of the most recent complete weeks
GROWING_WEEKS = 8                  # 4-7 weeks = "early", 8-11 = "growing", 12 = "established"
WINDOW_WEEKS = MAX_WINDOW_WEEKS    # old name, kept so existing imports keep working
MIN_TRADING_DAYS_PER_WEEK = 3      # a week counts as a "trading week" at this many active days
REVENUE_BENCHMARK_MONTHLY = 10000  # ZAR monthly equivalent that earns a full Revenue Level score
WEEKS_PER_MONTH = 52 / 12

GROWTH_FLAT_SCORE = 60             # flat revenue is healthy, so it scores above "unknown" (50)
GROWTH_UNKNOWN_SCORE = 50
GROWTH_SLOPE = 0.4                 # score points per 1% of growth

WEIGHTS = {
    "stability": 0.35,
    "growth": 0.25,
    "revenue_level": 0.25,
    "consistency": 0.15,
}


class InsufficientHistoryError(ValueError):
    """Not enough trading history to score. Subclasses ValueError, so callers that
    already catch ValueError keep working."""

    def __init__(self, message, weeks_of_history=0, weeks_required=MIN_WEEKS_TO_SCORE):
        super().__init__(message)
        self.weeks_of_history = weeks_of_history
        self.weeks_required = weeks_required


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def score_maturity(weeks_scored: int) -> str:
    """How much history sits behind the score. A 4-week score is real but less settled."""
    if weeks_scored >= MAX_WINDOW_WEEKS:
        return "established"
    if weeks_scored >= GROWING_WEEKS:
        return "growing"
    return "early"


# ---------------------------------------------------------------------------
# Pure scoring functions (no database access)
# ---------------------------------------------------------------------------
def calculate_stability_score(weekly_revenues: list[float]) -> float:
    """100 minus the coefficient of variation (in %) of weekly revenue.

    Weekly buckets absorb quiet and busy days. Weeks with no sales count as zero,
    so an erratic merchant scores lower.
    """
    if len(weekly_revenues) < 2:
        return 0
    mean = statistics.mean(weekly_revenues)
    if mean <= 0:
        return 0
    cv = statistics.stdev(weekly_revenues) / mean
    return clamp(100 - (cv * 100))


def calculate_revenue_growth_pct(weekly_revenues: list[float]) -> float | None:
    """Second half of the window against the first half. None if the first half had no sales."""
    half = len(weekly_revenues) // 2
    if half == 0:
        return None
    earlier = sum(weekly_revenues[:half])
    recent = sum(weekly_revenues[-half:])
    if earlier <= 0:
        return None
    return (recent - earlier) / earlier * 100


def calculate_growth_score(revenue_growth_pct: float | None) -> float:
    if revenue_growth_pct is None:
        return GROWTH_UNKNOWN_SCORE
    return clamp(GROWTH_FLAT_SCORE + revenue_growth_pct * GROWTH_SLOPE)


def calculate_revenue_level_score(typical_weekly_revenue: float) -> float:
    monthly_equivalent = typical_weekly_revenue * WEEKS_PER_MONTH
    return clamp((monthly_equivalent / REVENUE_BENCHMARK_MONTHLY) * 100)


def calculate_consistency_score(weekly_active_days: list[int]) -> float:
    """Share of weeks in which the merchant traded on enough days.

    Individual quiet or closed days are not penalised. Only weeks with very little
    trading are.
    """
    if not weekly_active_days:
        return 0
    trading_weeks = sum(1 for days in weekly_active_days if days >= MIN_TRADING_DAYS_PER_WEEK)
    return clamp(trading_weeks / len(weekly_active_days) * 100)


def score_weekly_history(weekly_revenues: list[float], weekly_active_days: list[int]) -> dict:
    """Score from weekly buckets. Returns the score, its components and supporting metrics."""
    if len(weekly_revenues) < 2 or len(weekly_revenues) != len(weekly_active_days):
        raise ValueError("Need matching weekly revenue and active-day lists with at least 2 weeks")

    growth_pct = calculate_revenue_growth_pct(weekly_revenues)
    typical_weekly = statistics.median(weekly_revenues)  # median: one big week doesn't inflate it
    quiet_weekly = statistics.quantiles(weekly_revenues, n=4, method="inclusive")[0]

    components = {
        "stability": calculate_stability_score(weekly_revenues),
        "growth": calculate_growth_score(growth_pct),
        "revenue_level": calculate_revenue_level_score(typical_weekly),
        "consistency": calculate_consistency_score(weekly_active_days),
    }
    score = sum(components[name] * WEIGHTS[name] for name in WEIGHTS)

    return {
        "score": round(score, 2),
        "components": {name: round(value, 2) for name, value in components.items()},
        "metrics": {
            "weeks_scored": len(weekly_revenues),
            "total_revenue_zar": round(sum(weekly_revenues), 2),
            "typical_weekly_revenue_zar": round(typical_weekly, 2),
            "quiet_week_revenue_zar": round(quiet_weekly, 2),
            "revenue_growth_pct": round(growth_pct, 2) if growth_pct is not None else None,
            "trading_weeks": sum(1 for d in weekly_active_days if d >= MIN_TRADING_DAYS_PER_WEEK),
            "weeks_without_sales": sum(1 for r in weekly_revenues if r == 0),
        },
    }


def calculate_credit_score(weekly_revenues: list[float], weekly_active_days: list[int]) -> float:
    return score_weekly_history(weekly_revenues, weekly_active_days)["score"]


# ---------------------------------------------------------------------------
# Scoring window
# ---------------------------------------------------------------------------
def _to_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def first_complete_week_start(first_transaction: date) -> date:
    """Monday of the first Mon-Sun week the merchant traded for the whole of.

    A merchant who starts on a Thursday has a partial first week, which would look like a
    quiet week and unfairly drag the score down, so history starts from the next Monday.
    """
    monday = first_transaction - timedelta(days=first_transaction.weekday())
    return monday if first_transaction == monday else monday + timedelta(weeks=1)


def scoring_window(as_of: date, first_transaction: date) -> tuple[date, date, int]:
    """(window_start, window_end, weeks) for the complete weeks that can be scored.

    window_start is a Monday. window_end is the Monday of the current week and is
    EXCLUSIVE, so the week in progress is never scored. The window never reaches back
    past the merchant's first complete week, and covers at most MAX_WINDOW_WEEKS.
    """
    current_week_start = as_of - timedelta(days=as_of.weekday())
    earliest = first_complete_week_start(first_transaction)
    window_start = max(earliest, current_week_start - timedelta(weeks=MAX_WINDOW_WEEKS))
    weeks = max(0, (current_week_start - window_start).days // 7)
    return window_start, current_week_start, weeks


# ---------------------------------------------------------------------------
# Database access (merchant level: all of a merchant's stores combined)
# ---------------------------------------------------------------------------
def get_first_transaction_date(merchant_id, conn) -> date | None:
    cursor = conn.execute(
        """SELECT MIN((t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date)
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE""",
        (merchant_id,),
    )
    return cursor.fetchone()[0]


def get_weekly_activity(merchant_id, window_start: date, window_end: date, conn):
    """Weekly revenue and active trading days, SAST weeks starting Monday.

    Covers every week from window_start up to (not including) window_end.
    Weeks with no sales are filled in as zero, so quiet weeks count.
    """
    weeks = max(0, (window_end - window_start).days // 7)
    cursor = conn.execute(
        """SELECT date_trunc('week', t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date,
                  SUM(t.amount_zar),
                  COUNT(DISTINCT (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date)
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s
             AND t.is_voided = FALSE
             AND t.transaction_date >= %s
             AND t.transaction_date < %s
           GROUP BY 1
           ORDER BY 1""",
        (
            merchant_id,
            datetime.combine(window_start, time.min, SAST),
            datetime.combine(window_end, time.min, SAST),
        ),
    )
    by_week = {row[0]: (float(row[1]), int(row[2])) for row in cursor.fetchall()}

    revenues, active_days = [], []
    for i in range(weeks):
        revenue, days = by_week.get(window_start + timedelta(weeks=i), (0.0, 0))
        revenues.append(revenue)
        active_days.append(days)
    return revenues, active_days


def get_week_to_date(merchant_id, week_start: date, conn) -> tuple[float, int]:
    """Revenue and active days so far in the week that starts on `week_start`."""
    revenues, active_days = get_weekly_activity(
        merchant_id, week_start, week_start + timedelta(weeks=1), conn
    )
    return revenues[0], active_days[0]


def get_merchant_credit_assessment(merchant_id, conn, as_of=None) -> dict:
    """Full assessment: score, components, metrics and the window that was scored.

    Raises InsufficientHistoryError until the merchant has MIN_WEEKS_TO_SCORE complete
    weeks of history. A thin file is "not scored yet", not a low score.
    """
    as_of_date = _to_date(as_of) if as_of is not None else datetime.now(SAST).date()

    first_transaction = get_first_transaction_date(merchant_id, conn)
    if first_transaction is None:
        raise InsufficientHistoryError("No transactions recorded yet")

    window_start, window_end, weeks = scoring_window(as_of_date, first_transaction)
    if weeks < MIN_WEEKS_TO_SCORE:
        raise InsufficientHistoryError(
            f"Needs {MIN_WEEKS_TO_SCORE} complete weeks of history; has {weeks}",
            weeks_of_history=weeks,
        )

    revenues, active_days = get_weekly_activity(merchant_id, window_start, window_end, conn)
    if sum(revenues) <= 0:
        raise InsufficientHistoryError("No sales in the scoring window", weeks_of_history=weeks)

    assessment = score_weekly_history(revenues, active_days)
    assessment["metrics"]["weeks_of_history"] = weeks
    assessment["maturity"] = score_maturity(weeks)
    assessment["weekly_revenues_zar"] = [round(value, 2) for value in revenues]
    assessment["weekly_active_days"] = active_days
    assessment["window"] = {
        "start": window_start.isoformat(),
        "end": (window_end - timedelta(days=1)).isoformat(),  # inclusive, for display
    }
    return assessment


def get_merchant_credit_score(merchant_id, period_start, period_end, conn):
    """Kept so the existing route keeps working.

    period_start is no longer used: the score covers the most recent complete weeks
    (at most MAX_WINDOW_WEEKS) before period_end. Raises ValueError (InsufficientHistoryError)
    for merchants without enough history, which the route already turns into a null score.
    """
    return get_merchant_credit_assessment(merchant_id, conn, as_of=period_end)["score"]