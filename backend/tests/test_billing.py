"""
Tests for /api/billing/* endpoints.

Stripe SDK calls are monkey-patched so tests don't hit the network.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from main import app


# ----------------------------------------------------------- HTTP basics --

def test_billing_checkout_requires_auth():
    client = TestClient(app)
    r = client.post("/api/billing/checkout")
    assert r.status_code == 401


def test_billing_portal_requires_auth():
    client = TestClient(app)
    r = client.post("/api/billing/portal")
    assert r.status_code == 401


def test_billing_status_requires_auth():
    client = TestClient(app)
    r = client.get("/api/billing/status")
    assert r.status_code == 401


def test_billing_checkout_rejects_get():
    client = TestClient(app)
    r = client.get("/api/billing/checkout")
    assert r.status_code == 405


# ---------------------------------------------------- service-level logic --

@pytest.mark.asyncio
async def test_create_pro_checkout_503_when_stripe_not_configured():
    """If STRIPE_SECRET_KEY is empty, the helper raises 503."""
    from fastapi import HTTPException
    from services.stripe_service import create_pro_checkout_session

    user = type("U", (), {"plan": "free", "email": "x@y.com", "id": "00000000-0000-0000-0000-000000000001"})()

    with patch("services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = ""

        with pytest.raises(HTTPException) as exc:
            await create_pro_checkout_session(user)
        assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_create_pro_checkout_400_when_user_already_pro():
    from fastapi import HTTPException
    from services.stripe_service import create_pro_checkout_session

    user = type("U", (), {"plan": "pro", "email": "x@y.com", "id": "00000000-0000-0000-0000-000000000001"})()

    with patch("services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_xxx"

        with pytest.raises(HTTPException) as exc:
            await create_pro_checkout_session(user)
        assert exc.value.status_code == 400
        assert "Pro" in exc.value.detail


@pytest.mark.asyncio
async def test_create_pro_checkout_503_when_price_not_configured():
    from fastapi import HTTPException
    from services.stripe_service import create_pro_checkout_session

    user = type("U", (), {"plan": "free", "email": "x@y.com", "id": "00000000-0000-0000-0000-000000000001"})()

    with patch("services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_xxx"
        mock_settings.STRIPE_PRICE_ID_PRO = ""

        with pytest.raises(HTTPException) as exc:
            await create_pro_checkout_session(user)
        assert exc.value.status_code == 503
        assert "Precio" in exc.value.detail


@pytest.mark.asyncio
async def test_create_pro_checkout_returns_session_url():
    """Happy path — Stripe returns a session, helper returns {url, session_id}."""
    from services.stripe_service import create_pro_checkout_session

    user = type("U", (), {"plan": "free", "email": "x@y.com", "id": "00000000-0000-0000-0000-000000000001"})()

    fake_session = type("S", (), {"url": "https://checkout.stripe.com/c/pay/cs_test_xxx", "id": "cs_test_xxx"})()

    with patch("services.stripe_service.settings") as mock_settings, \
         patch("services.stripe_service.run_stripe", return_value=fake_session):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_xxx"
        mock_settings.STRIPE_PRICE_ID_PRO = "price_xxx"
        mock_settings.STRIPE_SUCCESS_URL = "https://app.example.com/success.html"
        mock_settings.STRIPE_CANCEL_URL = "https://app.example.com/pricing.html"

        result = await create_pro_checkout_session(user)

    assert result["url"].startswith("https://checkout.stripe.com/")
    assert result["session_id"] == "cs_test_xxx"


# ------------------------------------------ legacy /api/stripe/* aliases --

def test_stripe_create_checkout_session_alias_requires_auth():
    """Legacy alias must keep returning 401 without token (frontend back-compat)."""
    client = TestClient(app)
    r = client.post("/api/stripe/create-checkout-session")
    assert r.status_code == 401


def test_stripe_portal_alias_requires_auth():
    client = TestClient(app)
    r = client.post("/api/stripe/portal")
    assert r.status_code == 401
