from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, reset_database_state


@asynccontextmanager
async def lifespan(_: FastAPI):
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield
    reset_database_state()


def create_application() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/", tags=["meta"])
    def read_root() -> dict[str, str]:
        return {
            "message": f"{settings.app_name} is running.",
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    return application


app = create_application()
