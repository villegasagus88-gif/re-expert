"""
Tests del módulo de geolocalización (/api/location/* + location_service).

Correr aislado (convención del repo):
    cd backend && python -m pytest tests/test_location.py --import-mode=importlib -q

Dos capas:
  - HTTP: auth obligatoria en todos los endpoints (TestClient, sin DB).
  - Unit: lógica pura del service (geohash, validación, coarsen, consent,
    clamp de timestamps) — sin DB ni red.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from main import app
from services import location_service as svc


# ─────────────────────────────────────────────── HTTP: auth requerida ──

def test_consent_get_requires_auth():
    client = TestClient(app)
    assert client.get("/api/location/consent").status_code == 401


def test_consent_put_requires_auth():
    client = TestClient(app)
    r = client.put("/api/location/consent", json={"consent": "granted"})
    assert r.status_code == 401


def test_fix_post_requires_auth():
    client = TestClient(app)
    r = client.post("/api/location/fix", json={"lat": -34.6, "lon": -58.38})
    assert r.status_code == 401


def test_me_get_requires_auth():
    client = TestClient(app)
    assert client.get("/api/location/me").status_code == 401


def test_history_requires_auth():
    client = TestClient(app)
    assert client.get("/api/location/history").status_code == 401


def test_purge_requires_auth():
    client = TestClient(app)
    assert client.delete("/api/location/me").status_code == 401


def test_fix_rejects_get_method():
    client = TestClient(app)
    assert client.get("/api/location/fix").status_code == 405


# ───────────────────────────────────────────────── Unit: geohash ──────

def test_geohash_origin():
    # (0,0) → celda 's' (referencia estándar del algoritmo)
    assert svc.encode_geohash(0.0, 0.0, 9).startswith("s00")


def test_geohash_buenos_aires():
    # Obelisco (CABA) cae en la celda '69y' (referencia pública conocida)
    assert svc.encode_geohash(-34.6037, -58.3816, 9).startswith("69y")


def test_geohash_precision_lengths():
    gh9 = svc.encode_geohash(-34.6037, -58.3816, 9)
    gh5 = svc.encode_geohash(-34.6037, -58.3816, 5)
    assert len(gh9) == 9
    assert len(gh5) == 5
    # La celda coarse es prefijo de la exacta (propiedad jerárquica del geohash)
    assert gh9.startswith(gh5)


def test_geohash_clamps_precision():
    assert len(svc.encode_geohash(1.0, 1.0, 99)) == 12
    assert len(svc.encode_geohash(1.0, 1.0, 0)) == 1


# ─────────────────────────────────────────── Unit: validación coords ──

def test_validate_ok():
    svc.validate_coordinates(-34.6, -58.38)  # no levanta


@pytest.mark.parametrize(
    "lat,lon",
    [
        (91.0, 0.0),
        (-91.0, 0.0),
        (0.0, 181.0),
        (0.0, -181.0),
        (float("nan"), 0.0),
        (0.0, float("inf")),
    ],
)
def test_validate_rejects_out_of_range(lat, lon):
    with pytest.raises(ValueError):
        svc.validate_coordinates(lat, lon)


# ──────────────────────────────────────────────── Unit: privacidad ────

def test_coarsen_rounds_to_grid():
    lat, lon = svc.coarsen(-34.603722, -58.381592)
    assert lat == -34.6
    assert lon == -58.38


def test_ensure_consent_rejects_none():
    with pytest.raises(svc.ConsentRequiredError):
        svc.ensure_consent(None)


def test_ensure_consent_rejects_denied():
    row = type("S", (), {"consent": "denied", "precision": "exact"})()
    with pytest.raises(svc.ConsentRequiredError):
        svc.ensure_consent(row)


def test_ensure_consent_rejects_unset():
    row = type("S", (), {"consent": "unset", "precision": "exact"})()
    with pytest.raises(svc.ConsentRequiredError):
        svc.ensure_consent(row)


def test_ensure_consent_accepts_granted():
    row = type("S", (), {"consent": "granted", "precision": "coarse"})()
    assert svc.ensure_consent(row) is row


# ─────────────────────────────────────────── Unit: clamp captured_at ──

def test_clamp_none_becomes_now():
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    assert svc.clamp_captured_at(None, now) == now


def test_clamp_future_is_clamped():
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    future = now + timedelta(hours=2)
    assert svc.clamp_captured_at(future, now) == now


def test_clamp_small_skew_tolerated():
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    slight = now + timedelta(minutes=3)  # < 5 min de skew: se respeta
    assert svc.clamp_captured_at(slight, now) == slight


def test_clamp_past_passes_through():
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    past = now - timedelta(hours=8)  # device que sincroniza offline
    assert svc.clamp_captured_at(past, now) == past


def test_clamp_naive_assumed_utc():
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    naive = datetime(2026, 7, 25, 10, 0)
    out = svc.clamp_captured_at(naive, now)
    assert out.tzinfo is not None
    assert out == datetime(2026, 7, 25, 10, 0, tzinfo=timezone.utc)


# ─────────────────────────────────────────────── Unit: haversine ──────

def test_haversine_zero_distance():
    assert svc.haversine_m(-34.6, -58.38, -34.6, -58.38) == 0.0


def test_haversine_known_distance():
    # Obelisco → Casa Rosada ≈ 1.1 km (tolerancia 15%)
    d = svc.haversine_m(-34.6037, -58.3816, -34.6083, -58.3702)
    assert 900 < d < 1300
