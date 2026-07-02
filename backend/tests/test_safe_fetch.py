"""Tests del guard anti-SSRF (core/safe_fetch.assert_public_url).

Cubre el vector confirmado en la auditoría: /api/news/digest y
/api/opportunities/extract bajaban URLs arbitrarias. assert_public_url debe
bloquear destinos internos y esquemas no http(s), y permitir IPs públicas.
"""
import pytest

from core.safe_fetch import UnsafeUrlError, assert_public_url


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://127.0.0.1:8000/admin",
    "http://169.254.169.254/latest/meta-data/",   # metadata de nube
    "http://10.0.0.5/",                             # RFC1918
    "http://172.16.5.4/",                           # RFC1918
    "http://192.168.1.1/",                          # RFC1918
    "http://100.64.0.1/",                           # CGNAT
    "http://[::1]/",                                # loopback v6
    "http://0.0.0.0/",                              # unspecified
    "http://[::ffff:127.0.0.1]/",                   # IPv4-mapped loopback
])
def test_bloquea_ips_internas(url):
    with pytest.raises(UnsafeUrlError):
        assert_public_url(url)


@pytest.mark.parametrize("url", [
    "ftp://example.com/x",
    "file:///etc/passwd",
    "gopher://internal/",
    "http://",           # sin host
    "not-a-url",
])
def test_bloquea_esquemas_invalidos(url):
    with pytest.raises(UnsafeUrlError):
        assert_public_url(url)


@pytest.mark.parametrize("url", [
    "http://8.8.8.8/",              # IP pública literal
    "https://1.1.1.1/",            # IP pública literal
])
def test_permite_ips_publicas_literales(url):
    # No debe lanzar (IP pública, sin resolución DNS).
    assert_public_url(url)


def test_hostname_localhost_bloqueado():
    # 'localhost' resuelve a 127.0.0.1 → debe bloquearse.
    with pytest.raises(UnsafeUrlError):
        assert_public_url("http://localhost:9200/")


@pytest.mark.anyio
async def test_safe_get_revalida_redirect_a_interno(monkeypatch):
    """Un host permitido que redirige a una IP interna debe ser bloqueado."""
    import core.safe_fetch as sf

    class _Resp:
        def __init__(self, redirect_to=None):
            self.is_redirect = redirect_to is not None
            self.headers = {"location": redirect_to} if redirect_to else {}

    class _FakeClient:
        def __init__(self, *a, **k): ...
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url):
            # primer host público → redirige a metadata interno
            return _Resp(redirect_to="http://169.254.169.254/")

    # saltear la resolución DNS del host inicial (público) y forzar el fake client
    monkeypatch.setattr(sf, "assert_public_url",
                        lambda u: None if "publico.test" in u else (_ for _ in ()).throw(UnsafeUrlError(u)))
    monkeypatch.setattr(sf.httpx, "AsyncClient", _FakeClient)
    with pytest.raises(UnsafeUrlError):
        await sf.safe_get("http://publico.test/")
