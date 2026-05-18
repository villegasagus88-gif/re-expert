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
import httpx
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


def _build_reset_email_html(name: str, url: str) -> str:
    """Cuerpo HTML del email de recuperación. Inline styles para que
    Gmail/Outlook no lo rompan. Texto en español neutral."""
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding:40px 20px">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" border="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)">
        <tr><td style="padding:32px 40px 0">
          <div style="font-size:22px;font-weight:700;color:#09090b;letter-spacing:-.3px">RE Expert</div>
          <div style="font-size:12px;color:#71717a;margin-top:2px">Real Estate AI</div>
        </td></tr>
        <tr><td style="padding:24px 40px">
          <h1 style="font-size:20px;font-weight:700;color:#18181b;margin:0 0 12px">Restablecé tu contraseña</h1>
          <p style="font-size:14px;line-height:1.6;color:#3f3f46;margin:0 0 16px">
            Hola {name}, alguien (esperemos que vos) pidió restablecer la contraseña de tu cuenta en RE Expert.
            Hacé click en el botón de abajo para elegir una nueva. El link es válido {RESET_TOKEN_TTL_MINUTES} minutos.
          </p>
          <div style="margin:28px 0">
            <a href="{url}" style="display:inline-block;padding:12px 24px;background:#6366f1;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;font-size:14px">
              Restablecer contraseña
            </a>
          </div>
          <p style="font-size:13px;line-height:1.6;color:#71717a;margin:0 0 8px">
            Si el botón no funciona, copiá y pegá este link en el navegador:
          </p>
          <p style="font-size:12px;line-height:1.5;color:#52525b;word-break:break-all;background:#f4f4f5;padding:10px 12px;border-radius:6px;margin:0 0 24px">
            {url}
          </p>
          <p style="font-size:13px;line-height:1.6;color:#71717a;margin:0">
            Si no fuiste vos, ignorá este mail — tu contraseña no cambió.
          </p>
        </td></tr>
        <tr><td style="padding:20px 40px 32px;border-top:1px solid #e4e4e7">
          <p style="font-size:11px;color:#a1a1aa;margin:0;text-align:center">
            © 2026 RE Expert · Real Estate AI para Argentina
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>"""


async def _send_via_resend(email: str, name: str, url: str) -> bool:
    """Envía vía Resend API. Devuelve True si OK, False si falló (loggea
    pero NO levanta — un fallo de email no debe romper el flow del user)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.RESEND_FROM,
                    "to": [email],
                    "subject": "Restablecé tu contraseña — RE Expert",
                    "html": _build_reset_email_html(name, url),
                },
            )
        if resp.status_code >= 400:
            logger.error(
                "Resend API error %s para %s: %s",
                resp.status_code, email, resp.text[:300],
            )
            return False
        logger.info("Reset email enviado vía Resend a %s", email)
        return True
    except Exception as e:
        logger.exception("Excepción enviando email via Resend: %s", e)
        return False


async def _send_reset_email(email: str, full_name: str | None, url: str) -> None:
    """
    Envía el email de reset. Prioridad:
      1. Si RESEND_API_KEY está seteada → manda real via Resend API.
      2. Si DEBUG=True y no hay Resend → loggea el URL al stdout (dev).
      3. Si DEBUG=False y no hay Resend → loggea ERROR y no envía
         (NO loguea el URL: el token quedaría en logs y cualquiera con
         acceso a logs podría tomar la cuenta).
    """
    name = full_name or "amigo/a"

    if settings.RESEND_API_KEY:
        ok = await _send_via_resend(email, name, url)
        if not ok and settings.DEBUG:
            # En dev, si Resend falla pero estamos en DEBUG, loguear el
            # link al stdout como fallback útil.
            logger.warning("Resend falló; link dev → %s", url)
        return

    if not settings.DEBUG:
        logger.error(
            "Password reset triggered in PRODUCTION for %s pero NO hay "
            "RESEND_API_KEY configurada. Email no enviado. Setear "
            "RESEND_API_KEY (https://resend.com/api-keys) en las env vars.",
            email,
        )
        return

    # Dev sin Resend: log al stdout con el link clickeable.
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

        await _send_reset_email(user.email, user.full_name, _build_reset_url(token))


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

        # Update password + bump token_version (invalida JWTs viejos del
        # usuario) + mark token used, todo en una transacción.
        await db.execute(
            update(User)
            .where(User.id == reset.user_id)
            .values(
                password_hash=_hash_password(new_password),
                token_version=User.token_version + 1,
            )
        )
        reset.used_at = now
        await db.commit()
