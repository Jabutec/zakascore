import asyncio
import os
from datetime import date, datetime, timezone
from uuid import uuid4

import psycopg
import pytest
from fastapi import HTTPException
from psycopg import sql

# Route modules construct their OpenAI clients during import.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-bytes")

from api import auth, webhook
from scripts.init_db import init_database


@pytest.fixture
def route_database(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL must point to a PostgreSQL test database")

    schema_name = f"test_{uuid4().hex}"
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
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
                """INSERT INTO merchants
                       (merchant_id, business_name, location, tier)
                   VALUES (%s, %s, %s, %s)""",
                ("M001", "Test Shop", "", "insights"),
            )
            connection.execute(
                """INSERT INTO stores (store_id, merchant_id, store_name, location)
                   VALUES (%s, %s, %s, %s)""",
                ("ST001", "M001", "Test Shop", ""),
            )
            connection.execute(
                """INSERT INTO data_sources
                       (source_id, store_id, source_name, source_type, external_identifier)
                   VALUES (%s, %s, %s, %s, %s)""",
                ("S001", "ST001", "WhatsApp", "whatsapp", "+27821234567"),
            )

        monkeypatch.setattr(auth, "get_db", connect)
        monkeypatch.setattr(webhook, "get_db", connect)
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


def run(coroutine):
    return asyncio.run(coroutine)


def test_webhook_registers_new_number(route_database):
    response = run(
        webhook.whatsapp_webhook(
            From="whatsapp:+27821234568",
            Body="register: New Shop",
            NumMedia="0",
            MediaUrl0=None,
        )
    )

    assert response.body.decode() == (
        "Registered! Now send your sale amounts anytime, e.g. 300"
    )
    with route_database() as connection:
        merchant = connection.execute(
            """SELECT m.business_name, ds.external_identifier
               FROM merchants m
               JOIN stores s ON s.merchant_id = m.merchant_id
               JOIN data_sources ds ON ds.store_id = s.store_id
               WHERE ds.source_type = 'whatsapp'
                 AND ds.external_identifier = %s""",
            ("+27821234568",),
        ).fetchone()
    assert merchant == ("New Shop", "+27821234568")


def test_webhook_logs_parsed_transaction(route_database, monkeypatch):
    monkeypatch.setattr(webhook, "has_reached_limit", lambda *args: False)
    monkeypatch.setattr(
        webhook,
        "extract_transaction_details",
        lambda text: {"item": "shirt", "quantity": 2, "amount": 300},
    )

    response = run(
        webhook.whatsapp_webhook(
            From="whatsapp:+27821234567",
            Body="sold 2 shirts for 300",
            NumMedia="0",
            MediaUrl0=None,
        )
    )

    assert response.body.decode() == "Logged: R300"
    with route_database() as connection:
        transaction = connection.execute(
            """SELECT s.merchant_id, t.amount_zar, t.quantity, t.input_type, t.raw_message
               FROM transactions t
               JOIN stores s ON s.store_id = t.store_id"""
        ).fetchone()
        offering = connection.execute(
            "SELECT offering_name FROM offerings WHERE store_id = %s",
            ("ST001",),
        ).fetchone()
    assert transaction == ("M001", 300.0, 2, "whatsapp", "sold 2 shirts for 300")
    assert offering == ("shirt",)


