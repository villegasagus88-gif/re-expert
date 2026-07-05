"""Tests del modo Jarvis de SOL: context pack, tools de conocimiento
(noticias/chats/deal room), Telegram como agente completo y daily digest.

Sin red ni DB real: fakes mínimos y monkeypatch.
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest

import services.agent_service as agent_service
import services.agent_tools as agent_tools
import services.scheduler_service as scheduler_service
import services.telegram_service as telegram_service
from config.settings import settings as _settings


# ── render_context_pack (pura) ──

def test_context_pack_completo():
    data = {
        "nombre": "Mati", "email": "m@x.com", "plan": "pro", "telegram": True,
        "automation_prefs": {"daily_summary": True, "alert_overruns": False},
        "contacts_count": 4,
        "projects": [
            {"nombre": "Edificio Sarmiento", "avance_real_pct": 62, "avance_plan_pct": 70,
             "presupuesto_base": 100000, "costo_real": 112000},
        ],
        "pagos_pendientes": [
            {"concepto": "Hormigón", "monto": 5000, "fecha": "2026-07-10"},
        ],
        "reminders": [{"message": "Llamar a Carlos", "due_at": "2026-07-05T10:00:00"}],
        "opportunities": [{"titulo": "Lote Núñez", "score": 78, "recomendacion": "Avanzar"}],
    }
    pack = agent_service.render_context_pack(data)
    assert "Mati" in pack and "plan pro" in pack and "Telegram conectado" in pack
    assert "Edificio Sarmiento" in pack and "avance 62%" in pack
    assert "+12%" in pack  # desvío de costo calculado
    assert "Hormigón" in pack and "Llamar a Carlos" in pack
    assert "Lote Núñez" in pack and "daily_summary" in pack


def test_context_pack_usuario_nuevo():
    pack = agent_service.render_context_pack({"email": "n@x.com", "plan": "trial"})
    assert "ninguno cargado" in pack
    assert "SIN Telegram" in pack


def test_context_pack_no_miente_totales():
    """GROUNDING: con 20 pagos totales pero 8 en el preview, el pack muestra el
    total REAL (no la suma de los 8) y marca cuántos quedan fuera."""
    data = {
        "email": "x", "plan": "pro",
        "pagos_pendientes": [{"concepto": f"p{i}", "monto": 1000, "fecha": "2026-07-10"}
                             for i in range(8)],
        "pagos_pendientes_count": 20,
        "pagos_pendientes_total": 50000.0,
    }
    pack = agent_service.render_context_pack(data)
    assert "20 por $50,000" in pack   # total real, no $8.000
    assert "+12 más" in pack          # marca los que no están en el preview


@pytest.mark.anyio
async def test_get_payments_summary_agrega_en_sql():
    """La tool de agregación devuelve count+sum por estado (el modelo no suma)."""
    class _AggDB:
        async def execute(self, *_a, **_k):
            rows = [("pendiente", 3, 15000.0), ("pagado", 2, 8000.0)]
            class _R:
                def all(self): return rows
            return _R()
    out = await agent_tools._tool_get_payments_summary(_AggDB(), SimpleNamespace(id=uuid4()))
    assert out["por_estado"]["pendiente"] == {"count": 3, "total": 15000.0}
    assert out["total_general"] == 23000.0


class _CtxDB:
    """DB fake que devuelve, en orden, los resultados de las 7 queries de
    build_context_pack: projects, pagos, pagos_agg, reminders, opps, count, tg.
    Cada item puede ser una lista (scalars().all/first) o una tupla (first())."""
    def __init__(self, results):
        self._results = list(results)
    async def execute(self, *_a, **_k):
        val = self._results.pop(0)
        class _R:
            def __init__(self, v): self._v = v
            def scalar(self): return self._v
            def first(self):
                # tupla → agregación; lista → primera fila o None
                if isinstance(self._v, tuple): return self._v
                return self._v[0] if isinstance(self._v, list) and self._v else None
            def scalars(self):
                v = self._v
                class _S:
                    def all(self): return v if isinstance(v, list) else []
                    def first(self): return v[0] if isinstance(v, list) and v else None
                return _S()
        return _R(val)


@pytest.mark.anyio
async def test_build_context_pack_no_se_cae_con_reminders():
    """REGRESIÓN bug B: un Reminder real tiene .title, NO .message. El código
    usaba r.message → AttributeError tragado por el try/except → pack vacío para
    cualquiera con recordatorios pendientes (SOL perdía TODO el contexto)."""
    from datetime import datetime
    user = SimpleNamespace(
        id=uuid4(), full_name="Mati", email="m@x.com", plan="pro",
        automation_prefs={},
    )
    # SimpleNamespace NO tiene .message → si el código lo usa, revienta.
    reminder = SimpleNamespace(title="Pagar hormigón", due_at=datetime(2026, 7, 10))
    # Orden: projects, pagos, pagos_agg(count,sum), reminders, opps, count, tg
    db = _CtxDB([[], [], (0, 0), [reminder], [], 0, []])
    pack = await agent_service.build_context_pack(db, user)
    assert pack != ""  # el pack NO se cayó
    assert "Pagar hormigón" in pack  # el título del reminder está presente
    assert "Mati" in pack


def test_system_prompt_inyecta_pack():
    s = agent_service._system_prompt("- Usuario: Test · plan pro")
    assert "- Usuario: Test · plan pro" in s
    assert "__CONTEXT_PACK__" not in s
    # sin pack → placeholder amable, no el marcador crudo
    s2 = agent_service._system_prompt("")
    assert "__CONTEXT_PACK__" not in s2


def test_tools_jarvis_registradas():
    for name in ("get_news", "search_chats", "get_opportunities"):
        assert name in agent_tools.TOOL_IMPLS
        assert any(t["name"] == name for t in agent_tools.TOOL_SCHEMAS)


# ── get_news (fetch_feed mockeado) ──

@pytest.mark.anyio
async def test_get_news_mapea_feed(monkeypatch):
    async def _fake_feed(category="todas", page=1, per_page=12, refresh=False):
        return {"items": [{"title": "Sube el dólar", "source": "Ámbito",
                           "category": "macro", "snippet": "x" * 500, "url": "https://a"}]}
    import services.news_live as nl
    monkeypatch.setattr(nl, "fetch_feed", _fake_feed)
    out = await agent_tools._tool_get_news(None, None, category="macro", limit=3)
    assert out["count"] == 1
    it = out["items"][0]
    assert it["titulo"] == "Sube el dólar" and it["fuente"] == "Ámbito"
    assert len(it["resumen"]) <= 220


@pytest.mark.anyio
async def test_get_news_degrada_sin_romper(monkeypatch):
    async def _boom(**_k):
        raise RuntimeError("red caída")
    import services.news_live as nl
    monkeypatch.setattr(nl, "fetch_feed", _boom)
    out = await agent_tools._tool_get_news(None, None)
    assert "error" in out


# ── search_chats ──

class _FakeChatDB:
    def __init__(self, rows): self._rows = rows
    async def execute(self, *_a, **_k):
        rows = self._rows
        class _R:
            def all(self): return rows
        return _R()


@pytest.mark.anyio
async def test_search_chats_snippets():
    from datetime import datetime
    msg = SimpleNamespace(
        content="Hablamos del terreno de Belgrano y el FOT permitido en la zona R2b.",
        role="assistant", conversation_id=uuid4(), created_at=datetime(2026, 6, 1),
    )
    db = _FakeChatDB([(msg, "Análisis Belgrano")])
    user = SimpleNamespace(id=uuid4())
    out = await agent_tools._tool_search_chats(db, user, query="FOT")
    assert out["count"] == 1
    it = out["items"][0]
    assert it["conversacion"] == "Análisis Belgrano"
    assert "FOT" in it["fragmento"]


@pytest.mark.anyio
async def test_search_chats_query_corta():
    out = await agent_tools._tool_search_chats(None, None, query="a")
    assert "error" in out


# ── get_opportunities ──

class _FakeOppDB:
    def __init__(self, rows): self._rows = rows
    async def execute(self, *_a, **_k):
        rows = self._rows
        class _S:
            def all(self): return rows
        class _R:
            def scalars(self): return _S()
        return _R()


@pytest.mark.anyio
async def test_get_opportunities_shape():
    o = SimpleNamespace(
        id=uuid4(), titulo="Lote Núñez", zona="Núñez", ciudad="CABA",
        tipo_inmueble="terreno", estado_pipeline="analizada", score=78.0,
        recomendacion="Avanzar", last_analyzed_at=None,
        analysis={"finanzas": {"margen_neto_pct": 22.5, "tir_anual_pct": 31.0}},
    )
    out = await agent_tools._tool_get_opportunities(_FakeOppDB([o]), SimpleNamespace(id=uuid4()))
    assert out["count"] == 1
    it = out["items"][0]
    assert it["margen_neto_pct"] == 22.5 and it["tir_anual_pct"] == 31.0


# ── Telegram: mensaje libre → agente ──

@pytest.mark.anyio
async def test_telegram_mensaje_libre_sin_pairing(monkeypatch):
    monkeypatch.setattr(_settings, 'TELEGRAM_AGENT_ENABLED', True, raising=False)
    sent = []
    async def _fake_send(chat_id, text):
        sent.append(text); return {"ok": True}
    monkeypatch.setattr(telegram_service, "send_message", _fake_send)

    class _DB:
        async def execute(self, *_a, **_k):
            class _S:
                def first(self): return None
            class _R:
                def scalars(self): return _S()
            return _R()

    out = await telegram_service.handle_webhook_update(
        _DB(), {"message": {"chat": {"id": 123}, "text": "hola SOL"}}
    )
    assert out.get("unpaired") is True
    assert any("Conectar Telegram" in t for t in sent)


@pytest.mark.anyio
async def test_telegram_dedupe_update_id(monkeypatch):
    monkeypatch.setattr(_settings, 'TELEGRAM_AGENT_ENABLED', True, raising=False)
    """El mismo update_id no se procesa dos veces (Telegram re-entrega ante error)."""
    async def _fake_send(chat_id, text): return {"ok": True}
    monkeypatch.setattr(telegram_service, "send_message", _fake_send)

    class _DB:
        async def execute(self, *_a, **_k):
            class _S:
                def first(self): return None
            class _R:
                def scalars(self): return _S()
            return _R()

    uid = 987654321  # update_id único para este test
    payload = {"update_id": uid, "message": {"chat": {"id": 5}, "text": "hola"}}
    first = await telegram_service.handle_webhook_update(_DB(), payload)
    second = await telegram_service.handle_webhook_update(_DB(), payload)
    assert first.get("unpaired") is True  # se procesó
    assert second.get("skipped") == "duplicate_update"  # el reenvío se ignoró


@pytest.mark.anyio
async def test_telegram_mensaje_libre_despacha_agente(monkeypatch):
    monkeypatch.setattr(_settings, 'TELEGRAM_AGENT_ENABLED', True, raising=False)
    calls = {}
    async def _fake_reply(chat_id, user_id, text):
        calls["args"] = (chat_id, str(user_id), text)
    monkeypatch.setattr(telegram_service, "_agent_reply", _fake_reply)

    uid = uuid4()
    row = SimpleNamespace(user_id=uid)

    class _DB:
        async def execute(self, *_a, **_k):
            class _S:
                def first(self): return row
            class _R:
                def scalars(self): return _S()
            return _R()

    out = await telegram_service.handle_webhook_update(
        _DB(), {"message": {"chat": {"id": 55}, "text": "cuánto gasté este mes?"}}
    )
    assert out.get("agent_dispatched") is True
    # el task corre async; darle un tick al loop
    import asyncio
    await asyncio.sleep(0)
    assert calls["args"] == ("55", str(uid), "cuánto gasté este mes?")


@pytest.mark.anyio
async def test_telegram_mensaje_muy_largo(monkeypatch):
    monkeypatch.setattr(_settings, 'TELEGRAM_AGENT_ENABLED', True, raising=False)
    sent = []
    async def _fake_send(chat_id, text):
        sent.append(text); return {"ok": True}
    monkeypatch.setattr(telegram_service, "send_message", _fake_send)
    row = SimpleNamespace(user_id=uuid4())

    class _DB:
        async def execute(self, *_a, **_k):
            class _S:
                def first(self): return row
            class _R:
                def scalars(self): return _S()
            return _R()

    out = await telegram_service.handle_webhook_update(
        _DB(), {"message": {"chat": {"id": 9}, "text": "x" * 1600}}
    )
    assert out.get("too_long") is True


# ── Daily digest ──

@pytest.mark.anyio
async def test_daily_digest_respeta_prefs(monkeypatch):
    u_si = SimpleNamespace(id=uuid4(), automation_prefs={"daily_summary": True})
    u_no = SimpleNamespace(id=uuid4(), automation_prefs={"daily_summary": False})
    u_vacio = SimpleNamespace(id=uuid4(), automation_prefs=None)
    ch = SimpleNamespace()

    class _DB:
        async def execute(self, *_a, **_k):
            class _R:
                def all(self): return [(u_si, ch), (u_no, ch), (u_vacio, ch)]
            return _R()
        async def commit(self): pass
        async def rollback(self): pass

    async def _fake_pack(db, user):
        return "- Usuario: X · plan pro"
    monkeypatch.setattr(agent_service, "build_context_pack", _fake_pack)

    dispatched = []
    async def _fake_dispatch(db, user, *, channel, title, body, attachment_url=None):
        dispatched.append((user.id, channel, body)); return {"ok": True, "channel": channel}
    monkeypatch.setattr(scheduler_service, "dispatch", _fake_dispatch)

    n = await scheduler_service._run_daily_digest(_DB())
    assert n == 1
    assert dispatched[0][0] == u_si.id and dispatched[0][1] == "telegram"
    assert "Tu resumen de hoy" in dispatched[0][2]

    # IDEMPOTENCIA: el segundo run del mismo día (reinicio/deploy) no re-manda —
    # la marca _last_digest_date quedó en las prefs del usuario.
    assert u_si.automation_prefs.get("_last_digest_date")
    n2 = await scheduler_service._run_daily_digest(_DB())
    assert n2 == 0 and len(dispatched) == 1
