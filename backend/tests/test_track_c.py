"""
Track C — pricing (C5), find_contact disambiguation (C6), Telegram setWebhook (C3).

No real DB or network: find_contact uses a mocked AsyncSession; set_webhook is
tested only on its config-skip paths.
"""
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

# Importamos `settings` desde un módulo de servicio (no desde config.settings):
# test_auth_standalone.py reemplaza sys.modules["config.settings"] por un mock,
# así que `from config.settings import settings` da el mock en la suite completa.
# El singleton real lo comparten todos los servicios que ya lo importaron.
from services.telegram_service import settings
from services.token_usage_service import (
    DEFAULT_PRICING,
    GEMINI_DEFAULT_PRICING,
    PRICING,
    _pricing_for,
    calculate_cost_usd,
)


# ── C5: token pricing ────────────────────────────────────────────────

def test_sonnet_alias_now_priced_explicitly():
    # El alias sin fecha (modelo por defecto) ahora matchea PRICING.
    assert "claude-sonnet-4-6" in PRICING
    assert _pricing_for("claude-sonnet-4-6") == PRICING["claude-sonnet-4-6"]


def test_gemini_priced_as_gemini_not_claude():
    p = _pricing_for("gemini-2.5-flash")
    assert p["input"] == Decimal("0.30")  # no 3.00 (Claude Sonnet)
    gemini = calculate_cost_usd("gemini-2.5-flash", 1_000_000, 1_000_000)
    claude = calculate_cost_usd("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert gemini < claude  # Gemini ya no se cobra como Claude


def test_unknown_gemini_falls_to_gemini_default():
    assert _pricing_for("gemini-9.9-ultra-future") == GEMINI_DEFAULT_PRICING


def test_unknown_model_falls_to_claude_default():
    assert _pricing_for("modelo-desconocido-xyz") == DEFAULT_PRICING


# ── C6: find_contact disambiguation ──────────────────────────────────

def _contact(name, **kw):
    c = MagicMock()
    c.id = kw.get("id", uuid4())
    c.name = name
    c.phone = kw.get("phone")
    c.email = kw.get("email")
    c.role = kw.get("role")
    return c


def _db_returning(rows):
    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute = AsyncMock(return_value=result)
    return db


def _find(rows, name):
    from services.agent_tools import _tool_find_contact

    return asyncio.run(_tool_find_contact(_db_returning(rows), MagicMock(id=uuid4()), name=name))


def test_find_contact_ambiguous_without_top_level_id():
    res = _find([_contact("Carla Lopez"), _contact("Carlos Suarez")], "Car")
    assert res["found"] is True
    assert res["ambiguous"] is True
    assert "id" not in res  # clave: no elige uno solo
    assert len(res["candidates"]) == 2


def test_find_contact_exact_match_wins_over_substring():
    res = _find([_contact("Carlos"), _contact("Carlos Suarez")], "Carlos")
    assert res["ambiguous"] is False
    assert res["name"] == "Carlos"
    assert res["id"]


def test_find_contact_single_match_is_unambiguous():
    res = _find([_contact("Carlos Suarez")], "Carlos")
    assert res["ambiguous"] is False
    assert res["name"] == "Carlos Suarez"


def test_find_contact_not_found():
    res = _find([], "Nadie")
    assert res["found"] is False


# ── C3: Telegram setWebhook ──────────────────────────────────────────

def test_webhook_url_none_without_base(monkeypatch):
    from services import telegram_service

    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_BASE_URL", "")
    assert telegram_service.webhook_url() is None


def test_webhook_url_built_from_base(monkeypatch):
    from services import telegram_service

    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_BASE_URL", "https://x.up.railway.app/")
    assert (
        telegram_service.webhook_url()
        == "https://x.up.railway.app/api/channels/telegram/webhook"
    )


def test_set_webhook_skips_when_bot_not_configured(monkeypatch):
    from services import telegram_service

    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")
    res = asyncio.run(telegram_service.set_webhook())
    assert res.get("skipped") == "telegram_not_configured"


def test_set_webhook_skips_without_base_url(monkeypatch):
    from services import telegram_service

    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "dummy-token")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_BASE_URL", "")
    res = asyncio.run(telegram_service.set_webhook())
    assert res.get("skipped") == "no_webhook_base_url"
