# ZakaScore — Software Requirements Specification (SRS)

**Release:** V1.0.0
**Author:** Jabulani Mokoena
**Last updated:** 2026-08-16
**Status:** Database layer implemented — validation layer next

---

## 1. Purpose

This document specifies the requirements for ZakaScore V1.0.0, derived from and kept in sync with the as-built database schema (`scripts/init_db.py`). It reflects the actual system, as the schema evolves, this document evolves with it.

---

## 2. As-Built Database Schema

Four tables, SQLite, foreign keys enforced (`PRAGMA foreign_keys = ON`).

### 2.1 `merchants`

| Column          | Type     | Constraints               |
| --------------- | -------- | ------------------------- |
| `merchant_id`   | TEXT     | PRIMARY KEY               |
| `business_name` | TEXT     | NOT NULL                  |
| `location`      | TEXT     | —                         |
| `created_at`    | DATETIME | DEFAULT CURRENT_TIMESTAMP |

**Notes:** No auth fields (email/password) at the database level yet. If merchant login is still in scope for V1.0.0, those fields (or a separate `auth` table) need to be added before the validation/API layers are built against this table.

### 2.2 `transactions`

| Column             | Type     | Constraints                                      |
| ------------------ | -------- | ------------------------------------------------ |
| `transaction_id`   | TEXT     | PRIMARY KEY                                      |
| `merchant_id`      | TEXT     | NOT NULL, FOREIGN KEY → `merchants(merchant_id)` |
| `input_type`       | TEXT     | CHECK IN (`pos_tap`, `voice`, `manual`)          |
| `amount_zar`       | REAL     | NOT NULL                                         |
| `payment_method`   | TEXT     | CHECK IN (`cash`, `digital`)                     |
| `transaction_date` | DATETIME | DEFAULT CURRENT_TIMESTAMP                        |

**Notes:** `input_type` including `voice` suggests a voice-logging capture path is planned — worth confirming this is intentional for V1.0.0 or a forward-looking placeholder. There is currently no `source_id` linking a transaction back to a `data_sources` row (see below).

### 2.3 `data_sources`

| Column        | Type     | Constraints                                        |
| ------------- | -------- | -------------------------------------------------- |
| `source_id`   | TEXT     | PRIMARY KEY                                        |
| `source_name` | TEXT     | NOT NULL                                           |
| `source_type` | TEXT     | CHECK IN (`pos`, `bank`, `manual`, `online_store`) |
| `created_at`  | DATETIME | DEFAULT CURRENT_TIMESTAMP                          |

**Notes:** This table is not yet referenced by a foreign key from `transactions`. As it stands, `data_sources` is defined but structurally disconnected from the rest of the schema — see Open Items below.

### 2.4 `financial_snapshots`

| Column                    | Type     | Constraints                                      |
| ------------------------- | -------- | ------------------------------------------------ |
| `snapshot_id`             | TEXT     | PRIMARY KEY                                      |
| `merchant_id`             | TEXT     | NOT NULL, FOREIGN KEY → `merchants(merchant_id)` |
| `period_start`            | DATE     | NOT NULL                                         |
| `period_end`              | DATE     | NOT NULL, CHECK (`period_end >= period_start`)   |
| `total_revenue_zar`       | REAL     | NOT NULL, CHECK (>= 0)                           |
| `transaction_count`       | INTEGER  | NOT NULL, CHECK (>= 0)                           |
| `average_transaction_zar` | REAL     | NOT NULL, CHECK (>= 0)                           |
| `cash_revenue_zar`        | REAL     | NOT NULL, CHECK (>= 0)                           |
| `digital_revenue_zar`     | REAL     | NOT NULL, CHECK (>= 0)                           |
| `revenue_growth_pct`      | REAL     | —                                                |
| `revenue_volatility`      | REAL     | —                                                |
| `created_at`              | DATETIME | DEFAULT CURRENT_TIMESTAMP                        |

**Notes:** This table is effectively the BI engine's output store — a pre-computed, periodized rollup per merchant, rather than something calculated live on every request. This is a good design call: it means the API layer can serve score-supporting data fast (read a row) instead of recomputing aggregates on every call. It implies the BI engine's job is to _populate_ `financial_snapshots` on a schedule or trigger, not just answer live queries.

---

## 3. Entity Relationship Summary

```
merchants (1) ───< (many) transactions
merchants (1) ───< (many) financial_snapshots
data_sources                                    ← not yet linked (orphaned table)
```

---

## 4. Requirements by Layer

### 4.1 Database Layer

