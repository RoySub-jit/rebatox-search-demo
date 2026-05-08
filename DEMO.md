# RebaTox Demo Runbook

This is the fastest local demo path for the current RebaTox reviewer workflow.

## 1. Start The Backend

From the repo root:

```bash
cd apps/backend
bash scripts/run_demo_backend.sh
```

This command:

- creates or reuses `.venv`
- installs backend dependencies
- resets the local SQLite demo database
- seeds a full reviewer dataset with `productId=1`
- starts the FastAPI backend on `http://localhost:8000`

## 2. Start The Frontend

From a second terminal:

```bash
cd apps/frontend
cp .env.example .env
npm install
npm run dev
```

Open:

- `http://localhost:3000/product-overview`
- `http://localhost:3000/calculations`
- `http://localhost:3000/report?productId=1`

## 3. Recommended Demo Flow

### Product Overview

Open:

- `http://localhost:3000/product-overview`

Talk track:

- RebaTox is a reviewer workspace for evidence, POD, and nonclinical risk support.
- The workspace is structured around evidence, calculations, candidate POD assessment, and expert review.

### Calculations

Open:

- `http://localhost:3000/calculations`

Demo:

- Run the default margin-of-exposure example.
- Show the structured output:
  - formula
  - inputs
  - assumptions
  - result
  - warnings/status
- Explain that deterministic calculations are persisted and later surfaced in the report audit trail.

### Report Reviewer Workspace

Open:

- `http://localhost:3000/report?productId=1`

Show, in this order:

1. Product overview and evidence counts
2. Comparator summary with relevance score and rationale
3. Evidence summary and calculation audit trails
4. Candidate POD assessment with:
   - support category
   - support score
   - expert review required flag
5. Limitations and suggested next experiments
6. Expert review history and override controls

### Expert Override Workflow

In the candidate POD section:

- add expert notes
- optionally override support category
- optionally override support score
- mark expert review as resolved if appropriate
- save the review
- refresh the page and confirm the saved state persists in the report view

## 4. Demo Reset

If you want to reset the demo back to a clean seeded state:

```bash
cd apps/backend
source .venv/bin/activate
export DATABASE_URL=sqlite+pysqlite:///./rebatox_demo.db
python scripts/bootstrap_demo_db.py
```

Then refresh:

- `http://localhost:3000/report?productId=1`
- `http://localhost:3000/calculations`

## 5. Troubleshooting

### Calculations page says "Failed to fetch"

This usually means the backend demo database is not in sync with the running API process.

Fix:

```bash
cd apps/backend
pkill -f 'uvicorn app.main:app --reload --host 0.0.0.0 --port 8000' || true
bash scripts/run_demo_backend.sh
```

### Report page loads but expert overrides do not persist

Make sure the backend from `scripts/run_demo_backend.sh` is still running and has not been replaced by another local `uvicorn` process.

### Frontend page looks stale

Restart the frontend dev server:

```bash
cd apps/frontend
npm run dev
```

## 6. Suggested Short Narrative

Use this arc for a 5-minute demo:

1. RebaTox organizes nonclinical evidence into a reviewer-friendly workspace.
2. Deterministic calculations are auditable and feed directly into evidence review.
3. Candidate PODs are scored using support logic, comparator relevance, and limitations.
4. Experts can review, override, and resolve the assessment while preserving rationale and history.
