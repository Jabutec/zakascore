# Frontend setup

Install dependencies and configure environment values before running the app:

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Set these values in `.env.local`:

- `NEON_AUTH_BASE_URL`: the Auth URL from Neon Console → Project → Branch → Auth → Configuration.
- `NEON_AUTH_COOKIE_SECRET`: a private random secret of at least 32 characters.
- `BACKEND_API_URL`: the FastAPI origin, without a path such as `/api`.

The backend also needs `NEON_AUTH_URL` pointing at the Neon Auth URL so it can verify Neon-issued access tokens against the published JWKS. The browser uses Neon Auth through the same-origin `/api/auth/` proxy. Dashboard server-side requests and browser-originated onboarding requests forward the access token from the validated Neon Auth session; the backend verifies the token and resolves merchant access through `merchant_users`.

The installable `/app` route uses the authenticated businesses API to show only businesses and PWA-enabled stores available to the signed-in user. Sale descriptions are parsed on-device with WebLLM, reviewed before submission, and posted through the authenticated backend proxy. Offline-confirmed sales are persisted per store in local storage with stable idempotency keys and retried in order when connectivity returns; an unsuccessful server response leaves the sale queued and visible for retry.

The service worker caches the app entry and immutable Next.js assets for shell loading. It does not cache authenticated account or API data. Each team member uses an individual Neon Auth account; one-time invite codes grant employee access to the authorized business.
