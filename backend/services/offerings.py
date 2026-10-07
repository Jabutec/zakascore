"""Offerings (the things a store sells), one row per store and case-insensitive name.

The database enforces this with the unique index
    uniq_offering_per_store ON offerings (store_id, lower(offering_name))
so "Shirt", "shirt" and " SHIRT " are the same offering.
"""
from uuid import UUID

MAX_OFFERING_NAME_CHARS = 60  # same limit the parser applies


def _as_uuid(value) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _clean_name(name: str) -> str:
    cleaned = " ".join((name or "").split())
    if not cleaned or len(cleaned) > MAX_OFFERING_NAME_CHARS:
        raise ValueError(f"Offering name must be 1 to {MAX_OFFERING_NAME_CHARS} characters")
    return cleaned


def _find_offering(store_id: UUID, name: str, conn) -> UUID | None:
    row = conn.execute(
        "SELECT offering_id FROM offerings WHERE store_id = %s AND lower(offering_name) = lower(%s)",
        (store_id, name),
    ).fetchone()
    return row[0] if row is not None else None


def get_or_create_offering(store_id, offering_name: str, conn) -> UUID:
    """Return the offering's id, creating it the first time it is seen.

    Safe when two messages create the same offering at the same moment: the loser of the
    race gets the winner's row instead of an error. The first spelling seen is kept as the
    display name.

    This does NOT commit. The caller owns the transaction, so the offering and the
    transaction that uses it are saved together or not at all.
    """
    store = _as_uuid(store_id)
    name = _clean_name(offering_name)

    # Fast path: almost every sale is for an offering that already exists.
    existing = _find_offering(store, name, conn)
    if existing is not None:
        return existing

    row = conn.execute(
        """INSERT INTO offerings (store_id, offering_name)
           VALUES (%s, %s)
           ON CONFLICT (store_id, lower(offering_name)) DO NOTHING
           RETURNING offering_id""",
        (store, name),
    ).fetchone()
    if row is not None:
        return row[0]

    # Someone else created it between our SELECT and INSERT.
    return _find_offering(store, name, conn)