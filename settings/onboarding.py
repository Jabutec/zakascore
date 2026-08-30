from validation.models import Merchant, Tier


def get_merchant_by_number(whatsapp_number: str, conn) -> Merchant | None:
    cursor = conn.execute(
        """SELECT merchant_id, business_name, whatsapp_number, location, tier, created_at
           FROM merchants WHERE whatsapp_number = ?""",
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
        created_at=row[5]
    )

def generate_next_merchant_id(conn) -> str:
    cursor = conn.execute(
        "SELECT merchant_id FROM merchants ORDER BY merchant_id DESC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        return "M001"

    last_number = int(row[0][1:])
    return f"M{last_number + 1:03d}"

def create_merchant(whatsapp_number: str, business_name: str, conn):
    merchant_id = generate_next_merchant_id(conn)

    merchant = Merchant(
        merchant_id=merchant_id,
        business_name=business_name,
        whatsapp_number=whatsapp_number,
        location="",
        tier=Tier.FREE
    )

    conn.execute(
        """INSERT INTO merchants (merchant_id, business_name, whatsapp_number, location, tier)
           VALUES (?, ?, ?, ?, ?)""",
        (merchant.merchant_id, merchant.business_name, merchant.whatsapp_number,
         merchant.location, merchant.tier.value)
    )
    conn.commit()

    return merchant