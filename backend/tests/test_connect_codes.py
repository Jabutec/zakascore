import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest

from services.onboarding import (
    create_dashboard_merchant,
    issue_connect_code,
    redeem_connect_code_for_user,
)

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="set TEST_DATABASE_URL to run the database tests"
)


def _cleanup(conn):
    conn.rollback()
    conn.execute("DELETE FROM merchants WHERE business_name LIKE 'TEST ConnectCode %'")
    conn.commit()


@pytest.fixture
def conn():
    connection = psycopg.connect(TEST_DATABASE_URL)
    _cleanup(connection)
    yield connection
    _cleanup(connection)
    connection.close()


def _new_dashboard_store(conn, label):
    return create_dashboard_merchant(
        uuid4(), f"TEST ConnectCode {label}", conn, store_name=f"Store {label}"
    )


def test_dashboard_first_creates_owner_store_pwa_source_and_code(conn):
    user_id = uuid4()

    result = create_dashboard_merchant(
        user_id, "TEST ConnectCode Dashboard", conn
    )

    assert result["connect_code"]
    assert len(result["connect_code"]) == 8
    assert conn.execute(
        "SELECT role FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
        (user_id, result["merchant_id"]),
    ).fetchone() == ("owner",)
    assert conn.execute(
        """SELECT source_type FROM data_sources
           WHERE source_id = %s AND store_id = %s""",
        (result["source_id"], result["store_id"]),
    ).fetchone() == ("pwa",)
    assert conn.execute(
        "SELECT store_id, used_at FROM connect_codes WHERE code = %s",
        (result["connect_code"],),
    ).fetchone() == (result["store_id"], None)


def test_connect_code_joins_a_separate_user_as_employee(conn):
    owner = uuid4()
    result = create_dashboard_merchant(
        owner, "TEST ConnectCode Team", conn, store_name="Team Store"
    )
    user_id = uuid4()

    linked = redeem_connect_code_for_user(result["connect_code"], user_id, conn)

    assert linked == {
        "store_id": result["store_id"],
        "merchant_id": result["merchant_id"],
    }
    assert conn.execute(
        "SELECT role FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
        (user_id, result["merchant_id"]),
    ).fetchone() == ("employee",)
    assert conn.execute(
        "SELECT role FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
        (owner, result["merchant_id"]),
    ).fetchone() == ("owner",)


@pytest.mark.parametrize("code", ["NO-SUCH-CODE"])
def test_invalid_code_is_not_consumed_or_redeemed(conn, code):
    with pytest.raises(ValueError, match="Invalid or expired"):
        redeem_connect_code_for_user(code, uuid4(), conn)


def test_expired_code_is_not_consumed(conn):
    result = _new_dashboard_store(conn, "Expired")
    conn.execute(
        "UPDATE connect_codes SET expires_at = now() - interval '1 hour' WHERE code = %s",
        (result["connect_code"],),
    )
    conn.commit()

    with pytest.raises(ValueError, match="Invalid or expired"):
        redeem_connect_code_for_user(result["connect_code"], uuid4(), conn)

    assert conn.execute(
        "SELECT used_at FROM connect_codes WHERE code = %s",
        (result["connect_code"],),
    ).fetchone() == (None,)


def test_user_cannot_redeem_an_invite_to_their_existing_business(conn):
    owner = uuid4()
    result = create_dashboard_merchant(owner, "TEST ConnectCode Existing", conn)
    next_code = issue_connect_code(result["store_id"], conn)

    with pytest.raises(ValueError, match="Invalid or expired"):
        redeem_connect_code_for_user(next_code, owner, conn)

    assert conn.execute(
        "SELECT used_at FROM connect_codes WHERE code = %s",
        (next_code,),
    ).fetchone() == (None,)


def test_deleted_store_invalidates_its_connect_code(conn):
    result = _new_dashboard_store(conn, "DeletedStore")
    conn.execute("DELETE FROM stores WHERE store_id = %s", (result["store_id"],))
    conn.commit()

    with pytest.raises(ValueError, match="Invalid or expired"):
        redeem_connect_code_for_user(result["connect_code"], uuid4(), conn)


def test_concurrent_redemptions_have_at_most_one_success(conn):
    result = create_dashboard_merchant(
        uuid4(), "TEST ConnectCode Concurrent", conn
    )
    users = (uuid4(), uuid4())

    def redeem(user_id):
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            try:
                redeem_connect_code_for_user(
                    result["connect_code"], user_id, connection
                )
                return True
            except ValueError:
                return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        successes = list(executor.map(redeem, users))

    assert successes.count(True) == 1
    assert conn.execute(
        "SELECT count(*) FROM merchant_users WHERE merchant_id = %s",
        (result["merchant_id"],),
    ).fetchone() == (2,)
