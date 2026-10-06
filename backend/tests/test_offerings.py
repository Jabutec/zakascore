"""Run against a real Postgres that already has the schema:

    TEST_DATABASE_URL=postgresql://... python -m pytest tests/test_offerings.py

Only creates and deletes merchants named "TEST ...".
"""
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import psycopg
import pytest

from services.offerings import get_or_create_offering

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="set TEST_DATABASE_URL to run the database tests"
)


def cleanup(conn):
    conn.rollback()
    conn.execute("DELETE FROM merchants WHERE business_name LIKE 'TEST %'")
    conn.commit()


@pytest.fixture
def conn():
    connection = psycopg.connect(TEST_DATABASE_URL)
    cleanup(connection)
    yield connection
    cleanup(connection)
    connection.close()


def make_store(conn, merchant_name="TEST Shop"):
    merchant_id = conn.execute(
        "INSERT INTO merchants (business_name) VALUES (%s) RETURNING merchant_id", (merchant_name,)
    ).fetchone()[0]
    store_id = conn.execute(
        "INSERT INTO stores (merchant_id, store_name) VALUES (%s, 'Main') RETURNING store_id",
        (merchant_id,),
    ).fetchone()[0]
    conn.commit()
    return store_id


def offering_rows(conn, store_id):
    return conn.execute(
        "SELECT offering_name FROM offerings WHERE store_id = %s", (store_id,)
    ).fetchall()


def test_creates_and_returns_a_uuid(conn):
    store_id = make_store(conn)
    offering_id = get_or_create_offering(store_id, "shirt", conn)
    conn.commit()
    assert isinstance(offering_id, UUID)
    assert offering_rows(conn, store_id) == [("shirt",)]


def test_same_name_returns_the_same_offering(conn):
    store_id = make_store(conn)
    first = get_or_create_offering(store_id, "shirt", conn)
    second = get_or_create_offering(store_id, "shirt", conn)
    conn.commit()
    assert first == second
    assert len(offering_rows(conn, store_id)) == 1


def test_case_and_spacing_do_not_create_duplicates(conn):
    store_id = make_store(conn)
    first = get_or_create_offering(store_id, "Hair  Extension", conn)
    others = [
        get_or_create_offering(store_id, name, conn)
        for name in ["hair extension", "  HAIR EXTENSION ", "Hair\tExtension"]
    ]
    conn.commit()
    assert all(other == first for other in others)
    assert offering_rows(conn, store_id) == [("Hair Extension",)]  # first spelling is kept


def test_different_stores_have_separate_offerings(conn):
    store_a = make_store(conn, "TEST Shop A")
    store_b = make_store(conn, "TEST Shop B")
    a = get_or_create_offering(store_a, "shirt", conn)
    b = get_or_create_offering(store_b, "shirt", conn)
    conn.commit()
    assert a != b


def test_accepts_string_store_ids(conn):
    store_id = make_store(conn)
    assert get_or_create_offering(str(store_id), "dress", conn) == get_or_create_offering(
        store_id, "dress", conn
    )


@pytest.mark.parametrize("bad", ["", "   ", None, "x" * 61])
def test_invalid_names_are_rejected(conn, bad):
    store_id = make_store(conn)
    with pytest.raises(ValueError):
        get_or_create_offering(store_id, bad, conn)


def test_it_does_not_commit_so_the_caller_controls_atomicity(conn):
    store_id = make_store(conn)
    get_or_create_offering(store_id, "airtime", conn)
    conn.rollback()  # e.g. the transaction insert that followed it failed
    assert offering_rows(conn, store_id) == []


def test_simultaneous_first_sales_of_a_new_offering_share_one_row(conn):
    store_id = make_store(conn)

    def log_sale(_):
        own = psycopg.connect(TEST_DATABASE_URL)
        try:
            offering_id = get_or_create_offering(store_id, "Cooldrink", own)
            own.commit()
            return offering_id
        finally:
            own.close()

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(log_sale, range(4)))

    assert len(set(ids)) == 1
    assert len(offering_rows(conn, store_id)) == 1