def determine_revenue_trend(revenue_growth):
    if revenue_growth is None:
        return "insufficient_data"
    
    if revenue_growth > 5:
        return "growing"
    
    if revenue_growth < -5:
        return "declining"
    
    return "stable"

def calculate_transaction_activity(transaction_count, active_days):
    if active_days <= 0:
        return "insufficient_data"
    
    transaction_per_day = transaction_count/ active_days
    
    if transaction_per_day > 10:
        return "high"
    
    if transaction_per_day >= 5:
        return "moderate"
    
    return "low"

def determine_revenue_stability(revenue_volatility):
    if revenue_volatility is None:
        return "insufficient_data"
    
    if revenue_volatility > 0.10:
        return "high"
    
    if revenue_volatility >= 0.25:
        return "moderate"
    
    return "low"

def determine_activity_status(days_since_transaction):
    if days_since_transaction is None:
        return "insufficient_data"

    if days_since_transaction <= 7:
        return "active"

    if days_since_transaction <= 30:
        return "at_risk"

    return "inactive"

def determine_digital_payment_adoption(cash_revenue, digital_revenue):
    total_revenue = cash_revenue + digital_revenue

    if total_revenue <= 0:
        return "insufficient_data"

    digital_percentage = (digital_revenue / total_revenue) * 100

    if digital_percentage >= 70:
        return "high"

    if digital_percentage >= 30:
        return "moderate"

    return "low"