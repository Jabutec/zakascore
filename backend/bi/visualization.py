import matplotlib.pyplot as plt


def plot_revenue_by_date(revenue_data):
    dates = list(revenue_data.keys())
    revenue = list(revenue_data.values())

    plt.plot(dates, revenue)

    plt.title("Revenue Over Time")
    plt.xlabel("Date")
    plt.ylabel("Revenue (ZAR)")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def prepare_revenue_data(revenue_data):
    return [
        {
            "date": date,
            "revenue": amount
        }
        for date, amount in revenue_data.items()
    ]

def prepare_sales_data(sales_data):
    return [
        {
            "date": date,
            "sales": count
        }
        for date, count in sales_data.items()
    ]

def prepare_payment_method_data(payment_method_data):
    return [
        {
            "payment_method": method,
            "amount": amount
        }
        for method, amount in payment_method_data.items()
    ]

def prepare_top_offerings_data(merchant_id, conn):
    cursor = conn.execute("""
        SELECT o.offering_name, SUM(t.amount_zar) as total_revenue, SUM(t.quantity) as total_quantity
        FROM transactions t
        JOIN offerings o ON t.offering_id = o.offering_id
        WHERE t.merchant_id = ? AND t.is_voided = 0
        GROUP BY o.offering_name
        ORDER BY total_revenue DESC
    """, (merchant_id,))
    return [
        {"offering": row[0], "revenue": row[1], "quantity": row[2]}
        for row in cursor.fetchall()
    ]
    