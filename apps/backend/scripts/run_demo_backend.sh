#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt -r requirements-dev.txt >/dev/null

export DATABASE_URL="${DATABASE_URL:-sqlite+pysqlite:///./rebatox_demo.db}"

python scripts/bootstrap_demo_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
