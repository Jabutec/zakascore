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

The PWA foundation includes a web manifest, app entry route, offline fallback, and service worker caching for the app entry and immutable Next.js assets. It intentionally does not yet cache account data. Offline transaction capture, local persistence, model download/caching, and WebLLM transaction parsing belong to the next frontend implementation pass.
