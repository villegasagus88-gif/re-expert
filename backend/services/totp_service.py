"""
TOTP (RFC 6238) para 2FA con app authenticator — sin dependencias nuevas.

Compatible con Google Authenticator, Authy, 1Password, Microsoft
Authenticator, etc. (SHA-1, 30 segundos, 6 dígitos: los defaults que todas
las apps asumen). Implementado a mano sobre hmac/struct/base64 de la stdlib;
los vectores de prueba oficiales del RFC están en tests/test_account_security.py.

El usuario carga el secret en su app (clave manual o link otpauth://) y a
partir de ahí la app genera códigos de 6 dígitos que rotan cada 30 s, sin
red ni SMS. Nosotros solo verificamos con una ventana de ±1 período para
tolerar relojes desincronizados.
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

TOTP_STEP = 30       # segundos por período (default universal)
TOTP_DIGITS = 6      # dígitos del código (default universal)
TOTP_WINDOW = 1      # ±1 período de tolerancia (90 s efectivos)


def generate_secret() -> str:
    """Secret nuevo: 20 bytes aleatorios en base32 (32 chars, sin padding)."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")


def _hotp(key: bytes, counter: int, digits: int = TOTP_DIGITS) -> str:
    """HOTP (RFC 4226): HMAC-SHA1 + truncamiento dinámico."""
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    code = struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def totp_at(secret_b32: str, at: int, digits: int = TOTP_DIGITS,
            step: int = TOTP_STEP) -> str:
    """Código TOTP para un timestamp unix dado (determinista, para tests)."""
    # base32 estándar exige padding múltiplo de 8; las apps lo omiten.
    pad = "=" * (-len(secret_b32) % 8)
    key = base64.b32decode(secret_b32.upper() + pad)
    return _hotp(key, at // step, digits)


def verify_totp(secret_b32: str, code: str, at: int | None = None,
                window: int = TOTP_WINDOW) -> bool:
    """
    ¿El código es válido ahora (±window períodos)?

    Comparación en tiempo constante: el código es secreto igual que una
    contraseña. Cualquier input malformado devuelve False, nunca explota.
    """
    code = (code or "").strip().replace(" ", "")
    if not code.isdigit() or len(code) != TOTP_DIGITS:
        return False
    now = int(time.time()) if at is None else at
    try:
        for delta in range(-window, window + 1):
            esperado = totp_at(secret_b32, now + delta * TOTP_STEP)
            if hmac.compare_digest(esperado, code):
                return True
    except Exception:
        return False
    return False


def otpauth_uri(secret_b32: str, account: str, issuer: str = "RE Expert") -> str:
    """
    Link otpauth:// para enrolar: en el celular abre directo la app
    authenticator; en desktop el usuario copia la clave manual.
    """
    label = quote(f"{issuer}:{account}", safe="")
    return (
        f"otpauth://totp/{label}?secret={secret_b32}"
        f"&issuer={quote(issuer, safe='')}&algorithm=SHA1"
        f"&digits={TOTP_DIGITS}&period={TOTP_STEP}"
    )
