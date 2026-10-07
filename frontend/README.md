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
- `JWT_SECRET`: a private random secret of at least 32 characters. It must match `backend/JWT_SECRET`. The Next.js server uses it to issue short-lived API tokens only after validating the Neon Auth session.
- `BACKEND_API_URL`: the FastAPI origin, without a path such as `/api`.

The browser uses Neon Auth through the same-origin `/api/auth/` proxy. Dashboard server-side requests and browser-originated onboarding requests use short-lived backend tokens minted only after the server validates the Neon Auth session. The JWT signing secret is not exposed to browser code.

The PWA foundation includes a web manifest, app entry route, offline fallback, and service worker caching for the app entry and immutable Next.js assets. It intentionally does not yet cache account data. Offline transaction capture, local persistence, model download/caching, and WebLLM transaction parsing belong to the next frontend implementation pass.
