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
async def test_telegram_mensaje_libre_despacha_agente(monkeypatch):
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
