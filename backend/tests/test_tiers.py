import os
from datetime import datetime, timedelta, timezone

import pytest

from services import tiers
from services.tiers import Feature, FeatureLockedError
from validation.models import Tier

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


def created(days_ago):
    return NOW - timedelta(days=days_ago)


# --- trial ------------------------------------------------------------------
def test_trial_boundary():
    assert tiers.is_in_trial(created(0), NOW)
    assert tiers.is_in_trial(created(29), NOW)
    assert not tiers.is_in_trial(created(30), NOW)
    assert not tiers.is_in_trial(created(200), NOW)


def test_trial_accepts_strings_and_naive_datetimes():
    assert tiers.is_in_trial(created(5).isoformat(), NOW)
    assert tiers.is_in_trial(created(5).replace(tzinfo=None), NOW)  # treated as UTC


def test_trial_days_left():
    assert tiers.trial_days_left(created(0), NOW) == 30
    assert tiers.trial_days_left(created(10), NOW) == 20
    assert tiers.trial_days_left(created(90), NOW) == 0


# --- effective tier and features --------------------------------------------------
def test_effective_tier():
    assert tiers.effective_tier(Tier.INSIGHTS, created(5), NOW) == Tier.FULL       # trial
    assert tiers.effective_tier(Tier.INSIGHTS, created(90), NOW) == Tier.INSIGHTS  # after trial
    assert tiers.effective_tier(Tier.FULL, created(90), NOW) == Tier.FULL          # paid
    assert tiers.effective_tier("insights", created(90), NOW) == Tier.INSIGHTS     # DB strings work


def test_free_features_are_always_available():
    for feature in Feature:
        if feature not in tiers.PREMIUM_FEATURES:
            assert tiers.has_feature(feature, Tier.INSIGHTS, created(90), NOW)


def test_logging_sales_can_never_be_premium():
    # The principle of this module: the data the score is built from is never paywalled.
    assert Feature.SALES_LOGGING not in tiers.PREMIUM_FEATURES
    assert Feature.DASHBOARD not in tiers.PREMIUM_FEATURES
    assert Feature.CREDIT_PREVIEW not in tiers.PREMIUM_FEATURES


def test_premium_features_lock_after_the_trial_and_unlock_for_paying_merchants():
    for feature in tiers.PREMIUM_FEATURES:
        assert not tiers.has_feature(feature, Tier.INSIGHTS, created(90), NOW)
        assert tiers.has_feature(feature, Tier.INSIGHTS, created(5), NOW)   # trial
        assert tiers.has_feature(feature, Tier.FULL, created(90), NOW)


def test_require_feature_raises_with_the_feature_attached():
    with pytest.raises(FeatureLockedError) as error:
        tiers.require_feature("credit_access", Tier.INSIGHTS, created(90), NOW)
    assert error.value.feature == Feature.CREDIT_ACCESS
    tiers.require_feature(Feature.CREDIT_ACCESS, Tier.FULL, created(90), NOW)  # no error
    tiers.require_feature(Feature.SALES_LOGGING, Tier.INSIGHTS, created(90), NOW)


def test_unknown_feature_is_an_error():
    with pytest.raises(ValueError):
        tiers.has_feature("teleportation", Tier.FULL, created(1), NOW)


def test_entitlements_for_the_dashboard():
    trial = tiers.get_entitlements(Tier.INSIGHTS, created(10), NOW)
    assert trial["tier"] == "full" and trial["in_trial"] and trial["trial_days_left"] == 20

    free = tiers.get_entitlements(Tier.INSIGHTS, created(90), NOW)
    assert free["tier"] == "insights" and not free["in_trial"] and free["trial_days_left"] == 0
    assert free["features"]["sales_logging"] is True
    assert free["features"]["credit_preview"] is True
    assert free["features"]["credit_access"] is False
    assert free["features"]["report_download"] is False
    assert set(free["features"]) == {f.value for f in Feature}

    paid = tiers.get_entitlements(Tier.FULL, created(90), NOW)
    assert paid["tier"] == "full" and not paid["in_trial"]
    assert all(paid["features"].values())


# --- the daily abuse ceiling, against a real database --------------------------------
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def db():
    if not TEST_DATABASE_URL:
        pytest.skip("set TEST_DATABASE_URL to run the database tests")
    import psycopg

    conn = psycopg.connect(TEST_DATABASE_URL)
    conn.execute("DELETE FROM merchants WHERE business_name LIKE 'TEST %'")
    conn.commit()
    yield conn
    conn.rollback()
    conn.execute("DELETE FROM merchants WHERE business_name LIKE 'TEST %'")
    conn.commit()
    conn.close()


def seed(conn, today=3, voided=1, old=2):
    merchant_id = conn.execute(
        "INSERT INTO merchants (business_name) VALUES ('TEST tiers') RETURNING merchant_id"
    ).fetchone()[0]
    store_id = conn.execute(
        "INSERT INTO stores (merchant_id, store_name) VALUES (%s, 'Main') RETURNING store_id",
        (merchant_id,),
    ).fetchone()[0]
    source_id = conn.execute(
        "INSERT INTO data_sources (store_id, source_name, source_type) "
        "VALUES (%s, 'Manual', 'manual') RETURNING source_id",
        (store_id,),
    ).fetchone()[0]

    def add(when_sql, is_voided=False):
        conn.execute(
            f"""INSERT INTO transactions (store_id, source_id, input_type, amount_zar,
                    payment_method, transaction_date, is_voided, voided_at)
                VALUES (%s, %s, 'manual', 100, 'cash', {when_sql}, %s,
                        CASE WHEN %s THEN now() END)""",
            (store_id, source_id, is_voided, is_voided),
        )

    for _ in range(today):
        add("now()")
    for _ in range(voided):
        add("now()", is_voided=True)
    for _ in range(old):
        add("now() - interval '3 days'")
    conn.commit()
    return merchant_id


def test_ceiling_counts_only_todays_unvoided_sales(db, monkeypatch):
    merchant_id = seed(db, today=3, voided=1, old=2)
    monkeypatch.setitem(tiers.DAILY_LOGGING_CEILING, Tier.INSIGHTS, 3)
    monkeypatch.setitem(tiers.DAILY_LOGGING_CEILING, Tier.FULL, 5)

    long_ago = created(90)
    assert tiers.has_reached_limit(merchant_id, Tier.INSIGHTS, long_ago, db)        # 3 >= 3
    assert not tiers.has_reached_limit(merchant_id, Tier.FULL, long_ago, db)        # 3 < 5
    # still in the trial: premium ceiling applies
    assert not tiers.has_reached_limit(
        merchant_id, Tier.INSIGHTS, datetime.now(timezone.utc), db
    )


def test_real_merchants_are_nowhere_near_the_ceiling(db):
    merchant_id = seed(db, today=40, voided=0, old=0)  # a very busy salon day
    assert not tiers.has_reached_limit(merchant_id, Tier.INSIGHTS, created(90), db)