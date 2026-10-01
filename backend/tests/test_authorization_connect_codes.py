import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from scripts.init_db import init_database
from services.authorization import get_user_merchants, require_merchant_access, require_store_access, get_user_role
from services.onboarding import create_connect_code, create_dashboard_merchant, redeem_connect_code, link_whatsapp_source_to_store


@pytest.fixture
def auth_database(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL must point to a PostgreSQL test database")

    schema_name = f"test_{uuid4().hex}"
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            sql.SQL("CREATE SCHEMA {}" ).format(sql.Identifier(schema_name))
        )

    def connect():
        return psycopg.connect(
            database_url,
            options=f"-c search_path={schema_name}",
            application_name=schema_name,
        )

    try:
        with connect() as connection:
            init_database(connection)
            connection.execute(
                """INSERT INTO merchants (merchant_id, business_name, location, tier)
                   VALUES (%s, %s, %s, %s)""",
                ("M001", "Alpha Shop", "Johannesburg", "insights"),
            )
            connection.execute(
                """INSERT INTO merchants (merchant_id, business_name, location, tier)
                   VALUES (%s, %s, %s, %s)""",
                ("M002", "Beta Shop", "Cape Town", "insights"),
            )
            connection.execute(
                """INSERT INTO stores (store_id, merchant_id, store_name, location)
                   VALUES (%s, %s, %s, %s)""",
                ("ST001", "M001", "Main Store", "Johannesburg"),
            )
            connection.execute(
                """INSERT INTO stores (store_id, merchant_id, store_name, location)
                   VALUES (%s, %s, %s, %s)""",
                ("ST002", "M002", "Second Store", "Cape Town"),
            )
            connection.execute(
                """INSERT INTO merchant_users (user_id, merchant_id, role)
                   VALUES (%s, %s, %s)""",
                ("user-1", "M001", "owner"),
            )
            connection.execute(
                """INSERT INTO merchant_users (user_id, merchant_id, role)
                   VALUES (%s, %s, %s)""",
                ("user-2", "M002", "admin"),
            )

        yield connect
    finally:
        with psycopg.connect(database_url, autocommit=True) as connection:
            connection.execute(
                """SELECT pg_terminate_backend(pid)
                   FROM pg_stat_activity
                   WHERE application_name = %s AND pid <> pg_backend_pid()""",
                (schema_name,),
            )
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema_name))
            )


def test_user_merchants_and_role_lookup(auth_database):
    with auth_database() as conn:
        merchants = get_user_merchants("user-1", conn)
        assert merchants[0]["merchant_id"] == "M001"
        assert get_user_role("user-1", "M001", conn) == "owner"


def test_user_cannot_access_other_merchant_store(auth_database):
    with auth_database() as conn:
        with pytest.raises(PermissionError):
            require_merchant_access("user-1", "M002", conn)

        with pytest.raises(PermissionError):
            require_store_access("user-1", "ST002", conn)


def test_user_can_access_own_store(auth_database):
    with auth_database() as conn:
        result = require_store_access("user-1", "ST001", conn)
        assert result["merchant_id"] == "M001"
        assert result["role"] == "owner"


def test_connect_code_redemption_is_atomic_and_single_use(auth_database):
    with auth_database() as conn:
        code = create_connect_code("ST001", merchant_id="M001", conn=conn)

        redeemed = redeem_connect_code(code.code, conn, user_id="user-3")
        assert redeemed.used is True

        with pytest.raises(ValueError):
            redeem_connect_code(code.code, conn, user_id="user-4")


def test_connect_code_rejects_expired_code(auth_database):
    with auth_database() as conn:
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO connect_codes (code, store_id, merchant_id, used, expires_at) VALUES (%s, %s, %s, %s, %s)",
                ("EXPIRED1", "ST001", "M001", False, expires_at),
            )
        conn.commit()

        with pytest.raises(ValueError):
            redeem_connect_code("EXPIRED1", conn)


def test_whatsapp_source_idempotency_and_conflict(auth_database):
    with auth_database() as conn:
        first = link_whatsapp_source_to_store("ST001", "+27821234567", conn)
        second = link_whatsapp_source_to_store("ST001", "+27821234567", conn)
        assert first == second

        with pytest.raises(ValueError):
            link_whatsapp_source_to_store("ST002", "+27821234567", conn)


def test_dashboard_onboarding_creates_membership_and_code(auth_database):
    with auth_database() as conn:
        data = create_dashboard_merchant("user-9", "New Merchant", conn, store_name="New Store")
        assert data["merchant_id"].startswith("M")
        assert data["store_id"].startswith("ST")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
                ("user-9", data["merchant_id"]),
            )
            assert cur.fetchone() is not None
