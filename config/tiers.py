from validation.models import Tier

TIER_DAILY_VALUE_LIMITS = {
    Tier.FREE: 500,
    Tier.INSIGHTS: 2000,
    Tier.FULL: float("inf"),
}

def has_reached_limit(merchant_id: str, tier: Tier, conn) -> bool:
    limit = TIER_DAILY_VALUE_LIMITS[tier]
    if limit == float("inf"):
        return False
    
    cursor = conn.execute(
        """SELECT COALESCE(SUM(amount_zar), 0) FROM transactions 
           WHERE merchant_id = ? AND date(transaction_date) = date('now') AND is_voided = 0""",
        (merchant_id,)
    )
    total_today = cursor.fetchone()[0]
    return total_today >= limit