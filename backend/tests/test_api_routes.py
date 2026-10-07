"""End-to-end tests of the dashboard routes through FastAPI, against a real Postgres that
already has the schema:

    TEST_DATABASE_URL=postgresql://... python -m pytest tests/test_api_auth.py

Token verification is stubbed (tokens are just names mapped to user ids); everything else,
including authorization and the SQL, is real. Only creates and deletes merchants named "TEST ...".
"""
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import psycopg
import pytest
from fastapi.testclient import TestClient

from api import auth as api_auth
from api.webhook import app
from services.onboarding import create_dashboard_merchant

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL, reason="set TEST_DATABASE_URL to run the database tests"
)

SAST = ZoneInfo("Africa/Johannesburg")


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


@pytest.fixture
def client(monkeypatch):
    tokens = {}
    monkeypatch.setattr(api_auth, "verify_access_token", lambda token: tokens.get(token))

    def request_conn():
        request_connection = psycopg.connect(TEST_DATABASE_URL)
        try:
            yield request_connection
        except Exception:
            request_connection.rollback()
            raise
        else:
            request_connection.commit()
        finally:
            request_connection.close()

    monkeypatch.setitem(app.dependency_overrides, api_auth.get_conn, request_conn)

    test_client = TestClient(app)
    test_client.tokens = tokens
    return test_client


def login(client, user_id, name="token"):
    token = f"{name}-{user_id}"
    client.tokens[token] = str(user_id)
    return {"Authorization": f"Bearer {token}"}


def make_merchant(
    conn, name, owner=None, tier="insights", created_days_ago=0, role="owner"
):
    merchant_id = conn.execute(
        "INSERT INTO merchants (business_name, tier, created_at) "
        "VALUES (%s, %s, now() - make_interval(days => %s)) RETURNING merchant_id",
        (name, tier, created_days_ago),
    ).fetchone()[0]
    store_id = conn.execute(
        "INSERT INTO stores (merchant_id, store_name) VALUES (%s, 'Main') RETURNING store_id",
        (merchant_id,),
    ).fetchone()[0]
    source_id = conn.execute(
        "INSERT INTO data_sources (store_id, source_name, source_type) "
        "VALUES (%s, 'Manual', 'manual') RETURNING source_id",
        (store_id,),
    ).fetchone()[0]
    if owner is not None:
        conn.execute(
            "INSERT INTO merchant_users (user_id, merchant_id, role) VALUES (%s, %s, %s)",
            (owner, merchant_id, role),
        )
    conn.commit()
    return merchant_id, store_id, source_id


def add_sale(conn, store_id, source_id, amount, when=None, payment="cash", voided=False,
             offering_id=None, quantity=None, input_type="manual"):
    conn.execute(
        """INSERT INTO transactions (
                store_id, source_id, client_txn_id, input_type, amount_zar,
                payment_method, transaction_date, is_voided, voided_at,
                offering_id, quantity
           )
           VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, now()), %s,
                   CASE WHEN %s THEN now() END, %s, %s)""",
        (
            store_id, source_id, uuid4(), input_type, amount, payment, when,
            voided, voided, offering_id, quantity,
        ),
    )
    conn.commit()


def add_pwa_source(conn, store_id):
    source_id = conn.execute(
        """INSERT INTO data_sources (store_id, source_name, source_type)
           VALUES (%s, 'PWA', 'pwa') RETURNING source_id""",
        (store_id,),
    ).fetchone()[0]
    conn.commit()
    return source_id


def post_transaction(client, user_id, store_id, **overrides):
    payload = {
        "store_id": str(store_id),
        "client_txn_id": str(uuid4()),
        "amount_zar": "100.25",
        "payment_method": "cash",
    }
    payload.update(overrides)
    return client.post("/transactions", headers=login(client, user_id), json=payload)


# --- authentication -----------------------------------------------------------
def test_missing_or_malformed_authorization_is_401(client):
    assert client.get("/api/overview").status_code == 401
    assert client.get("/api/overview", headers={"Authorization": "Basic abc"}).status_code == 401
    assert client.get("/api/overview", headers={"Authorization": "Bearer"}).status_code == 401
    response = client.get("/api/overview")
    assert response.json()["detail"] == "Invalid authorization header"
    assert response.headers["www-authenticate"] == "Bearer"


