"""
Robustez del JWT_SECRET (P0 de la auditoría 2026-07).

El JWT_SECRET firma todos los tokens de sesión (HS256); un secreto débil los
hace forjables offline. En producción (DEBUG=False) el arranque debe FALLAR si
el secreto es débil; en dev (DEBUG=True) solo advierte.

Se testea el validator instanciando Settings con overrides. conftest ya setea
los required (DATABASE_URL, etc.) en el env, así que solo pisamos JWT_SECRET/DEBUG.
"""
import logging

import pytest
from config.settings import Settings
from pydantic import ValidationError

STRONG = "test-jwt-secret-not-for-prod-9f3a71c2e8b45d60a"  # 45 chars, variado


def _make(**over):
    return Settings(**over)


# ── Producción (DEBUG=False): el arranque FALLA con secreto débil ──

def test_prod_secreto_fuerte_ok():
    s = _make(JWT_SECRET=STRONG, DEBUG=False)
    assert s.JWT_SECRET == STRONG


def test_prod_secreto_corto_falla():
    with pytest.raises(ValidationError, match="muy corto"):
        _make(JWT_SECRET="corto-123", DEBUG=False)


def test_prod_placeholder_falla():
    # Placeholder conocido, aunque tuviera 32+ chars sería rechazado.
    with pytest.raises(ValidationError, match="placeholder"):
        _make(JWT_SECRET="your-jwt-secret-here", DEBUG=False)


def test_prod_baja_variedad_falla():
    # 40 chars pero un solo carácter distinto → poca entropía.
    with pytest.raises(ValidationError, match="poca variedad"):
        _make(JWT_SECRET="a" * 40, DEBUG=False)


def test_prod_vacio_falla():
    with pytest.raises(ValidationError):
        _make(JWT_SECRET="", DEBUG=False)


# ── Dev (DEBUG=True): NO rompe, solo advierte ──

def test_dev_secreto_debil_no_rompe_pero_advierte(caplog):
    with caplog.at_level(logging.WARNING, logger="re_expert.settings"):
        s = _make(JWT_SECRET="test-dummy-secret", DEBUG=True)
    assert s.JWT_SECRET == "test-dummy-secret"        # arrancó igual
    assert any("JWT_SECRET inseguro" in r.message for r in caplog.records)


def test_dev_secreto_fuerte_no_advierte(caplog):
    with caplog.at_level(logging.WARNING, logger="re_expert.settings"):
        _make(JWT_SECRET=STRONG, DEBUG=True)
    assert not any("JWT_SECRET inseguro" in r.message for r in caplog.records)


# ── El singleton real (env de conftest) construye OK en DEBUG=False ──

def test_singleton_de_conftest_es_fuerte():
    from config.settings import settings
    assert len(settings.JWT_SECRET) >= 32
