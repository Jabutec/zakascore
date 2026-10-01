import random
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from validation.models import Merchant, DataSource, Tier, SourceType, ConnectCode


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
            (whatsapp_number,),
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
            (merchant.merchant_id, merchant.business_name, merchant.location, merchant.tier.value),
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


def create_dashboard_merchant(user_id: str, business_name: str, conn, *, store_name: str | None = None, code_ttl_hours: int = 24):
    merchant_id = generate_next_merchant_id(conn)
    store_id = generate_next_store_id(conn)
    target_store_name = store_name or business_name

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO merchants (merchant_id, business_name, location, tier)
               VALUES (%s, %s, %s, %s)""",
            (merchant_id, business_name, None, Tier.INSIGHTS.value),
        )
        cur.execute(
            """INSERT INTO stores (store_id, merchant_id, store_name, location)
               VALUES (%s, %s, %s, %s)""",
            (store_id, merchant_id, target_store_name, None),
        )
        cur.execute(
            """INSERT INTO merchant_users (user_id, merchant_id, role)
               VALUES (%s, %s, %s)""",
            (user_id, merchant_id, "owner"),
        )
    conn.commit()

    code = create_connect_code(store_id, merchant_id=merchant_id, conn=conn, expires_in_hours=code_ttl_hours)
    return {"merchant_id": merchant_id, "store_id": store_id, "connect_code": code.code}


def create_whatsapp_merchant(whatsapp_number: str, business_name: str, conn, *, code_ttl_hours: int = 24):
    merchant_context = create_merchant(whatsapp_number, business_name, conn)
    code = create_connect_code(
        merchant_context.store_id,
        merchant_id=merchant_context.merchant.merchant_id,
        conn=conn,
        expires_in_hours=code_ttl_hours,
    )
    return {
        "merchant_id": merchant_context.merchant.merchant_id,
        "store_id": merchant_context.store_id,
        "source_id": merchant_context.source_id,
        "connect_code": code.code,
    }


def link_whatsapp_source_to_store(store_id: str, whatsapp_number: str, conn) -> str:
    normalized = whatsapp_number.replace("whatsapp:", "")
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_id
            FROM data_sources
            WHERE source_type = 'whatsapp'
              AND external_identifier = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (normalized,),
        )
        existing = cur.fetchone()
        if existing is not None:
            if existing[0] is not None:
                cur.execute(
                    "SELECT store_id FROM data_sources WHERE source_id = %s",
                    (existing[0],),
                )
                linked_store = cur.fetchone()
                if linked_store is not None and linked_store[0] != store_id:
                    raise ValueError("WhatsApp number is already connected to another store")
                return existing[0]

        cur.execute(
            """
            SELECT source_id
            FROM data_sources
            WHERE store_id = %s AND source_type = 'whatsapp' AND external_identifier = %s
            """,
            (store_id, normalized),
        )
        existing_store = cur.fetchone()
        if existing_store is not None:
            return existing_store[0]

        source_id = generate_next_source_id(conn)
        cur.execute(
            """
            INSERT INTO data_sources (source_id, store_id, source_name, source_type, external_identifier)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (source_id, store_id, "WhatsApp", SourceType.WHATSAPP.value, normalized),
        )
    conn.commit()
    return source_id


def generate_connect_code(*args, conn=None, code_length: int = 8):
    if conn is None:
        if args and hasattr(args[0], "cursor"):
            conn = args[0]
            args = args[1:]
        else:
            raise ValueError("A database connection is required to generate a connect code")

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choice(alphabet) for _ in range(code_length))
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM connect_codes WHERE code = %s", (code,))
            if cur.fetchone() is None:
                return code


