"""
Password reset service — forgot-password flow.

Flow:
  1. request_reset(email): if user exists, create a single-use token,
     store its SHA-256 hash, and "send" the reset link (logged for now;
     plug an email provider in `_send_reset_email`).
  2. confirm_reset(token, new_password): validate token → hash new
     password → update profile → mark token used.

Security notes:
  - We hash the token in DB; the plaintext lives only in the email.
  - Tokens are single-use and expire (default 30 min).
  - request_reset is constant-response (always 200) so it doesn't
    leak which emails are registered.
  - URL-safe tokens generated with `secrets.token_urlsafe(32)` → 256
    bits of entropy.
"""
import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from config.settings import settings
from fastapi import HTTPException, status
from models.base import get_session_factory
from models.password_reset import PasswordReset
from models.user import User
from sqlalchemy import and_, func, select, update

logger = logging.getLogger(__name__)

# Token vive 30 minutos. Suficiente para revisar el mail sin que un
# token filtrado quede vivo demasiado tiempo.
RESET_TOKEN_TTL_MINUTES = 30


def _hash_token(token: str) -> str:
    """SHA-256 hex digest of the plaintext token (64 chars)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _build_reset_url(token: str) -> str:
    """
    Build the URL the user clicks in the email. Prefer FRONTEND_URL
    (production), fall back to localhost dev.
    """
    base = settings.FRONTEND_URL or "http://localhost:5173"
    return f"{base.rstrip('/')}/reset-password.html?token={token}"


def _send_reset_email(email: str, full_name: str | None, url: str) -> None:
    """
    Send the reset email. Stub for now — logs to stdout so devs can
    copy the link manually during testing.

    SECURITY: en producción (DEBUG=False) NO loguea el URL completo
    (que contiene el token) porque queda en Sentry/Railway logs y
    cualquiera con acceso a logs podría tomar la cuenta. Falla loudly
    para que sea obvio que hay que wirear un proveedor real.

    To wire a real provider (SendGrid/Resend/Postmark/etc.):
      1. Add SDK + API key env var in settings.
      2. Replace this body with the provider call.
      3. Keep the function signature so callers don't change.
    """
    if not settings.DEBUG:
        # No hacer logger.error con el URL: el token quedaría en logs.
        logger.error(
            "Password reset email stub triggered in PRODUCTION for %s. "
            "Email no enviado. Configurá un proveedor real "
            "(SendGrid/Resend/Postmark) en services/password_reset_service.py.",
            email,
        )
        return

    name = full_name or "amigo/a"
    logger.warning(
        "\n"
        "════════════ PASSWORD RESET EMAIL (stub, DEV ONLY) ════════════\n"
        " To:      %s\n"
        " Subject: Restablecé tu contraseña — RE Expert\n"
        " Body:\n"
        "   Hola %s, alguien (esperemos que vos) pidió restablecer la\n"
        "   contraseña de tu cuenta. Si fuiste vos, abrí este link\n"
        "   (válido %d minutos):\n\n"
        "   %s\n\n"
        "   Si no fuiste vos, ignorá este mail. Tu contraseña no cambió.\n"
        "═══════════════════════════════════════════════════════════════\n",
        email,
        name,
        RESET_TOKEN_TTL_MINUTES,
        url,
    )


# Throttle por email: máximo 3 pedidos de reset por hora para el mismo
# usuario. Esto complementa el rate limit por IP del endpoint (3/h) —
# sin esto un atacante con IPs rotantes podría spamear resets a una
# víctima específica para llenarle el buzón de mails.
_RESET_THROTTLE_WINDOW = timedelta(hours=1)
_RESET_THROTTLE_MAX = 3


async def request_reset(email: str) -> None:
    """
    Initiate a password reset for `email`. Always returns None and
    never raises 404 — that way callers can return the same response
    regardless of whether the email is registered.
    """
    async with get_session_factory()() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            # No leak: pretend success.
            logger.info("Password reset requested for non-existent email %r", email)
            return

        now = datetime.now(UTC)

        # Throttle per email: contar tokens emitidos en la última hora.
        # Si ya hay >= _RESET_THROTTLE_MAX, no creamos otro. Igual
        # devolvemos 200 para no filtrar el throttle al atacante.
        recent_count = await db.scalar(
            select(func.count(PasswordReset.id)).where(
                and_(
                    PasswordReset.user_id == user.id,
                    PasswordReset.created_at >= now - _RESET_THROTTLE_WINDOW,
                )
            )
        )
        if recent_count is not None and recent_count >= _RESET_THROTTLE_MAX:
            logger.warning(
                "Password reset throttled for user_id=%s (count=%s in last hour)",
                user.id,
                recent_count,
            )
            return

        # Invalidate any previously-issued unused token for this user.
        # Sin esto, un atacante que interceptó un email viejo lo puede
        # usar incluso después de que el legítimo dueño pidió uno nuevo.
        await db.execute(
            update(PasswordReset)
            .where(
                and_(
                    PasswordReset.user_id == user.id,
                    PasswordReset.used_at.is_(None),
                )
            )
            .values(used_at=now)
        )

        # Generate single-use token. 32 bytes → ~43 url-safe chars.
        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        expires_at = now + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)

        reset = PasswordReset(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(reset)
        await db.commit()

        _send_reset_email(user.email, user.full_name, _build_reset_url(token))


async def confirm_reset(token: str, new_password: str) -> None:
    """
    Apply the new password if `token` is valid (not expired, not used).
    Raises 400 on invalid/expired/used tokens.
    """
    token_hash = _hash_token(token)
    now = datetime.now(UTC)

    async with get_session_factory()() as db:
        result = await db.execute(
            select(PasswordReset).where(PasswordReset.token_hash == token_hash)
        )
        reset = result.scalar_one_or_none()

        if reset is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de recuperación inválido",
            )
        if reset.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este link de recuperación ya fue usado",
            )
        # Compare as offset-aware datetimes. expires_at is timezone-aware
        # because the column is DateTime(timezone=True).
        if reset.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El link de recuperación expiró. Pedí uno nuevo.",
            )

        # Update password + mark token used in a single transaction.
        await db.execute(
            update(User)
            .where(User.id == reset.user_id)
            .values(password_hash=_hash_password(new_password))
        )
        reset.used_at = now
        await db.commit()
