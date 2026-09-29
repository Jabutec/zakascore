import random
import statistics
from datetime import datetime, timedelta

from faker import Faker

from database.connection import get_db
from utils.helpers import get_month_start, get_next_month


fake = Faker("en_GB")
SOURCE_TYPES = [
    "pos",
    "online_store",
    "bank_statement",
    "accounting_software",
    "whatsapp",
]
SAMPLE_OFFERINGS = [
    "shirt",
    "dress",
    "haircut",
    "manicure",
    "phone case",
    "airtime",
    "bread",
    "cooldrink",
    "hair extension",
    "makeup session",
]


def seed_data():
    conn = get_db()
    try:
        cursor = conn.cursor()
        store_ids = []
        sources_by_store = {}
        offerings_by_store = {}
        source_number = 1

        for index in range(1, 11):
            merchant_id = f"M{index:03d}"
            store_id = f"ST{index:03d}"
            store_ids.append(store_id)
            whatsapp_number = f"+27{random.randint(600000000, 899999999)}"

            cursor.execute(
                """INSERT INTO merchants
                       (merchant_id, business_name, location, tier)
                   VALUES (%s, %s, %s, %s)""",
                (merchant_id, fake.company(), fake.city(), random.choice(["insights", "full"])),
            )
            cursor.execute(
                """INSERT INTO stores (store_id, merchant_id, store_name, location)
                   VALUES (%s, %s, %s, %s)""",
                (store_id, merchant_id, "Main Store", fake.city()),
            )

            sources_by_store[store_id] = []
            for source_type in SOURCE_TYPES:
                source_id = f"S{source_number:03d}"
                source_number += 1
                cursor.execute(
                    """INSERT INTO data_sources
                           (source_id, store_id, source_name, source_type, external_identifier)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        source_id,
                        store_id,
                        source_type.replace("_", " ").title(),
                        source_type,
                        whatsapp_number if source_type == "whatsapp" else None,
                    ),
                )
                sources_by_store[store_id].append((source_id, source_type))

            chosen_offerings = random.sample(
                SAMPLE_OFFERINGS, k=random.randint(2, 4)
            )
            offerings_by_store[store_id] = []
            for offering_index, offering_name in enumerate(chosen_offerings, start=1):
                offering_id = f"O{index * 10 + offering_index:03d}"
                cursor.execute(
                    """INSERT INTO offerings (offering_id, store_id, offering_name)
                       VALUES (%s, %s, %s)""",
                    (offering_id, store_id, offering_name),
                )
                offerings_by_store[store_id].append(offering_id)

        for index in range(1, 301):
            transaction_id = f"T{index:03d}"
            store_id = random.choice(store_ids)
            source_id, _ = random.choice(sources_by_store[store_id])
            input_type = random.choice(["pos_tap", "voice", "manual", "whatsapp"])
            amount_zar = round(random.uniform(50, 5000), 2)

            if input_type == "whatsapp":
                payment_method = None
                offering_id = random.choice(offerings_by_store[store_id])
                quantity = random.randint(1, 5)
            else:
                payment_method = random.choice(["cash", "digital"])
                offering_id = None
                quantity = None

            raw_message = str(int(amount_zar)) if input_type == "whatsapp" else None
            whatsapp_message_id = (
                f"SM{fake.uuid4().replace('-', '')[:32]}"
                if input_type == "whatsapp"
                else None
            )
            transaction_date = fake.date_time_between(
                start_date="-6m",
                end_date="now",
            )

            cursor.execute(
                """INSERT INTO transactions (
                       transaction_id, store_id, source_id, offering_id, quantity,
                       input_type, amount_zar, payment_method, raw_message,
                       whatsapp_message_id, is_voided, transaction_date
                   )
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    transaction_id,
                    store_id,
                    source_id,
                    offering_id,
                    quantity,
                    input_type,
                    amount_zar,
                    payment_method,
                    raw_message,
                    whatsapp_message_id,
                    random.random() < 0.03,
                    transaction_date,
                ),
            )

        current_month = get_month_start(datetime.now())
        period_starts = []
        for months_back in range(5, -1, -1):
            month = current_month
            for _ in range(months_back):
                month = (
                    month.replace(year=month.year - 1, month=12)
                    if month.month == 1
                    else month.replace(month=month.month - 1)
                )
            period_starts.append(month)

        snapshot_number = 1
        for store_id in store_ids:
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
                    (store_id, period_start, period_end),
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
                           snapshot_id, store_id, period_start, period_end,
                           total_revenue_zar, transaction_count,
                           average_transaction_zar, cash_revenue_zar,
                           digital_revenue_zar, revenue_growth_pct, revenue_volatility
                       )
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        f"F{snapshot_number:03d}",
                        store_id,
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
                snapshot_number += 1

        conn.commit()
    finally:
        conn.close()
    print("Data seeded successfully.")


if __name__ == "__main__":
    seed_data()
