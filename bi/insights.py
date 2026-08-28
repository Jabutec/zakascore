def generate_revenue_insight(revenue_trend):
    if revenue_trend == "growing":
        return "Revenue is growing."

    if revenue_trend == "declining":
        return "Revenue is declining."

    if revenue_trend == "stable":
        return "Revenue is relatively stable."

    return "Revenue insight is unavailable."


def generate_stability_insight(revenue_stability):
    if revenue_stability == "high":
        return "Revenue is highly volatile."

    if revenue_stability == "moderate":
        return "Revenue shows moderate volatility."

    if revenue_stability == "low":
        return "Revenue is relatively stable."

    return "Revenue stability insight is unavailable."


def generate_activity_insight(activity_status):
    if activity_status == "active":
        return "The business is actively recording transactions."

    if activity_status == "at_risk":
        return "Transaction activity is slowing and may require attention."

    if activity_status == "inactive":
        return "The business has not recorded transactions recently."

    return "Transaction activity insight is unavailable."


def generate_business_insights(
    revenue_trend,
    revenue_stability,
    activity_status
):
    return [
        generate_revenue_insight(revenue_trend),
        generate_stability_insight(revenue_stability),
        generate_activity_insight(activity_status),
    ]