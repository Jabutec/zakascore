def get_or_create_offering(store_id: str, offering_name: str, conn) -> str:
    cursor = conn.execute(
        "SELECT offering_id FROM offerings WHERE store_id = %s AND offering_name = %s",
        (store_id, offering_name)
    )
    row = cursor.fetchone()

    if row is not None:
        return row[0]

    cursor = conn.execute(
        """SELECT COALESCE(MAX(substring(offering_id FROM 2)::INTEGER), 0)
           FROM offerings WHERE offering_id ~ '^O[0-9]+$'"""
    )
    offering_id = f"O{cursor.fetchone()[0] + 1:03d}"

    conn.execute(
        "INSERT INTO offerings (offering_id, store_id, offering_name) VALUES (%s, %s, %s)",
        (offering_id, store_id, offering_name)
    )
    conn.commit()

    return offering_id