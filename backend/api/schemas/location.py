"""Pydantic schemas — módulo de geolocalización (/api/location/*)."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

LocationConsent = Literal["granted", "denied"]
LocationPrecision = Literal["exact", "coarse"]
# 'ip' se reserva para el server (fallback futuro); el cliente no puede declararlo.
LocationSource = Literal["gps", "network", "manual"]


class ConsentUpdateRequest(BaseModel):
    consent: LocationConsent
    precision: LocationPrecision = "exact"


class ConsentOut(BaseModel):
    consent: Literal["unset", "granted", "denied"]
    precision: LocationPrecision
    consent_updated_at: datetime | None


class LocationFixRequest(BaseModel):
    # ge/le también rechazan NaN/Inf (no comparan) → doble barrera con el service.
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    accuracy_m: float | None = Field(None, ge=0, le=100_000)
    altitude_m: float | None = Field(None, ge=-500, le=10_000)
    heading_deg: float | None = Field(None, ge=0, le=360)
    speed_mps: float | None = Field(None, ge=0, le=200)
    source: LocationSource = "gps"
    # Timestamp del device. El server lo clampa si viene del futuro.
    captured_at: datetime | None = None


class LocationFixOut(BaseModel):
    id: UUID
    lat: float
    lon: float
    accuracy_m: float | None
    source: str
    geohash: str
    captured_at: datetime
    created_at: datetime


class LatestLocationOut(BaseModel):
    found: bool
    fix: LocationFixOut | None = None


class LocationHistoryResponse(BaseModel):
    items: list[LocationFixOut]
    total: int


class PurgeResponse(BaseModel):
    deleted: int
