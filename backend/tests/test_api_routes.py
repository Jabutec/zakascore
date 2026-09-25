import asyncio
import os
import sqlite3
from datetime import datetime

import pytest
from fastapi import HTTPException

# Route modules construct their OpenAI clients during import.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-bytes")

from api import auth, webhook
from validation.models import Tier


@pytest.fixture
def route_database(tmp_path, monkeypatch):
    database_path = tmp_path / "routes.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE merchants (
            merchant_id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            whatsapp_number TEXT NOT NULL UNIQUE,
            location TEXT,
            tier TEXT NOT NULL,
            created_at DATETIME
        );
        CREATE TABLE otp_codes (
            otp_id TEXT PRIMARY KEY,
            merchant_id TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE offerings (
            offering_id TEXT PRIMARY KEY,
            merchant_id TEXT NOT NULL,
            offering_name TEXT NOT NULL
        );
        CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            merchant_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            offering_id TEXT,
            quantity INTEGER,
            input_type TEXT,
            amount_zar REAL NOT NULL,
            raw_message TEXT,
            is_voided INTEGER NOT NULL DEFAULT 0,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.execute(
        """
        INSERT INTO merchants
            (merchant_id, business_name, whatsapp_number, location, tier, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "M001",
            "Test Shop",
            "+27821234567",
            "",
            Tier.INSIGHTS.value,
            datetime.now().isoformat(),
        ),
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(auth, "get_db", lambda: sqlite3.connect(database_path))
    monkeypatch.setattr(webhook, "get_db", lambda: sqlite3.connect(database_path))
    yield database_path


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
    with sqlite3.connect(route_database) as connection:
        merchant = connection.execute(
            "SELECT business_name, whatsapp_number FROM merchants "
            "WHERE whatsapp_number = ?",
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
    with sqlite3.connect(route_database) as connection:
        transaction = connection.execute(
            "SELECT merchant_id, amount_zar, quantity, input_type, raw_message "
            "FROM transactions"
        ).fetchone()
        offering = connection.execute(
            "SELECT offering_name FROM offerings WHERE merchant_id = ?",
            ("M001",),
        ).fetchone()
    assert transaction == ("M001", 300.0, 2, "whatsapp", "sold 2 shirts for 300")
    assert offering == ("shirt",)


def test_request_and_verify_otp_return_access_token(route_database):
    request_response = run(auth.request_otp(phone_number="+27821234567"))

    assert request_response["message"] == "OTP sent"
    assert request_response["dev_otp_code"].isdigit()

    verify_response = run(
        auth.verify_otp_route(
            phone_number="+27821234567",
            code=request_response["dev_otp_code"],
        )
    )

    assert verify_response["access_token"]
    assert auth.verify_access_token(verify_response["access_token"]) == "M001"


def test_auth_routes_reject_unknown_number(route_database):
    request_response = run(auth.request_otp(phone_number="+27821234568"))
    verify_response = run(
        auth.verify_otp_route(phone_number="+27821234568", code="123456")
    )

    assert request_response == {"error": "No account found for this number"}
    assert verify_response == {"error": "No account found for this number"}


@pytest.mark.parametrize("authorization", ["Basic abc", "Bearer invalid"])
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
    assert response == {
        "credit_score": 72.5,
    }
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
