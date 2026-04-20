from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Spatial Platform API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_server: str = Field(default="db", alias="POSTGRES_SERVER")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="spatial_platform", alias="POSTGRES_DB")
    postgres_user: str = Field(default="spatial_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="spatial_password", alias="POSTGRES_PASSWORD")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @computed_field(return_type=str)
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url

        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
