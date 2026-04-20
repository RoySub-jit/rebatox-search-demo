# Spatial Platform Monorepo

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
