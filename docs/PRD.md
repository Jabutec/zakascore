# ZakaScore — System Requirements Specification

**Release:** V1.0.0
**Author:** Jabulani Mokoena
**Last updated:** 2026-08-16
**Status:** Active development — Database layer in progress

---

## 1. System Purpose

ZakaScore is a data aggregation and credit-scoring engine for South African SMEs. V1.0.0 is a **backend-first, single-service system** that proves the core pipeline: structured transaction data → validated ingestion → deterministic scoring logic → queryable API.

**V1.0.0 is not:** a lender, a frontend product, or a live-data system. It is the engineered core the rest of the product will sit on top of.

---

## 2. Architecture Overview

V1.0.0 is composed of four layers, built and delivered in this order:

```
┌─────────────────────────────────────────────────────┐
│  4. INTERFACE — FastAPI application + /docs (OpenAPI) │
│     Exposes endpoints to query merchants, transactions,│
│     and computed scores. Auto-generated interactive    │
│     documentation via FastAPI's built-in Swagger UI.    │
├─────────────────────────────────────────────────────┤
│  3. BI ENGINE — Python scoring & analytics module       │
│     Consumes validated transaction data, computes        │
│     score + supporting metrics (volume, consistency,      │
│     recency). Pure Python, decoupled from the API layer   │
│     so it can be tested and reasoned about independently.  │
├─────────────────────────────────────────────────────┤
│  2. VALIDATION — Pydantic models                          │
│     Defines the contract for what a valid Merchant,         │
│     Product, and Transaction record looks like. Rejects      │
│     malformed data before it reaches the database.            │
├─────────────────────────────────────────────────────┤
│  1. DATABASE — SQLite (V1), schema-first design              │
│     merchants, products, transactions. Source-agnostic         │
│     schema designed to later accept real payment-provider       │
│     data without structural rewrite.                             │
└─────────────────────────────────────────────────────────────┘
```

**Design principle:** each layer only knows about the layer directly beneath it. The BI engine never touches raw database rows directly — it consumes Pydantic-validated objects. The API layer never computes scores itself — it calls the BI engine. This separation is what makes the system testable and lets each layer be swapped later (e.g., SQLite → Postgres, synthetic data → live Yoco feed) without a full rewrite.

---

## 3. Components & Requirements

### 3.1 Database Layer

**Purpose:** Persist merchant, product, and transaction records in a normalized, source-agnostic schema.

| ID   | Requirement                                                                                                                                                         | Priority |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| DB-1 | System shall store merchant records (id, business name, email, hashed password, created_at).                                                                        | Must     |
| DB-2 | System shall store product records associated with a merchant (id, merchant_id, name, category, price).                                                             | Must     |
| DB-3 | System shall store transaction records associated with a merchant (id, merchant_id, product_id, amount, timestamp, status, source).                                 | Must     |
| DB-4 | Transaction schema shall include a `source` field (e.g., `synthetic`, `yoco`, `bank`) so future real data sources plug into the same table without a schema change. | Must     |
| DB-5 | Foreign key constraints shall enforce that transactions and products cannot exist without a valid merchant.                                                         | Must     |
| DB-6 | Schema shall be designed to migrate cleanly from SQLite to a production RDBMS (e.g., PostgreSQL) — avoid SQLite-specific type shortcuts.                            | Should   |

**Definition of Done:** `scripts/init_db.py` creates all tables with constraints enforced; a test script confirms invalid inserts (e.g., orphaned transaction) are rejected at the database level.

---

### 3.2 Validation Layer (FastAPI + Pydantic)

**Purpose:** Guarantee that no malformed or incomplete data reaches the database or the BI engine.

| ID    | Requirement                                                                                                                                                                              | Priority |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| VAL-1 | System shall define a Pydantic model for `MerchantCreate` validating business name, email format, and password strength.                                                                 | Must     |
| VAL-2 | System shall define a Pydantic model for `TransactionCreate` validating amount (positive, correct decimal precision), timestamp, and status enum.                                        | Must     |
| VAL-3 | System shall reject and return a structured error (HTTP 422) for any payload failing validation, with a clear field-level error message.                                                 | Must     |
| VAL-4 | Pydantic response models shall be separate from input models, so internal fields (e.g., hashed password) are never serialized back to a client.                                          | Must     |
| VAL-5 | Validation models shall be reused as the single source of truth for both API request bodies and internal data generation (synthetic data generator must produce Pydantic-valid records). | Should   |

**Definition of Done:** every write path (API endpoint or synthetic data seeder) passes through a Pydantic model; no raw dict is inserted into the database unvalidated.

---

### 3.3 BI Engine (Python)

**Purpose:** Compute a business score and supporting metrics from a merchant's validated transaction history.

