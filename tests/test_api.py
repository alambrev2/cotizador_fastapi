"""Smoke tests de la API real usando una BD temporal (pytest + TestClient)."""
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_root_ok(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200


def test_protected_endpoint_requires_auth(client: TestClient):
    resp = client.get("/api/v1/customers/")
    assert resp.status_code == 401


def test_login_wrong_credentials(client: TestClient):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "incorrecta"},
    )
    assert resp.status_code == 400
