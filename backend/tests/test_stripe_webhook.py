"""
Tests for POST /api/stripe/webhook.

Strategy:
  - patch services.stripe_service.settings to control webhook-secret toggling
  - override get_db with a thin async stub that mimics enough of AsyncSession
    to drive idempotency (StripeEvent insert) + user lookup/update.
"""
import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from main import app
from models.base import get_db
from models.stripe_event import StripeEvent
from models.user import User
from sqlalchemy.exc import IntegrityError


# ───────────────────────────────────────────────────────── helpers ─────

def _make_user(plan: str = "free", customer_id: str | None = None) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.plan = plan
    user.stripe_customer_id = customer_id
    return user


class _MockDB:
    """
    Async-session stub: tracks added events and serves a single user
    looked up either by id (User.id) or by stripe_customer_id.

    `seen_event_ids` simulates the UNIQUE constraint on stripe_events.event_id.
    """

    def __init__(self, user: MagicMock | None = None):
        self.user = user
        self.added: list = []
        self.commits = 0
        self.rollbacks = 0
        self.seen_event_ids: set[str] = set()

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        # Enforce UNIQUE(event_id) for StripeEvent rows.
        for obj in list(self.added):
            if isinstance(obj, StripeEvent):
                if obj.event_id in self.seen_event_ids:
                    self.added.remove(obj)
                    raise IntegrityError("UNIQUE event_id", None, None)
                self.seen_event_ids.add(obj.event_id)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def execute(self, stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = self.user
        return result


@contextmanager
def _client(user: MagicMock | None = None, webhook_secret: str = ""):
    """Build a TestClient with get_db overridden and stripe settings patched."""
    db = _MockDB(user=user)

    async def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db

    with patch("services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_xxx"
        mock_settings.STRIPE_WEBHOOK_SECRET = webhook_secret
        try:
            yield TestClient(app), db
        finally:
            app.dependency_overrides.clear()


def _post_event(client: TestClient, event: dict) -> "TestClient":
    return client.post(
        "/api/stripe/webhook",
        content=json.dumps(event),
        headers={"Content-Type": "application/json"},
    )


# ────────────────────────────────────────────────────── basic auth ─────

def test_webhook_does_not_require_jwt():
    """Stripe webhook is intentionally unauthenticated (signature is the auth)."""
    with _client() as (client, _):
        r = _post_event(client, {"id": "evt_1", "type": "ping", "data": {"object": {}}})
        # No 401 — endpoint is reachable without JWT.
        assert r.status_code != 401


def test_webhook_503_when_stripe_not_configured():
    with _client() as (client, _), \
         patch("services.stripe_service.settings") as ms:
        ms.STRIPE_SECRET_KEY = ""
        r = _post_event(client, {"id": "evt_1", "type": "x", "data": {"object": {}}})
        assert r.status_code == 503


def test_webhook_400_on_malformed_json():
    with _client() as (client, _):
        r = client.post(
            "/api/stripe/webhook",
            content=b"not-json{{",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 400


def test_webhook_400_on_event_without_id():
    """A parsed event missing `id` is rejected (required for idempotency)."""
    with _client() as (client, _):
        r = _post_event(client, {"type": "checkout.session.completed", "data": {"object": {}}})
        assert r.status_code == 400


# ───────────────────────────────────────────── signature verification ─

def test_webhook_400_on_bad_signature_when_secret_configured():
    with _client(webhook_secret="whsec_xxx") as (client, _):
        r = client.post(
            "/api/stripe/webhook",
            content=b'{"id":"evt_1","type":"x","data":{"object":{}}}',
            headers={
                "Content-Type": "application/json",
                "stripe-signature": "t=1,v1=invalid",
            },
        )
        assert r.status_code == 400
        assert "Firma" in r.json()["detail"]


# ─────────────────────────────────────────────── happy-path handlers ──

def test_checkout_session_completed_activates_pro():
    user = _make_user(plan="free")
    event = {
        "id": "evt_checkout_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user.id)},
                "customer": "cus_test_123",
            }
        },
    }
    with _client(user=user) as (client, db):
        r = _post_event(client, event)

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert user.plan == "pro"
    assert user.stripe_customer_id == "cus_test_123"
    assert "evt_checkout_1" in db.seen_event_ids


def test_subscription_deleted_downgrades_to_inactive():
    # Modelo pago-only: al cancelar la suscripción el plan pasa a "inactive"
    # (no existe "free"). El gate de acceso lo trata como sin-acceso.
    user = _make_user(plan="pro", customer_id="cus_existing")
    event = {
        "id": "evt_del_1",
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_existing"}},
    }
    with _client(user=user) as (client, _):
        r = _post_event(client, event)

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert user.plan == "inactive"


def test_invoice_payment_failed_downgrades_to_inactive():
    """Renewal failure → user pierde el acceso (inactive) hasta actualizar la tarjeta."""
    user = _make_user(plan="pro", customer_id="cus_existing")
    event = {
        "id": "evt_fail_1",
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_existing"}},
    }
    with _client(user=user) as (client, _):
        r = _post_event(client, event)

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert user.plan == "inactive"


def test_unknown_event_type_is_ignored():
    user = _make_user(plan="free")
    event = {
        "id": "evt_misc_1",
        "type": "charge.dispute.created",
        "data": {"object": {}},
    }
    with _client(user=user) as (client, _):
        r = _post_event(client, event)

    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
    # plan is unchanged
    assert user.plan == "free"


# ──────────────────────────────────────────────────── idempotency ────

def test_duplicate_event_is_skipped():
    """Stripe redelivers up to 3 days; 2nd call must not double-process."""
    user = _make_user(plan="free")
    event = {
        "id": "evt_dup_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user.id)},
                "customer": "cus_dup",
            }
        },
    }
    with _client(user=user) as (client, db):
        r1 = _post_event(client, event)
        # Reset plan to detect re-processing
        user.plan = "free"
        r2 = _post_event(client, event)

    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
    # Second call must NOT have flipped plan back to pro
    assert user.plan == "free"
