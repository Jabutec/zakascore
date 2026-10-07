from collections import defaultdict
import statistics

MIN_DAYS_FOR_VOLATILITY = 7


def calculate_total_revenue(transactions):
    return sum(transaction.amount_zar for transaction in transactions)


def calculate_transaction_count(transactions):
    return len(transactions)


def calculate_average_transaction(transactions):
    if not transactions:
        return 0.0

    return float(calculate_total_revenue(transactions)) / calculate_transaction_count(transactions)


def calculate_revenue_by_date(transactions):
    revenue = defaultdict(float)

    for transaction in transactions:
        transaction_date = transaction.transaction_date.date()
        revenue[transaction_date] += float(transaction.amount_zar)

    return dict(sorted(revenue.items()))


def calculate_revenue_growth(current_revenue, previous_revenue):
    if previous_revenue == 0:
        return None
    return ((current_revenue - previous_revenue) / previous_revenue) * 100


def calculate_revenue_volatility(transactions):
    """Return daily revenue standard deviation when there are enough active days."""
    daily_revenue = calculate_revenue_by_date(transactions)

    if len(daily_revenue) < MIN_DAYS_FOR_VOLATILITY:
        return None

    return statistics.stdev(daily_revenue.values())


def calculate_recency(transactions, reference_date):
    if not transactions:
        return None

    latest_transaction = max(
        transaction.transaction_date
        for transaction in transactions
    )

    return (reference_date - latest_transaction).days