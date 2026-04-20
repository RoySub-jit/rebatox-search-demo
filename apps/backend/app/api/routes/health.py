from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.schemas.health import DatabaseHealth, HealthResponse
from app.services.health import check_database

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck(response: Response) -> HealthResponse:
    settings = get_settings()
    database_status = check_database()
    overall_status = "ok" if database_status.ok else "degraded"

    if overall_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database=database_status,
    )
