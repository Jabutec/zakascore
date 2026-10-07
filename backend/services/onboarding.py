"""Dashboard merchant, store and PWA-source onboarding."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID

from services.authorization import require_merchant_access
from validation.models import Tier

MAX_BUSINESS_NAME_CHARS = 100
CONNECT_CODE_TTL_HOURS = 24
CONNECT_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@contextmanager
def _atomic(conn):
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _as_uuid(value) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _clean_business_name(name: str) -> str:
    cleaned = " ".join((name or "").split())
    if not cleaned or len(cleaned) > MAX_BUSINESS_NAME_CHARS:
        raise ValueError(f"Business name must be 1 to {MAX_BUSINESS_NAME_CHARS} characters")
    return cleaned


def _insert_pwa_source(cur, store_id) -> UUID:
    cur.execute(
        """INSERT INTO data_sources (store_id, source_name, source_type)
           VALUES (%s, 'PWA', 'pwa') RETURNING source_id""",
        (store_id,),
    )
    return cur.fetchone()[0]


def _create_connect_code(cur, store_id, *, expires_in_hours: int = CONNECT_CODE_TTL_HOURS) -> str:
    if expires_in_hours < 1 or expires_in_hours > 168:
        raise ValueError("Connect-code expiry must be between 1 and 168 hours")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    while True:
        code = "".join(secrets.choice(CONNECT_CODE_ALPHABET) for _ in range(8))
        cur.execute(
            """INSERT INTO connect_codes (code, store_id, expires_at)
               VALUES (%s, %s, %s)
               ON CONFLICT (code) DO NOTHING
               RETURNING code""",
            (code, store_id, expires_at),
        )
        row = cur.fetchone()
        if row is not None:
            return row[0]


def issue_connect_code(
    store_id, conn, *, expires_in_hours: int = CONNECT_CODE_TTL_HOURS
) -> str:
    store = _as_uuid(store_id)
    with _atomic(conn), conn.cursor() as cur:
        cur.execute(
            """SELECT store_id FROM stores
               WHERE store_id = %s
               FOR UPDATE""",
            (store,),
        )
        if cur.fetchone() is None:
            raise ValueError("Store does not exist")
        return _create_connect_code(
            cur, store, expires_in_hours=expires_in_hours
        )


def create_dashboard_merchant(
    user_id,
    business_name: str,
    conn,
    *,
    store_name: str | None = None,
    code_ttl_hours: int = CONNECT_CODE_TTL_HOURS,
) -> dict:
    user = _as_uuid(user_id)
    name = _clean_business_name(business_name)
    store = _clean_business_name(store_name) if store_name else name

    with _atomic(conn), conn.cursor() as cur:
        cur.execute(
            """INSERT INTO merchants (business_name, tier)
               VALUES (%s, %s) RETURNING merchant_id""",
            (name, Tier.INSIGHTS.value),
        )
        merchant_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO merchant_users (user_id, merchant_id, role) VALUES (%s, %s, 'owner')",
            (user, merchant_id),
        )

        cur.execute(
            """INSERT INTO stores (merchant_id, store_name)
               VALUES (%s, %s) RETURNING store_id""",
            (merchant_id, store),
        )
        store_id = cur.fetchone()[0]
        source_id = _insert_pwa_source(cur, store_id)
        connect_code = _create_connect_code(
            cur, store_id, expires_in_hours=code_ttl_hours
        )

    return {
        "merchant_id": merchant_id,
        "store_id": store_id,
        "source_id": source_id,
        "connect_code": connect_code,
    }


def _lock_valid_connect_code(cur, code: str):
    cur.execute(
        """SELECT cc.store_id, s.merchant_id
           FROM connect_codes cc
           JOIN stores s ON s.store_id = cc.store_id
           JOIN merchants m ON m.merchant_id = s.merchant_id
           WHERE cc.code = %s
             AND cc.used_at IS NULL
             AND cc.expires_at > now()
           FOR UPDATE OF cc""",
        (code.strip().upper(),),
    )
    row = cur.fetchone()
    if row is None:
        raise ValueError("Invalid or expired connect code")
    return row


def redeem_connect_code_for_user(code: str, user_id, conn) -> dict:
    user = _as_uuid(user_id)
    with _atomic(conn), conn.cursor() as cur:
        store_id, merchant_id = _lock_valid_connect_code(cur, code)
        cur.execute(
            """INSERT INTO merchant_users (user_id, merchant_id, role)
               VALUES (%s, %s, 'owner')
               ON CONFLICT (user_id, merchant_id) DO NOTHING""",
            (user, merchant_id),
        )
        cur.execute(
            "UPDATE connect_codes SET used_at = now() WHERE code = %s",
            (code.strip().upper(),),
        )
    return {"store_id": store_id, "merchant_id": merchant_id}


def _normalize_whatsapp_number(whatsapp_number: str) -> str:
    normalized = (whatsapp_number or "").strip()
    if normalized.lower().startswith("whatsapp:"):
        normalized = normalized[len("whatsapp:"):].strip()
    if not normalized or len(normalized) > 64:
        raise ValueError("Invalid WhatsApp number")
    return normalized


def redeem_connect_code_for_whatsapp(code: str, whatsapp_number: str, conn) -> dict:
    number = _normalize_whatsapp_number(whatsapp_number)
    with _atomic(conn), conn.cursor() as cur:
        store_id, merchant_id = _lock_valid_connect_code(cur, code)
        cur.execute(
            """SELECT source_id, store_id
               FROM data_sources
               WHERE source_type = 'whatsapp' AND external_identifier = %s""",
            (number,),
        )
        existing = cur.fetchone()
        if existing is not None and existing[1] != store_id:
            raise ValueError("WhatsApp number is already connected")
        if existing is None:
            cur.execute(
                """INSERT INTO data_sources
                       (store_id, source_name, source_type, external_identifier)
                   VALUES (%s, 'WhatsApp', 'whatsapp', %s)
                   RETURNING source_id""",
                (store_id, number),
            )
            source_id = cur.fetchone()[0]
        else:
            source_id = existing[0]
        cur.execute(
            "UPDATE connect_codes SET used_at = now() WHERE code = %s",
            (code.strip().upper(),),
        )
    return {
        "store_id": store_id,
        "merchant_id": merchant_id,
        "source_id": source_id,
    }


def create_whatsapp_merchant(
    whatsapp_number: str,
    business_name: str,
    conn,
    *,
    store_name: str | None = None,
    code_ttl_hours: int = CONNECT_CODE_TTL_HOURS,
) -> dict:
    number = _normalize_whatsapp_number(whatsapp_number)
    name = _clean_business_name(business_name)
    store = _clean_business_name(store_name) if store_name else name
    with _atomic(conn), conn.cursor() as cur:
        cur.execute(
            """INSERT INTO merchants (business_name, tier)
               VALUES (%s, %s) RETURNING merchant_id""",
            (name, Tier.INSIGHTS.value),
        )
        merchant_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO stores (merchant_id, store_name)
               VALUES (%s, %s) RETURNING store_id""",
            (merchant_id, store),
        )
        store_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO data_sources
                   (store_id, source_name, source_type, external_identifier)
               VALUES (%s, 'WhatsApp', 'whatsapp', %s)
               RETURNING source_id""",
            (store_id, number),
        )
        source_id = cur.fetchone()[0]
        connect_code = _create_connect_code(
            cur, store_id, expires_in_hours=code_ttl_hours
        )
    return {
        "merchant_id": merchant_id,
        "store_id": store_id,
        "source_id": source_id,
        "connect_code": connect_code,
    }


def add_store(user_id, merchant_id, store_name: str, conn) -> dict:
    user = _as_uuid(user_id)
    merchant = _as_uuid(merchant_id)
    name = _clean_business_name(store_name)
    require_merchant_access(user, merchant, conn, min_role="admin")

    with _atomic(conn), conn.cursor() as cur:
        cur.execute(
            """INSERT INTO stores (merchant_id, store_name)
               VALUES (%s, %s) RETURNING store_id""",
            (merchant, name),
        )
        store_id = cur.fetchone()[0]
        source_id = _insert_pwa_source(cur, store_id)

    return {"store_id": store_id, "source_id": source_id}


def get_pwa_source_id(store_id, conn) -> UUID:
    store = _as_uuid(store_id)
    row = conn.execute(
        """SELECT source_id FROM data_sources
           WHERE store_id = %s AND source_type = 'pwa' AND is_active""",
        (store,),
    ).fetchone()
    if row is None:
        raise LookupError(f"No active PWA source is configured for store {store}")
    return row[0]
