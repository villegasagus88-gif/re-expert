"""Regresión de los fixes de seguridad (auditoría 2026-07).

Cubre lo crítico de cada fix a nivel unitario (sin red ni DB real):
- rate-limit: la clave sale del EXTREMO DERECHO de X-Forwarded-For (no forjable).
- safe_fetch: se bloquea la IP REAL conectada (anti DNS-rebinding).
"""
from types import SimpleNamespace

import pytest

import core.rate_limit as rl
import core.safe_fetch as sf


# ── Rate-limit: XFF spoofing ──

def _req(xff=None, client_host="10.0.0.9"):
    headers = {}
    if xff is not None:
        headers["x-forwarded-for"] = xff
    # slowapi.get_remote_address lee request.client.host; simulamos ambos.
    return SimpleNamespace(headers=_Headers(headers), client=SimpleNamespace(host=client_host))


class _Headers(dict):
    # request.headers de Starlette es case-insensitive; get() alcanza para el test.
    def get(self, k, default=None):
        return super().get(k.lower(), default)


def test_rate_limit_toma_el_extremo_derecho_del_xff():
    # El atacante controla el valor izquierdo; el edge de Railway appenda el real
    # a la derecha. La clave del rate-limit debe ser el de la DERECHA.
    r = _req(xff="1.1.1.1, 203.0.113.7")
    assert rl.client_ip_for_rate_limit(r) == "203.0.113.7"


def test_rate_limit_no_se_evade_rotando_el_leftmost():
    # Dos requests del mismo atacante rotando el XFF izquierdo → MISMA clave.
    a = rl.client_ip_for_rate_limit(_req(xff="9.9.9.9, 203.0.113.7"))
    b = rl.client_ip_for_rate_limit(_req(xff="8.8.8.8, 203.0.113.7"))
    assert a == b == "203.0.113.7"


def test_rate_limit_sin_xff_usa_client_host():
    r = _req(xff=None, client_host="198.51.100.4")
    assert rl.client_ip_for_rate_limit(r) == "198.51.100.4"


def test_rate_limit_hops_configurable(monkeypatch):
    # Con 2 hops confiables, toma el penúltimo desde la derecha.
    monkeypatch.setattr(rl.settings, "RATE_LIMIT_TRUSTED_PROXY_HOPS", 2, raising=False)
    r = _req(xff="1.1.1.1, 203.0.113.7, 172.16.0.1")
    assert rl.client_ip_for_rate_limit(r) == "203.0.113.7"


# ── safe_fetch: anti DNS-rebinding (valida la IP conectada) ──

def _resp_with_peer(ip):
    class _NS:
        def get_extra_info(self, k):
            return (ip, 443) if k == "server_addr" else None
    return SimpleNamespace(extensions={"network_stream": _NS()})


def test_safe_fetch_bloquea_peer_interno():
    # El host resolvió público al validar pero la conexión terminó en una IP
    # interna (DNS-rebinding) → se aborta.
    with pytest.raises(sf.UnsafeUrlError):
        sf._assert_peer_public(_resp_with_peer("169.254.169.254"))  # metadata cloud
    with pytest.raises(sf.UnsafeUrlError):
        sf._assert_peer_public(_resp_with_peer("127.0.0.1"))
    with pytest.raises(sf.UnsafeUrlError):
        sf._assert_peer_public(_resp_with_peer("10.1.2.3"))


def test_safe_fetch_permite_peer_publico():
    # Peer público → no lanza.
    sf._assert_peer_public(_resp_with_peer("8.8.8.8"))


def test_safe_fetch_sin_network_stream_no_rompe():
    # Si el transport no expone el stream, no revienta (queda la validación previa).
    sf._assert_peer_public(SimpleNamespace(extensions={}))


# ── auth: cambiar password invalida sesiones viejas (bump de token_version) ──

class _FakeSession:
    def __init__(self, user):
        self._user = user
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        user = self._user

        class _R:
            def scalar_one_or_none(self):
                return user
        return _R()

    async def commit(self):
        self.committed = True


def _patch_session(monkeypatch, auth, user):
    monkeypatch.setattr(auth, "get_session_factory", lambda: (lambda: _FakeSession(user)))
    monkeypatch.setattr(auth, "_verify_password", lambda p, h: True)
    monkeypatch.setattr(auth, "_hash_password", lambda p: "newhash")


@pytest.mark.anyio
async def test_update_profile_bumpea_token_version_al_cambiar_password(monkeypatch):
    from uuid import uuid4

    import services.auth_service as auth
    user = SimpleNamespace(id=uuid4(), password_hash="old", token_version=3, full_name="X")
    _patch_session(monkeypatch, auth, user)
    await auth.update_profile(str(user.id), email="m@x.com",
                              current_password="old", new_password="NuevaPass123!")
    assert user.token_version == 4  # +1 → invalida access/refresh tokens previos
    assert user.password_hash == "newhash"


@pytest.mark.anyio
async def test_update_profile_solo_nombre_no_bumpea(monkeypatch):
    from uuid import uuid4

    import services.auth_service as auth
    user = SimpleNamespace(id=uuid4(), password_hash="old", token_version=3, full_name="X")
    _patch_session(monkeypatch, auth, user)
    await auth.update_profile(str(user.id), email="m@x.com", full_name="Nuevo Nombre")
    assert user.token_version == 3  # sin cambio de password → NO se invalidan sesiones
    assert user.full_name == "Nuevo Nombre"
