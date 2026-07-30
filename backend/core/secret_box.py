"""
Cifrado simétrico de secretos en reposo, sólo con la stdlib.

Para qué: el secreto TOTP del 2FA se guardaba **en claro** en `profiles`. Con un
dump de la base, un atacante genera códigos válidos y el segundo factor deja de
existir. La clave de cifrado vive en las variables de entorno del hosting, NO en
la base, así que un dump por sí solo ya no alcanza.

Por qué no se usa `cryptography`: no está en `requirements.txt` y sumar una
dependencia nativa cambia el build del contenedor. Se implementa con `hmac` y
`hashlib`, que ya se usan en todo el proyecto.

Construcción (encrypt-then-MAC, estándar):
  - Claves separadas por rol, derivadas del secreto maestro con HMAC
    (`enc` para cifrar, `mac` para autenticar). Nunca la misma clave para dos cosas.
  - Keystream = HMAC-SHA256(k_enc, nonce || contador), en modo contador
    (la misma construcción que HKDF-Expand). Se XOR-ea contra el texto.
  - Tag = HMAC-SHA256(k_mac, nonce || ciphertext). Se verifica ANTES de
    descifrar y en tiempo constante: un ciphertext manipulado se rechaza.
  - Nonce aleatorio de 16 bytes por operación → cifrar dos veces el mismo
    secreto da resultados distintos.

Formato: `v1.<nonce_b64>.<ct_b64>.<tag_b64>` (base64 urlsafe sin padding).
El prefijo `v1.` permite rotar el esquema y distinguir un valor cifrado de uno
plano heredado (ver `descifrar_o_plano`).
"""
import base64
import hashlib
import hmac
import secrets

from config.settings import settings

_PREFIJO = "v1"
_NONCE_LEN = 16


def _maestra() -> bytes:
    """Secreto maestro. Mismo criterio que el resto del proyecto: uno propio si
    está definido, con el JWT_SECRET como respaldo."""
    return (settings.CONFIRM_SIGNING_SECRET or settings.JWT_SECRET).encode("utf-8")


def _subclave(rol: bytes) -> bytes:
    """Deriva una clave por rol. Nunca se usa la maestra directamente."""
    return hmac.new(_maestra(), rol, hashlib.sha256).digest()


def _keystream(k_enc: bytes, nonce: bytes, largo: int) -> bytes:
    """HMAC en modo contador hasta cubrir `largo` bytes."""
    out = bytearray()
    contador = 0
    while len(out) < largo:
        bloque = hmac.new(
            k_enc, nonce + contador.to_bytes(4, "big"), hashlib.sha256
        ).digest()
        out.extend(bloque)
        contador += 1
    return bytes(out[:largo])


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def cifrar(texto: str) -> str:
    """Texto plano → cadena cifrada y autenticada, lista para guardar."""
    if texto is None:
        return texto
    datos = texto.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_LEN)
    ks = _keystream(_subclave(b"enc"), nonce, len(datos))
    ct = bytes(a ^ b for a, b in zip(datos, ks, strict=True))
    tag = hmac.new(_subclave(b"mac"), nonce + ct, hashlib.sha256).digest()[:16]
    return f"{_PREFIJO}.{_b64e(nonce)}.{_b64e(ct)}.{_b64e(tag)}"


def descifrar(valor: str) -> str | None:
    """Cadena cifrada → texto plano. `None` si está manipulada o no es válida."""
    try:
        version, n_b64, ct_b64, tag_b64 = valor.split(".")
        if version != _PREFIJO:
            return None
        nonce, ct, tag = _b64d(n_b64), _b64d(ct_b64), _b64d(tag_b64)
    except (ValueError, AttributeError, TypeError, base64.binascii.Error):
        return None
    # Verificar ANTES de descifrar, y en tiempo constante.
    esperado = hmac.new(_subclave(b"mac"), nonce + ct, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(esperado, tag):
        return None
    try:
        ks = _keystream(_subclave(b"enc"), nonce, len(ct))
        return bytes(a ^ b for a, b in zip(ct, ks, strict=True)).decode("utf-8")
    except UnicodeDecodeError:
        return None


def esta_cifrado(valor: str | None) -> bool:
    return bool(valor) and valor.startswith(_PREFIJO + ".")


def descifrar_o_plano(valor: str | None) -> str | None:
    """
    Lectura tolerante para la transición.

    Si el valor ya está cifrado, lo descifra. Si es un secreto viejo guardado en
    claro, lo devuelve tal cual — así las cuentas que ya tenían 2FA activo
    siguen funcionando sin necesidad de migrar datos ni de que el usuario
    vuelva a enrolar su aplicación.
    """
    if not valor:
        return valor
    if esta_cifrado(valor):
        return descifrar(valor)
    return valor
