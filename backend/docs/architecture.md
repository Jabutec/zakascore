# ZakaScore — System Requirements Specification

**Release:** V1.0.0
**Author:** Jabulani Mokoena
**Last updated:** 2026-08-22
**Status:** Database, validation, and automated testing layers implemented — BI engine next

---

## 1. System Purpose

ZakaScore is a financial intelligence and business analytics engine for South African SMEs.

V1.0.0 is a **backend-first system** focused on establishing the core data and analytics foundation:

**structured business data → validated data → financial metrics → business insights → deterministic scoring**

The system is designed to eventually help small businesses understand their financial performance, make better business decisions, and build a structured financial profile that may support future credit-readiness and lending use cases.

**V1.0.0 is not:**

- a lender
- a machine-learning credit scoring system
- a frontend application
- a live banking/payment integration platform

It is the engineered foundation that future interfaces, integrations, and intelligence capabilities will build upon.

---

## 2. Architecture Overview

ZakaScore is composed of four primary layers, developed in the following order:

```text
┌─────────────────────────────────────────────────────┐
│ 4. INTERFACE — FastAPI                              │
│                                                     │
│ Exposes validated business data, financial         │
│ metrics, insights, and scoring functionality.       │
├─────────────────────────────────────────────────────┤
│ 3. BI ENGINE — Python                               │
│                                                     │
│ Consumes validated business data and produces       │
│ financial metrics, insights, snapshots, and         │
│ deterministic scoring outputs.                      │
├─────────────────────────────────────────────────────┤
│ 2. VALIDATION — Pydantic                            │
│                                                     │
│ Defines valid data structures and enforces          │
│ application-level business rules before data       │
│ reaches the database or analytics layer.            │
├─────────────────────────────────────────────────────┤
│ 1. DATABASE — SQLite                                │
│                                                     │
│ Schema-first storage for merchants, transactions,   │
│ data sources, and financial snapshots.              │
└─────────────────────────────────────────────────────┘
```

### Design principle

Each layer should have a clearly defined responsibility.

- The **database** provides persistence and structural integrity.
- **Pydantic** provides application-level validation.
- The **BI engine** performs calculations and generates financial intelligence.
- The **API** exposes functionality without embedding business calculations directly into endpoint handlers.

The architecture should allow individual implementation details to evolve without requiring a complete rewrite of the system.

For example:

- SQLite may eventually be replaced by PostgreSQL.
- Synthetic/manual data may eventually be supplemented by external integrations.
- New interfaces may consume the same BI engine without duplicating its logic.

---

## 3. Components & Requirements

### 3.1 Database Layer

**Purpose:** Persist merchant, transaction, data-source, and financial-snapshot records in a structured schema.

| ID   | Requirement                                                                                                                               | Priority | Status      |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------- |
| DB-1 | System shall store merchant records with a unique identifier, business name, optional location, and creation timestamp.                   | Must     | Implemented |
| DB-2 | System shall store transaction records associated with a merchant.                                                                        | Must     | Implemented |
| DB-3 | Transactions shall record input type, transaction amount, payment method, source, and timestamp.                                          | Must     | Implemented |
| DB-4 | System shall maintain a catalog of data sources with a defined source taxonomy.                                                           | Must     | Implemented |
| DB-5 | Transactions shall be traceable to their originating data source through a foreign key relationship.                                      | Must     | Implemented |
| DB-6 | Foreign key constraints shall enforce relationships between merchants, transactions, financial snapshots, and data sources where defined. | Must     | Implemented |
| DB-7 | System shall store periodized financial snapshots associated with merchants.                                                              | Must     | Implemented |
| DB-8 | Financial snapshot values shall enforce non-negative financial constraints and valid reporting periods.                                   | Must     | Implemented |
| DB-9 | Schema design should support eventual migration from SQLite to a production relational database.                                          | Should   | Ongoing     |

**Definition of Done:** The database schema is created through the initialization scripts, relationships and constraints are enforced, and automated tests verify database functionality.

---

### 3.2 Validation Layer — Pydantic

**Purpose:** Ensure application data conforms to the defined schema and business rules before being processed further.

