"""Exercise the real docs routes and password verification without a database server."""

from types import SimpleNamespace

import pytest
from app.auth.dependencies import _attempts
from app.auth.service import hasher
from app.database import get_db
from app.main import app
from fastapi.testclient import TestClient

PASSWORD = "test-admin-password-only"


@pytest.fixture
def docs_client():
    user = SimpleNamespace(role="admin", active=True, password_hash=hasher.hash(PASSWORD))
    db = SimpleNamespace(scalar=lambda query: user)
    app.dependency_overrides[get_db] = lambda: db
    _attempts.clear()
    try:
        with TestClient(app) as client:
            yield client, user
    finally:
        app.dependency_overrides.pop(get_db, None)
        _attempts.clear()


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_require_credentials(docs_client, path):
    client, _ = docs_client
    response = client.get(path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_admin_can_read_docs(docs_client, path):
    client, _ = docs_client
    response = client.get(path, auth=("admin@example.com", PASSWORD))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    if path == "/openapi.json":
        assert "/docs" not in response.json()["paths"]
        assert "/api/auth/login" in response.json()["paths"]
    else:
        assert "/openapi.json" in response.text


@pytest.mark.parametrize(
    "role,active,password,expected",
    [
        ("user", True, PASSWORD, 403),
        ("player", True, PASSWORD, 403),
        ("admin", False, PASSWORD, 401),
        ("admin", True, "wrong", 401),
    ],
)
def test_docs_reject_invalid_access(docs_client, role, active, password, expected):
    client, user = docs_client
    user.role, user.active = role, active
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path, auth=("admin@example.com", password)).status_code == expected


def test_docs_throttle(docs_client):
    client, _ = docs_client
    for _ in range(10):
        assert client.get("/docs").status_code == 401
    response = client.get("/docs")
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"


def test_docs_login_does_not_create_api_session(docs_client):
    client, _ = docs_client
    response = client.get("/docs", auth=("admin@example.com", PASSWORD))
    assert "set-cookie" not in response.headers
    assert client.get("/docs/oauth2-redirect").status_code == 404
