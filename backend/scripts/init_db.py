from database.connection import get_db


def init_database(connection=None):
    owns_connection = connection is None
    conn = connection or get_db()

    try:
        with conn.cursor() as cursor:
            print("Creating ZakaScore PostgreSQL schema...")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merchants (
                    merchant_id TEXT PRIMARY KEY,
                    business_name TEXT NOT NULL,
                    location TEXT,
                    tier TEXT NOT NULL DEFAULT 'insights'
                        CHECK (tier IN ('insights', 'full')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS merchant_users (
                    user_id TEXT NOT NULL,
                    merchant_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'owner'
                        CHECK (role IN ('owner', 'admin', 'employee', 'viewer')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, merchant_id),
                    FOREIGN KEY (merchant_id)
                        REFERENCES merchants(merchant_id)
                        ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stores (
                    store_id TEXT PRIMARY KEY,
                    merchant_id TEXT NOT NULL,
                    store_name TEXT NOT NULL,
                    location TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (merchant_id)
                        REFERENCES merchants(merchant_id)
                        ON DELETE CASCADE,
                    UNIQUE (merchant_id, store_name)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    source_id TEXT PRIMARY KEY,
                    store_id TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL
                        CHECK (source_type IN (
                            'pos',
                            'bank_statement',
                            'accounting_software',
                            'online_store',
                            'whatsapp',
                            'csv',
                            'manual'
                        )),
                    external_identifier TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id)
                        REFERENCES stores(store_id)
                        ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offerings (
                    offering_id TEXT PRIMARY KEY,
                    store_id TEXT NOT NULL,
                    offering_name TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id)
                        REFERENCES stores(store_id)
                        ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    store_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    offering_id TEXT,
                    quantity INTEGER CHECK (quantity IS NULL OR quantity > 0),
                    input_type TEXT CHECK (input_type IN (
                        'pos_tap',
                        'voice',
                        'manual',
                        'whatsapp',
                        'csv',
                        'api'
                    )),
                    amount_zar NUMERIC(12, 2) NOT NULL CHECK (amount_zar >= 0),
                    payment_method TEXT CHECK (payment_method IN ('cash', 'digital')),
                    raw_message TEXT,
                    whatsapp_message_id TEXT UNIQUE,
                    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
                    transaction_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id)
                        REFERENCES stores(store_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (source_id)
                        REFERENCES data_sources(source_id)
                        ON DELETE RESTRICT,
                    FOREIGN KEY (offering_id)
                        REFERENCES offerings(offering_id)
                        ON DELETE SET NULL
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    store_id TEXT NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    total_revenue_zar NUMERIC(12, 2) NOT NULL
                        CHECK (total_revenue_zar >= 0),
                    transaction_count INTEGER NOT NULL
                        CHECK (transaction_count >= 0),
                    average_transaction_zar NUMERIC(12, 2) NOT NULL
                        CHECK (average_transaction_zar >= 0),
                    cash_revenue_zar NUMERIC(12, 2) NOT NULL
                        CHECK (cash_revenue_zar >= 0),
                    digital_revenue_zar NUMERIC(12, 2) NOT NULL
                        CHECK (digital_revenue_zar >= 0),
                    revenue_growth_pct NUMERIC(8, 2),
                    revenue_volatility NUMERIC(12, 4),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id)
                        REFERENCES stores(store_id)
                        ON DELETE CASCADE,
                    CHECK (period_end >= period_start),
                    UNIQUE (store_id, period_start, period_end)
                );
            """)

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_merchant_users_merchant "
                "ON merchant_users(merchant_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_stores_merchant "
                "ON stores(merchant_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sources_store "
                "ON data_sources(store_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_store "
                "ON transactions(store_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_source "
                "ON transactions(source_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_date "
                "ON transactions(transaction_date);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_store "
                "ON financial_snapshots(store_id);"
            )

        conn.commit()
    finally:
        if owns_connection:
            conn.close()

    print("PostgreSQL schema initialized successfully.")


if __name__ == "__main__":
    init_database()