| ID    | Requirement                                                                                        | Priority | Status      |
| ----- | -------------------------------------------------------------------------------------------------- | -------- | ----------- |
| VAL-1 | System shall define Pydantic models for merchant data.                                             | Must     | Implemented |
| VAL-2 | System shall define Pydantic models for transaction data.                                          | Must     | Implemented |
| VAL-3 | System shall define Pydantic models for data-source records.                                       | Must     | Implemented |
| VAL-4 | System shall define Pydantic models for financial snapshots.                                       | Must     | Implemented |
| VAL-5 | Constrained fields shall reject invalid values such as unsupported payment methods or input types. | Must     | Implemented |
| VAL-6 | Financial values requiring non-negative constraints shall reject invalid negative values.          | Must     | Implemented |
| VAL-7 | Validation rules shall be covered by automated tests.                                              | Must     | Implemented |

The validation layer acts as the application-level contract between incoming data and the rest of the system.

**Definition of Done:** Core Pydantic models are implemented, validation rules are enforced, and automated tests cover valid and invalid inputs.

---

### 3.3 Automated Testing

**Purpose:** Protect the database and validation foundation as ZakaScore evolves.

| ID     | Requirement                                                                                            | Priority | Status      |
| ------ | ------------------------------------------------------------------------------------------------------ | -------- | ----------- |
| TEST-1 | Database functionality shall be covered by automated tests.                                            | Must     | Implemented |
| TEST-2 | Valid Pydantic models shall be accepted.                                                               | Must     | Implemented |
| TEST-3 | Invalid values shall be rejected according to defined validation rules.                                | Must     | Implemented |
| TEST-4 | Parameterized tests shall be used where the same validation rule applies to multiple fields or values. | Should   | Implemented |
| TEST-5 | The complete automated test suite shall pass before major development layers are introduced.           | Must     | Implemented |

**Current baseline:**

```text
39 tests passed
```

The testing foundation will continue to expand as the BI engine and API layers are implemented.

---

### 3.4 BI Engine — Python

**Purpose:** Transform validated business data into useful financial metrics, insights, and scoring outputs.

| ID    | Requirement                                                                                                        | Priority | Status  |
| ----- | ------------------------------------------------------------------------------------------------------------------ | -------- | ------- |
| BI-1  | Engine shall aggregate transaction data into financial metrics for a merchant and defined reporting period.        | Must     | Pending |
| BI-2  | Engine shall calculate revenue and transaction-volume metrics.                                                     | Must     | Pending |
| BI-3  | Engine shall calculate performance and consistency metrics.                                                        | Must     | Pending |
| BI-4  | Engine shall calculate revenue growth between comparable reporting periods.                                        | Must     | Pending |
| BI-5  | Engine shall calculate an explainable measure of financial volatility.                                             | Must     | Pending |
| BI-6  | Engine shall generate business insights from calculated metrics.                                                   | Must     | Pending |
| BI-7  | Engine shall combine defined metrics into a deterministic and explainable score.                                   | Must     | Pending |
| BI-8  | Engine shall return an insufficient-data state when available history does not meet the defined minimum threshold. | Must     | Pending |
| BI-9  | BI calculations shall be implemented independently from FastAPI endpoint logic.                                    | Must     | Pending |
| BI-10 | BI logic shall be covered by automated tests using representative business scenarios.                              | Must     | Pending |

The BI engine is not intended to produce a score alone. Metrics and insights are first-class outputs of the system.

**Definition of Done:** The BI engine has documented calculations, produces meaningful metrics and insights, implements an explainable scoring methodology, and passes automated tests across representative business scenarios.

---

### 3.5 Interface Layer — FastAPI

**Purpose:** Provide a future programmatic interface to ZakaScore functionality.

The API layer has not yet been implemented.

| ID    | Requirement                                                                                   | Priority | Status  |
| ----- | --------------------------------------------------------------------------------------------- | -------- | ------- |
| API-1 | System shall expose an endpoint for creating merchants.                                       | Must     | Pending |
| API-2 | System shall expose an endpoint for recording transactions.                                   | Must     | Pending |
| API-3 | System shall expose an endpoint for retrieving merchant transactions.                         | Must     | Pending |
| API-4 | System shall expose an endpoint for retrieving financial snapshots.                           | Must     | Pending |
| API-5 | System shall expose an endpoint for retrieving business metrics and insights.                 | Must     | Pending |
| API-6 | System shall expose an endpoint for retrieving the current ZakaScore.                         | Must     | Pending |
| API-7 | API endpoints shall use Pydantic request and response models.                                 | Must     | Pending |
| API-8 | Endpoints shall be documented and testable through FastAPI's automatically generated `/docs`. | Must     | Pending |
| API-9 | Endpoints shall return appropriate HTTP status codes for successful and failed operations.    | Must     | Pending |

