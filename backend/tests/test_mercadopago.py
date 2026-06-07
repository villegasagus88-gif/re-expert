"""Tests del servicio de Mercado Pago (suscripciones pago-only en ARS).

Cubre lo crítico que NO depende de la red:
  - mp_enabled() / gating (inerte sin credenciales).
  - plan_for_status(): mapeo estado de preapproval → plan.
  - verify_webhook_signature(): HMAC-SHA256, anti-forja.
  - create_subscription() / handle_webhook(): guards (503/400) antes de tocar red.

El detalle del request real a MP (init_point) se valida contra el sandbox
cuando tengamos credenciales — acá no se mockea httpx a propósito: los tests
ejercitan los caminos que cortan ANTES de la llamada de red.
"""
import asyncio
import hashlib
import hmac

import pytest
from fastapi import HTTPException


def _enable_mp(monkeypatch, secret=""):
    from config import settings as s
    monkeypatch.setattr(s.settings, "MP_ACCESS_TOKEN", "TEST-token", raising=False)
    monkeypatch.setattr(s.settings, "MP_PLAN_ID", "2c93808489", raising=False)
    monkeypatch.setattr(s.settings, "MP_WEBHOOK_SECRET", secret, raising=False)
    monkeypatch.setattr(s.settings, "DEBUG", False, raising=False)


def _disable_mp(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "MP_ACCESS_TOKEN", "", raising=False)
    monkeypatch.setattr(s.settings, "MP_PLAN_ID", "", raising=False)


def _user(plan="trial"):
    u = type("U", (), {})()
    u.id = "11111111-1111-1111-1111-111111111111"
    u.email = "test@re.app"
    u.plan = plan
    return u


# ── mp_enabled ───────────────────────────────────────────────────────────────
def test_mp_disabled_by_default(monkeypatch):
    _disable_mp(monkeypatch)
    from services.mercadopago_service import mp_enabled, mp_public_config
    assert mp_enabled() is False
    assert mp_public_config()["enabled"] is False


def test_mp_enabled_when_configured(monkeypatch):
    _enable_mp(monkeypatch)
    from services.mercadopago_service import mp_enabled
    assert mp_enabled() is True


def test_mp_needs_both_token_and_plan(monkeypatch):
    from config import settings as s
    from services.mercadopago_service import mp_enabled
    monkeypatch.setattr(s.settings, "MP_ACCESS_TOKEN", "x", raising=False)
    monkeypatch.setattr(s.settings, "MP_PLAN_ID", "", raising=False)
    assert mp_enabled() is False  # falta el plan


# ── plan_for_status ──────────────────────────────────────────────────────────
def test_plan_for_status_mapping():
    from services.mercadopago_service import plan_for_status
    assert plan_for_status("authorized") == "pro"
    assert plan_for_status("AUTHORIZED") == "pro"  # case-insensitive
    assert plan_for_status("paused") == "inactive"
    assert plan_for_status("cancelled") == "inactive"
    # Estados que NO deben cambiar el plan:
    assert plan_for_status("pending") is None
    assert plan_for_status("unknown") is None
    assert plan_for_status(None) is None
    assert plan_for_status("") is None


# ── verify_webhook_signature ─────────────────────────────────────────────────
def _sign(secret, data_id, request_id, ts):
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


def test_signature_valid():
    from services.mercadopago_service import verify_webhook_signature
    secret, did, rid, ts = "sekret", "12345", "req-abc", "1700000000"
    v1 = _sign(secret, did, rid, ts)
    sig = f"ts={ts},v1={v1}"
    assert verify_webhook_signature(sig, rid, did, secret) is True


def test_signature_tampered_fails():
    from services.mercadopago_service import verify_webhook_signature
    secret, did, rid, ts = "sekret", "12345", "req-abc", "1700000000"
    v1 = _sign(secret, did, rid, ts)
    sig = f"ts={ts},v1={v1}"
    # data_id distinto → manifest distinto → no matchea
    assert verify_webhook_signature(sig, rid, "99999", secret) is False
    # secret distinto
    assert verify_webhook_signature(sig, rid, did, "otro") is False
    # v1 alterado
    assert verify_webhook_signature(f"ts={ts},v1=deadbeef", rid, did, secret) is False


