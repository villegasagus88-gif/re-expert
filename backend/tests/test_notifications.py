"""
Track C (a) — WhatsApp (C1) + PDF public-URL warning (C4).

Sin red ni DB: probamos las rutas de configuración/fallback del dispatcher y la
heurística de URL pública. Los canales whatsapp/push/email/in_app del dispatcher
no tocan la DB, así que pasamos un db mockeado.
"""
import asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from services import notification_dispatcher, whatsapp_service
from services.document_service import _is_publicly_reachable


def _user(phone="+5491122334455", email="u@example.com"):
    u = MagicMock()
    u.id = uuid4()
    u.phone = phone
    u.email = email
    return u


def _dispatch(channel, user=None):
    return asyncio.run(
        notification_dispatcher.dispatch(
            MagicMock(),
            user or _user(),
            channel=channel,
            title="Recordatorio",
            body="Llamar al proveedor a las 10.",
        )
    )


# ── C4: public URL heuristic ─────────────────────────────────────────

def test_is_publicly_reachable():
    assert _is_publicly_reachable("https://re.up.railway.app/static/reports/a.pdf") is True
    assert _is_publicly_reachable("http://localhost:8000/static/reports/a.pdf") is False
    assert _is_publicly_reachable("http://127.0.0.1:8000/x") is False
    assert _is_publicly_reachable("http://0.0.0.0:8000/x") is False
    assert _is_publicly_reachable("") is False


# ── C1: WhatsApp service ─────────────────────────────────────────────

def test_whatsapp_not_configured():
    res = asyncio.run(whatsapp_service.send_whatsapp("+5491122334455", "hola"))
    assert res["ok"] is False
    assert res["detail"] == "whatsapp_not_configured"
    assert whatsapp_service.is_configured() is False


# ── C1: dispatcher fallbacks (sin canales configurados en tests) ─────

def test_dispatch_whatsapp_falls_back_to_in_app_when_unconfigured():
    res = _dispatch("whatsapp")
    assert res["ok"] is True
    assert res["channel"] == "in_app"
    assert res["fallback_from"] == "whatsapp"
    assert res["reason"] == "whatsapp_not_configured"


def test_dispatch_whatsapp_without_phone_falls_back():
    res = _dispatch("whatsapp", user=_user(phone=None))
    assert res["channel"] == "in_app"
    assert res["reason"] == "no_phone_on_file"


def test_dispatch_push_degrades_to_in_app():
    res = _dispatch("push")
    assert res["ok"] is True
    assert res["channel"] == "in_app"
    assert res["fallback_from"] == "push"


def test_dispatch_email_unconfigured_falls_back():
    res = _dispatch("email")
    assert res["channel"] == "in_app"
    assert res["fallback_from"] == "email"


def test_dispatch_in_app_always_ok():
    res = _dispatch("in_app")
    assert res["ok"] is True
    assert res["channel"] == "in_app"