---

## 4. Data Strategy

ZakaScore is designed to be **source-agnostic**.

The database currently supports the concept of multiple data sources, allowing transactions to be associated with their originating source.

Potential future sources may include:

- POS systems
- bank data
- manual entry
- online stores
- WhatsApp-based transaction capture
- other payment or business systems

V1.0.0 does not require live integrations with these external systems.

The objective at this stage is to establish a data model capable of supporting them later without requiring a fundamental redesign.

---

## 5. Non-Functional Requirements

| Category       | Requirement                                                                                                             |
| -------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Data integrity | Foreign key constraints shall be enforced at the database level.                                                        |
| Validation     | Application-level validation shall be performed using Pydantic.                                                         |
| Testability    | Database, validation, and BI logic shall be independently testable.                                                     |
| Explainability | Scoring calculations shall be deterministic and explainable in V1.0.0.                                                  |
| Security       | No plaintext passwords, API keys, or other secrets shall be stored in source code.                                      |
| Portability    | Application logic should avoid unnecessary SQLite-specific dependencies that would prevent future PostgreSQL migration. |
| Performance    | BI calculations should remain practical for small-business transaction datasets.                                        |
| Documentation  | System documentation shall remain synchronized with the as-built architecture and implementation.                       |

---

## 6. Explicit Exclusions — V1.0.0

To maintain a realistic scope, V1.0.0 excludes:

- Live bank integrations
- Live payment-provider integrations
- Yoco integration
- PayFast integration
- Ozow integration
- Stitch/Mono integration
- Machine-learning credit scoring
- A production frontend
- Full authentication and session management
- Lender-facing dashboards
- Automated lending decisions

These capabilities may be considered in future versions.

---

## 7. Open Engineering Decisions

### 7.1 Score scale

The final score scale must be defined before the scoring formula is finalized.

Potential approaches include a simple 0–100 scale or a more traditional credit-score-style range.

### 7.2 Minimum data threshold

The minimum transaction history required before ZakaScore can produce a meaningful score must be defined.

The threshold may consider:

- number of transactions
- number of reporting periods
- number of days of history

### 7.3 Scoring methodology

The relative contribution of different metrics such as volume, consistency, growth, and recency must be documented before the scoring engine is finalized.

The formula should remain deterministic and explainable in V1.0.0.

### 7.4 Synthetic/test data

Representative business scenarios should be established for BI testing, such as:

- steady business
- growing business
- declining business
- seasonal business
- sparse/new business

These scenarios will help ensure that scoring and insight generation behave sensibly across different operating patterns.

### 7.5 Snapshot generation

A decision is required on whether financial snapshots are generated:

- on demand,
- on a schedule,
- or through a combination of both.

---

## 8. Definition of Done — V1.0.0

V1.0.0 will be considered complete when:

- [x] Database schema is implemented and constraint-tested
- [x] Core Pydantic validation models are implemented
- [x] Automated database and validation tests are passing
- [ ] BI engine calculates required financial metrics
- [ ] BI engine generates business insights
- [ ] Deterministic scoring methodology is documented and implemented
- [ ] BI engine is covered by automated tests
- [ ] FastAPI interface is implemented
- [ ] API endpoints are documented through `/docs`
- [ ] API request and response models use Pydantic
- [ ] No hardcoded secrets or credentials exist in the repository
- [ ] System requirements documentation reflects the actual as-built architecture

---

## 9. Current Development Position

The foundational layers of ZakaScore are now complete:

```text
Database
   ↓
Pydantic Validation
   ↓
Automated Testing
   ↓
BI Engine       ← NEXT
   ↓
FastAPI
```

The next major development stage is therefore the **ZakaScore BI Engine**, where validated transaction and financial data will be transformed into metrics, insights, and eventually the ZakaScore itself.
