from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import get_default_sqlite_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Default None -> diisi ke SQLite lokal oleh validator di bawah kalau
    # tidak di-override (jalur desktop). Deployment hosted (docker-compose,
    # Render, dst) selalu set DATABASE_URL eksplisit ke Postgres.
    database_url: str | None = None

    @model_validator(mode="after")
    def _default_to_local_sqlite(self) -> "Settings":
        if self.database_url is None:
            self.database_url = get_default_sqlite_url()
        return self

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    jwt_secret_key: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    market_data_provider_idx: str = "yfinance"

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
