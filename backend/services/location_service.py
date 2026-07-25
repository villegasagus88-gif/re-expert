"""
Location service — lógica del módulo de geolocalización.

Diseño (ver docs/LOCATION_MODULE.md):
  - Consent-first y fail-safe: sin consent 'granted' NO se acepta ni guarda
    ningún fix (ConsentRequiredError → 403 en la ruta).
  - Privacidad por diseño: en modo 'coarse' la coordenada se redondea a
    ~1.1 km ANTES de persistir. La exacta nunca toca el disco.
  - Retención acotada: en cada insert se poda lo que exceda el tope por
    usuario y lo más viejo que la ventana de retención.
  - Geohash propio (base32 estándar, ~25 líneas): habilita proximidad por
    prefijo sin PostGIS ni dependencias nuevas.

Sin llamadas externas: todo local y determinístico. Reverse-geocoding e
IP-fallback quedan como extensiones pluggables (fase de integración).

Knobs por env var (self-contained, no toca config/settings.py):
  LOCATION_MAX_FIXES_PER_USER  (default 500)
  LOCATION_RETENTION_DAYS      (default 90)
"""
from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from models.user_location import UserLocation, UserLocationSettings
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# ─── Knobs de retención (env-overrideable) ────────────────────────────
MAX_FIXES_PER_USER = int(os.getenv("LOCATION_MAX_FIXES_PER_USER", "500"))
RETENTION_DAYS = int(os.getenv("LOCATION_RETENTION_DAYS", "90"))

# Precisión del geohash persistido según el modo del usuario.
#   exact  → 9 chars ≈ celda de 4.8 m × 4.8 m
#   coarse → 5 chars ≈ celda de 4.9 km × 4.9 km
GEOHASH_PRECISION = {"exact": 9, "coarse": 5}

# Redondeo decimal en modo coarse: 2 decimales ≈ 1.1 km de celda.
COARSE_DECIMALS = 2

VALID_CONSENT = {"granted", "denied"}
VALID_PRECISION = {"exact", "coarse"}
VALID_SOURCES = {"gps", "network", "ip", "manual"}


class ConsentRequiredError(Exception):
    """El usuario no otorgó consentimiento de ubicación (o lo negó)."""


# ════════════════════════════════════════════════════════════════════
# Lógica pura (testeable sin DB)
# ════════════════════════════════════════════════════════════════════

_GEOHASH_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def validate_coordinates(lat: float, lon: float) -> None:
    """Valida rangos y finitud. Levanta ValueError con mensaje claro."""
    if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
        raise ValueError("lat/lon deben ser numéricos")
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise ValueError("lat/lon deben ser finitos")
    if not -90.0 <= lat <= 90.0:
        raise ValueError("lat fuera de rango [-90, 90]")
    if not -180.0 <= lon <= 180.0:
        raise ValueError("lon fuera de rango [-180, 180]")


def encode_geohash(lat: float, lon: float, precision: int = 9) -> str:
    """Geohash estándar (base32). Implementación propia — sin dependencias.

    Referencia: https://en.wikipedia.org/wiki/Geohash. La celda se achica a
    la mitad por bit, alternando lon/lat; cada 5 bits → 1 char base32.
    """
    precision = max(1, min(12, precision))
    lat_lo, lat_hi = -90.0, 90.0
    lon_lo, lon_hi = -180.0, 180.0
    bits: list[int] = []
    even = True  # arranca por longitud (convención del estándar)
    while len(bits) < precision * 5:
        if even:
            mid = (lon_lo + lon_hi) / 2
            if lon >= mid:
                bits.append(1)
                lon_lo = mid
            else:
                bits.append(0)
                lon_hi = mid
        else:
            mid = (lat_lo + lat_hi) / 2
            if lat >= mid:
                bits.append(1)
                lat_lo = mid
            else:
                bits.append(0)
                lat_hi = mid
        even = not even
    chars = []
    for i in range(0, len(bits), 5):
        value = 0
        for b in bits[i : i + 5]:
            value = (value << 1) | b
        chars.append(_GEOHASH_BASE32[value])
    return "".join(chars)


