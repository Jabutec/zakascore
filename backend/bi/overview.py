from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bi.metrics import calculate_revenue_growth
from bi.indicators import (
    determine_revenue_trend,
    calculate_transaction_activity,
    determine_revenue_stability,
    determine_activity_status,
    determine_digital_payment_adoption,
)
from bi.insights import generate_business_insights

SAST = ZoneInfo("Africa/Johannesburg")

def get_business_overview(merchant_id, conn) -> dict:
    now = datetime.now(SAST).replace(tzinfo=None)
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    row = conn.execute(
        """WITH merchant_transactions AS (
               SELECT t.amount_zar,
                      t.payment_method,
                      t.transaction_date AT TIME ZONE 'Africa/Johannesburg'
                          AS local_transaction_date
               FROM transactions t
               JOIN stores s ON s.store_id = t.store_id
               WHERE s.merchant_id = %s AND t.is_voided = FALSE
           ), grouped_revenue AS (
               SELECT GROUPING(local_transaction_date::date) AS is_total,
                      local_transaction_date::date AS transaction_day,
                      COUNT(*) AS transaction_count,
                      SUM(amount_zar) AS total_revenue,
                      AVG(amount_zar) AS average_transaction,
                      SUM(amount_zar) FILTER (
                          WHERE local_transaction_date >= %s
                      ) AS current_revenue,
                      SUM(amount_zar) FILTER (
                          WHERE local_transaction_date >= %s
                            AND local_transaction_date < %s
                      ) AS previous_revenue,
                      MIN(local_transaction_date) AS first_transaction,
                      MAX(local_transaction_date) AS latest_transaction,
                      SUM(amount_zar) FILTER (
                          WHERE payment_method = 'cash'
                      ) AS cash_revenue,
                      SUM(amount_zar) FILTER (
                          WHERE payment_method = 'digital'
                      ) AS digital_revenue
               FROM merchant_transactions
               GROUP BY GROUPING SETS ((), (local_transaction_date::date))
           ), overall AS (
               SELECT * FROM grouped_revenue WHERE is_total = 1
           ), daily_stats AS (
               SELECT COUNT(*) AS active_days,
                      AVG(total_revenue) AS average_daily_revenue,
                      CASE WHEN COUNT(*) >= 7
                           THEN STDDEV_SAMP(total_revenue)
                      END AS revenue_volatility
               FROM grouped_revenue
               WHERE is_total = 0
           )
           SELECT transaction_count,
                  COALESCE(total_revenue, 0)::double precision,
                  COALESCE(average_transaction, 0)::double precision,
                  COALESCE(current_revenue, 0)::double precision,
                  COALESCE(previous_revenue, 0)::double precision,
                  (transaction_count > 0 AND first_transaction <= %s)
                      AS has_full_prior_window,
                  active_days,
                  COALESCE(average_daily_revenue, 0)::double precision,
                  revenue_volatility::double precision,
                  CASE WHEN latest_transaction IS NULL THEN NULL
                       ELSE FLOOR(EXTRACT(EPOCH FROM (%s - latest_transaction)) / 86400)::integer
                  END AS recency_days,
                  COALESCE(cash_revenue, 0)::double precision,
                  COALESCE(digital_revenue, 0)::double precision
           FROM overall CROSS JOIN daily_stats""",
        (
            merchant_id,
            thirty_days_ago,
            sixty_days_ago,
            thirty_days_ago,
            sixty_days_ago,
            now,
        ),
    ).fetchone()

    transaction_count = row[0]
    total_revenue = row[1]
    average_transaction = row[2]
    current_revenue = row[3]
    previous_revenue = row[4]
    has_full_prior_window = row[5]
    active_days = row[6]
    average_daily_revenue = row[7]
    revenue_volatility_raw = row[8]
    recency = row[9]
    cash_revenue = row[10]
    digital_revenue = row[11]

    revenue_growth = (
        calculate_revenue_growth(current_revenue, previous_revenue)
        if has_full_prior_window
        else None
    )

    coefficient_of_variation = (
        revenue_volatility_raw / average_daily_revenue
        if revenue_volatility_raw is not None and average_daily_revenue > 0
        else None
    )

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