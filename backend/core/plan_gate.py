"""
Access control para el modelo pago-only.

`has_access(user)` decide si un usuario puede usar el producto:
  - admin (email en ADMIN_EMAILS) → siempre (los fundadores/operadores no
    quedan paywalled de su propia app cuando vence el trial).
  - plan "pro"   → siempre.
  - plan "trial" → mientras now() < trial_ends_at.
  - "inactive" / vencido / desconocido → no (paywall).

`require_access` es la dependency de FastAPI que se aplica a los routers de
producto; devuelve 403 con un detalle estructurado para que el frontend muestre
el paywall (no un error genérico).
"""
from datetime import UTC, datetime

from core.auth import get_current_user, is_admin
from fastapi import Depends, HTTPException, status
from models.user import User

_PAYWALL_BASE = {
    "message": "Necesitás una suscripción activa para usar RE Expert.",
    "reason": "no_subscription",
    "upgrade_url": "/pricing.html",
}


def has_access(user: User) -> bool:
    """True si el usuario tiene acceso: admin, 'pro', o 'trial' aún vigente."""
    if is_admin(user):
        return True
    if user.plan == "pro":
        return True
    if user.plan == "trial" and user.trial_ends_at is not None:
        ends = user.trial_ends_at
        if ends.tzinfo is None:  # normalizar naive → aware por las dudas
            ends = ends.replace(tzinfo=UTC)
        return datetime.now(UTC) < ends
    return False


def require_access(user: User = Depends(get_current_user)) -> User:
    """Dependency: 403 con detalle de paywall si el usuario no tiene acceso."""
    if not has_access(user):
        detail = dict(_PAYWALL_BASE)
        if user.plan == "trial":  # tenía trial pero venció
            detail["reason"] = "trial_expired"
            detail["message"] = (
                "Tu período de prueba terminó. Suscribite para seguir usando RE Expert."
            )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return user


# Alias deprecado: en el modelo pago-only "requiere pro" pasa a ser "requiere
# acceso" (el trial también habilita). Se mantiene para no romper imports
# mientras se migran los usos a require_access.
require_pro = require_access