def coarsen(lat: float, lon: float) -> tuple[float, float]:
    """Redondea la coordenada al grid coarse (~1.1 km). Para modo privacidad."""
    return round(lat, COARSE_DECIMALS), round(lon, COARSE_DECIMALS)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos (esfera WGS84 media)."""
    r = 6_371_008.8  # radio medio terrestre en metros
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def ensure_consent(settings_row: UserLocationSettings | None) -> UserLocationSettings:
    """Gate central: solo consent='granted' habilita operar con fixes."""
    if settings_row is None or settings_row.consent != "granted":
        raise ConsentRequiredError(
            "El usuario no habilitó compartir ubicación (consent != granted)."
        )
    return settings_row


def clamp_captured_at(captured_at: datetime | None, now: datetime | None = None) -> datetime:
    """Normaliza el timestamp del device.

    - None → now (el server manda).
    - Naive → se asume UTC.
    - Futuro (> 5 min de skew tolerado) → clamp a now: un device con reloj
      roto no puede insertar fixes 'del futuro' que rompan el orden.
    """
    now = now or datetime.now(timezone.utc)
    if captured_at is None:
        return now
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    if captured_at > now + timedelta(minutes=5):
        return now
    return captured_at


# ════════════════════════════════════════════════════════════════════
# Operaciones con DB
# ════════════════════════════════════════════════════════════════════


async def get_settings(db: AsyncSession, user_id: UUID) -> UserLocationSettings | None:
    return await db.get(UserLocationSettings, user_id)


async def set_consent(
    db: AsyncSession,
    user_id: UUID,
    consent: str,
    precision: str = "exact",
) -> UserLocationSettings:
    """Crea/actualiza el consentimiento del usuario (upsert de su única fila)."""
    if consent not in VALID_CONSENT:
        raise ValueError(f"consent inválido: {consent}")
    if precision not in VALID_PRECISION:
        raise ValueError(f"precision inválida: {precision}")
    row = await db.get(UserLocationSettings, user_id)
    now = datetime.now(timezone.utc)
    if row is None:
        row = UserLocationSettings(
            user_id=user_id,
            consent=consent,
            precision=precision,
            consent_updated_at=now,
        )
        db.add(row)
    else:
        row.consent = consent
        row.precision = precision
        row.consent_updated_at = now
        row.updated_at = now
    await db.commit()
    await db.refresh(row)
    return row


async def record_fix(
    db: AsyncSession,
    user_id: UUID,
    *,
    lat: float,
    lon: float,
    accuracy_m: float | None = None,
    altitude_m: float | None = None,
    heading_deg: float | None = None,
    speed_mps: float | None = None,
    source: str = "gps",
    captured_at: datetime | None = None,
) -> UserLocation:
    """Valida, aplica precisión del usuario, persiste y poda retención.

    Levanta:
      - ConsentRequiredError si el usuario no otorgó consentimiento.
      - ValueError si la coordenada o el source son inválidos.
    """
    settings_row = ensure_consent(await get_settings(db, user_id))
    validate_coordinates(lat, lon)
    if source not in VALID_SOURCES:
        raise ValueError(f"source inválido: {source}")

    precision = settings_row.precision if settings_row.precision in VALID_PRECISION else "exact"
    if precision == "coarse":
        lat, lon = coarsen(lat, lon)
        # En coarse los metadatos finos también son señal: no se guardan.
        accuracy_m = None
        altitude_m = None
        heading_deg = None
        speed_mps = None

    fix = UserLocation(
        user_id=user_id,
        lat=lat,
        lon=lon,
        accuracy_m=accuracy_m,
        altitude_m=altitude_m,
        heading_deg=heading_deg,
        speed_mps=speed_mps,
        source=source,
        geohash=encode_geohash(lat, lon, GEOHASH_PRECISION[precision]),
        captured_at=clamp_captured_at(captured_at),
    )
    db.add(fix)
    await db.flush()
    await _prune(db, user_id)
    await db.commit()
    await db.refresh(fix)
    return fix


async def _prune(db: AsyncSession, user_id: UUID) -> None:
    """Retención: borra lo que excede MAX_FIXES_PER_USER y lo más viejo
    que RETENTION_DAYS. Corre dentro de la misma transacción del insert."""
    # Por edad
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    await db.execute(
        delete(UserLocation).where(
            UserLocation.user_id == user_id,
            UserLocation.created_at < cutoff,
        )
    )
    # Por cantidad: conservar los MAX_FIXES_PER_USER más nuevos
    keep_ids = select(UserLocation.id).where(
        UserLocation.user_id == user_id
    ).order_by(UserLocation.created_at.desc()).limit(MAX_FIXES_PER_USER)
    await db.execute(
        delete(UserLocation).where(
            UserLocation.user_id == user_id,
            UserLocation.id.not_in(keep_ids),
        )
    )


async def get_latest(db: AsyncSession, user_id: UUID) -> UserLocation | None:
    q = (
        select(UserLocation)
        .where(UserLocation.user_id == user_id)
        .order_by(UserLocation.created_at.desc())
        .limit(1)
    )
    return (await db.execute(q)).scalar_one_or_none()


async def get_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
    before: datetime | None = None,
) -> list[UserLocation]:
    limit = max(1, min(200, limit))
    q = select(UserLocation).where(UserLocation.user_id == user_id)
    if before is not None:
        if before.tzinfo is None:
            before = before.replace(tzinfo=timezone.utc)
        q = q.where(UserLocation.created_at < before)
    q = q.order_by(UserLocation.created_at.desc()).limit(limit)
    return list((await db.execute(q)).scalars().all())


async def purge(db: AsyncSession, user_id: UUID) -> int:
    """Borra TODOS los fixes del usuario (self-service, estilo GDPR).
    El consentimiento no se toca: es una decisión separada del usuario."""
    result = await db.execute(
        delete(UserLocation).where(UserLocation.user_id == user_id)
    )
    await db.commit()
    return int(result.rowcount or 0)
