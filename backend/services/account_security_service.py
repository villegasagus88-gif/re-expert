"""
Cuenta / seguridad: cambio de email verificado, teléfono, 2FA y baja con gracia.

Diseño (decisiones de producto ya tomadas):
- 2FA por app authenticator (TOTP, gratis, sin proveedor) o por código al
  email. SMS queda documentado para cuando se contrate un proveedor.
- Cambio de email en dos pasos: el código de 6 dígitos viaja al correo NUEVO
  (protege contra typos y contra secuestro por sesión abierta).
- Baja: requiere contraseña (y código si hay 2FA), se BLOQUEA con suscripción
  activa (plan 'pro' → primero cancelar en Facturación), marca
  `deletion_requested_at` y mata todas las sesiones (bump de token_version).
  Un login exitoso dentro de los 30 días la cancela; pasados los 30 días el
  cleanup diario purga la fila y los FK CASCADE arrastran todos sus datos.

Los códigos de un solo uso se guardan HASHEADOS (sha256) con expiración de
15 minutos, mismo criterio que password_reset_service.
"""
import hashlib
import html
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from config.settings import settings
from fastapi import HTTPException, status
from models.base import get_session_factory
from models.user import User
from services.auth_service import _verify_password  # mismo hasher que el login
from services.totp_service import generate_secret, otpauth_uri, verify_totp
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

CODE_TTL_MINUTES = 15
DELETION_GRACE_DAYS = 30
RECOVERY_CODES = 8
# Intentos fallidos permitidos contra un mismo código antes de quemarlo. El
# rate limit de la ruta es por IP; esto frena el ataque distribuido por cuenta.
MAX_CODE_ATTEMPTS = 5


# ─────────────────────────── helpers ───────────────────────────

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _new_code() -> str:
    """Código de 6 dígitos criptográficamente aleatorio (nunca arranca en 0-pad raro)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _now() -> datetime:
    return datetime.now(UTC)


def _expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return _now() >= expires_at


def _check_code_hash(code: str, stored_hash: str | None, expires_at: datetime | None) -> bool:
    """Compara el código contra el hash guardado, en tiempo constante."""
    if not stored_hash or _expired(expires_at):
        return False
    code = (code or "").strip().replace(" ", "")
    return secrets.compare_digest(_sha256(code), stored_hash)


async def _get_user(db, user_id: UUID | str) -> User:
    uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return user


def _require_password(user: User, password: str) -> None:
    if not user.password_hash or not _verify_password(password or "", user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña incorrecta"
        )


def _verify_second_factor(user: User, code: str) -> bool:
    """Valida un código contra el 2FA ACTIVO del usuario (totp/email/recovery).

    Consume el código de recuperación si fue el que matcheó (single-use).
    Anti-replay TOTP: el último código aceptado queda hasheado (reusa las
    columnas twofa_code_*, que el método totp no ocupa para otra cosa) y no
    se acepta dos veces dentro de su ventana de validez.
    """
    code = (code or "").strip().replace(" ", "").replace("-", "")
    if user.twofa_method == "totp" and user.twofa_secret:
        ya_usado = _check_code_hash(code, user.twofa_code_hash, user.twofa_code_expires_at)
        if not ya_usado and verify_totp(user.twofa_secret, code):
            user.twofa_code_hash = _sha256(code)
            user.twofa_code_expires_at = _now() + timedelta(seconds=95)  # ventana ±1 período
            return True
    if user.twofa_method == "email":
        if _check_code_hash(code, user.twofa_code_hash, user.twofa_code_expires_at):
            user.twofa_code_hash = None
            user.twofa_code_expires_at = None
            user.twofa_code_attempts = 0
            return True
    # Códigos de recuperación (para ambos métodos)
    hashes = list(user.twofa_recovery or [])
    h = _sha256(code.upper())
    if h in hashes:
        hashes.remove(h)                      # single-use
        user.twofa_recovery = hashes
        user.twofa_code_attempts = 0
        return True

    # Falló: contamos el intento y, pasado el tope, quemamos el código vigente
    # para que un atacante distribuido no pueda recorrer el espacio de 6 dígitos.
    user.twofa_code_attempts = int(user.twofa_code_attempts or 0) + 1
    if user.twofa_code_attempts >= MAX_CODE_ATTEMPTS:
        user.twofa_code_hash = None
        user.twofa_code_expires_at = None
        user.twofa_code_attempts = 0
        logger.warning("2FA: código quemado por %d intentos fallidos (user %s)",
                       MAX_CODE_ATTEMPTS, user.id)
    return False


async def _send_email(to: str, subject: str, html: str) -> bool:
    """Envía vía Resend. False si falló o no está configurado (loggea, no rompe)."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY no configurada — email a %s NO enviado (%s)", to, subject)
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"from": settings.RESEND_FROM, "to": [to], "subject": subject, "html": html},
            )
        if resp.status_code >= 400:
            logger.error("Resend error %s para %s: %s", resp.status_code, to, resp.text[:300])
            return False
        return True
    except Exception as e:
        logger.exception("Excepción enviando email vía Resend: %s", e)
        return False


