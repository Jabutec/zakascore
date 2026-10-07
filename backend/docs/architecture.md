# ZakaScore Architecture

ZakaScore is a localized financial data ingestion and alternative credit scoring engine designed for the South African SME ecosystem.

## System Architecture

ZakaScore uses a Next.js frontend, a FastAPI backend, and PostgreSQL hosted on Neon.

| Layer           | Technology                   | Responsibility                            |
| --------------- | ---------------------------- | ----------------------------------------- |
| Frontend        | Next.js, React, Tailwind CSS | Dashboard and user interface              |
| Backend         | FastAPI, Python              | API, validation, business logic           |
| Database        | PostgreSQL, Neon             | Persistent application data               |
| Database Driver | Psycopg 3                    | Backend-to-database connection            |
| Testing         | Pytest                       | Automated backend testing                 |
| CI              | GitHub Actions               | Automated test execution                  |
| Ingestion       | Authenticated PWA API        | Business data input                       |

The frontend communicates with FastAPI through HTTP/JSON. The backend is responsible for communicating with PostgreSQL.

## Backend

The FastAPI backend is responsible for:

- API endpoints
- Request validation
- Data ingestion
- Authenticated PWA transaction logging
- Business intelligence calculations
- Financial metrics
- Credit scoring
- PostgreSQL database access

The backend is organized into separate areas for APIs, services, BI logic, validation, database access, and tests.

## Database

ZakaScore uses PostgreSQL hosted on Neon.

The main database entities are:

| Table                 | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `merchants`           | Businesses using ZakaScore                           |
| `merchant_users`      | Users associated with merchants and their roles      |
| `stores`              | Stores or operating locations belonging to merchants |
| `data_sources`        | Sources from which business data is received         |
| `offerings`           | Products or services sold by a store                 |
| `transactions`        | Normalized business transactions                     |
| `financial_snapshots` | Calculated financial metrics for specific periods    |

### Relationships

A merchant can have multiple users and stores. A store can have multiple data sources, offerings, and transactions.

`merchant_users` handles the relationship between application users and merchants.

`data_sources` identifies where business data originated, such as the PWA, POS systems,
CSV files, or online stores. Each store created through dashboard onboarding receives a
PWA source.

## Data Sources

ZakaScore is designed to support multiple sources of business data.

| Source Type           | Example                    |
| --------------------- | -------------------------- |
| `pos`                 | Point-of-sale system       |
| `bank_statement`      | Bank transaction data      |
| `accounting_software` | Accounting platform        |
| `online_store`        | E-commerce platform        |
| `pwa`                  | Dashboard/PWA sale logging |
| `csv`                 | Imported business data     |
| `manual`              | Manually entered data      |

The PWA records sales through an authenticated API; the server resolves the store's
source rather than accepting a source identifier from the client. On-device parsing is
reviewed by the user before submission. Confirmed offline sales are queued locally with
stable idempotency keys and retried when the device reconnects.

## Transactions

Transactions represent normalized business activity.

A transaction can contain:

| Field              | Purpose                                      |
| ------------------ | -------------------------------------------- |
| `transaction_id`   | Unique transaction identifier                |
| `client_txn_id`    | Client-generated idempotency key per sale    |
| `store_id`         | Store associated with the transaction        |
| `source_id`        | Data source that produced the transaction    |
| `offering_id`      | Product or service involved                  |
| `quantity`         | Quantity sold                                |
| `amount_zar`       | Transaction value                            |
| `payment_method`   | Cash or digital                              |
| `input_type`       | How the transaction entered the system       |
| `transaction_date` | Date and time of the transaction             |
| `is_voided`        | Indicates whether the transaction was voided |

## Business Intelligence

The BI layer converts transaction data into useful business metrics.

The dashboard currently exposes:

| Endpoint                   | Purpose                  |
| -------------------------- | ------------------------ |
| `GET /api/transactions`    | Recent transactions      |
| `POST /transactions`       | Log a PWA transaction    |
| `GET /api/revenue`         | Revenue data             |
| `GET /api/top-offerings`   | Top-performing offerings |
| `GET /api/overview`        | Business overview        |
| `GET /api/payment-methods` | Payment method breakdown |
| `GET /api/credit-score`    | Merchant credit score    |

Financial snapshots can contain metrics such as revenue, transaction count, average transaction value, cash revenue, digital revenue, revenue growth, and revenue volatility.

## Credit Scoring

ZakaScore includes an alternative credit scoring engine based on business activity and financial indicators.

The scoring system uses structured financial information rather than relying only on traditional credit records.

The scoring logic is kept in the backend and is independent of the frontend.

## PWA Transaction Logging

The authenticated `POST /transactions` endpoint accepts a store, client-generated
idempotency key, amount, payment method, and optional offering, quantity, and transaction
date. The backend checks employee-level store access, resolves the store's PWA source,
validates the transaction, and inserts it once per `(store_id, client_txn_id)`. Repeated
requests with the same key return the original transaction.

## Authentication

Neon Auth identifies each team member with an individual account. The `merchant_users`
membership links a user's Neon Auth ID to an authorized business. One-time invite codes
let additional accounts join as employees; they do not share the owner's credentials.

Authentication and authorization are separate concerns. Authentication identifies the user, while authorization determines which merchant and stores that user can access.

## Frontend

The frontend is built with Next.js, React, and Tailwind CSS.

The dashboard currently displays:

- Revenue
- Business overview
- Recent transactions
- Top offerings
- Payment methods
- Credit score
- The selected authorized business and its stores

The installable PWA includes chatbot-assisted sale entry, review-before-save, and an
offline queue. The frontend communicates with FastAPI and does not connect directly to
PostgreSQL.

Loading, empty, and API error states are handled by the dashboard.

## Testing

The backend uses pytest for automated testing.

Current test areas include:

- API routes
- Business intelligence
- Financial indicators
- Insights
- Validation
- Visualization

GitHub Actions runs automated backend tests when changes are pushed through the repository workflow.

## Repository Structure

```text
zakascore/
├── backend/
│   ├── api/
│   ├── bi/
│   ├── config/
│   ├── database/
│   ├── docs/
│   ├── scripts/
│   ├── services/
│   ├── tests/
│   ├── validation/
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── package.json
│
├── .github/
│   └── workflows/
│
└── README.md
```

## Security Principles

- Database credentials remain server-side.
- Secrets must not be committed to Git.
- The frontend must not connect directly to PostgreSQL.
- Business authorization is handled by the backend.
- Destructive operations such as permanent data deletion should require explicit backend-controlled workflows.

## Architecture Direction

The system is designed so additional data sources can be added without changing the core merchant, store, and transaction model.

The current development path is:

1. PostgreSQL migration
2. Frontend and API integration
3. PWA transaction logging
4. End-to-end testing
5. Authentication integration
6. Production deployment
