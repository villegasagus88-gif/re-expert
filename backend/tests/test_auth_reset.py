"""
Tests for the forgot-password / reset-password flow.

Three layers, no real DB or network:
  - route layer: patch the auth_service functions, assert status/message/anti-enum
  - token layer (pure): reset-token shape + single-use fingerprint semantics
  - service 400 paths: reset_password rejects bad/expired/wrong-type tokens
    *before* touching the DB, so they're exercised directly
  - email_service: degrades gracefully when RESEND_API_KEY is unset
"""
import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core.rate_limit import limiter
from main import app
from services.jwt_service import (
    create_access_token,
    create_reset_token,
    decode_token,
    password_fingerprint,
)


@pytest.fixture(autouse=True)
def _disable_limiter():
    """forgot is 5/hour, reset is 10/hour — disable so repeated posts don't trip it."""
    prev = limiter.enabled
    limiter.enabled = False
    try:
        yield
    finally:
        limiter.enabled = prev


# ── forgot-password route ────────────────────────────────────────────

def test_forgot_password_returns_200_with_uniform_message():
    with patch(
        "api.routes.auth.request_password_reset", new=AsyncMock(return_value=None)
    ) as mock_req:
        client = TestClient(app)
        resp = client.post("/api/auth/forgot-password", json={"email": "user@example.com"})
    assert resp.status_code == 200
    assert "registrado" in resp.json()["message"]
    mock_req.assert_awaited_once()


def test_forgot_password_same_response_for_unknown_email():
    """Anti-enumeración: la respuesta no depende de si el email existe."""
    with patch("api.routes.auth.request_password_reset", new=AsyncMock(return_value=None)):
        client = TestClient(app)
        r1 = client.post("/api/auth/forgot-password", json={"email": "known@example.com"})
        r2 = client.post("/api/auth/forgot-password", json={"email": "ghost@example.com"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()


def test_forgot_password_rejects_invalid_email():
    client = TestClient(app)
    resp = client.post("/api/auth/forgot-password", json={"email": "not-an-email"})
    assert resp.status_code == 422


# ── reset-password route ─────────────────────────────────────────────

def test_reset_password_success_returns_200():
    with patch(
        "api.routes.auth.reset_password", new=AsyncMock(return_value=None)
    ) as mock_reset:
        client = TestClient(app)
        resp = client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token", "new_password": "NuevaClave1"},
        )
    assert resp.status_code == 200
    mock_reset.assert_awaited_once()


def test_reset_password_weak_password_rejected_422():
    client = TestClient(app)
    # too short / no uppercase / no digit → schema validation fails
    resp = client.post(
        "/api/auth/reset-password",
        json={"token": "x", "new_password": "weak"},
    )
    assert resp.status_code == 422


def test_reset_password_invalid_token_propagates_400():
    async def _raise(**kwargs):
        raise HTTPException(status_code=400, detail="El link de recuperación es inválido.")

    with patch("api.routes.auth.reset_password", new=AsyncMock(side_effect=_raise)):
        client = TestClient(app)
        resp = client.post(
            "/api/auth/reset-password",
            json={"token": "bad", "new_password": "NuevaClave1"},
        )
    assert resp.status_code == 400


# ── token logic (pure, no DB) ────────────────────────────────────────

def test_reset_token_shape_and_single_use_binding():
    uid = uuid4()
    token = create_reset_token(uid, "bcrypt-hash-A")
    payload = decode_token(token)
    assert payload["type"] == "reset"
    assert payload["sub"] == str(uid)
    # Bound to the current hash; a changed password (new hash) won't match.
    assert payload["pwf"] == password_fingerprint("bcrypt-hash-A")
    assert payload["pwf"] != password_fingerprint("bcrypt-hash-B")


def test_password_fingerprint_stable_and_distinct():
    assert password_fingerprint("same") == password_fingerprint("same")
    assert password_fingerprint("a") != password_fingerprint("b")
    assert len(password_fingerprint("anything")) == 32


# ── reset_password service: 400 paths that never touch the DB ────────

def test_reset_password_garbage_token_raises_400():
    from services.auth_service import reset_password

    with pytest.raises(HTTPException) as ei:
        asyncio.run(reset_password("not-a-jwt", "NuevaClave1"))
    assert ei.value.status_code == 400


def test_reset_password_wrong_token_type_raises_400():
    """An access token is a valid JWT but type='access' → rejected before DB."""
    from services.auth_service import reset_password

    access = create_access_token(uuid4())
    with pytest.raises(HTTPException) as ei:
        asyncio.run(reset_password(access, "NuevaClave1"))
    assert ei.value.status_code == 400


# ── email_service degradation ────────────────────────────────────────

def test_email_service_not_configured_returns_ok_false():
    from services import email_service

    res = asyncio.run(email_service.send_email("a@b.com", "subj", "<p>hola</p>"))
    assert res["ok"] is False
    assert res["detail"] == "email_not_configured"
    assert email_service.is_configured() is False