def _email_code_html(nombre: str, code: str, motivo: str) -> str:
    # ESCAPAR: `nombre` es full_name, texto libre del usuario. Sin esto, alguien
    # puede poner un <a> en su nombre y pedir un cambio de email hacia la casilla
    # de una víctima → phishing entregado desde nuestro remitente legítimo.
    n = html.escape(nombre or "Hola")
    motivo = html.escape(motivo)
    code = html.escape(code)
    return f"""
    <div style="font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;padding:24px">
      <h2 style="color:#1a1a1a">{n},</h2>
      <p style="color:#444;line-height:1.6">{motivo}</p>
      <div style="font-size:32px;font-weight:800;letter-spacing:8px;text-align:center;
                  background:#f6f1ec;border-radius:12px;padding:18px;margin:20px 0">{code}</div>
      <p style="color:#888;font-size:13px">El código vence en {CODE_TTL_MINUTES} minutos.
      Si no fuiste vos, ignorá este correo y cambiá tu contraseña.</p>
    </div>"""


# ─────────────────────────── cambio de email ───────────────────────────

async def request_email_change(user_id, new_email: str, password: str,
                               code: str | None = None) -> None:
    new_email = (new_email or "").strip().lower()
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        _require_password(user, password)
        # Con 2FA activo hay que pasarlo también: cambiar el email redirige los
        # códigos de login futuros, o sea que sin este control una sesión robada
        # + la contraseña alcanzaban para neutralizar el segundo factor.
        if user.twofa_method:
            ok = _verify_second_factor(user, code or "")
            await db.commit()          # persistir intentos / consumo de recovery
            if not ok:
                raise HTTPException(
                    status_code=401, detail="Código de verificación incorrecto"
                )
        if new_email == user.email:
            raise HTTPException(status_code=422, detail="Ese ya es tu email actual")
        # ¿Otro usuario ya lo usa? (case-insensitive: los emails se guardan lower)
        existente = (await db.execute(
            select(User.id).where(User.email == new_email)
        )).scalar_one_or_none()
        if existente:
            raise HTTPException(status_code=409, detail="Ese email ya está en uso")

        code = _new_code()
        user.pending_email = new_email
        user.pending_email_code_hash = _sha256(code)
        user.pending_email_expires_at = _now() + timedelta(minutes=CODE_TTL_MINUTES)
        await db.commit()

        enviado = await _send_email(
            new_email,
            "Confirmá tu nuevo email — RE Expert",
            _email_code_html(user.full_name or "", code,
                             "Usá este código para confirmar tu nuevo correo en RE Expert:"),
        )
        if not enviado:
            # Sin email no hay forma de completar el flujo: avisar honesto.
            raise HTTPException(
                status_code=503,
                detail="No pudimos enviar el código de verificación. Probá más tarde.",
            )


