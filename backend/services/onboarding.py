from validation.models import Merchant, Store, DataSource, Tier, SourceType
from dataclasses import dataclass


@dataclass
class MerchantContext:
    merchant: Merchant
    store_id: str
    source_id: str


def get_merchant_by_number(whatsapp_number: str, conn) -> MerchantContext | None:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT m.merchant_id, m.business_name, m.location, m.tier, m.created_at,
                      s.store_id, ds.source_id
               FROM data_sources ds
               JOIN stores s ON s.store_id = ds.store_id
               JOIN merchants m ON m.merchant_id = s.merchant_id
               WHERE ds.source_type = 'whatsapp'
                 AND ds.external_identifier = %s""",
            (whatsapp_number,)
        )
        row = cur.fetchone()

    if row is None:
        return None

    merchant = Merchant(
        merchant_id=row[0],
        business_name=row[1],
        location=row[2],
        tier=row[3],
        created_at=row[4],
    )

    return MerchantContext(merchant=merchant, store_id=row[5], source_id=row[6])


def generate_next_transaction_id(conn) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT transaction_id FROM transactions ORDER BY transaction_id DESC LIMIT 1"
        )
        row = cur.fetchone()

    if row is None:
        return "T001"

    last_number = int(row[0][1:])
    return f"T{last_number + 1:03d}"


def generate_next_merchant_id(conn) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT COALESCE(MAX(substring(merchant_id FROM 2)::INTEGER), 0)
               FROM merchants WHERE merchant_id ~ '^M[0-9]+$'"""
        )
        return f"M{cur.fetchone()[0] + 1:03d}"


def generate_next_store_id(conn) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(MAX(substring(store_id FROM 3)::INTEGER), 0) "
            "FROM stores WHERE store_id ~ '^ST[0-9]+$'"
        )
        return f"ST{cur.fetchone()[0] + 1:03d}"


def generate_next_source_id(conn) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT COALESCE(MAX(substring(source_id FROM 2)::INTEGER), 0)
               FROM data_sources WHERE source_id ~ '^S[0-9]+$'"""
        )
        return f"S{cur.fetchone()[0] + 1:03d}"


def create_merchant(whatsapp_number: str, business_name: str, conn) -> MerchantContext:
    merchant_id = generate_next_merchant_id(conn)
    store_id = generate_next_store_id(conn)
    source_id = generate_next_source_id(conn)

    merchant = Merchant(
        merchant_id=merchant_id,
        business_name=business_name,
        location=None,
        tier=Tier.INSIGHTS,
    )

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO merchants (merchant_id, business_name, location, tier)
               VALUES (%s, %s, %s, %s)""",
            (merchant.merchant_id, merchant.business_name, merchant.location, merchant.tier.value)
        )
        cur.execute(
            """INSERT INTO stores (store_id, merchant_id, store_name, location)
               VALUES (%s, %s, %s, %s)""",
            (store_id, merchant_id, business_name, None),
        )
        cur.execute(
            """INSERT INTO data_sources
                   (source_id, store_id, source_name, source_type, external_identifier)
               VALUES (%s, %s, %s, %s, %s)""",
            (source_id, store_id, "WhatsApp", SourceType.WHATSAPP.value, whatsapp_number),
        )
    conn.commit()

    return MerchantContext(merchant=merchant, store_id=store_id, source_id=source_id)