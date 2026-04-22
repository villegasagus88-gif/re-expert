"""Smoke tests for the chat endpoint — verify it's wired up and requires auth."""
from fastapi.testclient import TestClient
from main import app


def test_chat_endpoint_is_registered():
    """POST /api/chat should exist; without auth we expect 401, not 404."""
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "hola"})
    assert response.status_code == 401


def test_chat_rejects_missing_message():
    """Validation: missing 'message' should yield 422 if auth were present.
    Without auth we still expect 401 (auth runs before validation)."""
    client = TestClient(app)
    response = client.post("/api/chat", json={})
    assert response.status_code in (401, 422)


def test_chat_method_not_allowed_on_get():
    client = TestClient(app)
    response = client.get("/api/chat")
    assert response.status_code == 405