| ID   | Requirement                                                                                                                                                                                                            | Priority |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| BI-1 | Engine shall calculate transaction volume metrics (total, average, count) over a configurable time window.                                                                                                             | Must     |
| BI-2 | Engine shall calculate consistency metrics (e.g., variance in transaction frequency/amount over time).                                                                                                                 | Must     |
| BI-3 | Engine shall calculate recency (how current the merchant's data is).                                                                                                                                                   | Must     |
| BI-4 | Engine shall combine volume, consistency, and recency into a single deterministic score using a documented, explainable formula (rule-based, not a black-box model, for V1).                                           | Must     |
| BI-5 | Engine shall return a "insufficient data" state rather than a misleading score when a merchant has less than a defined minimum history (e.g., 30 days / N transactions).                                               | Must     |
| BI-6 | Engine logic shall be implemented as pure functions independent of FastAPI/database code, so it can be unit tested in isolation.                                                                                       | Must     |
| BI-7 | Engine shall be tested against multiple synthetic merchant profiles representing different business patterns (steady, seasonal, declining, sparse) to validate the scoring formula behaves sensibly across archetypes. | Should   |

**Definition of Done:** scoring formula is documented (inputs, weights, output range); unit tests cover at least the four synthetic merchant archetypes above with expected score ranges asserted.

---

### 3.4 Interface Layer (FastAPI + `/docs`)

**Purpose:** Expose the system's functionality via a documented, testable API — no frontend in V1.0.0.

| ID    | Requirement                                                                                                                                     | Priority |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| API-1 | System shall expose `POST /merchants` to create a merchant (validated via VAL-1).                                                               | Must     |
| API-2 | System shall expose `GET /merchants/{id}` to retrieve merchant details (excluding password hash).                                               | Must     |
| API-3 | System shall expose `POST /transactions` to record a transaction (validated via VAL-2).                                                         | Must     |
| API-4 | System shall expose `GET /merchants/{id}/transactions` to list a merchant's transaction history.                                                | Must     |
| API-5 | System shall expose `GET /merchants/{id}/score` to return the current computed score and supporting metrics from the BI engine.                 | Must     |
| API-6 | All endpoints shall be documented and testable via FastAPI's auto-generated `/docs` (Swagger UI) with example request/response schemas visible. | Must     |
| API-7 | Endpoints shall return appropriate HTTP status codes (200, 201, 404, 422) rather than generic 200s with error messages in the body.             | Must     |

**Definition of Done:** every endpoint above is callable and testable directly from `/docs` with no external client needed; example payloads in Swagger reflect real Pydantic schemas, not placeholders.

---

## 4. Synthetic Data Strategy

Since V1.0.0 has no live payment-provider connection, a **synthetic data generator** is a first-class part of this release, not an afterthought.

| ID    | Requirement                                                                                                                                                                     | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| SYN-1 | System shall include a script that generates realistic synthetic merchants, products, and transactions, passed through the same Pydantic validation as real input.              | Must     |
| SYN-2 | Generator shall support multiple archetypes (steady-volume, seasonal, growing, declining, sparse/new merchant) to stress-test the BI engine against varied real-world patterns. | Must     |
| SYN-3 | Generator shall be seedable/repeatable (fixed random seed option) so scoring results are reproducible for testing and demos.                                                    | Should   |
| SYN-4 | Synthetic transactions shall be tagged `source = "synthetic"` in the database, clearly distinguishing them from any future real data.                                           | Must     |

---

## 5. Non-Functional Requirements

| Category       | Requirement                                                                                                                                                |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Security       | Passwords hashed (e.g., bcrypt/passlib); no plaintext secrets in code or repo; `.env` used for any config values                                           |
| Data integrity | Foreign key constraints enforced at the database level, not just application level                                                                         |
| Testability    | Each layer (DB, validation, BI engine, API) shall have at least basic automated tests; BI engine logic shall be unit-testable without a running API server |
| Performance    | API responses for synthetic dataset sizes (hundreds–low thousands of transactions) shall return in under 500ms                                             |
| Portability    | No SQLite-specific logic embedded in application code that would block a future Postgres migration                                                         |
| Documentation  | `/docs` (Swagger) shall serve as the living API reference; `SRS.md` and this document shall be kept in sync with actual schema/endpoints as they evolve    |

---

## 6. Explicit Exclusions (V1.0.0)

To keep scope honest and prevent creep:

- No Yoco, bank, PayFast, Ozow, or Stitch/Mono integration — synthetic data only
- No frontend/UI — `/docs` is the only interface
- No authentication tokens/session management beyond basic merchant record creation (full auth flow can follow in a later version)
- No machine learning scoring model — V1 scoring is rule-based and explainable by design
- No multi-tenant/lender-facing views

---

## 7. Open Engineering Decisions

- **Score scale:** 0–100 vs. 300–850-style range, needs to be fixed before BI-4 is finalized, since it affects both the formula's normalization and any future UI.
- **Minimum data threshold:** exact number of days/transactions before a score is considered valid (BI-5) — needs a concrete value, not just "enough."
- **Weighting formula:** relative weight of volume vs. consistency vs. recency in the final score should be documented as a config (e.g., a `weights.py` or config dict) rather than hardcoded inline, so it can be tuned without touching core logic.
- **Synthetic data realism:** what statistical distributions best approximate real SME transaction patterns (e.g., Poisson-distributed daily transaction counts, log-normal transaction amounts) worth a short research pass before building SYN-1 in full.

---

## 8. Definition of Done — V1.0.0

V1.0.0 is complete when:

- [ ] Database schema is finalized, migrated, and constraint-tested
- [ ] All Pydantic validation models are implemented and enforced on every write path
- [ ] Synthetic data generator produces valid, varied merchant/transaction datasets
- [ ] BI engine computes scores deterministically and passes unit tests across all synthetic archetypes
- [ ] All FastAPI endpoints are implemented, documented, and functional via `/docs`
- [ ] No hardcoded secrets or credentials exist anywhere in the repository
- [ ] `SRS.md` reflects the actual, as-built schema and endpoint list
