"""Shape BI data for the dashboard charts.

Everything returned here is plain JSON-friendly data: money as float rounded to
2 decimals (Postgres NUMERIC arrives as Decimal), dates as ISO strings.
"""


def _money(value) -> float:
    return round(float(value or 0), 2)


def _iso(value) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def plot_revenue_by_date(revenue_data):
    """Local debugging helper only. Opens a desktop window, so never call it from the API."""
    import matplotlib.pyplot as plt  # imported here so the API doesn't load matplotlib

    dates = list(revenue_data.keys())
    revenue = [float(amount) for amount in revenue_data.values()]

    plt.plot(dates, revenue)

    plt.title("Revenue Over Time")
    plt.xlabel("Date")
    plt.ylabel("Revenue (ZAR)")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def prepare_revenue_data(revenue_data):
    """{date: amount} -> [{"date": "2026-10-01", "revenue": 1234.5}, ...] oldest first."""
    return [
        {"date": _iso(date), "revenue": _money(amount)}
        for date, amount in sorted(revenue_data.items())
    ]


def prepare_sales_data(sales_data):
    """{date: count} -> [{"date": "2026-10-01", "sales": 12}, ...] oldest first."""
    return [
        {"date": _iso(date), "sales": int(count)}
        for date, count in sorted(sales_data.items())
    ]


def prepare_payment_method_data(payment_method_data):
    """{method: amount} -> [{"payment_method", "amount", "pct"}, ...] largest first.

    A missing method (e.g. WhatsApp sales) is labelled "unknown" rather than dropped,
    so the chart adds up to total revenue.
    """
    totals = {}
    for method, amount in payment_method_data.items():
        label = method or "unknown"
        totals[label] = totals.get(label, 0.0) + float(amount or 0)

    grand_total = sum(totals.values())

    return [
        {
            "payment_method": method,
            "amount": round(amount, 2),
            "pct": round(amount / grand_total * 100, 2) if grand_total > 0 else 0.0,
        }
        for method, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def prepare_top_offerings_data(merchant_id, conn, limit: int | None = 10):
    """Top offerings by revenue across all of a merchant's stores.

    Names are grouped case-insensitively, so "Shirt" in one store and "shirt" in
    another count as one offering. Pass limit=None for every offering.
    """
    cursor = conn.execute(
        """SELECT MIN(o.offering_name)           AS offering_name,
                  SUM(t.amount_zar)              AS total_revenue,
                  COALESCE(SUM(t.quantity), 0)   AS total_quantity
           FROM transactions t
           JOIN offerings o ON o.offering_id = t.offering_id
           JOIN stores s    ON s.store_id = t.store_id
           WHERE s.merchant_id = %s AND t.is_voided = FALSE
           GROUP BY lower(o.offering_name)
           ORDER BY total_revenue DESC
           LIMIT %s""",
        (merchant_id, limit),  # LIMIT NULL means no limit in Postgres
    )
    return [
        {
            "offering": row[0],
            "revenue": _money(row[1]),
            "quantity": int(row[2]),
        }
        for row in cursor.fetchall()
    ]