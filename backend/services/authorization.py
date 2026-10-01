from __future__ import annotations


def get_user_merchants(user_id: str, conn) -> list[dict]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT merchant_id, role, created_at
            FROM merchant_users
            WHERE user_id = %s
            ORDER BY created_at ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()

    return [
        {"merchant_id": row[0], "role": row[1], "created_at": row[2]}
        for row in rows
    ]


def require_merchant_access(user_id: str, merchant_id: str, conn) -> dict:
    merchants = get_user_merchants(user_id, conn)
    for merchant in merchants:
        if merchant["merchant_id"] == merchant_id:
            return merchant

    raise PermissionError("User does not have access to the requested merchant")


def require_store_access(user_id: str, store_id: str, conn) -> dict:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.store_id, s.store_name, s.merchant_id, mu.role
            FROM stores s
            JOIN merchant_users mu ON mu.merchant_id = s.merchant_id
            WHERE mu.user_id = %s AND s.store_id = %s
            """,
            (user_id, store_id),
        )
        row = cursor.fetchone()

    if row is None:
        raise PermissionError("User does not have access to the requested store")

    return {
        "store_id": row[0],
        "store_name": row[1],
        "merchant_id": row[2],
        "role": row[3],
    }


def get_user_role(user_id: str, merchant_id: str, conn) -> str | None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT role
            FROM merchant_users
            WHERE user_id = %s AND merchant_id = %s
            """,
            (user_id, merchant_id),
        )
        row = cursor.fetchone()

    return row[0] if row is not None else None