def test_unknown_or_expired_token_is_401(client):
    response = client.get("/api/overview", headers={"Authorization": "Bearer nonsense"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_scheme_is_case_insensitive(client, conn):
    user = uuid4()
    make_merchant(conn, "TEST Shop", owner=user)
    headers = login(client, user)
    headers["Authorization"] = headers["Authorization"].replace("Bearer", "bearer")
    assert client.get("/api/overview", headers=headers).status_code == 200


# --- which merchant a request is for ---------------------------------------------
def test_user_without_a_business_gets_403(client):
    response = client.get("/api/overview", headers=login(client, uuid4()))
    assert response.status_code == 403
    assert response.json()["detail"] == api_auth.NO_MERCHANT_DETAIL


def test_a_user_id_that_equals_a_merchant_id_grants_nothing(client, conn):
    # The old code fell back to treating the user id as a merchant id.
    merchant_id, store_id, source_id = make_merchant(conn, "TEST Victim")  # nobody owns it
    add_sale(conn, store_id, source_id, 500)
    response = client.get("/api/transactions", headers=login(client, merchant_id))
    assert response.status_code == 403


def test_users_only_see_their_own_data(client, conn):
    alice, bob = uuid4(), uuid4()
    _, store_a, source_a = make_merchant(conn, "TEST Alice", owner=alice)
    _, store_b, source_b = make_merchant(conn, "TEST Bob", owner=bob)
    add_sale(conn, store_a, source_a, 111)
    add_sale(conn, store_b, source_b, 999)

    alice_rows = client.get("/api/transactions", headers=login(client, alice)).json()
    bob_rows = client.get("/api/transactions", headers=login(client, bob)).json()
    assert [row["amount_zar"] for row in alice_rows] == [111.0]
    assert [row["amount_zar"] for row in bob_rows] == [999.0]


def test_multi_merchant_users_default_to_the_oldest_and_can_choose(client, conn):
    user = uuid4()
    first, store_1, source_1 = make_merchant(conn, "TEST First", owner=user)
    second, store_2, source_2 = make_merchant(conn, "TEST Second", owner=user)
    add_sale(conn, store_1, source_1, 100)
    add_sale(conn, store_2, source_2, 200)
    headers = login(client, user)

    default = client.get("/api/transactions", headers=headers).json()
    assert [row["amount_zar"] for row in default] == [100.0]

    chosen = client.get("/api/transactions", headers={**headers, "X-Merchant-Id": str(second)}).json()
    assert [row["amount_zar"] for row in chosen] == [200.0]


def test_cannot_choose_someone_elses_or_a_malformed_merchant(client, conn):
    user, other = uuid4(), uuid4()
    make_merchant(conn, "TEST Mine", owner=user)
    theirs, _, _ = make_merchant(conn, "TEST Theirs", owner=other)
    headers = login(client, user)

    for bad in [str(theirs), str(uuid4()), "not-a-uuid"]:
        response = client.get("/api/transactions", headers={**headers, "X-Merchant-Id": bad})
        assert response.status_code == 403
        assert response.json()["detail"] == "No access to this business"


# --- routes --------------------------------------------------------------------
def test_transactions_excludes_voided_orders_newest_first_and_honours_limit(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST Shop", owner=user)
    now = datetime.now(timezone.utc)
    add_sale(conn, store_id, source_id, 10, when=now - timedelta(hours=3))
    add_sale(conn, store_id, source_id, 20, when=now - timedelta(hours=2))
    add_sale(conn, store_id, source_id, 30, when=now - timedelta(hours=1))
    add_sale(conn, store_id, source_id, 999, voided=True)
    headers = login(client, user)

    rows = client.get("/api/transactions", headers=headers).json()
    assert [row["amount_zar"] for row in rows] == [30.0, 20.0, 10.0]
    assert {
        "transaction_id", "amount_zar", "quantity", "payment_method",
        "transaction_date", "offering_name", "store_name", "input_type",
    } == set(rows[0])
    assert rows[0]["store_name"] == "Main"
    assert rows[0]["input_type"] == "manual"

    assert len(client.get("/api/transactions?limit=2", headers=headers).json()) == 2
    assert client.get("/api/transactions?limit=0", headers=headers).status_code == 422
    assert client.get("/api/transactions?limit=101", headers=headers).status_code == 422


def test_revenue_is_bucketed_by_south_african_day(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST Shop", owner=user)
    # 23:30 UTC on the 10th is 01:30 on the 11th in South Africa
    add_sale(conn, store_id, source_id, 100, when=datetime(2026, 3, 10, 23, 30, tzinfo=timezone.utc))
    add_sale(conn, store_id, source_id, 50, when=datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc))
    add_sale(conn, store_id, source_id, 25, when=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc))

    data = client.get("/api/revenue", headers=login(client, user)).json()
    assert data == [
        {"date": "2026-03-10", "revenue": 50.0},
        {"date": "2026-03-11", "revenue": 125.0},
    ]


def test_revenue_days_filter(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST Shop", owner=user)
    add_sale(conn, store_id, source_id, 10, when=datetime.now(timezone.utc) - timedelta(days=100))
    add_sale(conn, store_id, source_id, 20, when=datetime.now(timezone.utc) - timedelta(days=1))
    headers = login(client, user)

    assert len(client.get("/api/revenue", headers=headers).json()) == 2
    assert len(client.get("/api/revenue?days=30", headers=headers).json()) == 1


def test_payment_methods_include_recorded_methods(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST Shop", owner=user)
    add_sale(conn, store_id, source_id, 300, payment="cash")
    add_sale(conn, store_id, source_id, 100, payment="digital")
    data = client.get("/api/payment-methods", headers=login(client, user)).json()
    by_method = {row["payment_method"]: row for row in data}
    assert by_method["cash"]["amount"] == 300.0
    assert by_method["digital"]["amount"] == 100.0
    assert round(sum(row["pct"] for row in data)) == 100


def test_pwa_transaction_success_and_duplicate_is_idempotent(client, conn):
    user = uuid4()
    _, store_id, _ = make_merchant(conn, "TEST PWA", owner=user, role="employee")
    source_id = add_pwa_source(conn, store_id)
    client_txn_id = str(uuid4())
    payload = {
        "store_id": str(store_id),
        "client_txn_id": client_txn_id,
        "amount_zar": "123.45",
        "payment_method": "digital",
        "offering_name": "Shirt",
        "quantity": 2,
    }

    first = client.post(
        "/transactions", headers=login(client, user), json=payload
    )
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["amount_zar"] == 123.45
    assert first_data["source_id"] == str(source_id)
    assert first_data["client_txn_id"] == client_txn_id
    assert first_data["input_type"] == "pwa"
    assert first_data["payment_method"] == "digital"
    assert datetime.fromisoformat(first_data["transaction_date"]).tzinfo is not None

    retry = client.post(
        "/transactions", headers=login(client, user), json=payload
    )
    assert retry.status_code == 200
    assert retry.json() == first_data
    assert conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE store_id = %s AND client_txn_id = %s",
        (store_id, client_txn_id),
    ).fetchone()[0] == 1
    assert conn.execute(
        "SELECT COUNT(*) FROM offerings WHERE store_id = %s AND lower(offering_name) = 'shirt'",
        (store_id,),
    ).fetchone()[0] == 1
    case_variant = {
        **payload,
        "client_txn_id": str(uuid4()),
        "offering_name": "shirt",
    }
    second_offering_sale = client.post(
        "/transactions", headers=login(client, user), json=case_variant
    )
    assert second_offering_sale.status_code == 200
    assert second_offering_sale.json()["offering_id"] == first_data["offering_id"]
    assert conn.execute(
        "SELECT COUNT(*) FROM offerings WHERE store_id = %s AND lower(offering_name) = 'shirt'",
        (store_id,),
    ).fetchone()[0] == 1


def test_pwa_transaction_rejects_viewer_and_someone_elses_store(client, conn):
    viewer = uuid4()
    _, viewer_store, _ = make_merchant(
        conn, "TEST Viewer", owner=viewer, role="viewer"
    )
    add_pwa_source(conn, viewer_store)
    response = post_transaction(client, viewer, viewer_store)
    assert response.status_code == 403
    assert response.json()["detail"] == "Your role does not allow this action"

    owner, other = uuid4(), uuid4()
    make_merchant(conn, "TEST Owner", owner=owner)
    _, other_store, _ = make_merchant(conn, "TEST Other", owner=other)
    add_pwa_source(conn, other_store)
    response = post_transaction(client, owner, other_store)
    assert response.status_code == 403
    assert response.json()["detail"] == "User does not have access to the requested store"


def test_pwa_transaction_does_not_accept_client_source_id(client, conn):
    user = uuid4()
    _, store_id, _ = make_merchant(conn, "TEST Source", owner=user)
    add_pwa_source(conn, store_id)

    response = post_transaction(client, user, store_id, source_id=str(uuid4()))
    assert response.status_code == 422


def test_top_offerings_group_case_insensitively_and_honour_limit(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST Shop", owner=user)
    shirt = conn.execute(
        "INSERT INTO offerings (store_id, offering_name) VALUES (%s, 'shirt') RETURNING offering_id",
        (store_id,),
    ).fetchone()[0]
    dress = conn.execute(
        "INSERT INTO offerings (store_id, offering_name) VALUES (%s, 'dress') RETURNING offering_id",
        (store_id,),
    ).fetchone()[0]
    conn.commit()
    add_sale(conn, store_id, source_id, 100, offering_id=shirt, quantity=1)
    add_sale(conn, store_id, source_id, 150, offering_id=shirt, quantity=2)
    add_sale(conn, store_id, source_id, 500, offering_id=dress, quantity=1)
    headers = login(client, user)

    data = client.get("/api/top-offerings", headers=headers).json()
    assert data == [
        {"offering": "dress", "revenue": 500.0, "quantity": 1},
        {"offering": "shirt", "revenue": 250.0, "quantity": 3},
    ]
    assert len(client.get("/api/top-offerings?limit=1", headers=headers).json()) == 1


def test_overview_works_for_a_brand_new_merchant(client, conn):
    user = uuid4()
    make_merchant(conn, "TEST Empty", owner=user)
    data = client.get("/api/overview", headers=login(client, user)).json()
    assert data["total_revenue"] == 0 and data["transaction_count"] == 0
    assert data["revenue_trend"] == "insufficient_data"


def test_credit_score_is_still_building_for_a_new_merchant(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST New", owner=user)
    add_sale(conn, store_id, source_id, 100)
    headers = login(client, user)
    data = client.get("/api/credit-score", headers=headers).json()
    assert data == {"status": "building", "credit_score": None}

    details = client.get("/api/credit-score/details", headers=headers).json()
    assert details["status"] == "building"
    assert details["credit_score"] is None
    assert details["weeks_required"] == 12 and details["weeks_of_history"] == 0


def test_free_tier_cannot_access_credit_score_details(client, conn):
    user = uuid4()
    make_merchant(conn, "TEST Free Credit Details", owner=user, created_days_ago=90)

    response = client.get("/api/credit-score/details", headers=login(client, user))

    assert response.status_code == 403
    assert response.json()["detail"] == "credit_preview is a premium feature"


def test_credit_score_for_an_established_merchant(client, conn):
    user = uuid4()
    _, store_id, source_id = make_merchant(conn, "TEST Established", owner=user)
    today = datetime.now(SAST).date()
    this_monday = today - timedelta(days=today.weekday())
    for weeks_back in range(1, 15):
        monday = this_monday - timedelta(weeks=weeks_back)
        for offset in range(4):  # four trading days a week
            when = datetime.combine(monday + timedelta(days=offset), datetime.min.time(), SAST).replace(hour=10)
            add_sale(conn, store_id, source_id, 500, when=when)

    headers = login(client, user)
    data = client.get("/api/credit-score", headers=headers).json()
    assert data["status"] == "scored"
    assert 0 <= data["credit_score"] <= 100
    assert set(data) == {"status", "credit_score"}

    details = client.get("/api/credit-score/details", headers=headers).json()
    assert details["status"] == "scored"
    assert 0 <= details["credit_score"] <= 100
    assert set(details["components"]) == {"stability", "growth", "revenue_level", "consistency"}
    assert details["metrics"]["weeks_scored"] == 12
    assert {"start", "end"} == set(details["window"])


def test_entitlements(client, conn):
    new_user, old_user, paid_user = uuid4(), uuid4(), uuid4()
    make_merchant(conn, "TEST New", owner=new_user, created_days_ago=2)
    make_merchant(conn, "TEST Old", owner=old_user, created_days_ago=90)
    make_merchant(conn, "TEST Paid", owner=paid_user, tier="full", created_days_ago=90)

    trial = client.get("/api/entitlements", headers=login(client, new_user)).json()
    assert trial["tier"] == "full" and trial["in_trial"] and trial["role"] == "owner"

    free = client.get("/api/entitlements", headers=login(client, old_user)).json()
    assert free["tier"] == "insights" and not free["in_trial"]
    assert free["features"]["sales_logging"] is True
    assert free["features"]["credit_access"] is False

    paid = client.get("/api/entitlements", headers=login(client, paid_user)).json()
    assert paid["tier"] == "full" and all(paid["features"].values())


def test_dashboard_onboarding_creates_owner_membership_and_connect_code(client, conn):
    user = uuid4()
    response = client.post(
        "/api/onboarding/dashboard",
        headers=login(client, user),
        json={"business_name": "TEST Connect API", "store_name": "Main"},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["connect_code"]
    assert conn.execute(
        "SELECT role FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
        (user, result["merchant_id"]),
    ).fetchone() == ("owner",)
    assert conn.execute(
        "SELECT store_id FROM connect_codes WHERE code = %s",
        (result["connect_code"],),
    ).fetchone() == (UUID(result["store_id"]),)


def test_business_list_only_contains_businesses_the_user_can_access(client, conn):
    user, other_user = uuid4(), uuid4()
    first_merchant, first_store, _ = make_merchant(
        conn, "TEST Workspace One", owner=user
    )
    make_merchant(conn, "TEST Workspace Other", owner=other_user)

    response = client.get("/api/businesses", headers=login(client, user))

    assert response.status_code == 200
    data = response.json()
    assert data["selected_merchant_id"] == str(first_merchant)
    assert data["businesses"] == [
        {
            "merchant_id": str(first_merchant),
            "business_name": "TEST Workspace One",
            "role": "owner",
            "stores": [
                {
                    "store_id": str(first_store),
                    "store_name": "Main",
                    "pwa_logging_enabled": False,
                }
            ],
        }
    ]


def test_connect_code_redemption_requires_authentication_and_consumes_valid_code(client, conn):
    owner = uuid4()
    result = create_dashboard_merchant(
        owner, "TEST Connect Redemption", conn
    )
    user = uuid4()

    unauthenticated = client.post(
        "/api/connect-codes/redeem", json={"code": result["connect_code"]}
    )
    assert unauthenticated.status_code == 401

    redeemed = client.post(
        "/api/connect-codes/redeem",
        headers=login(client, user),
        json={"code": result["connect_code"]},
    )
    assert redeemed.status_code == 200
    assert redeemed.json() == {
        "store_id": str(result["store_id"]),
        "merchant_id": str(result["merchant_id"]),
    }
    assert conn.execute(
        "SELECT role FROM merchant_users WHERE user_id = %s AND merchant_id = %s",
        (user, result["merchant_id"]),
    ).fetchone() == ("employee",)
    assert conn.execute(
        "SELECT used_at IS NOT NULL FROM connect_codes WHERE code = %s",
        (result["connect_code"],),
    ).fetchone() == (True,)
    repeated = client.post(
        "/api/connect-codes/redeem",
        headers=login(client, uuid4()),
        json={"code": result["connect_code"]},
    )
    assert repeated.status_code == 400
    assert repeated.json()["detail"] == "Invalid or expired connect code"


def test_admin_can_issue_employee_invite_but_employee_cannot(client, conn):
    owner, employee = uuid4(), uuid4()
    merchant_id, store_id, _ = make_merchant(
        conn, "TEST Team Invites", owner=owner
    )
    conn.execute(
        "INSERT INTO merchant_users (user_id, merchant_id, role) VALUES (%s, %s, 'employee')",
        (employee, merchant_id),
    )
    conn.commit()

    issued = client.post(
        "/api/connect-codes",
        headers=login(client, owner),
        json={"store_id": str(store_id)},
    )
    assert issued.status_code == 201
    assert issued.json()["code"]

    denied = client.post(
        "/api/connect-codes",
        headers=login(client, employee),
        json={"store_id": str(store_id)},
    )
    assert denied.status_code == 403