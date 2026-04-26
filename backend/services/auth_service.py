"""
Auth service — standalone authentication with bcrypt + JWT.

Handles: password hashing, credential validation, token generation,
user registration, and session refresh. No external auth provider needed.
"""
from datetime import UTC, datetime
from uuid import uuid4

import bcrypt
from fastapi import HTTPException, status
from models.base import get_session_factory
from models.user import User
from services.jwt_service import create_token_pair, decode_token
from sqlalchemy import select


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
