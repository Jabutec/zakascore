import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest

from services.onboarding import (
    create_dashboard_merchant,
    create_whatsapp_merchant,
    issue_connect_code,
    redeem_connect_code_for_user,
    redeem_connect_code_for_whatsapp,
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


def test_whatsapp_first_onboarding_creates_source_then_user_can_claim_owner(conn):
    result = create_whatsapp_merchant(
        "whatsapp:+27820000001", "TEST ConnectCode WhatsApp", conn
    )
    user_id = uuid4()

    claimed = redeem_connect_code_for_user(result["connect_code"], user_id, conn)

    assert claimed == {
        "store_id": result["store_id"],
        "merchant_id": result["merchant_id"],
    }
    assert conn.execute(
        "SELECT role FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
        (user_id, result["merchant_id"]),
    ).fetchone() == ("owner",)
    assert conn.execute(
        """SELECT external_identifier FROM data_sources
           WHERE source_id = %s AND store_id = %s AND source_type = 'whatsapp'""",
        (result["source_id"], result["store_id"]),
    ).fetchone() == ("+27820000001",)


def test_dashboard_connect_code_links_whatsapp_idempotently(conn):
    result = _new_dashboard_store(conn, "WhatsApp")

    linked = redeem_connect_code_for_whatsapp(
        result["connect_code"], "whatsapp:+27820000002", conn
    )
    next_code = issue_connect_code(result["store_id"], conn)
    repeated = redeem_connect_code_for_whatsapp(
        next_code, "+27820000002", conn
    )

    assert linked["source_id"] == repeated["source_id"]
    assert conn.execute(
        """SELECT count(*) FROM data_sources
           WHERE store_id = %s AND source_type = 'whatsapp'
             AND external_identifier = %s""",
        (result["store_id"], "+27820000002"),
    ).fetchone() == (1,)


def test_whatsapp_number_cannot_be_moved_between_stores_and_code_rolls_back(conn):
    first = _new_dashboard_store(conn, "First")
    second = _new_dashboard_store(conn, "Second")
    redeem_connect_code_for_whatsapp(
        first["connect_code"], "+27820000003", conn
    )

    with pytest.raises(ValueError, match="already connected"):
        redeem_connect_code_for_whatsapp(
            second["connect_code"], "+27820000003", conn
        )

    assert conn.execute(
        "SELECT used_at FROM connect_codes WHERE code = %s",
        (second["connect_code"],),
    ).fetchone() == (None,)
    assert conn.execute(
        """SELECT store_id FROM data_sources
           WHERE source_type = 'whatsapp' AND external_identifier = %s""",
        ("+27820000003",),
    ).fetchone() == (first["store_id"],)


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


def test_code_cannot_assign_a_second_owner_to_dashboard_business(conn):
    result = _new_dashboard_store(conn, "Owner")

    with pytest.raises(ValueError, match="Invalid or expired"):
        redeem_connect_code_for_user(result["connect_code"], uuid4(), conn)

    assert conn.execute(
        "SELECT used_at FROM connect_codes WHERE code = %s",
        (result["connect_code"],),
    ).fetchone() == (None,)
    assert conn.execute(
        "SELECT count(*) FROM merchant_users WHERE merchant_id = %s AND role = 'owner'",
        (result["merchant_id"],),
    ).fetchone() == (1,)


def test_deleted_store_invalidates_its_connect_code(conn):
    result = _new_dashboard_store(conn, "DeletedStore")
    conn.execute("DELETE FROM stores WHERE store_id = %s", (result["store_id"],))
    conn.commit()

    with pytest.raises(ValueError, match="Invalid or expired"):
        redeem_connect_code_for_user(result["connect_code"], uuid4(), conn)


def test_concurrent_redemptions_have_at_most_one_success(conn):
    result = create_whatsapp_merchant(
        "+27820000004", "TEST ConnectCode Concurrent", conn
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
    ).fetchone() == (1,)
