# ZakaScore

**ZakaScore is a financial intelligence platform being built for small and medium-sized businesses in South Africa.**

The platform is designed to help businesses turn their financial and operational data into useful business insights, while creating a structured financial profile that can potentially support access to credit.

ZakaScore is being developed with the needs of small businesses and sole entrepreneurs in mind, particularly businesses that may not have access to sophisticated financial analytics.

## Current Development

ZakaScore is currently focused on building a reliable data foundation for the platform.

Current work includes:

- SQLite database architecture
- Structured financial data schemas
- Pydantic data models
- Data validation
- Automated testing
- Merchant data management
- Financial snapshot modelling
- Data source modelling

The BI engine is the next major development stage.

## Technology Stack

- **Python** — core application logic
- **SQLite** — database
- **Pydantic** — data schemas and validation
- **Pytest** — automated testing

Additional data-analysis and visualization technologies will be introduced as the BI engine develops.

## Data Architecture

The current architecture is designed around the business as the central entity.

Core concepts include:

- **Merchants** — businesses using ZakaScore
- **Financial Snapshots** — structured representations of business financial performance over a period
- **Data Sources** — records of where financial data originates
- **Transactions and financial data** — operational information that can eventually feed the analytics layer

The schema is designed to support multiple data sources and future expansion without tying the platform to a single method of data collection.

## Testing

ZakaScore uses automated tests to protect the data layer and validation rules.

Tests currently cover:

- Database functionality
- Pydantic model validation
- Valid model construction
- Invalid data handling
- Parameterized validation cases

Run the test suite with:

```bash
python -m pytest
```

## Development Roadmap

### Foundation

- [x] Database architecture
- [x] Core schemas
- [x] Pydantic models
- [x] Automated validation tests

### BI Engine

- [x] Financial metric calculations
- [x] Revenue and growth analysis
- [x] Business performance indicators
- [x] Automated business insights
- [ ] Data visualization

### Data Integration

- [ ] Transaction data ingestion
- [ ] External data sources
- [ ] Banking and payment integrations
- [ ] Online business integrations
- [ ] WhatsApp-based data interaction

### Financial Intelligence

- [ ] Business financial profiles
- [ ] Credit scoring engine
- [ ] Credit-readiness insights
- [ ] Decision-support tools

## Vision

ZakaScore aims to give small businesses access to financial intelligence that is often available only to larger, more digitally mature businesses.

A business should be able to understand its performance, identify opportunities, make better decisions, and build a credible financial history regardless of whether it operates through a sophisticated online platform or primarily through WhatsApp and direct customer interactions.

**Built by Flexure.**
