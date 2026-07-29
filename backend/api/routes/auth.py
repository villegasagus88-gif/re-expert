"""
Auth routes: register, login, refresh, and me (protected).
"""
from api.schemas.auth import (
    AuthResponse,
    CodeRequest,
    DeleteAccountRequest,
    EmailChangeRequest,
    ForgotPasswordRequest,
    GenericOk,
    LoginRequest,
    PasswordOnlyRequest,
    PhoneRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TwoFADisableRequest,
    TwoFAVerifyRequest,
    UpdateProfileRequest,
    UserOut,
)
from core.auth import get_current_user, is_admin
from core.rate_limit import limiter
from fastapi import APIRouter, Depends, HTTPException, Request
from models.user import User
from services import account_security_service as acct
from services.auth_service import (
    _refresh_days,
    _user_to_dict,
    complete_onboarding,
    login_user,
    refresh_session,
    register_user,
    update_profile,
)
from services.jwt_service import create_token_pair, decode_2fa_challenge
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
    # Sin response_model: con 2FA activo la respuesta es un desafío
    # ({twofa_required, twofa_method, challenge_token}) en vez de los tokens, y
    # AuthResponse (campos obligatorios) la rompería con un 500 de validación.
    # Para usuarios sin 2FA la respuesta es byte-idéntica a la de siempre.
    summary="Iniciar sesion",
    responses={
        200: {"description": "Tokens, o desafío 2FA si el usuario lo activó"},
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
        is_admin=is_admin(current_user),
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



# ═══ Cuenta / seguridad (Configuración → Cuenta) ═══════════════════════════
# Ninguno de estos endpoints lleva gate de plan a propósito: los derechos sobre
# la propia cuenta (cambiar datos, 2FA, pedir la baja) no dependen de estar al
# día con la suscripción. Lo ÚNICO que la suscripción bloquea es la baja
# mientras esté activa (regla de producto, validada en el servicio).


@router.get(
    "/account/security",
    summary="Estado de seguridad de la cuenta (para el pane Cuenta)",
)
async def account_security(current_user: User = Depends(get_current_user)):
    return acct.security_overview(current_user)


@router.post(
    "/email-change/request",
    response_model=GenericOk,
    summary="Cambiar email — paso 1: código al correo NUEVO",
    responses={
        401: {"description": "Contraseña incorrecta"},
        409: {"description": "Ese email ya está en uso"},
        503: {"description": "Envío de email no configurado / falló"},
    },
)
@limiter.limit("5/hour")
async def email_change_request(
    request: Request, body: EmailChangeRequest,
    current_user: User = Depends(get_current_user),
):
    await acct.request_email_change(
        current_user.id, body.new_email, body.password, body.code
    )
    return GenericOk(ok=True, message="Te enviamos un código al correo nuevo.")


@router.post(
    "/email-change/confirm",
    summary="Cambiar email — paso 2: confirmar con el código",
    responses={401: {"description": "Código incorrecto o vencido"}},
)
@limiter.limit("10/hour")
async def email_change_confirm(
    request: Request, body: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    return await acct.confirm_email_change(current_user.id, body.code)


@router.put(
    "/phone",
    summary="Actualizar teléfono (formato internacional)",
)
@limiter.limit("10/hour")
async def update_phone_route(
    request: Request, body: PhoneRequest,
    current_user: User = Depends(get_current_user),
):
    return await acct.update_phone(current_user.id, body.phone)


@router.post(
    "/2fa/totp/start",
    summary="2FA app — paso 1: generar clave para la app authenticator",
    responses={
        401: {"description": "Contraseña incorrecta"},
        409: {"description": "Ya hay 2FA activo"},
    },
)
@limiter.limit("5/hour")
async def twofa_totp_start(
    request: Request, body: PasswordOnlyRequest,
    current_user: User = Depends(get_current_user),
):
    return await acct.totp_start(current_user.id, body.password)


@router.post(
    "/2fa/totp/confirm",
    summary="2FA app — paso 2: confirmar con el primer código",
    responses={401: {"description": "Código incorrecto"}},
)
@limiter.limit("10/hour")
async def twofa_totp_confirm(
    request: Request, body: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    return await acct.totp_confirm(current_user.id, body.code)


@router.post(
    "/2fa/email/start",
    response_model=GenericOk,
    summary="2FA email — paso 1: enviar código al correo propio",
    responses={
        401: {"description": "Contraseña incorrecta"},
        409: {"description": "Ya hay 2FA activo"},
        503: {"description": "Envío de email no configurado / falló"},
    },
)
@limiter.limit("5/hour")
async def twofa_email_start(
    request: Request, body: PasswordOnlyRequest,
    current_user: User = Depends(get_current_user),
):
    await acct.email_2fa_start(current_user.id, body.password)
    return GenericOk(ok=True, message="Te enviamos un código a tu correo.")


@router.post(
    "/2fa/email/send-code",
    response_model=GenericOk,
    summary="2FA email YA activo — mandar un código para confirmar una acción",
    responses={
        400: {"description": "El 2FA activo no es por email"},
        503: {"description": "Envío de email no configurado / falló"},
    },
)
@limiter.limit("5/hour")
async def twofa_email_send_code(
    request: Request, current_user: User = Depends(get_current_user)
):
    """Sin esto, quien activó 2FA por email y perdió sus códigos de recuperación
    no podía desactivar el 2FA ni pedir la baja: el único código se generaba en
    el login y se consumía ahí mismo."""
    await acct.send_2fa_code_now(current_user.id)
    return GenericOk(ok=True, message="Te enviamos un código a tu correo.")


@router.post(
    "/2fa/email/confirm",
    summary="2FA email — paso 2: confirmar con el código",
    responses={401: {"description": "Código incorrecto o vencido"}},
)
@limiter.limit("10/hour")
async def twofa_email_confirm(
    request: Request, body: CodeRequest,
    current_user: User = Depends(get_current_user),
):
    return await acct.email_2fa_confirm(current_user.id, body.code)


@router.post(
    "/2fa/disable",
    response_model=GenericOk,
    summary="Desactivar 2FA (exige contraseña + código)",
    responses={401: {"description": "Contraseña o código incorrectos"}},
)
@limiter.limit("5/hour")
async def twofa_disable(
    request: Request, body: TwoFADisableRequest,
    current_user: User = Depends(get_current_user),
):
    await acct.disable_2fa(current_user.id, body.password, body.code)
    return GenericOk(ok=True, message="Verificación en dos pasos desactivada.")


@router.post(
    "/2fa/verify",
    # Sin response_model por el mismo motivo que /login (misma forma de respuesta).
    summary="Login — paso 2: canjear challenge + código por los tokens",
    responses={401: {"description": "Challenge vencido o código incorrecto"}},
)
@limiter.limit("10/minute")
async def twofa_verify(request: Request, body: TwoFAVerifyRequest):
    payload = decode_2fa_challenge(body.challenge_token)
    if not payload:
        raise HTTPException(
            status_code=401, detail="El desafío venció. Volvé a iniciar sesión."
        )
    user = await acct.verify_login_challenge(
        payload["sub"], body.code, expected_tv=payload.get("tv")
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Código incorrecto")
    access_token, refresh_token = create_token_pair(
        user.id, user.token_version, refresh_expire_days=_refresh_days(user)
    )
    out = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_to_dict(user),
    }
    if getattr(user, "_deletion_cancelled", False):
        out["deletion_cancelled"] = True
    return out


@router.post(
    "/account/delete",
    status_code=202,
    summary="Pedir la baja de la cuenta (30 días de gracia)",
    responses={
        401: {"description": "Contraseña o código incorrectos"},
        409: {"description": "Suscripción activa o baja ya pedida"},
    },
)
@limiter.limit("3/hour")
async def delete_account(
    request: Request, body: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
):
    return await acct.request_deletion(current_user.id, body.password, body.code)
