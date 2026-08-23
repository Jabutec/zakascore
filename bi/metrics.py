from collections import defaultdict
import statistics

def calculate_total_revenue(transactions):
    return sum(transaction.amount_zar for transaction in transactions)

def calculate_transaction_count(transactions):
    return len(transactions)

def calculate_average_transaction(transactions):
    if not transactions:
        return 0.0
    
    return calculate_total_revenue(transactions) / calculate_transaction_count(transactions)

def calculate_revenue_by_date(transactions):
    revenue = defaultdict(float)
    
    for transaction in transactions:
        date = transaction.transaction_date.date()
        revenue[date] += transaction.amount_zar
        
    return dict(sorted(revenue.items()))

def calculate_revenue_growth(current_revenue, previous_revenue):
    if previous_revenue == 0:
        return None
    return ((current_revenue - previous_revenue) / previous_revenue) * 100

def calculate_revenue_volatility(transactions):
    daily_revenue = calculate_revenue_by_date(transactions)
    
    if len(daily_revenue) < 2:
        return 0.0
    
    return statistics.stdev(daily_revenue.values())

def calculate_recency(transactions, reference_date):
    if not transactions:
        return None

    latest_transaction = max(
        transaction.transaction_date
        for transaction in transactions
    )

    return (reference_date - latest_transaction).days