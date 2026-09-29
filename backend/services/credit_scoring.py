from datetime import date, datetime, time
from zoneinfo import ZoneInfo
REVENUE_BENCHMARK_MONTHLY = 10000  # ZAR — top score ceiling for Revenue Level

WEIGHTS = {
    "stability": 0.35,
    "growth": 0.25,
    "revenue_level": 0.25,
    "consistency": 0.15,
}


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def calculate_stability_score(revenue_volatility: float | None, average_monthly_revenue: float) -> float:
    if revenue_volatility is None or average_monthly_revenue == 0:
        return 0
    cv = revenue_volatility / average_monthly_revenue
    return clamp(100 - (cv * 100))


def calculate_growth_score(revenue_growth_pct: float | None) -> float:
    if revenue_growth_pct is None:
        return 50  # neutral score when there's no prior period to compare
    return clamp((revenue_growth_pct + 50) / 150 * 100)


def calculate_revenue_level_score(total_revenue_zar: float) -> float:
    return clamp((total_revenue_zar / REVENUE_BENCHMARK_MONTHLY) * 100)


def calculate_consistency_score(days_with_transactions: int, total_days_in_period: int) -> float:
    if total_days_in_period == 0:
        return 0
    return clamp((days_with_transactions / total_days_in_period) * 100)


def calculate_credit_score(
    revenue_volatility: float | None,
    average_monthly_revenue: float,
    revenue_growth_pct: float | None,
    total_revenue_zar: float,
    days_with_transactions: int,
    total_days_in_period: int,
) -> float:
    stability = calculate_stability_score(revenue_volatility, average_monthly_revenue)
    growth = calculate_growth_score(revenue_growth_pct)
    revenue_level = calculate_revenue_level_score(total_revenue_zar)
    consistency = calculate_consistency_score(days_with_transactions, total_days_in_period)

    score = (
        stability * WEIGHTS["stability"]
        + growth * WEIGHTS["growth"]
        + revenue_level * WEIGHTS["revenue_level"]
        + consistency * WEIGHTS["consistency"]
    )

    return round(score, 2)

def get_days_with_transactions(merchant_id: str, period_start, period_end, conn) -> int:
    period_start_date = date.fromisoformat(period_start) if isinstance(period_start, str) else period_start
    period_end_date = date.fromisoformat(period_end) if isinstance(period_end, str) else period_end
    local_timezone = ZoneInfo("Africa/Johannesburg")
    cursor = conn.execute(
        """SELECT COUNT(DISTINCT
                          (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date)
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s
             AND t.transaction_date >= %s
             AND t.transaction_date < %s
             AND t.is_voided = FALSE""",
        (
            merchant_id,
            datetime.combine(period_start_date, time.min, local_timezone),
            datetime.combine(period_end_date, time.min, local_timezone),
        )
    )
    return cursor.fetchone()[0]

def get_merchant_credit_score(merchant_id: str, period_start, period_end, conn):
    period_start_date = (
        date.fromisoformat(period_start) if isinstance(period_start, str) else period_start
    )
    period_end_date = (
        date.fromisoformat(period_end) if isinstance(period_end, str) else period_end
    )
    cursor = conn.execute(
        """SELECT SUM(fs.total_revenue_zar), AVG(fs.revenue_growth_pct),
                  AVG(fs.revenue_volatility)
           FROM financial_snapshots fs
           JOIN stores s ON s.store_id = fs.store_id
           WHERE s.merchant_id = %s
             AND fs.period_start = %s
             AND fs.period_end = %s""",
        (merchant_id, period_start_date, period_end_date)
    )
    row = cursor.fetchone()

    if row is None or row[0] is None:
        raise ValueError(f"No financial snapshot found for {merchant_id} in this period")

    total_revenue_zar, revenue_growth_pct, revenue_volatility = (
        float(value) if value is not None else None for value in row
    )

    days_with_transactions = get_days_with_transactions(
        merchant_id,
        period_start_date,
        period_end_date,
        conn,
    )
    total_days_in_period = (period_end_date - period_start_date).days

    return calculate_credit_score(
        revenue_volatility=revenue_volatility,
        average_monthly_revenue=total_revenue_zar,
        revenue_growth_pct=revenue_growth_pct,
        total_revenue_zar=total_revenue_zar,
        days_with_transactions=days_with_transactions,
        total_days_in_period=total_days_in_period,
    )