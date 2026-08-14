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
        CREATE TABLE IF NOT EXISTS transactions(
            transaction_id TEXT PRIMARY KEY,
            merchant_id TEXT NOT NULL,
            input_type TEXT CHECK (input_type IN ('pos_tap', 'voice', 'manual')),
            amount_zar REAL NOT NULL,
            payment_method TEXT CHECK (payment_method IN ('cash', 'digital')),
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)   
        );                          
        """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_sources(
       source_id TEXT PRIMARY KEY,
       source_name TEXT NOT NULL,
       source_type TEXT CHECK(source_type IN ('pos', 'bank', 'manual', 'online_store')),
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );              
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_snapshots(
        snapshot_id TEXT PRIMARY KEY,
        merchant_id TEXT NOT NULL,
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        total_revenue_zar REAL NOT NULL CHECK(total_revenue_zar >= 0),
        transaction_count INTEGER NOT NULL CHECK(transaction_count >= 0),
        average_transaction_zar REAL NOT NULL CHECK(average_transaction_zar >=0),
        cash_revenue_zar REAL NOT NULL CHECK(cash_revenue_zar >= 0),
        digital_revenue_zar REAL NOT NULL CHECK(digital_revenue_zar >= 0),
        revenue_growth_pct REAL,
        revenue_volatility REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
        CHECK (period_end >= period_start)
    );
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfullly at {DB_PATH}")
    
if __name__ == "__main__":
    init_database()
    
