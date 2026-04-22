"""
Auth routes: register, login, refresh, and me (protected).
"""
from api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserOut,
)
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, Request
from models.base import get_db
from models.user import User
from services.auth_service import login_user, refresh_session, register_user, update_profile
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
    summary="Registrar nuevo usuario",
    responses={
        409: {"description": "Email ya registrado"},
        422: {"description": "Datos invalidos (password debil, email mal formado)"},
        429: {"description": "Demasiados intentos, espera un rato"},
    },
)
@limiter.limit("5/hour")
async def register(request: Request, body: RegisterRequest):
    return await register_user(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Iniciar sesion",
    responses={
        401: {"description": "Credenciales incorrectas"},
        429: {"description": "Demasiados intentos"},
    },
)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    return await login_user(email=body.email, password=body.password)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Renovar tokens con refresh_token",
    responses={
        401: {"description": "Refresh token invalido o expirado"},
    },
)
@limiter.limit("30/minute")
async def refresh(request: Request, body: RefreshRequest):
    return await refresh_session(refresh_token=body.refresh_token)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Obtener usuario actual (ruta protegida)",
    responses={
        401: {"description": "Token invalido, expirado o ausente"},
    },
)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        plan=current_user.plan,
    )


@router.put(
    "/me",
    response_model=UserOut,
    summary="Actualizar perfil (nombre y/o password)",
    responses={
        401: {"description": "Token invalido o password actual incorrecto"},
        422: {"description": "Datos invalidos"},
    },
)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Update in Supabase Auth
    await update_profile(
        user_id=str(current_user.id),
        email=current_user.email,
        full_name=body.full_name,
        current_password=body.current_password,
        new_password=body.new_password,
    )

    # Update local profile in DB
    if body.full_name is not None:
        current_user.full_name = body.full_name
        await db.commit()
        await db.refresh(current_user)

    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        plan=current_user.plan,
    )
