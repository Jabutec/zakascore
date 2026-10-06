"""Who may access which merchant or store.

Authentication (services/auth.py) says WHO the user is. This module says WHAT they may
touch. Every check fails closed: an unknown user, an unknown merchant, a malformed id and
"someone else's merchant" all produce the same PermissionError, so a caller can't probe
which ids exist. Route code should turn PermissionError into a 403 (or a 404).

This covers merchant-side users only. Lenders aren't merchant users; their access to a
merchant's assessment will be checked against that merchant's consent.
"""
from __future__ import annotations

from uuid import UUID

# Higher rank can do everything a lower rank can. Placeholder semantics:
#   viewer   read-only
#   employee read + log sales
#   admin    manage the business and its connections
#   owner    everything, including who else has access
ROLE_RANK = {"viewer": 1, "employee": 2, "admin": 3, "owner": 4}

NO_MERCHANT_ACCESS = "User does not have access to the requested merchant"
NO_STORE_ACCESS = "User does not have access to the requested store"
ROLE_TOO_LOW = "Your role does not allow this action"


def _as_uuid(value) -> UUID | None:
    """Ids arrive as strings (JWT sub, URL parameters) but are UUIDs in the database.
    Anything that isn't a valid UUID becomes None, which means 'no access'."""
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _check_role(role: str, min_role: str) -> None:
    if min_role not in ROLE_RANK:
        raise ValueError(f"Unknown role: {min_role}")  # a programming error, not a denial
    if ROLE_RANK.get(role, 0) < ROLE_RANK[min_role]:
        raise PermissionError(ROLE_TOO_LOW)


def get_user_merchants(user_id: str, conn) -> list[dict]:
    user = _as_uuid(user_id)
    if user is None:
        return []

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT merchant_id, role, created_at
            FROM merchant_users
            WHERE user_id = %s
            ORDER BY created_at ASC
            """,
            (user,),
        )
        rows = cursor.fetchall()

    return [
        {"merchant_id": row[0], "role": row[1], "created_at": row[2]}
        for row in rows
    ]


def require_merchant_access(user_id: str, merchant_id: str, conn, *, min_role: str = "viewer") -> dict:
    user, merchant = _as_uuid(user_id), _as_uuid(merchant_id)
    if user is None or merchant is None:
        raise PermissionError(NO_MERCHANT_ACCESS)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT merchant_id, role, created_at
            FROM merchant_users
            WHERE user_id = %s AND merchant_id = %s
            """,
            (user, merchant),
        )
        row = cursor.fetchone()

    if row is None:
        raise PermissionError(NO_MERCHANT_ACCESS)

    _check_role(row[1], min_role)
    return {"merchant_id": row[0], "role": row[1], "created_at": row[2]}


def require_store_access(user_id: str, store_id: str, conn, *, min_role: str = "viewer") -> dict:
    user, store = _as_uuid(user_id), _as_uuid(store_id)
    if user is None or store is None:
        raise PermissionError(NO_STORE_ACCESS)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.store_id, s.store_name, s.merchant_id, mu.role
            FROM stores s
            JOIN merchant_users mu ON mu.merchant_id = s.merchant_id
            WHERE mu.user_id = %s AND s.store_id = %s
            """,
            (user, store),
        )
        row = cursor.fetchone()

    if row is None:
        raise PermissionError(NO_STORE_ACCESS)

    _check_role(row[3], min_role)
    return {
        "store_id": row[0],
        "store_name": row[1],
        "merchant_id": row[2],
        "role": row[3],
    }


def get_user_role(user_id: str, merchant_id: str, conn) -> str | None:
    user, merchant = _as_uuid(user_id), _as_uuid(merchant_id)
    if user is None or merchant is None:
        return None

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT role
            FROM merchant_users
            WHERE user_id = %s AND merchant_id = %s
            """,
            (user, merchant),
        )
        row = cursor.fetchone()

    return row[0] if row is not None else None