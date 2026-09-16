# ZakaScore — Software Requirements Specification (SRS)

**Release:** V1.0.0
**Author:** Jabulani Mokoena
**Last updated:** 2026-08-22
**Status:** Database and validation layers implemented — BI engine next

---

## 1. Purpose

This document specifies the requirements for ZakaScore V1.0.0 and is maintained in alignment with the as-built system.

It reflects the current database schema, validation models, and automated testing implementation. As the system evolves, this document will be updated to remain consistent with the implemented architecture.

---

## 2. As-Built Database Schema

Four tables are currently defined in SQLite, with foreign keys enforced using `PRAGMA foreign_keys = ON`.

### 2.1 `merchants`

| Column          | Type     | Constraints               |
| --------------- | -------- | ------------------------- |
| `merchant_id`   | TEXT     | PRIMARY KEY               |
| `business_name` | TEXT     | NOT NULL                  |
| `location`      | TEXT     | —                         |
| `created_at`    | DATETIME | DEFAULT CURRENT_TIMESTAMP |

**Notes:** No authentication fields are currently stored at the database level. If merchant authentication remains in scope for V1.0.0, authentication fields or a separate authentication/credentials table will need to be introduced.

### 2.2 `transactions`

| Column             | Type     | Constraints                                      |
| ------------------ | -------- | ------------------------------------------------ |
| `transaction_id`   | TEXT     | PRIMARY KEY                                      |
| `merchant_id`      | TEXT     | NOT NULL, FOREIGN KEY → `merchants(merchant_id)` |
| `input_type`       | TEXT     | CHECK IN (`pos_tap`, `voice`, `manual`)          |
| `amount_zar`       | REAL     | NOT NULL                                         |
| `payment_method`   | TEXT     | CHECK IN (`cash`, `digital`)                     |
| `transaction_date` | DATETIME | DEFAULT CURRENT_TIMESTAMP                        |

**Notes:** `input_type` currently includes `voice`, indicating that voice-based transaction capture is anticipated. The implementation scope of this input method remains an open product decision.

There is currently no `source_id` foreign key connecting transactions to `data_sources`.

### 2.3 `data_sources`

| Column        | Type     | Constraints                                        |
| ------------- | -------- | -------------------------------------------------- |
| `source_id`   | TEXT     | PRIMARY KEY                                        |
| `source_name` | TEXT     | NOT NULL                                           |
| `source_type` | TEXT     | CHECK IN (`pos`, `bank`, `manual`, `online_store`) |
| `created_at`  | DATETIME | DEFAULT CURRENT_TIMESTAMP                          |

**Notes:** The table is currently defined but is not yet referenced by `transactions`.

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

Financial snapshots represent periodized financial information that will support the future BI and scoring layers.

---

## 3. Entity Relationship Summary

```text
merchants (1) ───< (many) transactions

merchants (1) ───< (many) financial_snapshots

data_sources
    │
    └── currently linked to transactions
```

---

## 4. Requirements by Layer

### 4.1 Database Layer

| ID   | Requirement                                                                                                                 | Status                   |
| ---- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| DB-1 | System shall store merchant records with a unique identifier, business name, and optional location.                         | Implemented              |
| DB-2 | System shall store transaction records linked to a merchant, capturing input method, amount, payment method, and timestamp. | Implemented              |
| DB-3 | System shall enforce referential integrity between transactions and merchants via foreign keys.                             | Implemented              |
| DB-4 | System shall store a catalog of data sources with a defined type taxonomy.                                                  | Implemented — table only |
| DB-5 | Transactions shall be traceable to the data source that produced them.                                                      | Pending                  |
| DB-6 | System shall store periodized financial snapshots per merchant for use by the BI engine and future API layer.               | Implemented              |
| DB-7 | Snapshot values shall be constrained to non-negative values and internally consistent dates.                                | Implemented              |
| DB-8 | Merchant authentication data shall be stored securely.                                                                      | Pending / scope decision |

---

### 4.2 Validation Layer — Pydantic

The validation layer has now been implemented using Pydantic models.

The validation layer provides application-level validation before data reaches the database and mirrors important constraints already established at the database level.

| ID    | Requirement                                                                                                             | Status      |
| ----- | ----------------------------------------------------------------------------------------------------------------------- | ----------- |
| VAL-1 | System shall define a Pydantic model for merchant data matching the `merchants` schema.                                 | Implemented |
| VAL-2 | System shall define a Pydantic model for transaction data enforcing valid `input_type` and `payment_method` values.     | Implemented |
| VAL-3 | System shall define a Pydantic model for data source records matching the `data_sources` schema.                        | Implemented |
| VAL-4 | System shall define a Pydantic model for `financial_snapshots`.                                                         | Implemented |
| VAL-5 | Validation shall enforce appropriate business rules such as non-negative financial values and valid constrained values. | Implemented |
| VAL-6 | Enum-style fields shall use centralized Python definitions where appropriate to prevent duplication of allowed values.  | Implemented |

