"""
Guard anti-SSRF compartido para fetches de URLs provistas por el usuario.

Contexto: varios features bajan HTML de una URL que el usuario pasa (digest de
noticias, extractor de oportunidades). Sin control, un atacante autenticado
puede forzar al backend a pegarle a la red interna / metadata de la nube (SSRF).

Este módulo centraliza la defensa:
  - Solo esquemas http/https.
  - Resuelve TODAS las IPs del host y rechaza privadas / loopback / link-local /
    reservadas / multicast / CGNAT (v4 y v6, incluidas IPv4-mapped).
  - `safe_get` sigue redirects MANUALMENTE revalidando cada salto (un host
    público que redirige a una IP interna es un bypass clásico).

Uso:
    from core.safe_fetch import safe_get, UnsafeUrlError
    resp = await safe_get(url, timeout=20.0, headers={...})

Nota: no cubre DNS-rebinding (TOCTOU entre resolución y conexión). Para el
modelo de amenaza actual (URLs públicas de medios/portales) el bloqueo de
destinos internos + revalidación de redirects cierra el vector explotable.
"""
from __future__ import annotations

import ipaddress
import socket

import httpx


class UnsafeUrlError(ValueError):
    """La URL apunta a un destino no permitido (interno / esquema inválido)."""


def _ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # IPv4-mapped IPv6 (::ffff:a.b.c.d) → evaluar la IPv4 embebida.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if (
        ip.is_private or ip.is_loopback or ip.is_link_local
        or ip.is_reserved or ip.is_multicast or ip.is_unspecified
    ):
        return True
    # CGNAT 100.64.0.0/10 (no lo marca is_private).
    if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network("100.64.0.0/10"):
        return True
    return False


def assert_public_url(url: str) -> None:
    """Valida que `url` sea http(s) y resuelva SOLO a IPs públicas. Si no, lanza
    UnsafeUrlError. No hace ninguna request."""
    try:
        parsed = httpx.URL(url)
    except Exception as exc:  # noqa: BLE001
        raise UnsafeUrlError(f"URL inválida: {exc}") from exc
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Esquema no permitido: {parsed.scheme!r}")
    host = parsed.host
    if not host:
        raise UnsafeUrlError("URL sin host")

    # Si el host YA es una IP literal, validarla directo.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if _ip_is_blocked(literal):
            raise UnsafeUrlError(f"IP no permitida: {host}")
        return

    # Resolver el hostname y rechazar si CUALQUIER IP resuelta es interna.
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80),
                                   proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise UnsafeUrlError(f"No se pudo resolver el host: {host}") from exc
    if not infos:
        raise UnsafeUrlError(f"Host sin direcciones: {host}")
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            raise UnsafeUrlError(f"IP resuelta inválida: {addr}") from None
        if _ip_is_blocked(ip):
            raise UnsafeUrlError(f"El host {host} resuelve a una IP interna ({addr})")


async def safe_get(
    url: str,
    *,
    timeout: float = 20.0,
    headers: dict | None = None,
    max_redirects: int = 5,
) -> httpx.Response:
    """GET con guard anti-SSRF: valida la URL inicial y CADA redirect contra
    `assert_public_url`. Lanza UnsafeUrlError si algún salto es no permitido."""
    assert_public_url(url)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False,
                                 headers=headers or {}) as client:
        current = url
        for _ in range(max_redirects + 1):
            resp = await client.get(current)
            if resp.is_redirect and resp.headers.get("location"):
                current = str(httpx.URL(current).join(resp.headers["location"]))
                assert_public_url(current)  # revalidar cada salto
                continue
            return resp
    raise UnsafeUrlError("Demasiados redirects")
