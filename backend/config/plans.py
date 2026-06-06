"""
Single source of truth for plan tiers, limits, features and pricing.

RE Expert es **pago-only** (no existe tier free). Estados del campo `plan`:
  - "trial"    → evaluación de 7 días, acceso completo.
  - "pro"      → suscripción paga activa, acceso completo.
  - "inactive" → trial vencido o suscripción cancelada/caída → sin acceso (paywall).

El acceso se resuelve en `core/plan_gate.has_access()`. Acá viven los límites de
rate y las features: `trial` y `pro` son equivalentes en capacidades (la única
diferencia es el cobro). El monto se cobra vía Mercado Pago (configurado en el
panel de MP); ver docs/MODELO_PAGO.md.

Si cambiás algo acá, actualizá también:
    - frontend/pricing.html      (copy visible)
    - docs/MODELO_PAGO.md        (spec)
"""
from __future__ import annotations

from typing import Literal

PlanName = Literal["trial", "pro", "inactive"]

# Duración del trial en días. Configurable; ver register_user.
TRIAL_DAYS = 7

# Rate-limits por plan CON acceso. trial == pro (no friccionar la evaluación).
# Un usuario "inactive" no llega al rate limit: el gate de acceso lo corta antes.
PLAN_LIMITS: dict[str, dict[str, int]] = {
    "trial": {"per_hour": 50, "per_day": 200},
    "pro": {"per_hour": 50, "per_day": 200},
}

# Capacidades. trial y pro son equivalentes (la diferencia es el cobro).
_FULL_FEATURES: dict[str, bool] = {
    "chat": True,
    "knowledge_read": True,
    "history_full": True,
    "sol_assistant": True,
    "project_dashboard": True,
    "indicators_cpi_spi": True,
    "data_ingest": True,
    "export": True,
    "priority_support": True,
}
PLAN_FEATURES: dict[str, dict[str, bool]] = {
    "trial": dict(_FULL_FEATURES),
    "pro": dict(_FULL_FEATURES),
}

# Plan sin acceso (inactive / desconocido): todas las features en False.
_NO_FEATURES: dict[str, bool] = dict.fromkeys(_FULL_FEATURES, False)

# Precio del plan pago (ARS). Anclado a ~USD 45/mes al dólar financiero
# (MEP/CCL ~1500); redondeado a un valor comercial. Revisar si el dólar se mueve
# fuerte. Configurar el mismo monto en el plan de suscripción de Mercado Pago.
PLAN_PRICING: dict[str, dict[str, float | str]] = {
    "pro": {"amount": 69900.0, "currency": "ARS", "period": "mes"},  # ~USD 45
}

# Límite mínimo para planes sin acceso (no debería usarse: el gate corta antes).
_MIN_LIMITS: dict[str, int] = {"per_hour": 0, "per_day": 0}


def has_feature(plan: str, feature: str) -> bool:
    """True si `plan` incluye `feature`. Plan sin acceso/desconocido → False."""
    return PLAN_FEATURES.get(plan, _NO_FEATURES).get(feature, False)


def limits_for(plan: str) -> dict[str, int]:
    """Caps per-hour/per-day del plan. Plan sin acceso/desconocido → mínimo."""
    return PLAN_LIMITS.get(plan, _MIN_LIMITS)
