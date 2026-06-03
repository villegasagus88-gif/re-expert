"""
Auth routes: register, login, refresh, and me (protected).
"""
from api.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    GenericOk,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserOut,
)
from core.auth import get_current_user
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, Request
from models.user import User
from services.auth_service import (
    complete_onboarding,
    login_user,
    refresh_session,
    register_user,
    update_profile,
)
from services.password_reset_service import confirm_reset, request_reset

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
        onboarding_completed=current_user.onboarding_completed,
        phone=current_user.phone,
        automation_prefs=current_user.automation_prefs,
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
):
    await update_profile(
        user_id=str(current_user.id),
        email=current_user.email,
        full_name=body.full_name,
        current_password=body.current_password,
        new_password=body.new_password,
    )

    # Response consistente con GET /me: incluir phone y automation_prefs
    # (si no, el cliente los recibe como null tras un update).
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        full_name=body.full_name if body.full_name is not None else current_user.full_name,
        role=current_user.role,
        plan=current_user.plan,
        onboarding_completed=current_user.onboarding_completed,
        phone=current_user.phone,
        automation_prefs=current_user.automation_prefs,
    )


@router.post(
    "/onboarding/complete",
    summary="Marcar onboarding como completado",
    status_code=200,
)
async def mark_onboarding_complete(current_user: User = Depends(get_current_user)):
    await complete_onboarding(str(current_user.id))
    return {"ok": True}


# ── Forgot / reset password ──────────────────────────────────────────
# Ambos endpoints son públicos (no requieren JWT). El de "forgot" tiene
# rate limit más agresivo para no permitir enumeración o spam de mails.

@router.post(
    "/forgot-password",
    response_model=GenericOk,
    summary="Solicitar email de recuperación de contraseña",
    responses={
        200: {"description": "Si el email existe, se envió el link"},
        422: {"description": "Email mal formado"},
        429: {"description": "Demasiados intentos, esperá un rato"},
    },
)
@limiter.limit("3/hour")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    # NO leak: respondemos lo mismo si el email existe o no.
    await request_reset(body.email)
    return GenericOk(
        ok=True,
        message="Si el email está registrado, te enviamos un link de recuperación.",
    )


@router.post(
    "/reset-password",
    response_model=GenericOk,
    summary="Aplicar nueva contraseña usando el token del email",
    responses={
        200: {"description": "Contraseña actualizada"},
        400: {"description": "Token inválido, usado o vencido"},
        422: {"description": "Nueva contraseña débil"},
        429: {"description": "Demasiados intentos"},
    },
)
@limiter.limit("10/hour")
async def reset_password(request: Request, body: ResetPasswordRequest):
    await confirm_reset(body.token, body.new_password)
    return GenericOk(ok=True, message="Contraseña actualizada. Ya podés iniciar sesión.")

