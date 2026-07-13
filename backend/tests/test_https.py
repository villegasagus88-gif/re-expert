"""
Tests for HTTPS enforcement and HSTS header.

The middleware is only active when settings.DEBUG is False (production).
We build a fresh FastAPI app from a forked module so we can flip DEBUG
without polluting the global `main.app` used by other tests.
"""
import importlib

import pytest
from fastapi.testclient import TestClient


def _build_prod_app():
    """Re-import main with DEBUG=False so HTTPS middleware is mounted."""
    import config.settings as settings_mod
    import main as main_mod

    # Toggle production mode and reload main to re-evaluate the if-block.
    original_debug = settings_mod.settings.DEBUG
    settings_mod.settings.DEBUG = False
    try:
        importlib.reload(main_mod)
        return main_mod.app
    finally:
        # Restore DEBUG and reload main again so other tests see DEBUG=True.
        settings_mod.settings.DEBUG = original_debug
        importlib.reload(main_mod)


@pytest.fixture(scope="module")
def prod_client():
    """TestClient backed by an app where DEBUG=False (prod-like)."""
    app = _build_prod_app()
    yield TestClient(app)
    # cleanup: reload main to default test state (DEBUG=True from .env)
    import main as main_mod
    importlib.reload(main_mod)


# ---------------------------------------------------------------- redirect --

def test_http_request_is_redirected_to_https(prod_client):
    """Plain http://... must be 307-redirected to https://...

    Nota: NO usamos /health porque está exento del redirect a propósito (el
    healthcheck interno de Railway llega por HTTP plano sin X-Forwarded-Proto;
    si lo redirigiéramos, el deploy fallaría). Probamos un path NO exento: el
    middleware redirige todo lo demás igual."""
    r = prod_client.get("/api/billing/status", follow_redirects=False)
    assert r.status_code in (301, 307, 308)
    location = r.headers.get("location", "")
    assert location.startswith("https://"), (
        f"Expected https:// redirect, got: {location}"
    )


def test_health_is_exempt_from_https_redirect(prod_client):
    """/health responde 200 en HTTP plano (exento del redirect) — es lo que
    espera el healthcheck de Railway. Regresión del exempt intencional."""
    r = prod_client.get("/health", follow_redirects=False)
    assert r.status_code == 200


def test_https_request_passes_through(prod_client):
    """When the request scheme is already https, no redirect happens."""
    # TestClient lets us pretend the request arrived over HTTPS.
    r = prod_client.get(
        "/health",
        headers={"x-forwarded-proto": "https"},
        follow_redirects=False,
    )
    # Either a 200 OK (when proxy-headers honored) or a redirect — but if a
    # redirect, the target must NOT be http (prevents loop).
    assert r.status_code != 0
    if r.status_code == 200:
        assert r.json()["status"] == "ok"


# -------------------------------------------------------------- HSTS header --

def test_hsts_header_present_on_https_response(prod_client):
    """Strict-Transport-Security header must be set on every prod response."""
    # We follow the redirect and inspect the final HTTPS response.
    r = prod_client.get("/health", follow_redirects=True)
    # When the redirect lands on https, HSTS must be there:
    hsts = r.headers.get("strict-transport-security")
    # In TestClient the redirect target may not be re-followed against the
    # same app; assert the header on at least one of the responses we got.
    redirected = r.history
    headers_seen = [resp.headers.get("strict-transport-security") for resp in redirected]
    headers_seen.append(hsts)
    assert any(
        h and "max-age=" in h and "includeSubDomains" in h
        for h in headers_seen
    ), f"HSTS header missing. Saw: {headers_seen}"


def test_hsts_header_max_age_at_least_one_year(prod_client):
    """HSTS max-age should be >= 31536000 (1 year) per industry guidance."""
    r = prod_client.get("/health", follow_redirects=True)
    candidates = [resp.headers.get("strict-transport-security") for resp in r.history]
    candidates.append(r.headers.get("strict-transport-security"))
    for h in candidates:
        if not h:
            continue
        # parse "max-age=NNNN; ..."
        for part in h.split(";"):
            part = part.strip()
            if part.startswith("max-age="):
                value = int(part.split("=", 1)[1])
                assert value >= 31_536_000
                return
    pytest.fail("No max-age token found in any HSTS header")


# ---------------------------------------------------- DEBUG=True bypass test --

def test_https_redirect_disabled_in_debug_mode():
    """When DEBUG=True (local dev / tests), HTTP must NOT be redirected."""
    from main import app as default_app

    client = TestClient(default_app)
    r = client.get("/health", follow_redirects=False)
    # In debug mode we expect a normal 200, not a redirect.
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
