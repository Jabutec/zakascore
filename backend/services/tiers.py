from datetime import date, datetime, timedelta
from validation.models import Tier

TRIAL_DAYS = 30
INSIGHTS_WEEKLY_TRANSACTION_LIMIT = 10


def is_in_trial(merchant_created_at) -> bool:
    if isinstance(merchant_created_at, str):
        created = datetime.fromisoformat(merchant_created_at)
    else:
        created = merchant_created_at
    now = datetime.now(created.tzinfo) if created.tzinfo else datetime.now()
    return (now - created).days < TRIAL_DAYS


def get_calendar_week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def has_reached_limit(merchant_id: str, tier: Tier, merchant_created_at: str, conn) -> bool:
    if is_in_trial(merchant_created_at):
        return False

    if tier == Tier.FULL:
        return False

    week_start = get_calendar_week_start(date.today())
    cursor = conn.execute(
        """SELECT COUNT(*)
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s
             AND (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date >= %s
             AND t.is_voided = FALSE""",
        (merchant_id, week_start)
    )
    count = cursor.fetchone()[0]
    return count >= INSIGHTS_WEEKLY_TRANSACTION_LIMIT