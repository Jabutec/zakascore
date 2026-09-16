def get_or_create_offering(merchant_id: str, offering_name: str, conn) -> str:
    cursor = conn.execute(
        "SELECT offering_id FROM offerings WHERE merchant_id = ? AND offering_name = ?",
        (merchant_id, offering_name)
    )
    row = cursor.fetchone()

    if row is not None:
        return row[0]

    cursor = conn.execute(
        "SELECT offering_id FROM offerings ORDER BY offering_id DESC LIMIT 1"
    )
    last_row = cursor.fetchone()

    if last_row is None:
        offering_id = "O001"
    else:
        last_number = int(last_row[0][1:])
        offering_id = f"O{last_number + 1:03d}"

    conn.execute(
        "INSERT INTO offerings (offering_id, merchant_id, offering_name) VALUES (?, ?, ?)",
        (offering_id, merchant_id, offering_name)
    )
    conn.commit()

    return offering_id