---

### 4.3 Automated Testing

Automated testing has been introduced using Pytest.

The test suite verifies both database functionality and Pydantic validation behaviour.

| ID     | Requirement                                                                     | Status      |
| ------ | ------------------------------------------------------------------------------- | ----------- |
| TEST-1 | Database functionality shall be covered by automated tests.                     | Implemented |
| TEST-2 | Valid Pydantic models shall be accepted.                                        | Implemented |
| TEST-3 | Invalid values shall be rejected according to defined validation rules.         | Implemented |
| TEST-4 | Parameterized tests shall cover common validation rules across multiple fields. | Implemented |
| TEST-5 | The complete test suite shall pass before major development layers are added.   | Implemented |

**Current test result:** 39 tests passing.

```text
39 passed in 0.42s
```

---

### 4.4 BI Engine — Python

The BI engine is the next major development layer.

| ID   | Requirement                                                                                                      | Status  |
| ---- | ---------------------------------------------------------------------------------------------------------------- | ------- |
| BI-1 | Engine shall aggregate raw `transactions` rows into `financial_snapshots` for a given merchant and period.       | Pending |
| BI-2 | Engine shall calculate `revenue_growth_pct` by comparing a snapshot period against the appropriate prior period. | Pending |
| BI-3 | Engine shall calculate `revenue_volatility` using a defined and explainable volatility measure.                  | Pending |
| BI-4 | Engine shall combine relevant financial metrics into a deterministic and explainable business score.             | Pending |
| BI-5 | Engine shall return an insufficient-data state when a merchant does not have the minimum required history.       | Pending |
| BI-6 | Engine shall produce business metrics and insights that can be consumed by future interfaces.                    | Pending |

The BI engine is intended to transform validated operational and financial data into useful business intelligence rather than limiting ZakaScore to a single credit score.

---

### 4.5 Interface Layer — FastAPI

The API layer has not yet been implemented.

| ID    | Requirement                                                          | Status  |
| ----- | -------------------------------------------------------------------- | ------- |
| API-1 | `POST /merchants` — create a merchant.                               | Pending |
| API-2 | `POST /transactions` — record a transaction.                         | Pending |
| API-3 | `GET /merchants/{id}/transactions` — list merchant transactions.     | Pending |
| API-4 | `GET /merchants/{id}/snapshots` — list merchant financial snapshots. | Pending |
| API-5 | `GET /merchants/{id}/score` — return the current computed score.     | Pending |
| API-6 | All endpoints shall be documented and testable through `/docs`.      | Pending |

---

## 5. Open Items Requiring a Decision

### 5.1 `data_sources` relationship — Resolved

The `data_sources` table is linked to `transactions` through `source_id` and a foreign key relationship.

Transactions can therefore be traced back to the data source that produced them.

No further schema decision is currently required for this relationship.

### 5.2 Authentication

The database currently contains no authentication credentials.

A decision is required on whether authentication belongs in V1.0.0 or should be deferred to a later release.

If authentication is required, credentials should be stored separately from core merchant information where appropriate, with passwords represented only as secure password hashes.

### 5.3 `voice` input type

The `voice` input type currently exists in the transaction schema.

A decision is required on whether voice-based transaction capture is part of V1.0.0 or represents a future interface capability.

### 5.4 Financial snapshot generation

A decision is required on how financial snapshots will be generated:

- on demand,
- on a scheduled basis,
- or through a combination of scheduled and on-demand processing.

This will determine how the BI engine is integrated with the application.

### 5.5 ID format

Primary keys currently use `TEXT`.

The application should eventually standardize ID generation, potentially using UUIDs, so identifiers are generated consistently rather than manually.

---

## 6. Definition of Done — Current Foundation

### Database

- [x] All four tables created through `scripts/init_db.py`
- [x] Foreign key constraints active and enforced
- [x] CHECK constraints implemented for constrained values
- [x] Non-negative financial constraints implemented
- [x] data_sources linked to transactions or explicitly descoped
- [ ] Authentication requirements resolved
- [x] Database functionality covered by automated tests

### Validation

- [x] Pydantic models implemented
- [x] Application-level validation implemented
- [x] Valid model construction tested
- [x] Invalid values tested
- [x] Parameterized validation tests implemented

### Testing

- [x] Automated test suite established
- [x] Database tests passing
- [x] Pydantic validation tests passing
- [x] 39 automated tests currently passing

---

## 7. Next Development Stage

With the database, schemas, validation layer, and initial automated testing foundation in place, the next major development stage is the **ZakaScore BI Engine**.

The BI engine will transform validated transaction data into:

- financial metrics
- performance indicators
- business insights
- financial snapshots
- and eventually the ZakaScore business/credit profile.

The objective is to build ZakaScore as a broader **financial intelligence platform for SMEs**, rather than as a credit score alone.

**Status: Foundation complete. BI engine next.**