async def confirm_email_change(user_id, code: str) -> dict:
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        if not user.pending_email:
            raise HTTPException(status_code=400, detail="No hay ningún cambio de email pendiente")
        if not _check_code_hash(code, user.pending_email_code_hash, user.pending_email_expires_at):
            raise HTTPException(status_code=401, detail="Código incorrecto o vencido")
        # Re-chequear unicidad: alguien pudo registrarse con ese email en el medio.
        existente = (await db.execute(
            select(User.id).where(User.email == user.pending_email, User.id != user.id)
        )).scalar_one_or_none()
        if existente:
            user.pending_email = None
            user.pending_email_code_hash = None
            user.pending_email_expires_at = None
            await db.commit()
            raise HTTPException(status_code=409, detail="Ese email ya está en uso")

        email_viejo = user.email
        user.email = user.pending_email
        user.pending_email = None
        user.pending_email_code_hash = None
        user.pending_email_expires_at = None
        try:
            await db.commit()
        except IntegrityError:
            # Carrera: otro usuario se quedó con ese email entre el chequeo y el
            # commit. El índice único protege el dato; devolvemos 409, no un 500.
            await db.rollback()
            raise HTTPException(status_code=409, detail="Ese email ya está en uso") from None
        logger.info("Email cambiado para user %s", user.id)

        # Avisar a la dirección VIEJA: convierte un robo de contraseña silencioso
        # y definitivo en algo que el dueño puede detectar y reportar.
        await _send_email(
            email_viejo,
            "Cambiaron el email de tu cuenta — RE Expert",
            _email_code_html(
                user.full_name or "", "—",
                f"El correo de tu cuenta de RE Expert pasó a ser {user.email}. "
                f"Si NO fuiste vos, escribinos ya mismo: alguien tiene acceso a tu cuenta.",
            ),
        )
        return {"email": user.email}


# ─────────────────────────── teléfono ───────────────────────────

async def update_phone(user_id, phone: str | None) -> dict:
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        user.phone = phone
        await db.commit()
        return {"phone": user.phone}


# ─────────────────────────── 2FA: enrolar / apagar ───────────────────────────

async def totp_start(user_id, password: str) -> dict:
    """Genera el secret pendiente y devuelve la clave manual + link otpauth.

    Exige la contraseña: sin esto, una sesión robada podía activar 2FA en la
    cuenta ajena y dejar al dueño afuera PARA SIEMPRE (el reset de contraseña
    no limpia el 2FA, así que ni recuperando la clave podía volver a entrar).
    """
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        _require_password(user, password)
        if user.twofa_method:
            raise HTTPException(status_code=409, detail="Ya tenés el doble factor activado")
        secret = generate_secret()
        user.twofa_pending_secret = secret
        await db.commit()
        return {"secret": secret, "otpauth_uri": otpauth_uri(secret, user.email)}


def _make_recovery_codes() -> tuple[list[str], list[str]]:
    """(códigos en claro para mostrar UNA vez, hashes para guardar)."""
    claros = []
    for _ in range(RECOVERY_CODES):
        raw = secrets.token_hex(4).upper()          # 8 hex chars
        claros.append(f"{raw[:4]}-{raw[4:]}")
    hashes = [_sha256(c.replace("-", "")) for c in claros]
    return claros, hashes


async def totp_confirm(user_id, code: str) -> dict:
    """Primer código válido → 2FA activo + códigos de recuperación (una sola vez)."""
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        # Mismo guard que totp_start: sin esto, un `pending_secret` viejo permitía
        # pisar un 2FA ya activo (cambiando el método y regenerando los recovery
        # codes) sin contraseña ni código del factor vigente.
        if user.twofa_method:
            raise HTTPException(status_code=409, detail="Ya tenés el doble factor activado")
        if not user.twofa_pending_secret:
            raise HTTPException(status_code=400, detail="Primero generá la clave (paso anterior)")
        if not verify_totp(user.twofa_pending_secret, code):
            raise HTTPException(
                status_code=401,
                detail="Código incorrecto. Revisá que la app tenga la clave bien cargada.",
            )
        claros, hashes = _make_recovery_codes()
        user.twofa_method = "totp"
        user.twofa_secret = user.twofa_pending_secret
        user.twofa_pending_secret = None
        user.twofa_recovery = hashes
        await db.commit()
        logger.info("2FA TOTP activado para user %s", user.id)
        return {"recovery_codes": claros}


