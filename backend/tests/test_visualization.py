from datetime import date
from decimal import Decimal

from bi.visualization import (
    prepare_payment_method_data,
    prepare_revenue_data,
    prepare_sales_data,
    prepare_top_offerings_data,
)


# ---------- prepare_revenue_data ----------

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


def test_prepare_revenue_data_sorts_oldest_first():
    result = prepare_revenue_data({"2026-08-03": 1, "2026-08-01": 2, "2026-08-02": 3})

    assert [row["date"] for row in result] == ["2026-08-01", "2026-08-02", "2026-08-03"]


def test_prepare_revenue_data_handles_decimal_dates_and_none():
    result = prepare_revenue_data(
        {
            date(2026, 8, 2): None,
            date(2026, 8, 1): Decimal("1234.567"),
        }
    )

    assert result == [
        {"date": "2026-08-01", "revenue": 1234.57},
        {"date": "2026-08-02", "revenue": 0.0},
    ]
    assert isinstance(result[0]["revenue"], float)


def test_prepare_revenue_data_empty():
    assert prepare_revenue_data({}) == []


# ---------- prepare_sales_data ----------

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


def test_prepare_sales_data_sorts_and_handles_date_objects():
    result = prepare_sales_data({date(2026, 8, 2): 4, date(2026, 8, 1): Decimal("3")})

    assert result == [
        {"date": "2026-08-01", "sales": 3},
        {"date": "2026-08-02", "sales": 4},
    ]


def test_prepare_sales_data_empty():
    assert prepare_sales_data({}) == []


# ---------- prepare_payment_method_data ----------

def test_prepare_payment_method_data():
    payment_method_data = {
        "Cash": 4200,
        "Digital": 8100,
    }

    result = prepare_payment_method_data(payment_method_data)

    # Largest first, with percentage of total
    assert result == [
        {"payment_method": "Digital", "amount": 8100, "pct": 65.85},
        {"payment_method": "Cash", "amount": 4200, "pct": 34.15},
    ]


def test_prepare_payment_method_data_labels_missing_method_unknown():
    # Legacy sales without a payment method map to "unknown" and merge
    result = prepare_payment_method_data({"Cash": 600, None: 300, "": 100})

    assert result == [
        {"payment_method": "Cash", "amount": 600, "pct": 60.0},
        {"payment_method": "unknown", "amount": 400, "pct": 40.0},
    ]


def test_prepare_payment_method_data_percentages_sum_to_total():
    result = prepare_payment_method_data(
        {"Cash": 1000, "Digital": 2000, None: 1000}
    )

    assert sum(row["amount"] for row in result) == 4000
    assert round(sum(row["pct"] for row in result), 2) == 100.0


def test_prepare_payment_method_data_zero_total_has_zero_pct():
    result = prepare_payment_method_data({"Cash": 0, "Digital": None})

    assert all(row["pct"] == 0.0 for row in result)


def test_prepare_payment_method_data_empty():
    assert prepare_payment_method_data({}) == []


# ---------- prepare_top_offerings_data ----------

class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeConn:
    """Records the query params and returns canned rows."""

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return FakeCursor(self.rows)


def test_prepare_top_offerings_data_shapes_rows():
    conn = FakeConn(
        [
            ("Shirt", Decimal("1500.505"), 12),
            ("Hat", Decimal("300"), 3),
        ]
    )

    result = prepare_top_offerings_data(7, conn)

    assert result == [
        {"offering": "Shirt", "revenue": 1500.51, "quantity": 12},
        {"offering": "Hat", "revenue": 300.0, "quantity": 3},
    ]


def test_prepare_top_offerings_data_default_limit_is_10():
    conn = FakeConn([])

    prepare_top_offerings_data(7, conn)

    assert conn.calls[0][1] == (7, 10)


def test_prepare_top_offerings_data_custom_limit():
    conn = FakeConn([])

    prepare_top_offerings_data(7, conn, limit=3)

    assert conn.calls[0][1] == (7, 3)


def test_prepare_top_offerings_data_limit_none_passes_null():
    conn = FakeConn([])

    prepare_top_offerings_data(7, conn, limit=None)

    assert conn.calls[0][1] == (7, None)


def test_prepare_top_offerings_data_empty():
    assert prepare_top_offerings_data(7, FakeConn([])) == []


def test_prepare_top_offerings_data_null_revenue_becomes_zero():
    result = prepare_top_offerings_data(7, FakeConn([("Shirt", None, 0)]))

    assert result == [{"offering": "Shirt", "revenue": 0.0, "quantity": 0}]