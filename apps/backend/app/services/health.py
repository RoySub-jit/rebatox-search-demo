from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_engine
from app.schemas.health import DatabaseHealth


def check_database() -> DatabaseHealth:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))

        return DatabaseHealth(ok=True, message="Database connection healthy")
    except SQLAlchemyError as exc:
        return DatabaseHealth(
            ok=False,
            message="Database connection failed",
            detail=exc.__class__.__name__,
        )
