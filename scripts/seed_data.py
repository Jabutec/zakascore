import sqlite3
import os
from faker import Faker
import random
import statistics
from datetime import datetime, timedelta
from utils.helpers import get_month_start,get_next_month

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "zakascore.db")

fake = Faker("en_GB")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

# Seed merchants data
for i in range (1,11):
    merchant_id = f"M{i:03d}"
    
    cursor.execute("""
        INSERT INTO merchants(
            merchant_id,
            business_name,
            location
         )
         VALUES (?,?,?);
     """,(
        merchant_id,
        fake.company(),
        fake.city()
    ))

cursor.execute("SELECT merchant_id FROM merchants")
merchant_ids = [row[0] for row in cursor.fetchall()]

if not merchant_ids:
    raise RuntimeError("No merchants found")


# Seed data sources data
sources = [
    "pos",
    "online_store",
    "bank_statement",
    "accounting_software"
]
    
for source_type in sources:
    source_id = f"S{sources.index(source_type) +1:03d}"
    
    cursor.execute("""
        INSERT INTO data_sources(
            source_id,
            source_name,
            source_type
        )
        VALUES(?,?,?);
    """,(
        source_id,
        fake.company(),
        source_type
    ))

cursor.execute("""
    SELECT source_id 
    FROM data_sources
""")
source_ids = [row[0] for row in cursor.fetchall()]


# Seed transactions data    
for i in range(1,301):
    transaction_id = f"T{i:04d}"
    merchant_id = random.choice(merchant_ids)
    source_id = random.choice(source_ids)
    input_type = random.choice([
        "pos_tap",
        "voice",
        "manual"   
    ])
    amount_zar = round(random.uniform(50, 5000), 2)
    payment_method = random.choice([
        "cash",
        "digital"
    ])
    transaction_date =fake.date_time_between(
        start_date ="-6m",
        end_date= "now"
    )
    
    cursor.execute("""
        INSERT INTO transactions(
            transaction_id,
            merchant_id,
            source_id,
            input_type,
            amount_zar,
            payment_method,
            transaction_date
        )
        VALUES (?,?,?,?,?,?,?);
    """,(
        transaction_id,
        merchant_id,
        source_id,
        input_type,
        amount_zar,
        payment_method,
        transaction_date
    ))


# Seed financial snapshots    
today = datetime.now()
current_month = get_month_start(today)

period_starts = []

for months_back in range(5,-1,-1):
    month = current_month
    
    for _ in range(months_back):
        if month.month ==1:
            month = month.replace(
                year= month.year -1,
                month=12
            )
        else:
            month = month.replace(
            month=month.month -1
            )
    period_starts.append(month)
    
snapshot_number = 1

for merchant_id in merchant_ids:
    monthly_revenues = []
    previous_revenue =None
    
    for period_start in period_starts:
        period_end = get_next_month(
            period_start
        )
        
        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(amount_zar), 0),
                COALESCE(AVG(amount_zar), 0),
                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'cash'
                            THEN amount_zar
                            ELSE 0
                        END
                    ),
                    0
                ),
                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'cash'
                            THEN amount_zar
                            ELSE 0
                        END
                    ),
                    0
                )
            FROM transactions
            WHERE merchant_id = ?
                AND transaction_date >= ?
                AND transaction_date < ?
        """,(
            merchant_id,
            period_start,
            period_end
        ))
        
        (
            transaction_count,
            total_revenue,
            average_transaction,
            cash_revenue,
            digital_revenue
        )= cursor.fetchone()
        
        revenue_growth_pct = None
        if (
            previous_revenue is not None
            and previous_revenue > 0
        ):
            revenue_growth_pct = round(
                (
                    (total_revenue-previous_revenue)/ previous_revenue
                ) * 100,
                2
            )
        
        monthly_revenues.append(total_revenue)
        revenue_volatility = None
        
        if len(monthly_revenues) >= 2:
            revenue_volatility = round(statistics.stdev(monthly_revenues),2)
        snapshot_id = f"FS{snapshot_number:03d}"
        cursor.execute("""
            INSERT INTO financial_snapshots(
                snapshot_id,
                merchant_id,
                period_start,
                period_end,
                total_revenue_zar,
                transaction_count,
                average_transaction_zar,
                cash_revenue_zar,
                digital_revenue_zar,
                revenue_growth_pct,
                revenue_volatility
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,(
            snapshot_id,
            merchant_id,
            period_start.date(),
            (period_end-timedelta(days=1)).date(),
            round(total_revenue,2),
            transaction_count,
            round(average_transaction,2),
            round(cash_revenue,2),
            round(digital_revenue,2),
            revenue_growth_pct,
            revenue_volatility
        ))
        
        previous_revenue= total_revenue
        snapshot_number += 1

conn.commit()
conn.close()

print("data seeded successfully.")