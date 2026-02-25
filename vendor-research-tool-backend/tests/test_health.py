"""Smoke test for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_200() -> None:
    """GET /health returns 200 with status ok."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