| ID   | Requirement                                                                                                                 | Status                                                            |
| ---- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| DB-1 | System shall store merchant records with a unique identifier, business name, and optional location.                         | Implemented                                                       |
| DB-2 | System shall store transaction records linked to a merchant, capturing input method, amount, payment method, and timestamp. | Implemented                                                       |
| DB-3 | System shall enforce referential integrity between transactions and merchants via foreign key.                              | Implemented                                                       |
| DB-4 | System shall store a catalog of data sources with a defined type taxonomy.                                                  | Implemented (table only)                                          |
| DB-5 | Transactions shall be traceable to the data source that produced them.                                                      | Not yet implemented — no FK from `transactions` to `data_sources` |
| DB-6 | System shall store periodized financial snapshots per merchant for use by the BI engine and API layer.                      | Implemented                                                       |
| DB-7 | Snapshot values shall be constrained to non-negative and internally consistent (e.g. `period_end >= period_start`).         | Implemented                                                       |
| DB-8 | Merchant authentication data (credentials) shall be stored securely.                                                        | Not yet implemented — no auth fields present                      |

### 4.2 Validation Layer (FastAPI + Pydantic) — Not Yet Built

| ID    | Requirement                                                                                                                                                                                                                                                                            | Status  |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| VAL-1 | System shall define a Pydantic model for `MerchantCreate` matching the `merchants` schema.                                                                                                                                                                                             | Pending |
| VAL-2 | System shall define a Pydantic model for `TransactionCreate`, enforcing `input_type` and `payment_method` against the same CHECK-constrained value sets as the database.                                                                                                               | Pending |
| VAL-3 | System shall define a Pydantic model for `DataSourceCreate` matching the `data_sources` schema.                                                                                                                                                                                        | Pending |
| VAL-4 | System shall define response models for `FinancialSnapshot` records served to the API layer.                                                                                                                                                                                           | Pending |
| VAL-5 | Enum-style fields (`input_type`, `payment_method`, `source_type`) shall be defined as Python `Enum` classes shared between Pydantic models and any seeding/synthetic data code, so the allowed values live in one place, not duplicated between SQL CHECK constraints and Python code. | Pending |

### 4.3 BI Engine (Python) — Not Yet Built

| ID   | Requirement                                                                                                          | Status  |
| ---- | -------------------------------------------------------------------------------------------------------------------- | ------- |
| BI-1 | Engine shall aggregate raw `transactions` rows into `financial_snapshots` for a given merchant and period.           | Pending |
| BI-2 | Engine shall calculate `revenue_growth_pct` by comparing a snapshot period against the prior period of equal length. | Pending |
| BI-3 | Engine shall calculate `revenue_volatility` as a measure of variance in per-transaction or per-period revenue.       | Pending |
| BI-4 | Engine shall combine snapshot metrics into a single deterministic, explainable business score.                       | Pending |
| BI-5 | Engine shall return an insufficient-data state when a merchant has no snapshot covering a minimum required history.  | Pending |

### 4.4 Interface Layer (FastAPI + `/docs`) — Not Yet Built

| ID    | Requirement                                                              | Status  |
| ----- | ------------------------------------------------------------------------ | ------- |
| API-1 | `POST /merchants` — create a merchant.                                   | Pending |
| API-2 | `POST /transactions` — record a transaction.                             | Pending |
| API-3 | `GET /merchants/{id}/transactions` — list a merchant's transactions.     | Pending |
| API-4 | `GET /merchants/{id}/snapshots` — list a merchant's financial snapshots. | Pending |
| API-5 | `GET /merchants/{id}/score` — return the current computed score.         | Pending |
| API-6 | All endpoints documented and testable via `/docs`.                       | Pending |

---

## 5. Open Items Requiring a Decision

1. **`data_sources` is currently orphaned.** Either add `source_id` as a foreign key on `transactions`, or fold `source_type` directly into `transactions` if a full source catalog isn't needed for V1. Worth deciding before the validation layer is built, since the Pydantic `TransactionCreate` model depends on this.
2. **No authentication fields exist on `merchants`.** Confirm whether merchant login is in V1.0.0 scope. If yes, schema needs `email` + `password_hash` (or a separate `credentials` table); if no, this should be explicitly logged as deferred, not just missing.
3. **`voice` as an `input_type`** implies a planned voice-capture feature. Confirm this is intentional for V1 or should be removed from the CHECK constraint until it's actually built, to avoid the API accepting a value nothing yet supports.
4. **`financial_snapshots` population trigger.** Decide whether snapshots are generated on-demand (API call triggers a BI engine run), on a schedule (e.g. nightly job), or both. This affects whether BI-1 is an API-adjacent function or a standalone script.
5. **ID format.** All primary keys are `TEXT` — confirm whether these are UUIDs, and standardize generation (e.g. `uuid4()` at the Pydantic/application layer) so IDs aren't left to be invented ad hoc per insert.

---

## 6. Definition of Done — Database Layer

- [x] All four tables created via `scripts/init_db.py`
- [x] Foreign key constraints active and enforced
- [x] CHECK constraints in place for enum-like fields and non-negative financial values
- [ ] `data_sources` linked to `transactions` (or explicitly descoped)
- [ ] Auth fields added to `merchants` (or explicitly descoped)
- [ ] Seed/test script confirming constraint violations are correctly rejected