def test_signature_missing_parts_fails():
    from services.mercadopago_service import verify_webhook_signature
    assert verify_webhook_signature(None, "r", "d", "sekret") is False
    assert verify_webhook_signature("ts=1,v1=x", "r", "d", "") is False  # sin secret
    assert verify_webhook_signature("v1=x", "r", "d", "sekret") is False  # sin ts
    assert verify_webhook_signature("ts=1", "r", "d", "sekret") is False  # sin v1
    assert verify_webhook_signature("garbage", "r", "d", "sekret") is False


# ── create_subscription (guards antes de la red) ─────────────────────────────
def test_create_subscription_503_when_disabled(monkeypatch):
    _disable_mp(monkeypatch)
    from services.mercadopago_service import create_subscription

    async def go():
        with pytest.raises(HTTPException) as e:
            await create_subscription(_user("trial"))
        assert e.value.status_code == 503

    asyncio.run(go())


def test_create_subscription_400_when_already_pro(monkeypatch):
    _enable_mp(monkeypatch)
    from services.mercadopago_service import create_subscription

    async def go():
        with pytest.raises(HTTPException) as e:
            await create_subscription(_user("pro"))
        assert e.value.status_code == 400

    asyncio.run(go())


# ── handle_webhook (guards antes de la red) ──────────────────────────────────
def test_webhook_503_when_disabled(monkeypatch):
    _disable_mp(monkeypatch)
    from services.mercadopago_service import handle_webhook

    async def go():
        with pytest.raises(HTTPException) as e:
            await handle_webhook(
                None, data_id="1", notif_type="preapproval",
                x_signature=None, x_request_id=None,
            )
        assert e.value.status_code == 503

    asyncio.run(go())


def test_webhook_400_on_bad_signature(monkeypatch):
    _enable_mp(monkeypatch, secret="sekret")
    from services.mercadopago_service import handle_webhook

    async def go():
        with pytest.raises(HTTPException) as e:
            await handle_webhook(
                None, data_id="123", notif_type="preapproval",
                x_signature="ts=1,v1=bad", x_request_id="r",
            )
        assert e.value.status_code == 400  # firma inválida → corta antes de la red

    asyncio.run(go())


def test_webhook_503_in_prod_without_secret(monkeypatch):
    _enable_mp(monkeypatch, secret="")  # MP activo pero sin webhook secret, DEBUG=False
    from services.mercadopago_service import handle_webhook

    async def go():
        with pytest.raises(HTTPException) as e:
            await handle_webhook(
                None, data_id="123", notif_type="preapproval",
                x_signature="ts=1,v1=x", x_request_id="r",
            )
        assert e.value.status_code == 503

    asyncio.run(go())


def test_webhook_ignores_non_subscription_types(monkeypatch):
    _enable_mp(monkeypatch, secret="sekret")
    from services.mercadopago_service import handle_webhook

    did, rid, ts = "999", "r1", "1700000000"
    v1 = _sign("sekret", did, rid, ts)
    sig = f"ts={ts},v1={v1}"

    async def go():
        # firma válida + tipo "payment" → ignorado SIN llamar a la red
        out = await handle_webhook(
            None, data_id=did, notif_type="payment",
            x_signature=sig, x_request_id=rid,
        )
        assert out["status"] == "ignored"

    asyncio.run(go())


def _run_all():
    import inspect
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

    class _MP:
        def setattr(self, obj, name, val, raising=True):
            setattr(obj, name, val)

    passed = 0
    for fn in fns:
        params = inspect.signature(fn).parameters
        fn(_MP()) if "monkeypatch" in params else fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed} tests pasaron.")


if __name__ == "__main__":
    _run_all()
