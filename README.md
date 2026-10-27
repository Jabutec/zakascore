<p align="center">
  <img src="frontend/public/logo.png" alt="ZakaScore Logo" width="140">
</p>

<h1 align="center">ZakaScore</h1>

<p align="center">
  Financial intelligence for businesses with more data than they have records.
</p>

ZakaScore helps small South African businesses turn everyday sales into a clear financial record and a credit profile they can take to suppliers and lenders. It works for the money that normally leaves no trail: cash, EFTs, cash send and card.

A merchant logs sales in a chat, adds bank messages and receipts when they have them, and watches a score build from their own activity. The score comes with the reasons behind it and specific tips for improving it.

|                               |                                                                            |
| ----------------------------- | -------------------------------------------------------------------------- |
| **For merchants**             | Record every sale, see how the business is trading, build a credit profile |
| **For suppliers and lenders** | A neutral, consistent view of a cash-heavy business (planned)              |
| **Stack**                     | Python and FastAPI, Next.js, PostgreSQL on Neon, Neon Auth                 |
| **Status**                    | V1 launched. See [Roadmap](#roadmap)                                       |

**Contents:** [Business](#part-1-business) · [Scale](#part-2-scale) · [Developer guide](#part-3-developer-guide) · [Roadmap](#roadmap)

---

# Part 1: Business

## The problem

Small traders earn real money but cannot prove it. Their income is split across cash, card, EFT and cash send, nobody keeps one record of it, and lenders and suppliers cannot verify any of it. Credit is refused, priced for the unknown, or limited to one supplier's goodwill.

Public estimates point the same way (2022 to 2026, re-check before external use):

- The SME funding gap is put at over R350 billion, and commentators describe it as a visibility problem more than a shortage of capital.
- About 56% of MSMEs are unregistered, so they depend on the owner's personal bankability.
- Roughly nine in ten South African transactions were still cash in 2023.
- There were about 1.75 million informal businesses and 710,000 small formal ones in 2022, and 3.57 million people working in the informal sector in the latest labour survey.
- Stock on payment terms is the credit small shops want most, and many fear formal financial services.

## Who it is for

**Primary user:** owners of cash-heavy micro businesses such as salons, small supermarkets and thrift stores, trading roughly R1,000 a week or more.

**Second side, planned:** suppliers, wholesalers and lenders who want to extend credit to these merchants but cannot assess them cheaply.

## What a merchant can do today

- **Log a sale in a chat.** Type "2 shirts, R300, cash" and the app prepares it for review. The chat asks for anything missing: the amount, cash or digital, what was sold, how many.
- **Add evidence.** Upload a bank screenshot, a receipt, or paste a money-in SMS. The app reads it on the phone, keeps only the money details, and asks if anything is unclear.
- **Work offline.** Sales are saved on the device and sync when the connection returns. The app installs to the home screen.
- **See the business.** A dashboard shows revenue, transaction volume, top offerings, payment channels and signals.
- **See the credit profile.** The score, what drives it, tips ranked by impact, the week in progress, and a plain range for next week's takings.
- **Invite a team.** Owners and admins create one-time codes for employees.

## How the score works

The score is built only from recorded sales, over complete Monday to Sunday weeks in South African time.

| Factor              | Weight | What it measures                                                  |
| ------------------- | ------ | ----------------------------------------------------------------- |
| Weekly stability    | 35%    | How evenly weekly takings hold. Weeks with no sales count as zero |
| Growth              | 25%    | Recent weeks compared with earlier weeks                          |
| Revenue level       | 25%    | The typical (median) week against a benchmark                     |
| Trading consistency | 15%    | The share of weeks with sales on at least three days              |

- A merchant needs **4 complete weeks** before a score is shown, and the score uses at most the latest 12. A thin file is "not scored yet", never a low score.
- A partial first week is skipped, and the week in progress is never scored.
- Each score carries a maturity label: early (4 to 7 weeks), growing (8 to 11), established (12).
- **Weights and the revenue benchmark are placeholders.** Nothing is calibrated against repayment outcomes yet, so the score describes business activity and health. It does not predict whether a loan would be repaid, and the product says so.

## Plans

| Plan         | Includes                                                                                                               |
| ------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **Insights** | Logging, uploads, dashboard, the score and its band, one tip, the week in progress                                     |
| **Full**     | Everything above plus the score breakdown, all tips, supporting figures, the forecast range and four-week score change |

Plan limits are enforced on the server. Merchants on the Insights plan never receive the Full fields, so there is nothing to unlock in a browser's network tab. Logging is free on every plan because the data is the foundation of the product.

## Business model

|                       |                                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Customer**          | The merchant is the user. Suppliers and lenders are the second side                                                                         |
| **Value**             | See every rand coming in, cash included, and build a credit score you can take to suppliers or lenders                                      |
| **Revenue**           | A merchant subscription (Full plan) and, later, verification fees from suppliers and lenders                                                |
| **Channels**          | Merchant communities, word of mouth, and wholesalers who onboard their own customers                                                        |
| **Moat (hypothesis)** | A neutral record that combines cash and digital activity with trust labels. A merchant's history becomes harder to walk away from over time |
| **Key metric**        | Merchants still logging after four weeks                                                                                                    |

## Principles

- **Money only.** Uploads are read on the device. Only the amount, date, payment type and a reference are kept. Names, account numbers and balances are discarded, and images are not stored.
- **Money in only.** The chat turns away expenses and money-out messages.
- **Sales cannot be edited.** An unchangeable record makes the score more trustworthy. Corrections go through voiding, not editing.
- **Explain, don't just score.** Every score comes with its factors and tips.
- **Decision support, not a decision.** The score informs people. It does not approve or reject credit.

## Responsible use

These are open questions to settle before scores are sold to lenders. This is not legal advice.

- Whether supplying scores to lenders requires registration as a credit bureau under the National Credit Act.
- POPIA section 71 limits decisions that substantially affect a person when they are based solely on automated processing of their information, and credit worthiness is a named case. Lenders should keep a human in the loop and merchants should be able to ask for a review.
- Retention and deletion rules for merchant data.

---

# Part 2: Scale

## How the product grows

New data enters through a **data source** attached to a store, so adding a channel does not change the scoring model. The planned order, from least to most partner access required:

1. **Typed sales** (live).
2. **Uploaded evidence:** bank screenshots, receipts, pasted SMS (live).
3. **Bank data** through an account aggregator, which covers card settlements, EFTs and cash send in one connection.
4. **Card machine and payment provider APIs**, which add itemised, verified sales.
5. **Accounting software** for merchants who formalise.
6. **Lender and supplier portals** that read a merchant's score with the merchant's consent.

Each step raises the share of revenue that is independently verified, which is what makes the score more useful to a lender.

## What breaks first, and what we will do

| Pressure                        | Today                                                                                                                     | Next step                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Score computed on every request | One weekly aggregate query per merchant, fine at current volume                                                           | Precompute weekly totals (a `financial_snapshots` table already exists) or cache the profile |
| Double counting                 | The server cannot tell a typed sale from a bank message for the same payment. Matching happens on the device              | Store the evidence type and a reference on each transaction and match on the server          |
| Self-reported cash              | Cash is typed in and trusted                                                                                              | Cross-check against bank deposits once bank data is connected                                |
| Thin history                    | 4 weeks is the minimum, so early scores are noisier                                                                       | Maturity labels now, calibration against real outcomes later                                 |
| Calibration                     | Weights are placeholders                                                                                                  | Pilot with one lender or supplier and compare scores with repayment                          |
| Device limits                   | Reading uploads and the on-device model need a modern phone browser. The model is a one-time download of a few hundred MB | Rule-based fallbacks already exist. Pasted SMS avoids OCR                                    |
| Offline backlog                 | Up to 500 unsynced sales per store                                                                                        | Raise the limit or move to IndexedDB if needed                                               |
| Recent sales list               | Kept on the phone only                                                                                                    | Move to the server with the evidence work above                                              |

## How the business grows

- **Distribution through suppliers.** A wholesaler onboarding its customers is cheaper than reaching traders one by one, and suppliers make simpler credit decisions than banks.
- **A first pilot.** One lender or supplier agreeing to use the score is worth more than any amount of sign-ups, because it creates the repayment data the score needs.
- **Premium conversion.** The credit profile and forecast are the paid layer. Logging stays free to keep data flowing.
- **Compliance as a gate.** The legal questions above must be settled before scores are sold.

## What the score needs to earn trust

Verified share of revenue, history length, and repayment outcomes. The first two are product work. The third needs a partner.

---

# Part 3: Developer guide

## Repository map

| Folder                    | Contents                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| `backend/`                | FastAPI application                                                                          |
| `backend/services/`       | Auth, authorization, onboarding, plan tiers, credit scoring and the credit profile           |
| `backend/bi/`             | Overview metrics and chart data preparation                                                  |
| `backend/database/`       | Connection pool and schema                                                                   |
| `backend/validation/`     | Pydantic models (`StrictModel`)                                                              |
| `backend/docs/`           | [Architecture](backend/docs/architecture.md)                                                 |
| `frontend/`               | Next.js app (App Router)                                                                     |
| `frontend/app/workspace/` | Logging chat (`/workspace`), dashboard, credit profile, onboarding                           |
| `frontend/lib/`           | Auth helpers, plus the sale conversation and document reading logic used by the logging chat |

## Prerequisites

- Python 3.10 or newer (the code uses modern type syntax and `zoneinfo`)
- A current Node.js LTS
- A PostgreSQL database and a Neon Auth project

## Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m database.init_db        # creates the schema (safe to re-run)
uvicorn main:app --reload
pytest

# Frontend
cd frontend
npm install
npm run dev
```

**Environment.** The frontend's server code reads `BACKEND_API_URL` (falling back to `NEXT_PUBLIC_API_URL`) for the API address. Database and Neon Auth settings are read in `backend/database/connection.py` and `frontend/lib/auth`. Browser code calls the API through `/api/backend/...`, which the frontend forwards to the backend.

## How a request is handled

Every dashboard route uses the same two dependencies:

1. `get_current_user_id` verifies the Neon Auth token and returns the user id.
2. `get_current_merchant` checks the user belongs to the merchant. Users with several businesses send an `X-Merchant-Id` header, which is checked against their memberships. There is no fallback that treats a user id as a merchant id.

Routes are plain `def`, not `async def`, because the database calls block, and FastAPI runs them in a thread pool. `get_conn` gives each request one pooled connection that commits on success and rolls back on error.

## API

All routes need `Authorization: Bearer <token>`.

| Method and path                  | Purpose                                                         |
| -------------------------------- | --------------------------------------------------------------- |
| `POST /api/onboarding/dashboard` | Create a business (and store) for the signed-in user            |
| `POST /api/connect-codes`        | Issue a one-time team invite code (admin or owner)              |
| `POST /api/connect-codes/redeem` | Join a business with a code                                     |
| `GET /api/businesses`            | The user's businesses, stores and whether logging is enabled    |
| `GET /api/stores`                | Stores with an active PWA logging source                        |
| `GET /api/transactions`          | Recent transactions (excluding voided)                          |
| `GET /api/revenue`               | Daily revenue in South African time                             |
| `GET /api/top-offerings`         | Top offerings by revenue                                        |
| `GET /api/overview`              | Headline metrics, signals and insights                          |
| `GET /api/payment-methods`       | Revenue by payment method                                       |
| `GET /api/credit-score`          | Headline score and status                                       |
| `GET /api/credit-score/details`  | Breakdown and metrics (Full plan only, otherwise 403)           |
| `GET /api/credit-profile`        | Everything the credit page needs, shaped by the merchant's plan |
| `GET /api/entitlements`          | Which features the merchant's plan includes                     |
| `POST /transactions`             | Sale logging from the PWA (separate router)                     |

## Data model

| Table                 | Notes                                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `merchants`           | A business. `tier` is `insights` or `full`                                                                               |
| `merchant_users`      | Membership and role (`owner`, `admin`, `employee`, `viewer`). One owner per merchant                                     |
| `stores`              | Belong to a merchant. Names are unique per merchant                                                                      |
| `data_sources`        | A channel feeding a store. Types: `pos`, `bank_statement`, `accounting_software`, `online_store`, `pwa`, `csv`, `manual` |
| `connect_codes`       | One-time invite codes that expire                                                                                        |
| `offerings`           | What a store sells. Unique per store, case-insensitive                                                                   |
| `transactions`        | The ledger (see below)                                                                                                   |
| `financial_snapshots` | Period summaries per store, available for precomputation                                                                 |

Key rules on `transactions`:

- `amount_zar` is positive. `payment_method` is `cash` or `digital`.
- `UNIQUE (store_id, client_txn_id)` makes retries safe. The PWA generates the id on the device, so a sale that is sent twice is stored once.
- A transaction references a data source belonging to the same store.
- Voiding sets `is_voided`, `voided_at` and `void_reason` together (enforced by a check). Every read excludes voided rows.
- `input_type` is `pos_tap`, `voice`, `manual`, `pwa`, `csv` or `api`.

## The scoring engine

Code lives in `services/credit_scoring.py` (the score) and `services/credit_profile.py` (the page payload).

**Window.** `scoring_window` returns the complete Monday to Sunday weeks (South African time) that can be scored. It never reaches before the merchant's first complete week, covers at most 12 weeks, and excludes the current week. Fewer than 4 weeks raises `InsufficientHistoryError`, which the routes turn into a "building" state.

**Components** (each 0 to 100):

- Stability: 100 minus the coefficient of variation of weekly revenue, as a percentage.
- Growth: 60 plus 0.4 points per 1% growth (recent half against earlier half), clamped. Unknown growth scores 50.
- Revenue level: the median weekly revenue converted to a monthly equivalent, as a share of the benchmark.
- Consistency: the share of weeks with at least 3 active days.

All weights and constants are at the top of `credit_scoring.py` and marked as uncalibrated.

**Profile.** `get_credit_profile` returns one of three states: `no_data`, `building` (progress, tips and the week in progress) or `scored` (band, factors, tips ranked by points available, metrics, forecast range, four-week change). `apply_plan` then removes everything the merchant's plan does not include and lists what is `locked`.

**Forecast.** A deliberately simple range: the middle of recent weeks and the range most weeks fall in. It is not a statistical interval and the UI says so.

## The logging chat

The page at `/workspace` is a chat that records one sale at a time.

- **Reading typed sales.** An on-device model (Qwen2.5 0.5B, quantised, through WebLLM) extracts details, and a rule-based reader cross-checks it. The model's amount is only trusted if that number appears in the message. If the model is unavailable, the rules still work.
- **Reading uploads.** Images are shrunk and read with Tesseract.js on the device. Rule-based money extraction runs first. The model is only a fallback, and its amount must also appear in the text.
- **Follow-up questions.** The conversation asks for the next missing piece in a fixed order: amount, cash or digital, whether a bank message was for a sale, whether it matches an earlier sale, what was sold, how many. Tapping a chip is identical to typing that answer.
- **Matching.** A new entry is only compared with a recent one when the evidence differs (for example a typed sale and a bank SMS), the amount matches, the payment types do not contradict, and it is under 24 hours old. It asks, and never merges silently.
- **Offline.** Confirmed sales are written to a per-store queue in `localStorage`, up to 500, and synced in order. Duplicate uploads on the same device are caught by a hash of the file or pasted text.
- **Scope.** The chat only records sales. Anything else gets a friendly reminder of what it can do.

## Conventions

- **Server-side gating.** Any premium route checks `require_feature`. Never rely on hiding things in the UI.
- **No schema changes without need.** Evidence handling currently lives on the device for this reason. See the roadmap for when that changes.
- **Friendly errors.** Users see short, plain messages. Technical detail goes to the console.
- **No hard-coded data.** Tunable values live in named constants at the top of a module.
- **Lean CSS.** Reuse existing classes before adding new ones. When two rules clash, the later one wins, so delete the earlier one.
- **Time zone.** Weeks and days are South African time. Convert in SQL (`AT TIME ZONE 'Africa/Johannesburg'`), not in the page.

## Recipes

**Add a data source.**

1. Add the source type to the `data_sources` check constraint using the existing drop-and-add migration pattern in the schema file.
2. Create a `data_sources` row for each store that connects it.
3. Write transactions with that `source_id`, an allowed `input_type`, and a stable `client_txn_id` so re-imports are safe.
4. Add a test that a re-import does not double count.

**Add a premium feature.**

1. Add a `Feature` in `services/tiers`.
2. Check it with `require_feature` in the route, or return a reduced payload and a `locked` list as `/api/credit-profile` does.
3. Return nothing for locked fields, not blanked or hidden values.

**Change the score.** Edit the constants in `credit_scoring.py`, update `test_credit_profile.py`, and keep the output keys stable because the credit page depends on them.

## Testing and CI

```bash
pytest
```

The scoring and profile tests use a small fake database connection, so they run without Postgres. They cover the scoring window, the partial first week, the building and scored states, plan gating, tip ranking and the forecast. GitHub Actions runs the suite on every push.

## Known limitations

- Weights and benchmarks are not calibrated against repayment.
- Evidence type, matching and the recent sales list live on the device, not on the server.
- Sales cannot be edited. Voiding exists in the schema, but no endpoint exposes it yet.
- A 4-week score is noisier than a 12-week one.
- OCR accuracy depends on the photo. Pasting the SMS text is more reliable.
- No self-serve upgrade flow yet, so locked sections point to the Full plan without a purchase button.

---

# Roadmap

| Now                                        | Next                                                                                         | Later                                                |
| ------------------------------------------ | -------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Logging chat with uploads and offline sync | Settings page: add stores, delete a store or account, manage the team (sales stay read-only) | Bank data through an account aggregator              |
| Dashboard and credit profile               | Documentation, Privacy Policy and Terms pages                                                | Card machine and payment provider APIs               |
| Plan gating on the server                  | Store evidence type and references on the server, with server-side matching                  | Accounting software links                            |
| Tests and CI                               | Forecasting and trend alerts built on the weekly history                                     | Verified, shareable report for suppliers and lenders |
|                                            | Billing and a self-serve upgrade                                                             | Calibration with a lender or supplier pilot          |

---

License

Released under the MIT License.

**Built by Jabulani Mokoena**
