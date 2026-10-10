<p align="center">
  <img src="frontend/public/logo.png" alt="ZakaScore Logo" width="140">
</p>

<h1 align="center">ZakaScore</h1>

<p align="center">
  Financial intelligence for businesses with more data than they have records.
</p>

ZakaScore is a localized financial data ingestion and alternative credit scoring engine designed for the South African SME ecosystem.

It turns everyday business activity into structured financial data, business insights, and alternative credit signals — helping create a clearer financial profile for businesses that may have limited traditional records.

---

## Core Features

### Multi-Source Financial Data

Designed to collect and normalize business activity from different sources, including:

- POS systems
- Online stores
- Banking and payment data
- CSV and structured financial data
- Dashboard/PWA sale logging

### Financial Intelligence

Transforms business data into useful financial metrics and performance indicators, including:

- Revenue analysis
- Growth trends
- Transaction insights
- Business performance metrics
- Financial statistics

### Alternative Credit Scoring

Generates an alternative financial score based on the underlying business data and calculated metrics.

The goal is not simply to produce a number, but to provide the financial context behind it.

### Business Dashboard

A web dashboard provides a visual interface for exploring financial performance, metrics, and scoring results.

---

## Development Map

```text
                    ZakaScore
                        │
          ┌─────────────┴─────────────┐
          │                           │
    Data Foundation             Intelligence
          │                           │
   Data ingestion              Financial metrics
   Data validation              Business insights
   Data sources                 Alternative scoring
          │                           │
          └─────────────┬─────────────┘
                        │
                   Product Layer
                        │
                  Web Dashboard
                        │
                Deployment & V1
```

### Current — V1

- [x] Core data architecture
- [x] Financial data models
- [x] Data validation
- [x] Financial metrics
- [x] Business intelligence
- [x] Alternative scoring
- [x] Authenticated transaction API
- [x] LLM-powered data parsing
- [x] Web dashboard
- [x] Neon Auth accounts and business onboarding
- [x] Installable PWA chatbot sale logging with offline sync
- [x] Automated testing
- [x] CI pipeline

### Next

- [ ] Additional data integrations
- [ ] Banking and payment integrations
- [ ] Online business integrations
- [x] Authenticated PWA transaction logging
- [ ] Production deployment
- [x] Production database
- [ ] Data quality improvements
- [ ] Production hardening

---

## Architecture & Stack

### Architecture

| Layer          | Responsibility                                                                  |
| -------------- | ------------------------------------------------------------------------------- |
| Data Sources   | Business activity from POS, online stores, financial records, and other sources |
| Ingestion      | Receives and processes incoming business data                                   |
| Validation     | Structures and validates incoming data                                          |
| Financial Data | Stores normalized merchant and financial information                            |
| Intelligence   | Calculates financial metrics, business insights, and alternative scores         |
| Dashboard      | Presents financial information and scoring results                              |

### Stack

| Area            | Technology          |
| --------------- | ------------------- |
| Backend         | Python, FastAPI     |
| Frontend        | Next.js             |
| Database        | PostgreSQL          |
| Data Validation | Pydantic            |
| Testing         | Pytest              |
| CI              | GitHub Actions      |
| AI              | LLM-powered parsing |
| Version Control | Git, GitHub         |

---

## Project Documentation

Detailed documentation covers the project's architecture, data model, API design, development decisions, and implementation details.

**Documentation:** [Architecture](backend/docs/architecture.md)

---

**Built by Jabulani Mokoena**
