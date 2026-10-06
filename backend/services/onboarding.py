"""Dashboard merchant, store and PWA-source onboarding."""
from contextlib import contextmanager
from uuid import UUID

from services.authorization import require_merchant_access
from validation.models import Tier

MAX_BUSINESS_NAME_CHARS = 100


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


def create_dashboard_merchant(
    user_id, business_name: str, conn, *, store_name: str | None = None
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

    return {
        "merchant_id": merchant_id,
        "store_id": store_id,
        "source_id": source_id,
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
