"""
JWT token generation and validation.

Generates access tokens (short-lived) and refresh tokens (long-lived)
using HS256 signing with the app's JWT_SECRET.

Token version (`tv` claim): cada token lleva el `token_version` del
usuario al momento de crearse. Cuando el usuario cambia password (o
hacemos logout global), bumpeamos `User.token_version` y todos los
JWTs viejos quedan inválidos automáticamente — `get_current_user`
verifica que `tv == user.token_version`.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from config.settings import settings

ALGORITHM = "HS256"


def create_access_token(user_id: UUID, token_version: int = 0) -> str:
    """Create a short-lived access token (default 15 min)."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "tv": int(token_version),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: UUID, token_version: int = 0, expire_days: int | None = None
) -> str:
    """Create a long-lived refresh token (default 7 days).

    `expire_days` permite una ventana más larga (p.ej. admins) sin tocar la de
    los usuarios normales. Si es None, usa settings.REFRESH_TOKEN_EXPIRE_DAYS."""
    now = datetime.now(UTC)
    days = expire_days if expire_days is not None else settings.REFRESH_TOKEN_EXPIRE_DAYS
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "tv": int(token_version),
        "iat": now,
        "exp": now + timedelta(days=days),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token (firma + expiración).

    NO verifica `tv` — el caller debe hacerlo contra `user.token_version`
    porque acá no tenemos acceso a la DB.

    Returns the payload dict. Raises jwt.ExpiredSignatureError or
    jwt.InvalidTokenError on failure.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])


def create_token_pair(
    user_id: UUID, token_version: int = 0, refresh_expire_days: int | None = None
) -> tuple[str, str]:
    """Convenience: returns (access_token, refresh_token).

    `refresh_expire_days` alarga la ventana del refresh (admins) sin afectar el
    access token ni a los usuarios normales."""
    return (
        create_access_token(user_id, token_version),
        create_refresh_token(user_id, token_version, expire_days=refresh_expire_days),
    )
