# RebaTox

Evidence, POD, and Risk Support for Nonclinical Safety

Production-ready starter monorepo with:

- FastAPI backend
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL
- Next.js frontend with TypeScript
- Docker Compose for local development
- Environment variable templates
- Pytest setup
- Database-aware health check endpoint

RebaTox is the reviewer-facing workspace for evidence synthesis, candidate POD support, and nonclinical safety risk framing.

## Structure

```text
spatial-platform/
├── apps/
│   ├── backend/
│   │   ├── alembic/
│   │   ├── app/
│   │   ├── tests/
│   │   ├── .env.example
│   │   ├── Dockerfile
│   │   ├── alembic.ini
│   │   ├── pytest.ini
│   │   ├── requirements-dev.txt
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       ├── .env.example
│       ├── Dockerfile
│       ├── next.config.ts
│       ├── package.json
│       └── tsconfig.json
├── .env.example
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Docker with Compose support for the containerized workflow
- Python 3.12+ for local backend development
- Node.js 20+ for local frontend development

## Environment Setup

Create local environment files from the templates:

```bash
cp .env.example .env
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
```

## Run With Docker Compose

From the monorepo root:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

The backend container runs `alembic upgrade head` before starting the API server, so the database schema is applied automatically in local development.

## Backend: Local Python Workflow

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests:

```bash
cd apps/backend
source .venv/bin/activate
pytest
```

## Demo Seed

To reset the local database and load a full reviewer demo dataset with
`productId=1`:

```bash
cd apps/backend
source .venv/bin/activate
python scripts/seed_demo_report.py
```

This seeds:

- one product
- one comparator
- one source document and citation span
- one study and finding
- one candidate POD
- one limitation
- one recommendation
- one calculation run
- one expert review

After seeding, open:

- `http://localhost:3000/report?productId=1`
- `http://localhost:3000/calculations`

## Fast Demo Path

If you want the fastest end-to-end local demo on this laptop, use the SQLite
demo backend instead of local PostgreSQL:

```bash
cd apps/backend
bash scripts/run_demo_backend.sh
```

That command will:

- create or reuse `.venv`
- install backend dependencies
- create a local SQLite demo database at `apps/backend/rebatox_demo.db`
- reset and seed the demo data with `productId=1`
- start the FastAPI server on `http://localhost:8000`

Then open:

- `http://localhost:3000/report?productId=1`
- `http://localhost:3000/calculations`

## Hosted Search Demo

If you want a stable external URL for stewardship reviewers, the shortest path is:

- frontend on Vercel
- backend on Render

That hosted path is currently designed around the live molecule search workflow
in this branch. See [DEPLOY.md](./DEPLOY.md) for the exact setup steps,
environment variables, and platform notes.

## Frontend: Local Node Workflow

```bash
cd apps/frontend
npm install
cp .env.example .env
npm run dev
```

## Database Migrations

Create a new migration:

```bash
cd apps/backend
alembic revision --autogenerate -m "describe_change"
```

Apply migrations:

```bash
cd apps/backend
alembic upgrade head
```

## Notes

- The backend health endpoint checks both API liveness and database reachability.
- The frontend calls the backend through `NEXT_PUBLIC_API_BASE_URL`, which defaults to `http://localhost:8000`.
- CORS is enabled through `CORS_ORIGINS` in the backend environment file.
