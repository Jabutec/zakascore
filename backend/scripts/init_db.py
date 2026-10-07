from database.connection import get_direct_connection


SCHEMA_STATEMENTS = [
    #merchants table
    """
    CREATE TABLE IF NOT EXISTS merchants (
        merchant_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        business_name TEXT NOT NULL,
        location      TEXT,
        tier          TEXT NOT NULL DEFAULT 'insights'
                      CHECK (tier IN ('insights', 'full')),
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    #merchant_users table
    """
    CREATE TABLE IF NOT EXISTS merchant_users (
        user_id     UUID NOT NULL,
        merchant_id UUID NOT NULL
                    REFERENCES merchants(merchant_id) ON DELETE CASCADE,
        role        TEXT NOT NULL DEFAULT 'owner'
                    CHECK (role IN ('owner', 'admin', 'employee', 'viewer')),
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (user_id, merchant_id)
    );
    """,
    #stores table
    """
    CREATE TABLE IF NOT EXISTS stores (
        store_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        merchant_id UUID NOT NULL
                    REFERENCES merchants(merchant_id) ON DELETE CASCADE,
        store_name  TEXT NOT NULL,
        location    TEXT,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (merchant_id, store_name)
    );
    """,
    #data_sources table
    """
    CREATE TABLE IF NOT EXISTS data_sources (
        source_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        store_id            UUID NOT NULL
                            REFERENCES stores(store_id) ON DELETE CASCADE,
        source_name         TEXT NOT NULL,
        source_type         TEXT NOT NULL
                            CHECK (source_type IN (
                                'pos', 'bank_statement', 'accounting_software',
                                'online_store', 'pwa', 'csv', 'manual'
                            )),
        external_identifier TEXT,
        is_active           BOOLEAN NOT NULL DEFAULT TRUE,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (source_id, store_id)
    );
    """,
    """
    ALTER TABLE data_sources
        DROP CONSTRAINT IF EXISTS data_sources_source_type_check;
    """,
    """
    UPDATE data_sources
       SET source_type = 'manual',
           source_name = 'Manual (legacy)',
           external_identifier = NULL
     WHERE source_type = 'whatsapp';
    """,
    """
    ALTER TABLE data_sources
        ADD CONSTRAINT data_sources_source_type_check
        CHECK (source_type IN (
            'pos', 'bank_statement', 'accounting_software',
            'online_store', 'pwa', 'csv', 'manual'
        ));
    """,
    """
    DROP INDEX IF EXISTS uniq_whatsapp_source_per_number;
    """,
    #connect_codes table
    """
    CREATE TABLE IF NOT EXISTS connect_codes (
        code       TEXT PRIMARY KEY,
        store_id   UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
        expires_at TIMESTAMPTZ NOT NULL,
        used_at    TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    #offerings table
    """
    CREATE TABLE IF NOT EXISTS offerings (
        offering_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        store_id      UUID NOT NULL
                      REFERENCES stores(store_id) ON DELETE CASCADE,
        offering_name TEXT NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
    
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_offering_per_store
        ON offerings (store_id, lower(offering_name));
    """,
    #transactions table
    """
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        store_id            UUID NOT NULL,
        source_id           UUID NOT NULL,
        client_txn_id       UUID NOT NULL,
        offering_id         UUID REFERENCES offerings(offering_id) ON DELETE RESTRICT,
        quantity            INTEGER CHECK (quantity IS NULL OR quantity > 0),
        input_type          TEXT NOT NULL
                            CHECK (input_type IN (
                                'pos_tap', 'voice', 'manual', 'pwa', 'csv', 'api'
                            )),
        amount_zar          NUMERIC(12, 2) NOT NULL CHECK (amount_zar > 0),
        payment_method      TEXT NOT NULL CHECK (payment_method IN ('cash', 'digital')),
        is_voided           BOOLEAN NOT NULL DEFAULT FALSE,
        voided_at           TIMESTAMPTZ,
        void_reason         TEXT,
        transaction_date    TIMESTAMPTZ NOT NULL DEFAULT now(),
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
        FOREIGN KEY (store_id)
            REFERENCES stores(store_id) ON DELETE CASCADE,
        FOREIGN KEY (source_id, store_id)
            REFERENCES data_sources(source_id, store_id) ON DELETE RESTRICT,
        CHECK (is_voided = (voided_at IS NOT NULL)),
        CHECK (quantity IS NULL OR offering_id IS NOT NULL),
        UNIQUE (store_id, client_txn_id)
    );
    """,
    #financial_snapshots table
    """
    CREATE TABLE IF NOT EXISTS financial_snapshots (
        snapshot_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        store_id                UUID NOT NULL
                                REFERENCES stores(store_id) ON DELETE CASCADE,
        period_start            DATE NOT NULL,
        period_end              DATE NOT NULL,
        total_revenue_zar       NUMERIC(12, 2) NOT NULL CHECK (total_revenue_zar >= 0),
        transaction_count       INTEGER NOT NULL CHECK (transaction_count >= 0),
        average_transaction_zar NUMERIC(12, 2) NOT NULL CHECK (average_transaction_zar >= 0),
        cash_revenue_zar        NUMERIC(12, 2) NOT NULL CHECK (cash_revenue_zar >= 0),
        digital_revenue_zar     NUMERIC(12, 2) NOT NULL CHECK (digital_revenue_zar >= 0),
        revenue_growth_pct      NUMERIC(8, 2),
        revenue_volatility      NUMERIC(12, 4),
        created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
        CHECK (period_end >= period_start),
        UNIQUE (store_id, period_start, period_end)
    );
    """,
    #indexes table
    "CREATE INDEX IF NOT EXISTS idx_merchant_users_merchant ON merchant_users (merchant_id);",
    """
    CREATE UNIQUE INDEX IF NOT EXISTS one_owner_per_merchant
        ON merchant_users (merchant_id) WHERE role = 'owner';
    """,
    "CREATE INDEX IF NOT EXISTS idx_stores_merchant ON stores (merchant_id);",
    "CREATE INDEX IF NOT EXISTS idx_sources_store ON data_sources (store_id);",
    # Dashboard queries:
    """
    CREATE INDEX IF NOT EXISTS idx_transactions_store_date_live
        ON transactions (store_id, transaction_date)
        WHERE NOT is_voided;
    """,
    "CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions (source_id);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_offering ON transactions (offering_id);",
]


def init_database(connection=None):
    owns_connection = connection is None
    conn = connection or get_direct_connection()

    try:
        print("Creating ZakaScore PostgreSQL schema...")
        with conn.cursor() as cursor:
            for statement in SCHEMA_STATEMENTS:
                cursor.execute(statement)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if owns_connection:
            conn.close()

    print("PostgreSQL schema initialized successfully.")


if __name__ == "__main__":
    init_database()