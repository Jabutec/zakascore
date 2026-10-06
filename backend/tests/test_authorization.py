"""Run against a real Postgres that already has the schema:

    TEST_DATABASE_URL=postgresql://... python -m pytest tests/test_authorization.py

Only creates and deletes merchants named "TEST ...".
"""
import os
from uuid import uuid4

import psycopg
import pytest

from services import authorization as authz

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


def make_merchant(conn, name, members):
    """Create a merchant with one store. members: {user_id: role}."""
    merchant_id = conn.execute(
        "INSERT INTO merchants (business_name) VALUES (%s) RETURNING merchant_id", (name,)
    ).fetchone()[0]
    store_id = conn.execute(
        "INSERT INTO stores (merchant_id, store_name) VALUES (%s, 'Main') RETURNING store_id",
        (merchant_id,),
    ).fetchone()[0]
    for user_id, role in members.items():
        conn.execute(
            "INSERT INTO merchant_users (user_id, merchant_id, role) VALUES (%s, %s, %s)",
            (user_id, merchant_id, role),
        )
    conn.commit()
    return merchant_id, store_id


# --- the regression: ids arrive as strings, the database returns UUIDs ---------
def test_owner_gets_access_when_ids_are_strings(conn):
    owner = uuid4()
    merchant_id, _ = make_merchant(conn, "TEST Shop", {owner: "owner"})

    access = authz.require_merchant_access(str(owner), str(merchant_id), conn)
    assert access["merchant_id"] == merchant_id and access["role"] == "owner"


def test_owner_gets_access_when_ids_are_uuids(conn):
    owner = uuid4()
    merchant_id, _ = make_merchant(conn, "TEST Shop", {owner: "owner"})
    assert authz.require_merchant_access(owner, merchant_id, conn)["role"] == "owner"


# --- denial: everything fails closed with the same error -----------------------
def test_other_users_and_unknown_merchants_are_denied(conn):
    owner, stranger = uuid4(), uuid4()
    merchant_id, store_id = make_merchant(conn, "TEST Shop", {owner: "owner"})

    with pytest.raises(PermissionError, match=authz.NO_MERCHANT_ACCESS):
        authz.require_merchant_access(str(stranger), str(merchant_id), conn)
    with pytest.raises(PermissionError, match=authz.NO_MERCHANT_ACCESS):
        authz.require_merchant_access(str(owner), str(uuid4()), conn)
    with pytest.raises(PermissionError, match=authz.NO_STORE_ACCESS):
        authz.require_store_access(str(stranger), str(store_id), conn)
    with pytest.raises(PermissionError, match=authz.NO_STORE_ACCESS):
        authz.require_store_access(str(owner), str(uuid4()), conn)


@pytest.mark.parametrize("bad", ["not-a-uuid", "", None, "123", "../etc/passwd", 42])
def test_malformed_ids_are_a_denial_not_a_database_error(conn, bad):
    owner = uuid4()
    merchant_id, store_id = make_merchant(conn, "TEST Shop", {owner: "owner"})

    with pytest.raises(PermissionError):
        authz.require_merchant_access(bad, str(merchant_id), conn)
    with pytest.raises(PermissionError):
        authz.require_merchant_access(str(owner), bad, conn)
    with pytest.raises(PermissionError):
        authz.require_store_access(bad, str(store_id), conn)
    with pytest.raises(PermissionError):
        authz.require_store_access(str(owner), bad, conn)
    assert authz.get_user_merchants(bad, conn) == []
    assert authz.get_user_role(bad, str(merchant_id), conn) is None
    assert authz.get_user_role(str(owner), bad, conn) is None


# --- stores ----------------------------------------------------------------
def test_store_access_returns_store_details(conn):
    owner = uuid4()
    merchant_id, store_id = make_merchant(conn, "TEST Shop", {owner: "admin"})

    store = authz.require_store_access(str(owner), str(store_id), conn)
    assert store == {
        "store_id": store_id,
        "store_name": "Main",
        "merchant_id": merchant_id,
        "role": "admin",
    }


# --- roles -----------------------------------------------------------------
def test_minimum_role_is_enforced(conn):
    owner, admin, employee, viewer = uuid4(), uuid4(), uuid4(), uuid4()
    merchant_id, store_id = make_merchant(
        conn, "TEST Shop",
        {owner: "owner", admin: "admin", employee: "employee", viewer: "viewer"},
    )
    m = str(merchant_id)

    # default is viewer: everyone with any role gets in
    for user in (owner, admin, employee, viewer):
        assert authz.require_merchant_access(str(user), m, conn)

    # admin-only action
    authz.require_merchant_access(str(owner), m, conn, min_role="admin")
    authz.require_merchant_access(str(admin), m, conn, min_role="admin")
    with pytest.raises(PermissionError, match=authz.ROLE_TOO_LOW):
        authz.require_merchant_access(str(employee), m, conn, min_role="admin")
    with pytest.raises(PermissionError, match=authz.ROLE_TOO_LOW):
        authz.require_merchant_access(str(viewer), m, conn, min_role="admin")

    # owner-only action, on a store
    authz.require_store_access(str(owner), str(store_id), conn, min_role="owner")
    with pytest.raises(PermissionError, match=authz.ROLE_TOO_LOW):
        authz.require_store_access(str(admin), str(store_id), conn, min_role="owner")


def test_unknown_min_role_is_a_programming_error_not_a_denial(conn):
    owner = uuid4()
    merchant_id, _ = make_merchant(conn, "TEST Shop", {owner: "owner"})
    with pytest.raises(ValueError):
        authz.require_merchant_access(str(owner), str(merchant_id), conn, min_role="superuser")


def test_get_user_role(conn):
    owner, stranger = uuid4(), uuid4()
    merchant_id, _ = make_merchant(conn, "TEST Shop", {owner: "owner"})
    assert authz.get_user_role(str(owner), str(merchant_id), conn) == "owner"
    assert authz.get_user_role(str(stranger), str(merchant_id), conn) is None


# --- listing ------------------------------------------------------------------
def test_get_user_merchants_lists_oldest_first(conn):
    user = uuid4()
    first, _ = make_merchant(conn, "TEST First", {user: "owner"})
    second, _ = make_merchant(conn, "TEST Second", {user: "admin"})
    make_merchant(conn, "TEST Someone Else", {uuid4(): "owner"})

    merchants = authz.get_user_merchants(str(user), conn)
    assert [m["merchant_id"] for m in merchants] == [first, second]
    assert [m["role"] for m in merchants] == ["owner", "admin"]


def test_unclaimed_merchants_have_no_users(conn):
    # a WhatsApp-first merchant nobody has claimed yet: nobody has access
    merchant_id, _ = make_merchant(conn, "TEST Unclaimed", {})
    with pytest.raises(PermissionError):
        authz.require_merchant_access(str(uuid4()), str(merchant_id), conn)