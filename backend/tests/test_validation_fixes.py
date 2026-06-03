"""Tests de regresión de los fixes del sweep de validación (2026-06-03).

Cubre los fixes verificables sin DB ni FastAPI app:
- C1: el costo de Haiku ya no se cobra a tarifa Sonnet (faltaban las pricing
  keys sin sufijo de fecha, que son las que devuelve pick_model()).
- F2: sanitización server-side de contactos/reminders (anti stored-XSS), igual
  que el resto de los schemas del backend.

Pure: no importan `main`. Corre con pytest o como script.
"""
from datetime import UTC, datetime
from decimal import Decimal

from api.schemas.contact import CreateContactRequest
from api.schemas.reminder import CreateReminderRequest
from services.token_usage_service import PRICING, calculate_cost_usd


# ── C1: pricing ──

def test_pricing_tiene_ids_sin_fecha():
    # pick_model() devuelve los ids sin sufijo de fecha; deben estar en PRICING
    # o el costo cae al fallback Sonnet.
    assert "claude-haiku-4-5" in PRICING
    assert "claude-sonnet-4-6" in PRICING


def test_haiku_no_se_cobra_como_sonnet():
    haiku = calculate_cost_usd("claude-haiku-4-5", 1_000_000, 1_000_000)
    sonnet = calculate_cost_usd("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert haiku == Decimal("6.000000")    # 1 (in) + 5 (out)
    assert sonnet == Decimal("18.000000")  # 3 (in) + 15 (out)
    assert haiku < sonnet                  # Haiku NO debe costar como Sonnet


# ── F2: sanitización server-side ──

def test_contact_schema_sanitiza_html():
    c = CreateContactRequest(
        name="<img src=x onerror=alert(1)>Juan",
        notes="<script>steal()</script>nota",
        phone="+54 11 1234",
    )
    assert c.name == "Juan"
    assert "<script" not in c.notes
    assert c.phone == "+54 11 1234"  # texto legítimo intacto


def test_reminder_schema_sanitiza_html():
    r = CreateReminderRequest(title="<b>Reunión</b> obra", due_at=datetime.now(UTC))
    assert r.title == "Reunión obra"
    assert "<" not in r.title


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests pasaron.")


if __name__ == "__main__":
    _run_all()
