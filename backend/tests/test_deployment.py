import pytest
from app.config import Settings
from pydantic import ValidationError


def production(**overrides):
    values = dict(
        app_env="production",
        database_url="postgresql://user:fake@ep-example-pooler.neon.tech/neondb?sslmode=require",
        jwt_secret="test-only-long-secret-that-is-not-real",
        auth_cookie_secure=True,
        cors_origins=["https://paris-chinois-fc.com"],
    )
    return Settings(_env_file=None, **(values | overrides))


def test_neon_url_uses_installed_driver_and_preserves_tls():
    settings = production(
        database_migration_url="postgres://user:fake@direct.neon.tech/db?sslmode=require"
    )
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.database_migration_url.startswith("postgresql+psycopg://")
    assert settings.database_url.endswith("sslmode=require")


@pytest.mark.parametrize(
    "values",
    [
        {"jwt_secret": "short"},
        {"auth_cookie_secure": False},
        {"cors_origins": ["*"]},
        {"cors_origins": ["http://localhost:4173"]},
        {"cors_origins": ["https://example.com/path"]},
        {"database_url": "postgresql://user:fake@db/db"},
        {"database_migration_url": "postgresql://user:fake@db/db?sslmode=disable"},
    ],
)
def test_unsafe_production_configuration_rejected(values):
    with pytest.raises(ValidationError):
        production(**values)
