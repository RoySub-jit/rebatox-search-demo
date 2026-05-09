# RebaTox Hosted Demo Deploy

This branch is set up for the fastest stable public demo path:

- frontend on Vercel
- backend on Render
- free platform-generated subdomains instead of a purchased custom domain

That means you can use:

- a `*.vercel.app` URL for the frontend
- a `*.onrender.com` URL for the backend

Official references:

- Vercel automatically assigns a domain ending in `.vercel.app` to deployments:
  [Vercel domains docs](https://vercel.com/docs/domains/working-with-domains)
- Render web services receive a unique `onrender.com` subdomain:
  [Render web services docs](https://render.com/docs/web-services/)
- Render supports `render.yaml` blueprints from the repo root:
  [Render blueprint reference](https://render.com/docs/blueprint-spec)

## Current Hosted Scope

The hosted demo should focus on:

- `/search`
- `/molecule`

These pages use live `openFDA` search and detail lookups and do not require a
local seeded database.

The deeper internal report, calculation, and expert-review workflow still
exists in the app, but the hosted frontend can hide that navigation by setting
`NEXT_PUBLIC_PUBLIC_DEMO_MODE=true`.

## 1. Deploy The Backend On Render

### Recommended setup

- Service type: `Web Service`
- Runtime: `Python`
- Root directory: `apps/backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

You can either:

1. create the service manually in the Render dashboard, or
2. import the repo with the root `render.yaml`

### Backend environment variables

Set these in Render:

```text
APP_NAME=RebaTox API
APP_ENV=production
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://<your-frontend>.vercel.app
```

Notes:

- `DATABASE_URL` is not required for the hosted search-only demo flow.
- Search endpoints do not depend on the local seeded SQLite/Postgres setup.
- If you later want hosted report/calculation/expert-review flows, add a real
  database and configure `DATABASE_URL`.

### Backend sanity checks

After deploy, confirm:

- `https://<your-backend>.onrender.com/`
- `https://<your-backend>.onrender.com/api/v1/molecule-search?q=aspirin&limit=3`

## 2. Deploy The Frontend On Vercel

### Recommended setup

- Framework: `Next.js`
- Root directory: `apps/frontend`

### Frontend environment variables

Set these in Vercel:

```text
NEXT_PUBLIC_APP_NAME=RebaTox
NEXT_PUBLIC_API_BASE_URL=https://<your-backend>.onrender.com
NEXT_PUBLIC_PUBLIC_DEMO_MODE=true
```

Notes:

- `NEXT_PUBLIC_PUBLIC_DEMO_MODE=true` hides the internal-only navigation and
  keeps the hosted reviewer entry point focused on molecule search.
- The frontend root already redirects to `/search`.

### Frontend sanity checks

After deploy, confirm:

- `https://<your-frontend>.vercel.app/`
- `https://<your-frontend>.vercel.app/search?q=aspirin`
- opening a result leads to `/molecule?...`

## 3. What To Send Reviewers

Send the Vercel URL, not the backend URL.

Best links:

- `https://<your-frontend>.vercel.app/`
- `https://<your-frontend>.vercel.app/search?q=aspirin`

## 4. Expected Behavior

Hosted reviewers should be able to:

- open the frontend independently
- search a molecule by name
- inspect live source-backed label details

They should not need:

- your laptop
- localhost
- a temporary tunnel

## 5. If You Want Me To Finish The Deploy

The remaining blocker is platform authentication, not code.

Once you are logged into:

- Vercel
- Render

I can help complete the exact hosted setup from there.
