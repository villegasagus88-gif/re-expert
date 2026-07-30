"""
Enlaces firmados para los reportes servidos desde disco.

Problema que resuelve: `/static/reports/<archivo>` se servía con `StaticFiles`
**sin ninguna autenticación**, y el nombre es `{scope}-{fecha}-{uuid8}.{ext}` —
32 bits de entropía con prefijo predecible. Cualquiera podía enumerar y bajarse
informes con presupuesto, costo real, pagos y proveedores de obras ajenas.

Por qué no se resuelve pidiendo JWT: el usuario COMPARTE estos links por
WhatsApp/Telegram con su cliente o su contador, que no tienen cuenta. Exigir
sesión rompería el caso de uso real.

Solución (el mismo patrón que usan los signed URLs de Supabase Storage): la URL
lleva vencimiento y firma HMAC-SHA256. Sigue siendo compartible, pero:
  - no se puede enumerar (hace falta la firma),
  - caduca sola,
  - y el que la tenga accede sólo a ESE archivo.

La firma cubre nombre + vencimiento, así que no se puede mover a otro archivo
ni estirar el plazo.
"""
import hashlib
import hmac
import time
from urllib.parse import urlencode

from config.settings import settings

# 48 h: mismo TTL que los signed URLs de Supabase para entregables financieros.
DEFAULT_TTL_SECONDS = 48 * 3600


def _key() -> bytes:
    """Mismo criterio que agent_confirm: secreto propio, o el JWT como fallback."""
    return (settings.CONFIRM_SIGNING_SECRET or settings.JWT_SECRET).encode("utf-8")


def _firma(filename: str, exp: int) -> str:
    mensaje = f"{filename}:{exp}".encode()
    return hmac.new(_key(), mensaje, hashlib.sha256).hexdigest()[:32]


def firmar_query(filename: str, ttl: int = DEFAULT_TTL_SECONDS) -> str:
    """Devuelve el querystring firmado: `exp=...&sig=...`."""
    exp = int(time.time()) + int(ttl)
    return urlencode({"exp": exp, "sig": _firma(filename, exp)})


def verificar(filename: str, exp: str | None, sig: str | None) -> bool:
    """¿La firma es válida y el enlace no venció? Cualquier basura → False."""
    if not exp or not sig:
        return False
    try:
        exp_i = int(exp)
    except (TypeError, ValueError):
        return False
    if exp_i < int(time.time()):
        return False
    # compare_digest: la firma es un secreto, no se compara con ==.
    return hmac.compare_digest(_firma(filename, exp_i), str(sig))
