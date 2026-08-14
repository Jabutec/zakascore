import sqlite3
import os
from faker import Faker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "zakascore.db")

fake = Faker("en_GB")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for i in range (1,11):
    merchant_id = f"M{i:03d}"
    business_name = fake.company()
    location = fake.city()
    
    cursor.execute("""
        INSERT INTO merchants(
            merchant_id,
            business_name,
            location
        )
        VALUES (?,?,?);
    """,(
        merchant_id,
        business_name,
        location
    ))

conn.commit()
conn.close()

print("10 merchants seeded successfully.")