import sqlite3
import os
from faker import Faker
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "zakascore.db")

fake = Faker("en_GB")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# for i in range (1,11):
#     merchant_id = f"M{i:03d}"
#     business_name = fake.company()
#     location = fake.city()
    
#     cursor.execute("""
#         INSERT INTO merchants(
#             merchant_id,
#             business_name,
#             location
#         )
#         VALUES (?,?,?);
#     """,(
#         merchant_id,
#         business_name,
#         location
#     ))
    
for i in range(1,301):
    transaction_id = f"T{i:04d}"
    merchant_id = f"M{random.randint(1,10):03d}"
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
            input_type,
            amount_zar,
            payment_method,
            transaction_date
        )
        VALUES (?,?,?,?,?,?);
    """,(
        transaction_id,
        merchant_id,
        input_type,
        amount_zar,
        payment_method,
        transaction_date
    ))

conn.commit()
conn.close()

print("data seeded successfully.")