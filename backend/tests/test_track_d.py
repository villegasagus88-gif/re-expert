"""
Track D — tests behavioral de paths críticos sin cubrir:
  1. SOL agent: el loop de tool-use ejecuta tools y emite los eventos correctos.
  2. Telegram webhook: valida el secret header (503 sin config, 403 secret malo).
  3. Stripe webhook: checkout.session.completed flippea el plan del user a 'pro'.

Sin red ni DB real: provider/tools/handlers mockeados, get_db overrideado.
"""
import asyncio
import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from config.settings import settings
from core.auth import get_current_user
from fastapi.testclient import TestClient
from main import app
from models.base import get_db


@contextmanager
def _override_db(mock_db=None):
    mock_db = mock_db or MagicMock()

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db
    try:
        yield mock_db
    finally:
        app.dependency_overrides.clear()


# ════════════════════════════════════════════════════════════════════
# 1. SOL agent — loop de tool-use
# ════════════════════════════════════════════════════════════════════
class _FakeProvider:
    name = "fake"
    model = "gemini-2.5-flash"

    def __init__(self):
        self.calls = 0

    async def generate(self, system, messages, tools, max_tokens=4096):
        from services.llm_providers import ContentBlock, LLMResponse

        self.calls += 1
        if self.calls == 1:
            # Primera vuelta: pide una tool.
            return LLMResponse(
                content=[
                    ContentBlock(
                        type="tool_use", id="t1", name="query_project_status", input={}
                    )
                ],
                stop_reason="tool_use",
                usage={"input_tokens": 10, "output_tokens": 5},
            )
        # Segunda vuelta: responde texto y termina.
        return LLMResponse(
            content=[ContentBlock(type="text", text="Tu obra va al 58%. ✓")],
            stop_reason="end_turn",
            usage={"input_tokens": 3, "output_tokens": 2},
        )


def _run_agent_collect():
    from services.agent_service import run_agent

    provider = _FakeProvider()

    async def _collect():
        events = []
        with (
            patch("services.agent_service.get_provider", return_value=provider),
            patch(
                "services.agent_service.run_tool",
                new=AsyncMock(return_value={"ok": True, "avance": "58%"}),
            ),
        ):
            async for ev in run_agent(MagicMock(), MagicMock(), [], "¿cómo va la obra?"):
                events.append(ev)
        return events

    return asyncio.run(_collect())


def test_agent_loop_dispatches_tool_and_emits_events():
    events = _run_agent_collect()
    types = [e["type"] for e in events]
    assert "tool_use" in types
    assert "tool_result" in types
    assert types[-1] == "done"
    # El tool pedido se ejecutó y se emitió con su nombre.
    tu = next(e for e in events if e["type"] == "tool_use")
    assert tu["name"] == "query_project_status"


def test_agent_done_reports_real_model_and_token_totals():
    events = _run_agent_collect()
    done = next(e for e in events if e["type"] == "done")
    assert done["model"] == "gemini-2.5-flash"  # no 'claude-...' (C5)
    assert done["input_tokens"] == 13  # 10 + 3
    assert done["output_tokens"] == 7  # 5 + 2


# ════════════════════════════════════════════════════════════════════
# 2. Telegram webhook — validación del secret
# ════════════════════════════════════════════════════════════════════
def test_telegram_webhook_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    with _override_db():
        client = TestClient(app)
        r = client.post("/api/channels/telegram/webhook", json={"message": {}})
    assert r.status_code == 503


def test_telegram_webhook_403_on_bad_secret(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "s3cr3t")
    with _override_db():
        client = TestClient(app)
        # sin header
        r1 = client.post("/api/channels/telegram/webhook", json={"message": {}})
        # header equivocado
        r2 = client.post(
            "/api/channels/telegram/webhook",
            json={"message": {}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
        )
    assert r1.status_code == 403
    assert r2.status_code == 403


def test_telegram_webhook_ok_with_correct_secret(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "s3cr3t")
    with _override_db():
        with patch(
            "services.telegram_service.handle_webhook_update",
            new=AsyncMock(return_value={"ok": True, "matched": True}),
        ):
            client = TestClient(app)
            r = client.post(
                "/api/channels/telegram/webhook",
                json={"message": {"text": "/start abc"}},
                headers={"X-Telegram-Bot-Api-Secret-Token": "s3cr3t"},
            )
    assert r.status_code == 200
    assert r.json().get("ok") is True


# ════════════════════════════════════════════════════════════════════
# 3. Stripe webhook — flip de plan
# ════════════════════════════════════════════════════════════════════
class _StripeMockDB:
    def __init__(self, user):
        self._user = user
        self.committed = False

    async def execute(self, stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = self._user
        return result

    async def commit(self):
        self.committed = True


def test_stripe_webhook_flips_user_to_pro(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "")  # ruta json.loads (dev)

    user = MagicMock()
    user.id = uuid4()
    user.plan = "free"
    mock_db = _StripeMockDB(user)

    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"user_id": str(user.id)}, "customer": "cus_123"}},
    }

    with _override_db(mock_db):
        client = TestClient(app)
        r = client.post("/api/stripe/webhook", content=json.dumps(event))

    assert r.status_code == 200
    assert user.plan == "pro"  # el webhook flippeó el plan
    assert user.stripe_customer_id == "cus_123"
    assert mock_db.committed is True


def test_stripe_webhook_503_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "")
    with _override_db():
        client = TestClient(app)
        r = client.post("/api/stripe/webhook", content=json.dumps({"type": "x"}))
    assert r.status_code == 503
