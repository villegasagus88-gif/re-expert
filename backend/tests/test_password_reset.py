"""
password_reset_service: emisión/consumo de tokens single-use de recuperación.

Superficie de seguridad sensible sin cobertura hasta ahora. Se testea el hashing
del token, la construcción del URL y el flujo de confirm_reset (inválido / usado
/ expirado / válido) con una sesión de DB falsa.
"""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
import services.password_reset_service as pr
from fastapi import HTTPException


def test_hash_token_deterministico_y_sha256():
    h1 = pr._hash_token("abc")
    h2 = pr._hash_token("abc")
    assert h1 == h2 and len(h1) == 64            # SHA-256 hex
    assert pr._hash_token("otro") != h1          # tokens distintos → hashes distintos


def test_build_reset_url_usa_frontend_url_y_lleva_token():
    url = pr._build_reset_url("TOK123")
    assert url.endswith("/reset-password.html?token=TOK123")
    assert url.startswith("http")                # deriva de FRONTEND_URL


# ── confirm_reset: fake session ──

class _Row:
    def __init__(self, obj):
        self._o = obj

    def scalar_one_or_none(self):
        return self._o


class _FakeDB:
    def __init__(self, reset_obj):
        self._reset = reset_obj
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def execute(self, *a, **k):
        return _Row(self._reset)   # select → reset; update → ignorado

    async def commit(self):
        self.committed = True


def _patch(monkeypatch, reset_obj):
    monkeypatch.setattr(pr, "get_session_factory", lambda: (lambda: _FakeDB(reset_obj)))
    monkeypatch.setattr(pr, "_hash_password", lambda p: "hashed")


@pytest.mark.anyio
async def test_confirm_token_inexistente_400(monkeypatch):
    _patch(monkeypatch, None)
    with pytest.raises(HTTPException) as e:
        await pr.confirm_reset("cualquiera", "NuevaPass1!")
    assert e.value.status_code == 400


@pytest.mark.anyio
async def test_confirm_token_ya_usado_400(monkeypatch):
    reset = SimpleNamespace(user_id=uuid4(), used_at=datetime.now(UTC),
                            expires_at=datetime.now(UTC) + timedelta(minutes=10))
    _patch(monkeypatch, reset)
    with pytest.raises(HTTPException) as e:
        await pr.confirm_reset("tok", "NuevaPass1!")
    assert e.value.status_code == 400


@pytest.mark.anyio
async def test_confirm_token_expirado_400(monkeypatch):
    reset = SimpleNamespace(user_id=uuid4(), used_at=None,
                            expires_at=datetime.now(UTC) - timedelta(minutes=1))
    _patch(monkeypatch, reset)
    with pytest.raises(HTTPException) as e:
        await pr.confirm_reset("tok", "NuevaPass1!")
    assert e.value.status_code == 400


@pytest.mark.anyio
async def test_confirm_valido_marca_usado_y_commitea(monkeypatch):
    reset = SimpleNamespace(user_id=uuid4(), used_at=None,
                            expires_at=datetime.now(UTC) + timedelta(minutes=10))
    db_holder = {}

    def _factory():
        def _mk():
            db = _FakeDB(reset)
            db_holder["db"] = db
            return db
        return _mk
    monkeypatch.setattr(pr, "get_session_factory", _factory)
    monkeypatch.setattr(pr, "_hash_password", lambda p: "hashed")

    await pr.confirm_reset("tok", "NuevaPass1!")
    assert reset.used_at is not None            # se marcó consumido
    assert db_holder["db"].committed is True     # persistió la transacción
