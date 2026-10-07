"""Plans, trial and feature gates.

Principle: LOGGING SALES IS ALWAYS FREE. The score and the credit offer are built from
the data merchants log, so a cap on logging starves the product. What can be premium is
what comes OUT of the data: reports, credit access, team features.

Database values are unchanged: Tier.INSIGHTS is the free plan, Tier.FULL is premium.
Always check features on the server (API layer), never only in the UI.
"""
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo

from validation.models import Tier

SAST = ZoneInfo("Africa/Johannesburg")

TRIAL_DAYS = 30

# Anti-abuse ceilings, not business limits. A normal merchant should never reach them.
DAILY_LOGGING_CEILING = {Tier.INSIGHTS: 200, Tier.FULL: 1000}


class Feature(str, Enum):
    # Free: data entry and the basic business dashboard, including its score.
    SALES_LOGGING = "sales_logging"
    DASHBOARD = "dashboard"
    SCORE_PROGRESS = "score_progress"      # how far through building their profile
    CREDIT_PREVIEW = "credit_preview"      # estimated amount and detailed score preview

    # Premium: acting on the data.
    CREDIT_ACCESS = "credit_access"        # share the assessment with lenders / apply
    REPORT_DOWNLOAD = "report_download"    # PDF / Excel statements
    LENDER_STATEMENT = "lender_statement"  # verified income statement with a check link
    PROFIT_INSIGHTS = "profit_insights"    # margins from logged expenses
    TEAM_MEMBERS = "team_members"          # staff and accountant logins
    MULTI_STORE = "multi_store"
    RECEIPTS = "receipts"                  # branded receipts / invoices to customers


PREMIUM_FEATURES = frozenset(
    {
        Feature.SCORE_PROGRESS,
        Feature.CREDIT_PREVIEW,
        Feature.CREDIT_ACCESS,
        Feature.REPORT_DOWNLOAD,
        Feature.LENDER_STATEMENT,
        Feature.PROFIT_INSIGHTS,
        Feature.TEAM_MEMBERS,
        Feature.MULTI_STORE,
        Feature.RECEIPTS,
    }
)


class FeatureLockedError(Exception):
    """The merchant's plan doesn't include this feature. Routes should answer with a
    403 that names the feature so the dashboard can show the upgrade prompt."""

    def __init__(self, feature: Feature):
        super().__init__(f"{feature.value} is a premium feature")
        self.feature = feature


def _parse_created(value) -> datetime:
    created = datetime.fromisoformat(value) if isinstance(value, str) else value
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created


def is_in_trial(merchant_created_at, now: datetime | None = None) -> bool:
    created = _parse_created(merchant_created_at)
    now = now or datetime.now(timezone.utc)
    return (now - created).days < TRIAL_DAYS


def trial_days_left(merchant_created_at, now: datetime | None = None) -> int:
    created = _parse_created(merchant_created_at)
    now = now or datetime.now(timezone.utc)
    return max(0, TRIAL_DAYS - (now - created).days)


def effective_tier(tier, merchant_created_at, now: datetime | None = None) -> Tier:
    """Premium during the trial, otherwise whatever the merchant is on."""
    if Tier(tier) == Tier.FULL or is_in_trial(merchant_created_at, now):
        return Tier.FULL
    return Tier.INSIGHTS


def has_feature(feature, tier, merchant_created_at, now: datetime | None = None) -> bool:
    feature = Feature(feature)
    if feature not in PREMIUM_FEATURES:
        return True
    return effective_tier(tier, merchant_created_at, now) == Tier.FULL


def require_feature(feature, tier, merchant_created_at, now: datetime | None = None) -> None:
    feature = Feature(feature)
    if not has_feature(feature, tier, merchant_created_at, now):
        raise FeatureLockedError(feature)


def get_entitlements(tier, merchant_created_at, now: datetime | None = None) -> dict:
    """Everything the dashboard needs to draw locks, from one source of truth."""
    return {
        "tier": effective_tier(tier, merchant_created_at, now).value,
        "in_trial": is_in_trial(merchant_created_at, now) and Tier(tier) != Tier.FULL,
        "trial_days_left": trial_days_left(merchant_created_at, now) if Tier(tier) != Tier.FULL else 0,
        "features": {
            feature.value: has_feature(feature, tier, merchant_created_at, now) for feature in Feature
        },
    }


def get_calendar_week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def has_reached_limit(merchant_id, tier, merchant_created_at, conn) -> bool:
    """True once a merchant has logged an implausible number of sales TODAY (SAST).

    This is abuse protection, not a plan limit. Normal merchants never reach it.
    """
    ceiling = DAILY_LOGGING_CEILING[effective_tier(tier, merchant_created_at)]
    today = datetime.now(SAST).date()

    cursor = conn.execute(
        """SELECT COUNT(*)
           FROM transactions t
           JOIN stores s ON s.store_id = t.store_id
           WHERE s.merchant_id = %s
             AND (t.transaction_date AT TIME ZONE 'Africa/Johannesburg')::date = %s
             AND t.is_voided = FALSE""",
        (merchant_id, today),
    )
    return cursor.fetchone()[0] >= ceiling