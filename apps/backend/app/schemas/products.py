from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    slug: str
    manufacturer: str | None = None
    description: str | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    manufacturer: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime
