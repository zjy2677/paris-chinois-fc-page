from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        extra="ignore",
        hide_input_in_errors=True,
    )
    app_env: Literal["development", "production"] = "development"
    database_url: str
    database_migration_url: str | None = None
    cors_origins: list[str] = ["http://localhost:4173"]
    contact_enabled: bool = False
    jwt_secret: str = ""
    auth_cookie_secure: bool = True
    auth_ttl_seconds: int = 28800
    r2_endpoint_url: str | None = None
    r2_bucket_name: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None

    @field_validator("database_url", "database_migration_url")
    @classmethod
    def psycopg_url(cls, value: str | None) -> str | None:
        # Neon supplies postgresql://; SQLAlchemy otherwise selects psycopg2.
        if value and value.startswith(("postgres://", "postgresql://")):
            return "postgresql+psycopg://" + value.split("://", 1)[1]
        return value

    @model_validator(mode="after")
    def production_requirements(self):
        if self.app_env != "production":
            return self
        if self.r2_endpoint_url:
            endpoint = urlsplit(self.r2_endpoint_url)
            if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username:
                raise ValueError("Production R2_ENDPOINT_URL must use HTTPS without credentials")
        if len(self.jwt_secret) < 32 or not self.auth_cookie_secure:
            raise ValueError("Production requires a strong JWT_SECRET and secure cookies")
        if not self.cors_origins or any(
            urlsplit(origin).scheme != "https"
            or not urlsplit(origin).hostname
            or urlsplit(origin).path
            or urlsplit(origin).query
            or urlsplit(origin).fragment
            or urlsplit(origin).username
            for origin in self.cors_origins
        ):
            raise ValueError("Production CORS_ORIGINS must contain exact HTTPS website origins")
        for value in (self.database_url, self.database_migration_url):
            if value:
                url = make_url(value)
                if url.drivername != "postgresql+psycopg" or url.query.get("sslmode") not in (
                    "require",
                    "verify-ca",
                    "verify-full",
                ):
                    raise ValueError("Production database connections require psycopg and TLS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
