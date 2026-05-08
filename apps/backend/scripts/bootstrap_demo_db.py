from __future__ import annotations

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import models  # noqa: F401
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from seed_demo_report import _reset_database, seed_demo_report


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    session_factory = get_session_factory()
    with session_factory() as db:
        _reset_database(db)
        seeded_ids = seed_demo_report(db)

    print("Demo database is ready.")
    for label, value in seeded_ids.items():
        print(f"{label}={value}")

    print("")
    print("Backend API:")
    print("http://localhost:8000")
    print("http://localhost:8000/docs")
    print("")
    print("Frontend URLs:")
    print("http://localhost:3000/report?productId=1")
    print("http://localhost:3000/calculations")
    print("http://localhost:3000/product-overview")


if __name__ == "__main__":
    main()
