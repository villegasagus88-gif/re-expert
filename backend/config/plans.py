"""
Single source of truth for plan tiers, limits, features and pricing.



Both `services/rate_limit_service.py` and any future plan-gating logic
should import from here so that changing a limit in one place updates
the whole app (and the frontend pricing copy is documented next to it).

If you change anything here, also update:
    - frontend/pricing.html      (visible copy)
    - docs/PLANS.md              (comparative table)
"""
from __future__ import annotations

from typing import Literal

PlanName = Literal["free", "pro"]

# Hard rate-limits enforced by services/rate_limit_service.py.
# Keep keys in sync with the service: it reads PLAN_LIMITS[plan]["per_hour"|"per_day"].
PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {"per_hour": 5, "per_day": 20},
    "pro": {"per_hour": 50, "per_day": 200},
}

# Feature flags per plan. True = included, False = gated/upsell.
# Read by gating logic and by the frontend (via /api/billing/status).
PLAN_FEATURES: dict[str, dict[str, bool]] = {
    "free": {
        "chat": True,
        "knowledge_read": True,        # Materiales / Noticias (lectura)
        "history_full": False,         # solo últimas 3 conversaciones
        "sol_assistant": False,        # asistente de obra con contexto del proyecto
        "project_dashboard": False,    # presupuesto, hitos, materiales
        "indicators_cpi_spi": False,
        "data_ingest": False,          # POST /api/data/ingest (vía SOL)
        "export": False,               # CSV / PDF
        "priority_support": False,
    },
    "pro": {
        "chat": True,
        "knowledge_read": True,
        "history_full": True,
        "sol_assistant": True,
        "project_dashboard": True,
        "indicators_cpi_spi": True,
        "data_ingest": True,
        "export": True,
        "priority_support": True,
    },
}

# Pricing (USD). Mostrado en pricing.html y usado para validar consistencia
# con el Stripe Price configurado en STRIPE_PRICE_ID_PRO.
PLAN_PRICING: dict[str, dict[str, float | str]] = {
    "free": {"amount": 0.0, "currency": "USD", "period": "mes"},
    "pro": {"amount": 19.0, "currency": "USD", "period": "mes"},
}


def has_feature(plan: str, feature: str) -> bool:
    """True if `plan` includes `feature`. Defaults to free if plan unknown."""
    return PLAN_FEATURES.get(plan, PLAN_FEATURES["free"]).get(feature, False)


def limits_for(plan: str) -> dict[str, int]:
    """Per-hour / per-day caps for a plan. Defaults to free if unknown."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
