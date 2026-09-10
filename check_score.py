import sqlite3
from datetime import date
from services.credit_scoring import (
    calculate_stability_score,
    calculate_growth_score,
    calculate_revenue_level_score,
    calculate_consistency_score,
    get_days_with_transactions,
)

conn = sqlite3.connect("data/zakascore.db")

cursor = conn.execute(
    """SELECT merchant_id, period_start, period_end, total_revenue_zar, revenue_growth_pct, revenue_volatility 
       FROM financial_snapshots 
       WHERE total_revenue_zar > 0 
       ORDER BY total_revenue_zar DESC 
       LIMIT 1"""
)
merchant_id, period_start, period_end, total_revenue_zar, revenue_growth_pct, revenue_volatility = cursor.fetchone()

period_start_date = date.fromisoformat(period_start)
period_end_date = date.fromisoformat(period_end)
total_days = (period_end_date - period_start_date).days
days_with_tx = get_days_with_transactions(merchant_id, period_start, period_end, conn)

print(f"Merchant: {merchant_id}, {period_start} to {period_end}")
print(f"Total revenue: R{total_revenue_zar}")
print(f"Growth %: {revenue_growth_pct}")
print(f"Volatility: {revenue_volatility}")
print(f"Days with transactions: {days_with_tx} / {total_days}")
print()
print(f"Stability score: {calculate_stability_score(revenue_volatility, total_revenue_zar)}")
print(f"Growth score: {calculate_growth_score(revenue_growth_pct)}")
print(f"Revenue level score: {calculate_revenue_level_score(total_revenue_zar)}")
print(f"Consistency score: {calculate_consistency_score(days_with_tx, total_days)}")

conn.close()