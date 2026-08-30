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
      whatsapp_number TEXT NOT NULL UNIQUE,
      location TEXT,
      tier TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free', 'insights', 'full')),
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_sources(
           source_id TEXT PRIMARY KEY,
           source_name TEXT NOT NULL,
           source_type TEXT CHECK(source_type IN ('pos', 'bank_statement', 'accounting_software', 'online_store', 'whatsapp')),
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            transaction_id TEXT PRIMARY KEY,
            merchant_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            input_type TEXT CHECK (input_type IN ('pos_tap', 'voice', 'manual', 'whatsapp')),
            amount_zar REAL NOT NULL CHECK(amount_zar >=0),
            payment_method TEXT CHECK (payment_method IN ('cash', 'digital')),
            raw_message TEXT,
            whatsapp_message_id TEXT UNIQUE,
            is_voided INTEGER NOT NULL DEFAULT 0 CHECK(is_voided IN (0, 1)),
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
            FOREIGN KEY (source_id) REFERENCES data_sources(source_id)
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
    print(f"Database initialized successfully at {DB_PATH}")
    
if __name__ == "__main__":
    init_database()