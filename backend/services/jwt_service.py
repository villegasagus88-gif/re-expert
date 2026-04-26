"""
JWT token generation and validation.

Generates access tokens (short-lived) and refresh tokens (long-lived)
using HS256 signing with the app's JWT_SECRET.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from config.settings import settings

ALGORITHM = "HS256"


def create_access_token(user_id: UUID) -> str:
    """Create a short-lived access token (default 15 min)."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """Create a long-lived refresh token (default 7 days)."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns the payload dict. Raises jwt.ExpiredSignatureError or
    jwt.InvalidTokenError on failure.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])


def create_token_pair(user_id: UUID) -> tuple[str, str]:
    """Convenience: returns (access_token, refresh_token)."""
    return create_access_token(user_id), create_refresh_token(user_id)
