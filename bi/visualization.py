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