async def email_2fa_start(user_id, password: str) -> None:
    """Activación del método email: manda un código al correo propio.

    Exige contraseña por el mismo motivo que totp_start.
    """
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        _require_password(user, password)
        if user.twofa_method:
            raise HTTPException(status_code=409, detail="Ya tenés el doble factor activado")
        code = _new_code()
        user.twofa_code_hash = _sha256(code)
        user.twofa_code_expires_at = _now() + timedelta(minutes=CODE_TTL_MINUTES)
        user.twofa_code_attempts = 0
        await db.commit()
        enviado = await _send_email(
            user.email,
            "Activá la verificación en dos pasos — RE Expert",
            _email_code_html(user.full_name or "", code,
                             "Usá este código para activar la verificación en dos pasos:"),
        )
        if not enviado:
            raise HTTPException(
                status_code=503,
                detail="No pudimos enviar el código. Probá más tarde o usá una app authenticator.",
            )


async def email_2fa_confirm(user_id, code: str) -> dict:
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        if user.twofa_method:
            raise HTTPException(status_code=409, detail="Ya tenés el doble factor activado")
        if not _check_code_hash(code, user.twofa_code_hash, user.twofa_code_expires_at):
            raise HTTPException(status_code=401, detail="Código incorrecto o vencido")
        claros, hashes = _make_recovery_codes()
        user.twofa_method = "email"
        user.twofa_code_hash = None
        user.twofa_code_expires_at = None
        user.twofa_code_attempts = 0
        user.twofa_pending_secret = None      # descartar un TOTP a medio enrolar
        user.twofa_recovery = hashes
        await db.commit()
        logger.info("2FA email activado para user %s", user.id)
        return {"recovery_codes": claros}


async def send_2fa_code_now(user_id) -> None:
    """Manda un código al correo del usuario con el 2FA email YA ACTIVO.

    Sin esto quedaba un callejón sin salida: desactivar el 2FA y pedir la baja
    exigen un segundo factor, pero para el método email el único código se
    generaba durante el login y se consumía al verificarlo. El usuario que no
    guardó sus códigos de recuperación no podía ni apagar el 2FA ni darse de
    baja — justo el derecho que esta sección promete.
    """
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        if user.twofa_method != "email":
            raise HTTPException(
                status_code=400,
                detail="Este método solo aplica al doble factor por email.",
            )
        code = _new_code()
        user.twofa_code_hash = _sha256(code)
        user.twofa_code_expires_at = _now() + timedelta(minutes=CODE_TTL_MINUTES)
        user.twofa_code_attempts = 0
        await db.commit()
        enviado = await _send_email(
            user.email,
            "Tu código de verificación — RE Expert",
            _email_code_html(user.full_name or "", code,
                             "Tu código para confirmar esta acción en tu cuenta:"),
        )
        if not enviado:
            raise HTTPException(
                status_code=503,
                detail="No pudimos enviarte el código. Probá más tarde o usá un código de recuperación.",
            )


async def disable_2fa(user_id, password: str, code: str) -> None:
    """Apagar 2FA exige contraseña + un código válido (o de recuperación)."""
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        if not user.twofa_method:
            raise HTTPException(status_code=400, detail="No tenés el doble factor activado")
        _require_password(user, password)
        if not _verify_second_factor(user, code):
            raise HTTPException(status_code=401, detail="Código incorrecto")
        user.twofa_method = None
        user.twofa_secret = None
        user.twofa_pending_secret = None
        user.twofa_recovery = None
        user.twofa_code_hash = None
        user.twofa_code_expires_at = None
        await db.commit()
        logger.info("2FA desactivado para user %s", user.id)


