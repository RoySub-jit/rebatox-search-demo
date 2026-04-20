from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DatabaseHealth(BaseModel):
    ok: bool
    message: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
    database: DatabaseHealth
