"""
Rate limiting configuration using slowapi.

La IP que usamos como clave del rate-limit se toma del EXTREMO DERECHO de
`X-Forwarded-For`, que es el valor que agrega el proxy confiable (el edge de
Railway) y que el cliente NO puede falsificar. El extremo izquierdo lo controla
el atacante: como el contenedor arranca uvicorn con `--forwarded-allow-ips='*'`,
tomar el leftmost (get_remote_address / request.client.host) permitía evadir el
límite rotando el header en cada request → brute-force / credential-stuffing sin
freno. Ver hallazgo de seguridad (2026-07).

`RATE_LIMIT_TRUSTED_PROXY_HOPS` (default 1) es la cantidad de proxies confiables
que appendan al XFF, contados desde la derecha; en Railway el único hop confiable
es el edge (1). Si algún día se agrega otro proxy que appenda, se sube el número
por env sin tocar código.
"""
from config.settings import settings
from slowapi import Limiter
from slowapi.util import get_remote_address


def client_ip_for_rate_limit(request) -> str:
    """IP real del cliente para el rate-limit, resistente a spoofing de XFF.

    Los proxies conformes al estándar APPENDAN a la derecha de X-Forwarded-For
    el IP del peer que les conectó. Por eso el último valor (el que puso el edge)
    no lo puede falsificar el cliente; el primero sí. Tomamos el N-ésimo desde la
    derecha, donde N = cantidad de hops confiables.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            hops = max(1, getattr(settings, "RATE_LIMIT_TRUSTED_PROXY_HOPS", 1))
            return parts[-min(hops, len(parts))]
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip_for_rate_limit)
