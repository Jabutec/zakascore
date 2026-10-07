from uuid import uuid4

import pytest

from services.onboarding import create_dashboard_merchant


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params):
        self.conn.statements.append((query, params))
        if "INSERT INTO merchants" in query:
            self.result = (self.conn.merchant_id,)
        elif "INSERT INTO stores" in query:
            self.result = (self.conn.store_id,)
        elif "INSERT INTO data_sources" in query:
            if self.conn.fail_source_insert:
                raise RuntimeError("simulated PWA source insert failure")
            self.result = (self.conn.source_id,)
        elif "INSERT INTO connect_codes" in query:
            self.result = (self.conn.connect_code,)
        else:
            self.result = None

    def fetchone(self):
        return self.result


class FakeConnection:
    def __init__(self, fail_source_insert=False):
        self.merchant_id = uuid4()
        self.store_id = uuid4()
        self.source_id = uuid4()
        self.connect_code = "TESTCODE"
        self.fail_source_insert = fail_source_insert
        self.statements = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_create_dashboard_merchant_creates_owner_store_and_pwa_source_atomically():
    conn = FakeConnection()
    user_id = uuid4()

    result = create_dashboard_merchant(user_id, " Demo Merchant ", conn)

    assert result == {
        "merchant_id": conn.merchant_id,
        "store_id": conn.store_id,
        "source_id": conn.source_id,
        "connect_code": conn.connect_code,
    }
    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert len(conn.statements) == 5
    assert conn.statements[0][1] == ("Demo Merchant", "insights")
    assert conn.statements[1][1] == (user_id, conn.merchant_id)
    assert "'owner'" in conn.statements[1][0]
    assert conn.statements[3][1] == (conn.store_id,)
    assert "'PWA', 'pwa'" in conn.statements[3][0]
    assert len(conn.statements[4][1][0]) == 8
    assert conn.statements[4][1][1] == conn.store_id


def test_create_dashboard_merchant_rolls_back_after_a_later_insert_fails():
    conn = FakeConnection(fail_source_insert=True)

    with pytest.raises(RuntimeError, match="simulated PWA source insert failure"):
        create_dashboard_merchant(uuid4(), "Demo Merchant", conn)

    assert conn.commits == 0
    assert conn.rollbacks == 1
