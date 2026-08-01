"""
Auth request/response schemas with validation.
"""
import re

from core.sanitize import SanitizedOptStr, SanitizedStr
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: SanitizedStr = Field(..., min_length=1, max_length=255)
    # Aceptación de Términos y Política. El checkbox del registro lo manda en
    # true y la fecha queda guardada en `profiles.terms_accepted_at`, que es lo
    # que le da respaldo probatorio.
    #
    # Opcional a propósito, y el backend NO rechaza si viene en false: Netlify
    # cachea el HTML y el JS por separado, así que durante la ventana de deploy
    # puede haber un navegador con el register.html viejo (sin checkbox) contra
    # el backend nuevo. Rechazarlo ahí dejaría a gente real sin poder crear
    # cuenta. El bloqueo real lo hace el frontend; acá se registra el hecho.
    accepted_terms: bool = False

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una letra mayúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un número")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str = "user"
    plan: str = "free"
    onboarding_completed: bool = False
    # Campos del agente SOL: SOL los lee/escribe vía tools.
    phone: str | None = None
    automation_prefs: dict | None = None
    # True si el email está en ADMIN_EMAILS (habilita la página /admin.html).
    is_admin: bool = False
    # False en las cuentas creadas ANTES del checkbox del registro: la app les
    # pide la aceptación al entrar. No se les puede inventar una fecha.
    terms_accepted: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    """Pedido de reset. Validado pero el endpoint nunca filtra si el
    email existe o no — responde siempre 200 con el mismo mensaje."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una letra mayúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un número")
        return v


class GenericOk(BaseModel):
    ok: bool = True
    message: str | None = None


class UpdateProfileRequest(BaseModel):
    full_name: SanitizedOptStr = Field(None, min_length=1, max_length=255)
    new_password: str | None = Field(None, min_length=8, max_length=128)
    current_password: str | None = Field(None, min_length=1)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.search(r"[A-Z]", v):
            raise ValueError("Debe contener al menos una letra mayuscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("Debe contener al menos un numero")
        return v

    def model_post_init(self, __context) -> None:
        if self.new_password and not self.current_password:
            raise ValueError("current_password es requerido para cambiar la contrasena")
        if not self.full_name and not self.new_password:
            raise ValueError("Debes enviar al menos full_name o new_password")


# ═══ Cuenta / seguridad (Configuración → Cuenta) ═══════════════════════════

class EmailChangeRequest(BaseModel):
    """Paso 1 del cambio de email: contraseña actual (+ código si hay 2FA)."""

    new_email: EmailStr
    password: str = Field(..., min_length=1)
    code: str | None = Field(None, max_length=16)   # requerido solo si hay 2FA


class PasswordOnlyRequest(BaseModel):
    """Acciones que solo re-autentican con la contraseña (enrolar 2FA)."""

    password: str = Field(..., min_length=1)


class CodeRequest(BaseModel):
    """Un código de verificación (6 dígitos o código de recuperación)."""

    code: str = Field(..., min_length=4, max_length=16)


class PhoneRequest(BaseModel):
    """Teléfono en formato internacional; None/vacío lo borra."""

    phone: str | None = Field(None, max_length=32)

    @field_validator("phone")
    @classmethod
    def normalizar(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.fullmatch(r"\+?[0-9 \-()]{6,31}", v):
            raise ValueError("Teléfono inválido (usá formato internacional, ej: +54 9 261 ...)")
        return v


class TwoFADisableRequest(BaseModel):
    password: str = Field(..., min_length=1)
    code: str = Field(..., min_length=4, max_length=16)


class TwoFAVerifyRequest(BaseModel):
    """Paso 2 del login con 2FA."""

    challenge_token: str = Field(..., min_length=10)
    code: str = Field(..., min_length=4, max_length=16)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1)
    code: str | None = Field(None, max_length=16)   # requerido solo si hay 2FA


# Rebuild model refs
AuthResponse.model_rebuild()