def test_bi_and_scoring_routes_query_all_merchant_stores(route_database):
    today = date.today()
    period_start = today.replace(day=1)
    transaction_time = datetime.now(timezone.utc)

    with route_database() as connection:
        connection.execute(
            """INSERT INTO data_sources
                   (source_id, store_id, source_name, source_type)
               VALUES (%s, %s, %s, %s)""",
            ("S002", "ST001", "POS", "pos"),
        )
        connection.execute(
            """INSERT INTO stores (store_id, merchant_id, store_name)
               VALUES (%s, %s, %s)""",
            ("ST002", "M001", "Second Store"),
        )
        connection.execute(
            """INSERT INTO data_sources
                   (source_id, store_id, source_name, source_type)
               VALUES (%s, %s, %s, %s)""",
            ("S003", "ST002", "POS", "pos"),
        )
        connection.execute(
            """INSERT INTO offerings (offering_id, store_id, offering_name)
               VALUES (%s, %s, %s)""",
            ("O001", "ST001", "shirt"),
        )
        connection.execute(
            """INSERT INTO transactions
                   (transaction_id, store_id, source_id, offering_id, quantity,
                    input_type, amount_zar, payment_method, transaction_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s),
               (%s, %s, %s, %s, %s, %s, %s, %s, %s),
               (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                "T001",
                "ST001",
                "S001",
                "O001",
                2,
                "whatsapp",
                300,
                None,
                transaction_time,
                "T002",
                "ST001",
                "S002",
                None,
                None,
                "pos_tap",
                50,
                "cash",
                transaction_time,
                "T003",
                "ST002",
                "S003",
                None,
                None,
                "pos_tap",
                25,
                "cash",
                transaction_time,
            ),
        )
        connection.execute(
            """INSERT INTO financial_snapshots
                   (snapshot_id, store_id, period_start, period_end,
                    total_revenue_zar, transaction_count, average_transaction_zar,
                    cash_revenue_zar, digital_revenue_zar, revenue_growth_pct,
                    revenue_volatility)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                "F001",
                "ST001",
                period_start,
                today,
                350,
                2,
                175,
                50,
                0,
                None,
                0,
            ),
        )
        connection.execute(
            """INSERT INTO financial_snapshots
                   (snapshot_id, store_id, period_start, period_end,
                    total_revenue_zar, transaction_count, average_transaction_zar,
                    cash_revenue_zar, digital_revenue_zar, revenue_growth_pct,
                    revenue_volatility)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                "F002",
                "ST002",
                period_start,
                today,
                25,
                1,
                25,
                25,
                0,
                None,
                0,
            ),
        )

    transactions = run(auth.get_my_transactions(merchant_id="M001"))
    revenue = run(auth.get_my_revenue(merchant_id="M001"))
    offerings = run(auth.get_my_top_offerings(merchant_id="M001"))
    overview = run(auth.get_my_overview(merchant_id="M001"))
    payment_methods = run(auth.get_my_payment_methods(merchant_id="M001"))
    credit_score = run(auth.get_my_credit_score(merchant_id="M001"))

    assert len(transactions) == 3
    assert sum(item["revenue"] for item in revenue) == 375
    assert offerings == [{"offering": "shirt", "revenue": 300, "quantity": 2}]
    assert overview["total_revenue"] == 375
    assert payment_methods == [{"payment_method": "cash", "amount": 75}]
    assert credit_score["credit_score"] is not None


def test_auth_routes_no_longer_include_otp_endpoints():
    route_paths = {route.path for route in auth.router.routes}
    assert "/auth/request-otp" not in route_paths
    assert "/auth/verify-otp" not in route_paths


@pytest.mark.parametrize("authorization", ["Basic abc", "******"])
def test_protected_routes_reject_invalid_authorization(authorization):
    with pytest.raises(HTTPException) as error:
        auth.get_current_merchant_id(authorization=authorization)

    assert error.value.status_code == 401


def test_credit_score_route_returns_score_for_current_period(route_database, monkeypatch):
    captured_period = {}

    def fake_get_score(merchant_id, period_start, period_end, connection):
        captured_period["values"] = (merchant_id, period_start, period_end)
        return 72.5

    monkeypatch.setattr(auth, "get_merchant_credit_score", fake_get_score)

    response = run(auth.get_my_credit_score(merchant_id="M001"))

    today = datetime.now().date()
    assert response == {"credit_score": 72.5}
    assert captured_period["values"] == (
        "M001",
        today.replace(day=1).isoformat(),
        today.isoformat(),
    )


def test_credit_score_route_returns_none_without_snapshot(route_database, monkeypatch):
    def missing_score(*args):
        raise ValueError("No financial snapshot found")

    monkeypatch.setattr(auth, "get_merchant_credit_score", missing_score)

    response = run(auth.get_my_credit_score(merchant_id="M001"))

    assert response == {"credit_score": None}
