"""Tests del flujo de confirmación de SOL (preview + confirm_action).

Cubre lo crítico de la regla 4: ninguna escritura ejecuta sin confirmación,
la validación server-side corta typos, el token HMAC garantiza integridad, y
el anti-replay por turno fuerza el human-in-the-loop.
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest

import services.agent_confirm as confirm
import services.agent_tools as agent_tools


# ── Validación server-side ──

@pytest.mark.parametrize("inputs", [
    {"concepto": "x", "monto": 0, "fecha": "2026-07-10", "estado": "pendiente"},
    {"concepto": "x", "monto": -100, "fecha": "2026-07-10", "estado": "pendiente"},
    {"concepto": "x", "monto": 1e11, "fecha": "2026-07-10", "estado": "pendiente"},
    {"concepto": "x", "monto": 100, "fecha": "no-fecha", "estado": "pendiente"},
    {"concepto": "x", "monto": 100, "fecha": "2026-07-10", "estado": "inventado"},
    {"concepto": "", "monto": 100, "fecha": "2026-07-10", "estado": "pendiente"},
])
def test_register_payment_rechaza_invalidos(inputs):
    with pytest.raises(confirm.ValidationError):
        confirm.validate("register_payment", inputs)


def test_register_payment_ok_normaliza():
    p, resumen = confirm.validate("register_payment", {
        "concepto": "Hormigón", "monto": "5000", "fecha": "2026-07-10", "estado": "pendiente"})
    assert p["monto"] == 5000.0 and p["estado"] == "pendiente"
    assert "5,000.00" in resumen


def test_schedule_reminder_rechaza_canal_stub():
    # whatsapp/email/push hoy son stubs que fallan → no dejar agendar ahí
    with pytest.raises(confirm.ValidationError):
        confirm.validate("schedule_reminder", {
            "title": "x", "due_at": "2027-01-01T10:00:00-03:00", "channel": "whatsapp"})


def test_telefono_normalizado():
    p, _ = confirm.validate("add_contact", {"name": "Juan", "phone": "(011) 15-5555-5555"})
    assert p["phone"] and p["phone"].lstrip("+").isdigit()
    with pytest.raises(confirm.ValidationError):
        confirm.validate("add_contact", {"name": "Juan", "phone": "123"})  # muy corto


# ── Token HMAC ──

def test_token_roundtrip_e_integridad():
    p, _ = confirm.validate("register_payment", {
        "concepto": "x", "monto": 5000, "fecha": "2026-07-10", "estado": "pendiente"})
    tok = confirm.make_token("register_payment", p)
    action, payload = confirm.verify_token(tok)
    assert action == "register_payment" and payload["monto"] == 5000.0
    # firma adulterada → rechazo
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(tok[:-4] + "dead")
    # payload adulterado (cambiar el monto) invalida la firma
    import base64
    import json
    b64, sig = tok.split(".", 1)
    body = json.loads(base64.urlsafe_b64decode(b64))
    body["p"]["monto"] = 999999
    fake_b64 = base64.urlsafe_b64encode(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).decode()
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(f"{fake_b64}.{sig}")


# ── run_tool: preview no ejecuta; confirm ejecuta ──

class _FakeDB:
    def __init__(self): self.added = []
    def add(self, obj): self.added.append(obj)
    async def commit(self): pass
    async def refresh(self, obj):
        if not getattr(obj, "id", None):
            obj.id = uuid4()
    async def rollback(self): pass


@pytest.mark.anyio
async def test_run_tool_write_action_no_ejecuta_devuelve_preview():
    db = _FakeDB()
    user = SimpleNamespace(id=uuid4())
    out = await agent_tools.run_tool("register_payment", db, user, {
        "concepto": "Hormigón", "monto": 5000, "fecha": "2026-07-10", "estado": "pendiente"})
    assert out["needs_confirmation"] is True
    assert out["action"] == "register_payment"
    assert out["confirm_token"] and "5,000.00" in out["resumen"]
    assert db.added == []  # NADA se escribió


@pytest.mark.anyio
async def test_run_tool_confirm_ejecuta_con_token_valido():
    db = _FakeDB()
    user = SimpleNamespace(id=uuid4())
    prev = await agent_tools.run_tool("register_payment", db, user, {
        "concepto": "Hormigón", "monto": 5000, "fecha": "2026-07-10", "estado": "pendiente"})
    out = await agent_tools.run_tool("confirm_action", db, user,
                                     {"confirm_token": prev["confirm_token"]})
    assert out.get("ok") is True and out.get("confirmed") is True
    assert len(db.added) == 1  # ahora SÍ se escribió el Payment
    assert str(db.added[0].concepto) == "Hormigón"


@pytest.mark.anyio
async def test_run_tool_confirm_rechaza_token_basura():
    db = _FakeDB()
    out = await agent_tools.run_tool("confirm_action", db, SimpleNamespace(id=uuid4()),
                                     {"confirm_token": "no.es.valido"})
    assert "error" in out and db.added == []


def test_token_ttl_y_reuso():
    import time as _t
    from services.agent_service import append_confirm_marker, strip_confirm_marker
    p, _ = confirm.validate("register_payment", {
        "concepto": "x", "monto": 7777, "fecha": "2026-07-10", "estado": "pendiente"})
    tok = confirm.make_token("register_payment", p)
    # marcador oculto persiste el token y el strip lo saca
    persisted = append_confirm_marker("¿Confirmás?", [tok])
    assert tok in persisted and "<!--sol-confirm:" in persisted
    assert strip_confirm_marker(persisted) == "¿Confirmás?"
    # token fresco OK
    assert confirm.verify_token(tok)[0] == "register_payment"
    # vencido → rechazo
    viejo = confirm.make_token("register_payment", p, now=int(_t.time()) - 2000)
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(viejo)
    # usado → rechazo
    confirm.mark_used(tok)
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(tok)


@pytest.mark.anyio
async def test_confirm_no_reejecuta_token_usado():
    """Un token ya confirmado no vuelve a ejecutar la acción (anti doble-pago)."""
    db = _FakeDB()
    user = SimpleNamespace(id=uuid4())
    prev = await agent_tools.run_tool("register_payment", db, user, {
        "concepto": "x", "monto": 8888, "fecha": "2026-07-10", "estado": "pendiente"})
    tok = prev["confirm_token"]
    first = await agent_tools.run_tool("confirm_action", db, user, {"confirm_token": tok})
    assert first.get("ok") is True and len(db.added) == 1
    # segundo intento con el MISMO token → rechazado, no crea otro pago
    second = await agent_tools.run_tool("confirm_action", db, user, {"confirm_token": tok})
    assert "error" in second and len(db.added) == 1


@pytest.mark.anyio
async def test_confirm_no_ejecuta_montos_alterados_via_validate():
    """Aunque el modelo pase por register_payment con monto inválido, el preview
    ni siquiera se genera: no hay token para confirmar."""
    db = _FakeDB()
    out = await agent_tools.run_tool("register_payment", db, SimpleNamespace(id=uuid4()),
                                     {"concepto": "x", "monto": -1, "fecha": "2026-07-10",
                                      "estado": "pendiente"})
    assert "error" in out and "confirm_token" not in out
