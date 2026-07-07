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
    tok = confirm.make_token("register_payment", p, user_id="user-a")
    action, payload, nonce = confirm.verify_token(tok, user_id="user-a")
    assert action == "register_payment" and payload["monto"] == 5000.0
    assert nonce  # todo token lleva nonce único
    # firma adulterada → rechazo
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(tok[:-4] + "dead", user_id="user-a")
    # payload adulterado (cambiar el monto) invalida la firma
    import base64
    import json
    b64, sig = tok.split(".", 1)
    body = json.loads(base64.urlsafe_b64decode(b64))
    body["p"]["monto"] = 999999
    fake_b64 = base64.urlsafe_b64encode(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).decode()
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(f"{fake_b64}.{sig}", user_id="user-a")


def test_token_atado_al_usuario():
    """El token de A no lo puede confirmar B (u va firmado en el body)."""
    p, _ = confirm.validate("register_payment", {
        "concepto": "x", "monto": 5000, "fecha": "2026-07-10", "estado": "pendiente"})
    tok = confirm.make_token("register_payment", p, user_id="user-a")
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(tok, user_id="user-b")


def test_nonces_distintos_y_rechazo_por_nonce_persistido():
    """Dos tokens del mismo payload llevan nonces distintos; un nonce ya
    consumido (persistido en prefs) rechaza el token aunque el proceso
    se haya reiniciado (no depende de _USED_TOKENS in-memory)."""
    p, _ = confirm.validate("register_payment", {
        "concepto": "x", "monto": 5000, "fecha": "2026-07-10", "estado": "pendiente"})
    t1 = confirm.make_token("register_payment", p, user_id="u")
    t2 = confirm.make_token("register_payment", p, user_id="u")
    assert t1 != t2
    _, _, n1 = confirm.verify_token(t1, user_id="u")
    # simular redeploy: el nonce quedó en prefs, la memoria está limpia
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(t1, user_id="u", used_nonces=[n1])
    # el otro token sigue vivo
    assert confirm.verify_token(t2, user_id="u", used_nonces=[n1])[0] == "register_payment"


def test_persist_nonce_en_prefs():
    user = SimpleNamespace(id=uuid4(), automation_prefs={"daily_summary": True})
    confirm.persist_nonce(user, "abc123")
    assert "abc123" in confirm.get_used_nonces(user)
    assert user.automation_prefs["daily_summary"] is True  # no pisa lo previo


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
    user = SimpleNamespace(id=uuid4(), automation_prefs=None)
    prev = await agent_tools.run_tool("register_payment", db, user, {
        "concepto": "Hormigón", "monto": 5000, "fecha": "2026-07-10", "estado": "pendiente"})
    out = await agent_tools.run_tool("confirm_action", db, user,
                                     {"confirm_token": prev["confirm_token"]})
    assert out.get("ok") is True and out.get("confirmed") is True
    assert len(db.added) == 1  # ahora SÍ se escribió el Payment
    assert str(db.added[0].concepto) == "Hormigón"
    # el nonce consumido quedó persistido en las prefs (anti-replay post-redeploy)
    assert len(confirm.get_used_nonces(user)) == 1


@pytest.mark.anyio
async def test_run_tool_confirm_rechaza_token_de_otro_usuario():
    db = _FakeDB()
    user_a = SimpleNamespace(id=uuid4(), automation_prefs=None)
    user_b = SimpleNamespace(id=uuid4(), automation_prefs=None)
    prev = await agent_tools.run_tool("register_payment", db, user_a, {
        "concepto": "x", "monto": 6100, "fecha": "2026-07-10", "estado": "pendiente"})
    out = await agent_tools.run_tool("confirm_action", db, user_b,
                                     {"confirm_token": prev["confirm_token"]})
    assert "error" in out and db.added == []


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
    tok = confirm.make_token("register_payment", p, user_id="u")
    # marcador oculto persiste el token y el strip lo saca
    persisted = append_confirm_marker("¿Confirmás?", [tok])
    assert tok in persisted and "<!--sol-confirm:" in persisted
    assert strip_confirm_marker(persisted) == "¿Confirmás?"
    # token fresco OK
    assert confirm.verify_token(tok, user_id="u")[0] == "register_payment"
    # vencido → rechazo
    viejo = confirm.make_token("register_payment", p, user_id="u", now=int(_t.time()) - 2000)
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(viejo, user_id="u")
    # usado → rechazo
    confirm.mark_used(tok)
    with pytest.raises(confirm.ValidationError):
        confirm.verify_token(tok, user_id="u")


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


# ── Human-in-the-loop server-side: no confirmar en el MISMO turno ──

class _Blk:
    def __init__(self, **kw): self.__dict__.update(kw)


class _Resp:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = {"input_tokens": 1, "output_tokens": 1}


class _SameTurnProvider:
    """Modelo que pide register_payment y en la MISMA vuelta intenta confirmar el
    token recién emitido (sin esperar al usuario). El corte server-side en
    run_agent tiene que rechazarlo: la confirmación va en el turno siguiente."""
    name = "fake"
    model = "fake-model"

    def __init__(self): self.calls = 0

    async def generate(self, *, system, messages, tools, max_tokens):
        import json as _j
        self.calls += 1
        if self.calls == 1:
            return _Resp([_Blk(type="tool_use", id="a", name="register_payment",
                               input={"concepto": "x", "monto": 4321,
                                      "fecha": "2026-07-10", "estado": "pendiente"})], "tool_use")
        if self.calls == 2:
            tok = None
            for m in reversed(messages):
                if m.get("role") == "user" and isinstance(m.get("content"), list):
                    for b in m["content"]:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            data = _j.loads(b["content"])
                            if data.get("confirm_token"):
                                tok = data["confirm_token"]
                    if tok:
                        break
            return _Resp([_Blk(type="tool_use", id="b", name="confirm_action",
                               input={"confirm_token": tok})], "tool_use")
        return _Resp([_Blk(type="text", text="ok")], "end_turn")


class _CtxlessDB:
    """Hace fallar build_context_pack (pack vacío, best-effort) y registra escrituras."""
    def __init__(self): self.added = []
    async def execute(self, *a, **k): raise RuntimeError("sin contexto en el test")
    def add(self, o): self.added.append(o)
    async def commit(self): pass
    async def refresh(self, o):
        if not getattr(o, "id", None):
            o.id = uuid4()
    async def rollback(self): pass


@pytest.mark.anyio
async def test_run_agent_rechaza_confirmar_en_el_mismo_turno(monkeypatch):
    """Defensa PRIMARIA: aunque el modelo emita register_payment y confirm_action
    en la misma vuelta, no se escribe nada — la confirmación exige un turno nuevo."""
    import services.agent_service as agent_service
    prov = _SameTurnProvider()
    monkeypatch.setattr(agent_service, "get_provider", lambda: prov)
    db = _CtxlessDB()
    user = SimpleNamespace(id=uuid4(), email="m@x.com", full_name="M", phone=None,
                           automation_prefs=None, plan="pro")
    events = []
    async for ev in agent_service.run_agent(db, user, [], "registrá un pago de 4321"):
        events.append(ev)
    confirm_results = [e for e in events
                       if e.get("type") == "tool_result" and e.get("name") == "confirm_action"]
    assert confirm_results, "esperaba un tool_result de confirm_action"
    assert "error" in confirm_results[-1]["result"]
    assert db.added == []  # NADA se escribió: el pago no se registró en el mismo turno
