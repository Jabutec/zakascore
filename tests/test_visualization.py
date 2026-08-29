from bi.visualization import prepare_revenue_data, prepare_sales_data, prepare_payment_method_data


def test_prepare_revenue_data():
    revenue_data = {
        "2026-08-01": 150,
        "2026-08-02": 300,
        "2026-08-03": 220,
    }

    result = prepare_revenue_data(revenue_data)

    assert result == [
        {"date": "2026-08-01", "revenue": 150},
        {"date": "2026-08-02", "revenue": 300},
        {"date": "2026-08-03", "revenue": 220},
    ]
    
def test_prepare_sales_data():
    sales_data = {
        "2026-08-01": 5,
        "2026-08-02": 12,
        "2026-08-03": 8,
    }

    result = prepare_sales_data(sales_data)

    assert result == [
        {"date": "2026-08-01", "sales": 5},
        {"date": "2026-08-02", "sales": 12},
        {"date": "2026-08-03", "sales": 8},
    ]
    
def test_prepare_payment_method_data():
    payment_method_data = {
        "Cash": 4200,
        "Digital": 8100,
    }

    result = prepare_payment_method_data(payment_method_data)

    assert result == [
        {"payment_method": "Cash", "amount": 4200},
        {"payment_method": "Digital", "amount": 8100},
       
    ]
    
