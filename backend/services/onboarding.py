from validation.models import Merchant, Tier


def get_merchant_by_number(whatsapp_number: str, conn) -> Merchant | None:
    cursor = conn.execute(
        """SELECT m.merchant_id, m.business_name, ds.external_identifier,
                  COALESCE(s.location, m.location, ''), m.tier, m.created_at,
                  s.store_id, ds.source_id
           FROM data_sources ds
           JOIN stores s ON s.store_id = ds.store_id
           JOIN merchants m ON m.merchant_id = s.merchant_id
           WHERE ds.source_type = 'whatsapp'
             AND ds.external_identifier = %s""",
        (whatsapp_number,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return Merchant(
        merchant_id=row[0],
        business_name=row[1],
        whatsapp_number=row[2],
        location=row[3],
        tier=row[4],
        created_at=row[5],
        store_id=row[6],
        source_id=row[7],
    )
    
def generate_next_transaction_id(conn) -> str:
    cursor = conn.execute(
        "SELECT transaction_id FROM transactions ORDER BY transaction_id DESC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        return "T001"

    last_number = int(row[0][1:])
    return f"T{last_number + 1:03d}"

def generate_next_merchant_id(conn) -> str:
    cursor = conn.execute(
        """SELECT COALESCE(MAX(substring(merchant_id FROM 2)::INTEGER), 0)
           FROM merchants WHERE merchant_id ~ '^M[0-9]+$'"""
    )
    return f"M{cursor.fetchone()[0] + 1:03d}"


def generate_next_store_id(conn) -> str:
    cursor = conn.execute(
        "SELECT COALESCE(MAX(substring(store_id FROM 3)::INTEGER), 0) "
        "FROM stores WHERE store_id ~ '^ST[0-9]+$'"
    )
    return f"ST{cursor.fetchone()[0] + 1:03d}"


def generate_next_source_id(conn) -> str:
    cursor = conn.execute(
        """SELECT COALESCE(MAX(substring(source_id FROM 2)::INTEGER), 0)
           FROM data_sources WHERE source_id ~ '^S[0-9]+$'"""
    )
    return f"S{cursor.fetchone()[0] + 1:03d}"

def create_merchant(whatsapp_number: str, business_name: str, conn):
    merchant_id = generate_next_merchant_id(conn)
    store_id = generate_next_store_id(conn)
    source_id = generate_next_source_id(conn)

    merchant = Merchant(
        merchant_id=merchant_id,
        business_name=business_name,
        whatsapp_number=whatsapp_number,
        location="",
        tier=Tier.INSIGHTS,
        store_id=store_id,
        source_id=source_id,
    )

    conn.execute(
        """INSERT INTO merchants (merchant_id, business_name, location, tier)
           VALUES (%s, %s, %s, %s)""",
        (merchant.merchant_id, merchant.business_name, merchant.location, merchant.tier.value)
    )
    conn.execute(
        """INSERT INTO stores (store_id, merchant_id, store_name, location)
           VALUES (%s, %s, %s, %s)""",
        (store_id, merchant_id, business_name, merchant.location),
    )
    conn.execute(
        """INSERT INTO data_sources
               (source_id, store_id, source_name, source_type, external_identifier)
           VALUES (%s, %s, %s, 'whatsapp', %s)""",
        (source_id, store_id, "WhatsApp", whatsapp_number),
    )
    conn.commit()

    return merchant