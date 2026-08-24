from bi.indicators import determine_revenue_trend


def test_revenue_trend_growing():
    assert determine_revenue_trend(20) == "growing"


def test_revenue_trend_declining():
    assert determine_revenue_trend(-20) == "declining"


def test_revenue_trend_stable():
    assert determine_revenue_trend(3) == "stable"


def test_revenue_trend_insufficient():
    assert determine_revenue_trend(None) == "insufficient_data"


def test_revenue_positive():
    assert determine_revenue_trend(5) == "stable"


def test_revenue_negative():
    assert determine_revenue_trend(-5) == "stable"