"""Dev/test seeder. NEVER run against production.

It DELETES every row in every table first, so it refuses to run unless you
explicitly pin the database host you intend to wipe:

    SEED_ALLOW_HOST=ep-your-branch-123456.eu-central-1.aws.neon.tech python -m <this module>

Optional env vars:
    SEED                 integer RNG seed (default 42) for reproducible data
    SEED_OWNER_USER_ID   your Neon Auth user id; becomes owner of the first merchant
"""
import os
import random
import statistics
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from faker import Faker

from database.connection import DATABASE_URL, get_db, close_pool
from utils.helpers import get_month_start, get_next_month

SEED = int(os.getenv("SEED", "42"))

# Python Faker has no en_ZA; names are locale-agnostic enough and
# locations come from SA_CITIES below.
SOURCE_TYPES = [
    "pos",
    "online_store",
    "bank_statement",
    "accounting_software",
    "whatsapp",
    "manual",
    "csv",
]

# Every input type is recorded against a matching source, so grouping by
# source in the BI layer gives meaningful results. Voice notes arrive via WhatsApp.
INPUT_TO_SOURCE = {
    "pos_tap": "pos",
    "manual": "manual",
    "csv": "csv",
    "whatsapp": "whatsapp",
    "voice": "whatsapp",
}

SA_CITIES = [
    "Johannesburg", "Cape Town", "Durban", "Pretoria", "Gqeberha",
    "Bloemfontein", "Soweto", "Tembisa", "Umlazi", "Khayelitsha",
    "Soshanguve", "Mamelodi", "Polokwane", "Mbombela", "Pietermaritzburg",
    "Komani", "Rustenburg", "Vereeniging", "Boksburg", "Tshwane",
]

SAMPLE_OFFERINGS = [
    "shirt", "dress", "haircut", "manicure", "phone case",
    "airtime", "bread", "cooldrink", "hair extension", "makeup session",
]

# Wipe in FK-safe order (children first) so the seed is re-runnable.
WIPE_ORDER = [
    "financial_snapshots",
    "transactions",
    "offerings",
    "connect_codes",
    "data_sources",
    "merchant_users",
    "stores",
    "merchants",
]

UNCLAIMED_CLAIM_CODE = "TESTCLAM"  # matches the 8-char code alphabet


def _assert_safe_to_seed() -> None:
    host = (urlparse(DATABASE_URL).hostname or "").replace("-pooler", "")
    allowed = os.getenv("SEED_ALLOW_HOST", "").strip().replace("-pooler", "")
    if not host or host != allowed:
        raise SystemExit(
            "Refusing to seed: this script DELETES all rows.\n"
            f"  DATABASE_URL host : {host or '(not set)'}\n"
            f"  SEED_ALLOW_HOST   : {allowed or '(not set)'}\n"
            "Set SEED_ALLOW_HOST to the host of the throwaway branch you "
            "intend to wipe."
        )
    print(f"Seeding database host: {host}")


def _uuid() -> uuid.UUID:
    # Built from the seeded RNG so IDs are reproducible.
    return uuid.UUID(int=random.getrandbits(128), version=4)


