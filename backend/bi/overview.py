import statistics
from datetime import datetime, timedelta
from collections import namedtuple
from zoneinfo import ZoneInfo

from bi.metrics import (
    calculate_total_revenue,
    calculate_transaction_count,
    calculate_average_transaction,
    calculate_revenue_by_date,
    calculate_revenue_growth,
    calculate_revenue_volatility,
    calculate_recency,
)
from bi.indicators import (
    determine_revenue_trend,
    calculate_transaction_activity,
    determine_revenue_stability,
    determine_activity_status,
    determine_digital_payment_adoption,
)
from bi.insights import generate_business_insights

SAST = ZoneInfo("Africa/Johannesburg")

SimpleTransaction = namedtuple("SimpleTransaction", ["amount_zar", "transaction_date", "payment_method"])


def get_transactions_for_merchant(merchant_id, conn) -> list[SimpleTransaction]:
    cursor = conn.execute(
        """SELECT amount_zar, transaction_date, payment_method
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE
           ORDER BY t.transaction_date ASC""",
        (merchant_id,)
    )
    rows = cursor.fetchall()

    result = []
    for amount, date_str, payment_method in rows:
        date_obj = date_str if isinstance(date_str, datetime) else datetime.fromisoformat(date_str)
        if date_obj.tzinfo is not None:
            # Naive SAST wall-clock time, so day buckets match the dashboard.
            date_obj = date_obj.astimezone(SAST).replace(tzinfo=None)
        result.append(SimpleTransaction(float(amount), date_obj, payment_method))

    return result


def get_business_overview(merchant_id, conn) -> dict:
    transactions = get_transactions_for_merchant(merchant_id, conn)

    total_revenue = calculate_total_revenue(transactions)
    transaction_count = calculate_transaction_count(transactions)
    average_transaction = calculate_average_transaction(transactions)
    daily_revenue = calculate_revenue_by_date(transactions)

    # Transactions are naive SAST, so "now" must be too (the server may run UTC).
    now = datetime.now(SAST).replace(tzinfo=None)
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_period_txns = [t for t in transactions if t.transaction_date >= thirty_days_ago]
    previous_period_txns = [t for t in transactions if sixty_days_ago <= t.transaction_date < thirty_days_ago]

    current_revenue = calculate_total_revenue(current_period_txns)
    previous_revenue = calculate_total_revenue(previous_period_txns)

    # Growth is only meaningful if the merchant was trading for the whole previous
    # window. Otherwise a new merchant's partial window makes growth look huge.
    # (transactions are ordered oldest first)
    has_full_prior_window = bool(transactions) and transactions[0].transaction_date <= sixty_days_ago
    revenue_growth = (
        calculate_revenue_growth(current_revenue, previous_revenue)
        if has_full_prior_window
        else None
    )

    revenue_volatility_raw = calculate_revenue_volatility(transactions)  # None if too little data
    average_daily_revenue = statistics.mean(daily_revenue.values()) if daily_revenue else 0
    coefficient_of_variation = (
        revenue_volatility_raw / average_daily_revenue
        if revenue_volatility_raw is not None and average_daily_revenue > 0
        else None
    )

    active_days = len(daily_revenue)
    recency = calculate_recency(transactions, now)

    cash_revenue = sum(t.amount_zar for t in transactions if t.payment_method == "cash")
    digital_revenue = sum(t.amount_zar for t in transactions if t.payment_method == "digital")
    known_payment_revenue = cash_revenue + digital_revenue
    payment_method_coverage_pct = (
        round(known_payment_revenue / total_revenue * 100, 2) if total_revenue > 0 else None
    )

    revenue_trend = determine_revenue_trend(revenue_growth)
    transaction_activity = calculate_transaction_activity(transaction_count, active_days)
    revenue_stability = determine_revenue_stability(coefficient_of_variation)
    activity_status = determine_activity_status(recency)
    digital_adoption = determine_digital_payment_adoption(cash_revenue, digital_revenue, total_revenue)

    insights = generate_business_insights(revenue_trend, revenue_stability, activity_status)

    return {
        "total_revenue": round(total_revenue, 2),
        "transaction_count": transaction_count,
        "average_transaction": round(average_transaction, 2),
        "revenue_growth_pct": round(revenue_growth, 2) if revenue_growth is not None else None,
        "revenue_trend": revenue_trend,
        "transaction_activity": transaction_activity,
        "revenue_stability": revenue_stability,
        "activity_status": activity_status,
        "digital_payment_adoption": digital_adoption,
        "payment_method_coverage_pct": payment_method_coverage_pct,
        "insights": insights,
    }