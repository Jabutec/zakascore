import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "zakascore.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    print("Creating tables...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchants(
      merchant_id TEXT PRIMARY KEY,
      business_name TEXT NOT NULL,
      location TEXT,  
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        unit_price_zar REAL NOT NULL
    );              
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        transaction_id TEXT PRIMARY KEY,
        merchant_id TEXT NOT NULL,
        input_type TEXT CHECK (input_type IN ('pos_tap', 'voice', 'manual')),
        total_amount_zar REAL NOT NULL,
        payment_method TEXT CHECK (payment_method IN ('cash', 'digital')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)   
    );                          
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfullly at {DB_PATH}")
    
if __name__ == "__main__":
    init_database()
    