def seed_data():
    _assert_safe_to_seed()

    random.seed(SEED)
    Faker.seed(SEED)
    fake = Faker("en_GB")

    now = datetime.now(timezone.utc)

    # Last 6 calendar months, oldest first. Computed up front so the
    # transactions below span exactly this window.
    period_starts = []
    month = get_month_start(datetime.now())
    for _ in range(6):
        period_starts.append(month)
        month = get_month_start(month - timedelta(days=1))
    period_starts.reverse()

    window_start = period_starts[0].replace(tzinfo=timezone.utc)
    window_seconds = int((now - window_start).total_seconds())

    owner_user_id = os.getenv("SEED_OWNER_USER_ID", "").strip() or None

    with get_db() as conn:  # commits on clean exit, rolls back on error
        cursor = conn.cursor()

        for table in WIPE_ORDER:
            cursor.execute(f"DELETE FROM {table}")

        stores = []  # [{store_id, sources: {type: id}, offerings: [ids]}]

        for i in range(10):
            merchant_id = cursor.execute(
                """INSERT INTO merchants (business_name, location, tier)
                   VALUES (%s, %s, %s) RETURNING merchant_id""",
                (
                    fake.company(),
                    random.choice(SA_CITIES),
                    random.choice(["insights", "full"]),
                ),
            ).fetchone()[0]

            # One owner per merchant so auth flows are testable. The first
            # merchant belongs to SEED_OWNER_USER_ID when it is set.
            user_id = owner_user_id if (i == 0 and owner_user_id) else _uuid()
            cursor.execute(
                """INSERT INTO merchant_users (user_id, merchant_id, role)
                   VALUES (%s, %s, 'owner')""",
                (user_id, merchant_id),
            )

            store_id = cursor.execute(
                """INSERT INTO stores (merchant_id, store_name, location)
                   VALUES (%s, %s, %s) RETURNING store_id""",
                (merchant_id, "Main Store", random.choice(SA_CITIES)),
            ).fetchone()[0]

            whatsapp_number = f"+27{random.randint(600000000, 899999999)}"
            sources = {}
            for source_type in SOURCE_TYPES:
                sources[source_type] = cursor.execute(
                    """INSERT INTO data_sources
                           (store_id, source_name, source_type, external_identifier)
                       VALUES (%s, %s, %s, %s) RETURNING source_id""",
                    (
                        store_id,
                        source_type.replace("_", " ").title(),
                        source_type,
                        whatsapp_number if source_type == "whatsapp" else None,
                    ),
                ).fetchone()[0]

            offerings = []
            for offering_name in random.sample(
                SAMPLE_OFFERINGS, k=random.randint(2, 4)
            ):
                offerings.append(
                    cursor.execute(
                        """INSERT INTO offerings (store_id, offering_name)
                           VALUES (%s, %s) RETURNING offering_id""",
                        (store_id, offering_name),
                    ).fetchone()[0]
                )

            stores.append(
                {"store_id": store_id, "sources": sources, "offerings": offerings}
            )

        # WhatsApp-first fixture: a merchant with NO owner and a known claim code,
        # for testing the dashboard "claim your business" step.
        unclaimed_merchant_id = cursor.execute(
            """INSERT INTO merchants (business_name, location)
               VALUES ('Unclaimed Demo Spaza', 'Soweto') RETURNING merchant_id"""
        ).fetchone()[0]
        unclaimed_store_id = cursor.execute(
            """INSERT INTO stores (merchant_id, store_name)
               VALUES (%s, 'Main Store') RETURNING store_id""",
            (unclaimed_merchant_id,),
        ).fetchone()[0]
        cursor.execute(
            """INSERT INTO data_sources
                   (store_id, source_name, source_type, external_identifier)
               VALUES (%s, 'Whatsapp', 'whatsapp', '+27500000000')""",
            (unclaimed_store_id,),
        )
        cursor.execute(
            """INSERT INTO connect_codes (code, purpose, store_id, expires_at)
               VALUES (%s, 'claim_merchant', %s, now() + interval '365 days')""",
            (UNCLAIMED_CLAIM_CODE, unclaimed_store_id),
        )

        for _ in range(300):
            store = random.choice(stores)
            input_type = random.choice(list(INPUT_TO_SOURCE))
            source_id = store["sources"][INPUT_TO_SOURCE[input_type]]
            amount_zar = round(random.uniform(50, 5000), 2)

            if input_type == "whatsapp":
                payment_method = None
                offering_id = random.choice(store["offerings"])
                quantity = random.randint(1, 5)
            else:
                payment_method = random.choice(["cash", "digital"])
                offering_id = None
                quantity = None

            transaction_date = window_start + timedelta(
                seconds=random.randint(0, window_seconds)
            )
            is_voided = random.random() < 0.03
            # Live schema: CHECK (is_voided = (voided_at IS NOT NULL)).
            voided_at = (
                min(transaction_date + timedelta(days=random.randint(0, 3)), now)
                if is_voided
                else None
            )

            cursor.execute(
                """INSERT INTO transactions (
                       store_id, source_id, offering_id, quantity, input_type,
                       amount_zar, payment_method, raw_message,
                       whatsapp_message_id, is_voided, voided_at, transaction_date
                   )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    store["store_id"],
                    source_id,
                    offering_id,
                    quantity,
                    input_type,
                    amount_zar,
                    payment_method,
                    str(int(amount_zar)) if input_type == "whatsapp" else None,
                    f"SM{_uuid().hex[:32]}" if input_type == "whatsapp" else None,
                    is_voided,
                    voided_at,
                    transaction_date,
                ),
            )

        # TEMPORARY: this duplicates the snapshot logic in the BI engine.
        # Replace with a call to the real engine once it has been reviewed.
        for store in stores:
            monthly_revenues = []
            previous_revenue = None

            for period_start in period_starts:
                period_end = get_next_month(period_start)
                cursor.execute(
                    """SELECT COUNT(*),
                              COALESCE(SUM(amount_zar), 0),
                              COALESCE(AVG(amount_zar), 0),
                              COALESCE(SUM(amount_zar) FILTER
                                  (WHERE payment_method = 'cash'), 0),
                              COALESCE(SUM(amount_zar) FILTER
                                  (WHERE payment_method = 'digital'), 0)
                       FROM transactions
                       WHERE store_id = %s
                         AND transaction_date >= %s
                         AND transaction_date < %s
                         AND is_voided = FALSE""",
                    (store["store_id"], period_start, period_end),
                )
                (
                    transaction_count,
                    total_revenue,
                    average_transaction,
                    cash_revenue,
                    digital_revenue,
                ) = cursor.fetchone()

                revenue_growth_pct = None
                if previous_revenue is not None and previous_revenue > 0:
                    revenue_growth_pct = round(
                        ((total_revenue - previous_revenue) / previous_revenue) * 100,
                        2,
                    )

                monthly_revenues.append(total_revenue)
                revenue_volatility = (
                    round(statistics.stdev(monthly_revenues), 2)
                    if len(monthly_revenues) >= 2
                    else None
                )

                cursor.execute(
                    """INSERT INTO financial_snapshots (
                           store_id, period_start, period_end,
                           total_revenue_zar, transaction_count,
                           average_transaction_zar, cash_revenue_zar,
                           digital_revenue_zar, revenue_growth_pct, revenue_volatility
                       )
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        store["store_id"],
                        period_start.date(),
                        (period_end - timedelta(days=1)).date(),
                        round(total_revenue, 2),
                        transaction_count,
                        round(average_transaction, 2),
                        round(cash_revenue, 2),
                        round(digital_revenue, 2),
                        revenue_growth_pct,
                        revenue_volatility,
                    ),
                )
                previous_revenue = total_revenue

    print("Data seeded successfully.")
    print(f"Unclaimed merchant claim code: {UNCLAIMED_CLAIM_CODE}")
    if owner_user_id:
        print("First merchant is owned by SEED_OWNER_USER_ID.")


if __name__ == "__main__":
    try:
        seed_data()
    finally:
        close_pool()