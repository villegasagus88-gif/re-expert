"""Tests de la compra de cursos (Checkout Pro + webhook de pago único).

Cubre lo crítico sin red ni DB: precio SIEMPRE del catálogo, payload correcto
de la preference, mapeo estado-de-pago→compra e idempotencia del webhook.
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest

import services.mercadopago_service as mp
from api.routes.academia import _find_course
from config.settings import settings


# ── _find_course: precio/is_free salen del catálogo real, no del cliente ──

def test_find_course_devuelve_curso_real():
    # tomamos el primer curso del catálogo real
    from api.routes.academia import _COURSES_PATH, _load_json
    cat0 = _load_json(str(_COURSES_PATH))["categories"][0]["courses"][0]
    found = _find_course(cat0["id"])
    assert found is not None and found["id"] == cat0["id"]
    assert "price_ars" in found and "is_free" in found


def test_find_course_inexistente():
    assert _find_course("no-existe-xyz") is None


# ── create_course_preference: payload correcto + precio del backend ──

@pytest.mark.anyio
async def test_create_course_preference_payload(monkeypatch):
    monkeypatch.setattr(settings, "MP_ACCESS_TOKEN", "TESTTOKEN", raising=False)
    monkeypatch.setattr(settings, "MP_PLAN_ID", "PLAN123", raising=False)
    captured = {}

    class _Resp:
        status_code = 201
        def json(self):
            return {"init_point": "https://mp/checkout/xyz", "id": "PREF-1"}

    class _Client:
        def __init__(self, *a, **k): ...
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            return _Resp()

    monkeypatch.setattr(mp.httpx, "AsyncClient", _Client)
    user = SimpleNamespace(id=uuid4(), email="u@x.com")
    out = await mp.create_course_preference(user, purchase_id="PID-9", title="Curso X", price_ars=220000)

    assert out["url"] == "https://mp/checkout/xyz"
    assert out["preference_id"] == "PREF-1"
    assert captured["url"].endswith("/checkout/preferences")
    item = captured["json"]["items"][0]
    assert item["unit_price"] == 220000.0 and item["currency_id"] == "ARS"
    assert captured["json"]["external_reference"] == "PID-9"  # matchea el webhook


# ── _apply_payment_to_purchase: mapeo + idempotencia ──

class _FakeResult:
    """La query por id usa scalar_one_or_none(); la búsqueda de otra fila owned
    (anti-duplicado) usa scalars().first() → acá devuelve None (sin duplicado)."""
    def __init__(self, obj): self._o = obj
    def scalar_one_or_none(self): return self._o
    def scalars(self):
        class _S:
            def first(self): return None
            def all(self): return []
        return _S()

class _FakeDB:
    def __init__(self, obj): self._o = obj
    async def execute(self, *_a, **_k): return _FakeResult(self._o)


@pytest.mark.anyio
@pytest.mark.parametrize("mp_status,expected", [
    ("approved", "approved"),
    ("rejected", "rejected"),
    ("cancelled", "rejected"),
    ("refunded", "refunded"),
])
async def test_apply_payment_mapea_estados(mp_status, expected):
    pid = uuid4()
    purchase = SimpleNamespace(id=uuid4(), user_id=uuid4(), course_id="c-1",
                               status="pending", mp_payment_id=None)
    db = _FakeDB(purchase)
    res = await mp._apply_payment_to_purchase(
        db, {"status": mp_status, "external_reference": str(pid), "id": "PAY-1"})
    assert res == str(pid)
    assert purchase.status == expected
    assert purchase.mp_payment_id == "PAY-1"


@pytest.mark.anyio
async def test_apply_payment_estado_pendiente_no_toca():
    purchase = SimpleNamespace(status="pending", mp_payment_id=None)
    res = await mp._apply_payment_to_purchase(
        _FakeDB(purchase), {"status": "in_process", "external_reference": str(uuid4())})
    assert res is None
    assert purchase.status == "pending"  # sin cambios


@pytest.mark.anyio
async def test_apply_payment_idempotente_no_degrada_approved():
    purchase = SimpleNamespace(status="approved", mp_payment_id="PAY-OLD")
    # un webhook 'approved' repetido no cambia nada
    await mp._apply_payment_to_purchase(
        _FakeDB(purchase), {"status": "approved", "external_reference": str(uuid4()), "id": "PAY-2"})
    assert purchase.status == "approved"
    # pero un refund SÍ debe degradar un approved
    await mp._apply_payment_to_purchase(
        _FakeDB(purchase), {"status": "refunded", "external_reference": str(uuid4()), "id": "PAY-3"})
    assert purchase.status == "refunded"


@pytest.mark.anyio
async def test_apply_payment_external_reference_invalido():
    purchase = SimpleNamespace(status="pending", mp_payment_id=None)
    res = await mp._apply_payment_to_purchase(
        _FakeDB(purchase), {"status": "approved", "external_reference": "no-uuid"})
    assert res is None
    assert purchase.status == "pending"


# ── _apply_payment_to_purchase: pago duplicado no viola el unique parcial ──

class _FakeDBDup:
    """Primera query devuelve la compra target; la segunda (búsqueda de otra fila
    owned del mismo user+curso) devuelve `other`."""
    def __init__(self, target, other):
        self._results = [target, other]
    async def execute(self, *_a, **_k):
        obj = self._results.pop(0) if self._results else None
        class _R:
            def __init__(self, o): self._o = o
            def scalar_one_or_none(self): return self._o
            def scalars(self):
                o = self._o
                class _S:
                    def first(self): return o
                    def all(self): return [o] if o else []
                return _S()
        return _R(obj)


@pytest.mark.anyio
async def test_apply_payment_duplicado_no_pisa_al_owned():
    """Segundo pago aprobado del mismo (user, curso) → la fila queda 'duplicate'
    (para reembolso manual), NUNCA 'approved' (violaría el unique parcial)."""
    uid, cid = uuid4(), "curso-x"
    target = SimpleNamespace(id=uuid4(), user_id=uid, course_id=cid,
                             status="pending", mp_payment_id=None)
    owned = SimpleNamespace(id=uuid4(), user_id=uid, course_id=cid,
                            status="approved", mp_payment_id="PAY-1")
    res = await mp._apply_payment_to_purchase(
        _FakeDBDup(target, owned),
        {"status": "approved", "external_reference": str(target.id), "id": "PAY-2"})
    assert res == str(target.id)
    assert target.status == "duplicate"
    assert target.mp_payment_id == "PAY-2"  # trazable para el refund
    assert owned.status == "approved"       # el acceso original no se toca


# ── handle_webhook: el topic "payment" despacha al flujo de cursos ──

@pytest.mark.anyio
async def test_webhook_payment_despacha_a_cursos(monkeypatch):
    """Un webhook tipo 'payment' consulta el pago y lo aplica a la compra."""
    monkeypatch.setattr(settings, "MP_ACCESS_TOKEN", "TEST", raising=False)
    monkeypatch.setattr(settings, "MP_PLAN_ID", "PLAN123", raising=False)  # mp_enabled()
    monkeypatch.setattr(settings, "MP_WEBHOOK_SECRET", "", raising=False)
    monkeypatch.setattr(settings, "DEBUG", True, raising=False)  # sin firma en DEBUG

    calls = {}

    async def _fake_fetch(pid):
        calls["fetched"] = pid
        return {"id": pid, "status": "approved", "external_reference": str(uuid4())}

    async def _fake_apply(db, payment):
        calls["applied"] = payment["id"]
        return payment["external_reference"]

    class _DB:
        async def commit(self):
            calls["committed"] = True

    monkeypatch.setattr(mp, "fetch_payment", _fake_fetch)
    monkeypatch.setattr(mp, "_apply_payment_to_purchase", _fake_apply)

    out = await mp.handle_webhook(
        _DB(), data_id="PAY-77", notif_type="payment",
        x_signature="", x_request_id="",
    )
    assert out["status"] == "ok"
    assert calls == {"fetched": "PAY-77", "applied": "PAY-77", "committed": True}


@pytest.mark.anyio
@pytest.mark.parametrize("topic", [
    # Cobro recurrente de suscripción: contiene "payment" pero NO es un pago de
    # curso — data.id no existe en /v1/payments → si se procesara, 502 en loop.
    "subscription_authorized_payment",
    # Notificación de plan: contiene "preapproval" pero NO es un preapproval.
    "subscription_preapproval_plan",
    "merchant_order",
])
async def test_webhook_topics_no_manejados_se_ignoran_sin_red(monkeypatch, topic):
    """El dispatch es por match EXACTO: los topics parecidos (substring) se
    ignoran con 200 en vez de consultar el endpoint equivocado."""
    monkeypatch.setattr(settings, "MP_ACCESS_TOKEN", "TEST", raising=False)
    monkeypatch.setattr(settings, "MP_PLAN_ID", "PLAN123", raising=False)
    monkeypatch.setattr(settings, "MP_WEBHOOK_SECRET", "", raising=False)
    monkeypatch.setattr(settings, "DEBUG", True, raising=False)

    async def _boom(*_a, **_k):
        raise AssertionError("no debe llamar a la red para topics ignorados")
    monkeypatch.setattr(mp, "fetch_payment", _boom)
    monkeypatch.setattr(mp, "fetch_preapproval", _boom)

    out = await mp.handle_webhook(
        None, data_id="123", notif_type=topic, x_signature="", x_request_id="",
    )
    assert out["status"] == "ignored"


@pytest.mark.anyio
@pytest.mark.parametrize("topic", ["preapproval", "subscription_preapproval"])
async def test_webhook_preapproval_sigue_despachando_suscripcion(monkeypatch, topic):
    """Los dos nombres reales del topic de suscripción llegan a su branch."""
    monkeypatch.setattr(settings, "MP_ACCESS_TOKEN", "TEST", raising=False)
    monkeypatch.setattr(settings, "MP_PLAN_ID", "PLAN123", raising=False)
    monkeypatch.setattr(settings, "MP_WEBHOOK_SECRET", "", raising=False)
    monkeypatch.setattr(settings, "DEBUG", True, raising=False)

    calls = {}
    async def _fake_pre(pid):
        calls["fetched"] = pid
        return {"status": "authorized", "external_reference": str(uuid4())}
    async def _fake_apply(db, ext, status):
        calls["applied"] = status
        return ext
    class _DB:
        async def commit(self): calls["committed"] = True

    monkeypatch.setattr(mp, "fetch_preapproval", _fake_pre)
    monkeypatch.setattr(mp, "_apply_status_to_user", _fake_apply)

    out = await mp.handle_webhook(
        _DB(), data_id="PRE-9", notif_type=topic, x_signature="", x_request_id="",
    )
    assert out["status"] == "ok"
    assert calls == {"fetched": "PRE-9", "applied": "authorized", "committed": True}
