"""
JWT token generation and validation.

Generates access tokens (short-lived) and refresh tokens (long-lived)
using HS256 signing with the app's JWT_SECRET.
"""
import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from config.settings import settings

ALGORITHM = "HS256"


def password_fingerprint(password_hash: str) -> str:
    """Short, non-reversible fingerprint of the current password hash.

    Embedded in reset tokens (claim 'pwf') so that once the password changes
    (its hash changes), any previously-issued reset token stops validating —
    giving single-use semantics without a server-side token store.
    """
    return hashlib.sha256((password_hash or "").encode("utf-8")).hexdigest()[:32]


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


def create_reset_token(user_id: UUID, password_hash: str) -> str:
    """Create a short-lived, single-purpose password-reset token.

    Bound to the current password hash via the 'pwf' claim so it can only be
    used once: completing a reset rotates the hash and invalidates the token.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "reset",
        "pwf": password_fingerprint(password_hash),
        "iat": now,
        "exp": now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_token_pair(user_id: UUID) -> tuple[str, str]:
    """Convenience: returns (access_token, refresh_token)."""
    return create_access_token(user_id), create_refresh_token(user_id)