def create_connect_code(store_id: str | None = None, *, conn=None, merchant_id: str | None = None, expires_in_hours: int = 24, code_length: int = 8) -> ConnectCode:
    if conn is None:
        raise ValueError("A database connection is required to create a connect code")

    code = generate_connect_code(conn=conn, code_length=code_length)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

    with conn.cursor() as cur:
        if store_id is None:
            raise ValueError("A store_id is required to create a connect code")
        cur.execute(
            """INSERT INTO connect_codes (code, store_id, merchant_id, used, expires_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (code, store_id, merchant_id, False, expires_at),
        )
    conn.commit()

    return ConnectCode(code=code, store_id=store_id, merchant_id=merchant_id, used=False, expires_at=expires_at)


def redeem_connect_code(code: str, conn, *, expected_store_id: str | None = None, expected_merchant_id: str | None = None, user_id: str | None = None, whatsapp_number: str | None = None) -> ConnectCode:
    if conn is None:
        raise ValueError("A database connection is required to redeem a connect code")

    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """SELECT code, store_id, merchant_id, used, expires_at
               FROM connect_codes
               WHERE code = %s
               FOR UPDATE""",
            (code,),
        )
        row = cur.fetchone()

        if row is None:
            raise ValueError("Invalid or expired connect code")

        stored_code, store_id, merchant_id, used, expires_at = row
        if used or expires_at <= now:
            raise ValueError("Invalid or expired connect code")
        if expected_store_id is not None and store_id != expected_store_id:
            raise ValueError("Invalid or expired connect code")
        if expected_merchant_id is not None and merchant_id is not None and merchant_id != expected_merchant_id:
            raise ValueError("Invalid or expired connect code")

        if store_id is None:
            raise ValueError("Invalid or expired connect code")

        cur.execute("SELECT 1 FROM stores WHERE store_id = %s", (store_id,))
        if cur.fetchone() is None:
            raise ValueError("Invalid or expired connect code")

        if merchant_id is not None:
            cur.execute("SELECT 1 FROM merchants WHERE merchant_id = %s", (merchant_id,))
            if cur.fetchone() is None:
                raise ValueError("Invalid or expired connect code")

        if user_id is not None:
            cur.execute(
                """SELECT 1 FROM merchant_users WHERE user_id = %s AND merchant_id = %s""",
                (user_id, merchant_id),
            )
            if cur.fetchone() is None:
                cur.execute(
                    """INSERT INTO merchant_users (user_id, merchant_id, role)
                       VALUES (%s, %s, %s)""",
                    (user_id, merchant_id, "owner"),
                )

        if whatsapp_number is not None:
            link_whatsapp_source_to_store(store_id, whatsapp_number, conn)

        cur.execute(
            """UPDATE connect_codes
               SET used = TRUE
               WHERE code = %s AND used = FALSE""",
            (stored_code,),
        )
        if cur.rowcount != 1:
            raise ValueError("Invalid or expired connect code")

    conn.commit()
    return ConnectCode(code=stored_code, store_id=store_id, merchant_id=merchant_id, used=True, expires_at=expires_at)


def redeem_dashboard_connect_code(code: str, user_id: str, conn, *, expected_store_id: str | None = None) -> ConnectCode:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT merchant_id, store_id FROM connect_codes WHERE code = %s",
            (code,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Invalid or expired connect code")
        merchant_id, store_id = row
        if expected_store_id is not None and store_id != expected_store_id:
            raise ValueError("Invalid or expired connect code")
    return redeem_connect_code(code, conn, user_id=user_id, expected_store_id=expected_store_id, expected_merchant_id=merchant_id)


def redeem_whatsapp_connect_code(code: str, whatsapp_number: str, conn, *, expected_store_id: str | None = None) -> ConnectCode:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT merchant_id, store_id FROM connect_codes WHERE code = %s",
            (code,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Invalid or expired connect code")
        merchant_id, store_id = row
        if expected_store_id is not None and store_id != expected_store_id:
            raise ValueError("Invalid or expired connect code")
    return redeem_connect_code(code, conn, whatsapp_number=whatsapp_number, expected_store_id=expected_store_id, expected_merchant_id=merchant_id)