# ─────────────────────────── 2FA en el login ───────────────────────────

async def send_login_code(user: User, db) -> bool:
    """Método email: genera y manda el código del desafío de login.

    Devuelve si el envío salió. El caller lo propaga al frontend: decir "te
    enviamos un código" cuando el mail nunca salió deja al usuario esperando
    algo que no existe, sin ninguna pista de que el problema es el envío.
    """
    code = _new_code()
    user.twofa_code_hash = _sha256(code)
    user.twofa_code_expires_at = _now() + timedelta(minutes=CODE_TTL_MINUTES)
    user.twofa_code_attempts = 0
    await db.commit()
    return await _send_email(
        user.email,
        "Tu código de acceso — RE Expert",
        _email_code_html(user.full_name or "", code, "Tu código para iniciar sesión:"),
    )


async def verify_login_challenge(user_id: str, code: str,
                                 expected_tv: int | None = None) -> User | None:
    """Segundo paso del login. Devuelve el User si el código es válido.

    `expected_tv` es el token_version que traía el challenge: si la contraseña
    cambió entre el paso 1 y el 2, el challenge queda inválido junto con ella.
    """
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        if not user.twofa_method:
            return None
        if expected_tv is not None and int(user.token_version or 0) != int(expected_tv):
            return None
        if not _verify_second_factor(user, code):
            return None
        # Login completo: recién acá se cancela una baja pendiente (ver
        # login_user — con 2FA el password solo no alcanza para "entrar").
        cancelada = user.deletion_requested_at is not None
        user.deletion_requested_at = None
        user.last_login = _now()
        await db.commit()
        await db.refresh(user)
        user._deletion_cancelled = cancelada   # flag efímero para la respuesta
        return user


# ─────────────────────────── baja de cuenta ───────────────────────────

async def request_deletion(user_id, password: str, code: str | None) -> dict:
    async with get_session_factory()() as db:
        user = await _get_user(db, user_id)
        _require_password(user, password)
        if user.twofa_method and not _verify_second_factor(user, code or ""):
            raise HTTPException(status_code=401, detail="Código de verificación incorrecto")
        if user.plan == "pro":
            raise HTTPException(status_code=409, detail=(
                "Tenés una suscripción activa. Cancelala primero desde "
                "Configuración → Facturación y después pedí la baja."
            ))
        if user.deletion_requested_at is not None:
            raise HTTPException(status_code=409, detail="La baja ya está pedida")

        user.deletion_requested_at = _now()
        # Matar TODAS las sesiones (esta incluida): la única forma de volver es
        # un login con contraseña, y ese login cancela la baja — exactamente la
        # semántica pedida ("si entra se cancela la eliminación").
        user.token_version = int(user.token_version or 0) + 1
        purge_at = user.deletion_requested_at + timedelta(days=DELETION_GRACE_DAYS)
        await db.commit()

        # Aviso por email (best-effort: si Resend no está, la baja igual queda).
        await _send_email(
            user.email,
            "Tu cuenta se eliminará en 30 días — RE Expert",
            _email_code_html(
                user.full_name or "", "—",
                f"Pediste eliminar tu cuenta. Se borra definitivamente el "
                f"{purge_at.strftime('%d/%m/%Y')}. Si te arrepentís, alcanza con "
                f"volver a iniciar sesión antes de esa fecha.",
            ),
        )
        logger.info("Baja pedida para user %s (purga %s)", user.id, purge_at.date())
        return {"purge_at": purge_at.isoformat()}


def security_overview(user: User) -> dict:
    """Estado de seguridad para pintar el pane de Cuenta."""
    return {
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "twofa_method": user.twofa_method,
        "recovery_codes_left": len(user.twofa_recovery or []) if user.twofa_method else None,
        "pending_email": user.pending_email if not _expired(user.pending_email_expires_at) else None,
        "plan": user.plan,
        "subscription_active": user.plan == "pro",
    }
