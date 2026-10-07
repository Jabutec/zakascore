from bi.overview import get_business_overview


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.fetchone_calls = 0

    def fetchone(self):
        self.fetchone_calls += 1
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.execute_calls = []
        self.cursor = FakeCursor(row)

    def execute(self, query, params):
        self.execute_calls.append((query, params))
        return self.cursor


def test_business_overview_uses_one_aggregate_row():
    conn = FakeConnection(
        (
            15,
            1250.0,
            1250 / 15,
            700.0,
            350.0,
            True,
            15,
            1250 / 15,
            25.0,
            2,
            900.0,
            350.0,
        )
    )

    result = get_business_overview("merchant-id", conn)

    assert len(conn.execute_calls) == 1
    assert "GROUPING SETS" in conn.execute_calls[0][0]
    assert conn.cursor.fetchone_calls == 1
    assert result == {
        "total_revenue": 1250.0,
        "transaction_count": 15,
        "average_transaction": 83.33,
        "revenue_growth_pct": 100.0,
        "revenue_trend": "growing",
        "transaction_activity": "low",
        "revenue_stability": "low",
        "activity_status": "active",
        "digital_payment_adoption": "low",
        "payment_method_coverage_pct": 100.0,
        "insights": [
            "Revenue is growing.",
            "Daily revenue is highly volatile.",
            "The business is actively recording transactions.",
        ],
    }