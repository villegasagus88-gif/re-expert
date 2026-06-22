"""
Auth service — standalone authentication with bcrypt + JWT.

Handles: password hashing, credential validation, token generation,
user registration, and session refresh. No external auth provider needed.
"""
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import bcrypt
from config.settings import settings
from fastapi import HTTPException, status
from models.base import get_session_factory
from models.user import User
from services.email_service import send_email
from services.jwt_service import (
    create_reset_token,
    create_token_pair,
    decode_token,
    password_fingerprint,
)
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _user_to_dict(user: User) -> dict:
    """Convert a User ORM instance to the API response dict."""
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "plan": user.plan,
        "onboarding_completed": user.onboarding_completed,
    }


async def register_user(email: str, password: str, full_name: str) -> dict:
    """
    Register a new user with bcrypt-hashed password.

    Returns dict with access_token, refresh_token, and user data.
    Raises 409 if email already exists.
    """
    async with get_session_factory()() as db:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con este email",
            )

        # Create user
        user = User(
            id=uuid4(),
            email=email,
            password_hash=_hash_password(password),
            full_name=full_name,
            role="user",
            plan="free",
            last_login=datetime.now(UTC),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Generate tokens
        access_token, refresh_token = create_token_pair(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": _user_to_dict(user),
        }


async def login_user(email: str, password: str) -> dict:
    """
    Authenticate user by email + password.

    Returns dict with access_token, refresh_token, and user data.
    Raises 401 if credentials are invalid.
    """
    async with get_session_factory()() as db:
        # Find user by email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        # Validate credentials
        if user is None or user.password_hash is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        if not _verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        # Update last_login
        user.last_login = datetime.now(UTC)
        await db.commit()
        await db.refresh(user)

        # Generate tokens
        access_token, refresh_token = create_token_pair(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": _user_to_dict(user),
        }


async def refresh_session(refresh_token: str) -> dict:
    """
    Exchange a valid refresh token for a new token pair.

    Raises 401 if the token is invalid, expired, or not a refresh token.
    """
    import jwt as pyjwt

    try:
        payload = decode_token(refresh_token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    # Verify it's actually a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no es de tipo refresh",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario",
        )

    # Load user from DB
    async with get_session_factory()() as db:
        from uuid import UUID

        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
            )

        # Generate new token pair
        new_access, new_refresh = create_token_pair(user.id)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "user": _user_to_dict(user),
        }


async def complete_onboarding(user_id: str) -> None:
    """Mark the user's onboarding as completed."""
    async with get_session_factory()() as db:
        from uuid import UUID

        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if user and not user.onboarding_completed:
            user.onboarding_completed = True
            await db.commit()


def _reset_link(token: str) -> str:
    """Construye el link absoluto a la página de reset del frontend."""
    base = (settings.FRONTEND_URL or "http://localhost:5173").rstrip("/")
    return f"{base}/reset-password.html?token={token}"


async def request_password_reset(email: str) -> None:
    """
    Inicia el flujo de recuperación de contraseña.

    Si existe un usuario con ese email (y tiene password), genera un token de
    reset de un solo uso y le manda el link por email. NO revela si el email
    existe: siempre retorna None sin error (anti-enumeración). El caller (la
    ruta) responde siempre 200 con un mensaje uniforme.
    """
    async with get_session_factory()() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None or not user.password_hash:
        logger.info("forgot-password: email sin cuenta/sin password (%s)", email)
        return

    token = create_reset_token(user.id, user.password_hash)
    link = _reset_link(token)
    mins = settings.RESET_TOKEN_EXPIRE_MINUTES
    subject = "Restablecé tu contraseña — RE Expert"
    html = (
        "<div style=\"font-family:Inter,Arial,sans-serif;max-width:480px;margin:auto;"
        "color:#1f2937\">"
        "<h2 style=\"color:#4f46e5\">RE Expert</h2>"
        "<p>Recibimos un pedido para restablecer tu contraseña.</p>"
        f"<p style=\"margin:24px 0\"><a href=\"{link}\" "
        "style=\"background:#4f46e5;color:#fff;padding:12px 20px;border-radius:8px;"
        "text-decoration:none;display:inline-block\">Restablecer contraseña</a></p>"
        f"<p style=\"color:#6b7280;font-size:13px\">El link vence en {mins} minutos. "
        "Si no lo pediste, ignorá este mensaje: tu contraseña no cambia.</p>"
        f"<p style=\"color:#9ca3af;font-size:12px\">Si el botón no funciona, copiá este "
        f"link:<br>{link}</p>"
        "</div>"
    )
    text = (
        f"Restablecé tu contraseña entrando a:\n{link}\n\n"
        f"El link vence en {mins} minutos. Si no lo pediste, ignorá este mensaje."
    )
    result = await send_email(user.email, subject, html, text)
    if not result.get("ok"):
        # No fallamos la request: logueamos para diagnóstico (p.ej. key faltante).
        logger.warning(
            "forgot-password: email a %s no entregado (%s)",
            user.email,
            result.get("detail"),
        )


async def reset_password(token: str, new_password: str) -> None:
    """
    Completa el reset: valida el token de un solo uso y setea la nueva contraseña.

    Raises 400 si el token es inválido, expiró, o ya fue usado (el fingerprint
    del password embebido no matchea el hash actual).
    """
    import jwt as pyjwt

    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El link de recuperación venció. Pedí uno nuevo.",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El link de recuperación es inválido.",
        )

    if payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El link de recuperación es inválido.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El link de recuperación es inválido.",
        )
    try:
        uid = UUID(user_id)
    except (ValueError, TypeError):
        # sub viene firmado (siempre un UUID real), pero por robustez devolvemos
        # el mismo 400 que el resto de los paths de token inválido en vez de 500.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El link de recuperación es inválido.",
        )

    async with get_session_factory()() as db:
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()

        if user is None or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El link de recuperación es inválido.",
            )

        # Single-use: el fingerprint del token debe coincidir con el hash actual.
        if payload.get("pwf") != password_fingerprint(user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El link ya fue usado o venció. Pedí uno nuevo.",
            )

        user.password_hash = _hash_password(new_password)
        await db.commit()


async def update_profile(
    user_id: str,
    email: str,
    full_name: str | None = None,
    current_password: str | None = None,
    new_password: str | None = None,
) -> None:
    """
    Update user profile (name and/or password).

    If changing password, validates current password first.
    """
    async with get_session_factory()() as db:
        from uuid import UUID

        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
            )

        # Validate current password if changing password
        if new_password:
            if not current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="current_password es requerido para cambiar la contraseña",
                )
            if not user.password_hash or not _verify_password(current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Contraseña actual incorrecta",
                )
            user.password_hash = _hash_password(new_password)

        if full_name is not None:
            user.full_name = full_name

        await db.commit()
