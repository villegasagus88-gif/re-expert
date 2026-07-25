"""
User location models — capacidad de geolocalización de plataforma.

Dos tablas:
  - UserLocationSettings: consentimiento y precisión elegida por el usuario.
    Fail-safe: sin fila (o consent != 'granted') no se aceptan fixes.
  - UserLocation: fixes append-only con geohash indexado. La retención la
    aplica services/location_service.py en cada insert (poda por cantidad
    y por edad) — la tabla nunca crece sin tope.

Privacidad por diseño:
  - En modo 'coarse' la coordenada se redondea ANTES de persistir: la
    ubicación exacta nunca toca el disco.
  - Purga total self-service vía DELETE /api/location/me.
  - ON DELETE CASCADE: borrar la cuenta borra todo rastro de ubicación.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class UserLocationSettings(Base):
    __tablename__ = "user_location_settings"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # unset | granted | denied
    consent: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="unset"
    )
    # exact | coarse
    precision: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="exact"
    )
    consent_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<UserLocationSettings user={self.user_id} "
            f"consent={self.consent} precision={self.precision}>"
        )


class UserLocation(Base):
    __tablename__ = "user_locations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    lat: Mapped[float] = mapped_column(Float(53), nullable=False)
    lon: Mapped[float] = mapped_column(Float(53), nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float(53), nullable=True)
    altitude_m: Mapped[float | None] = mapped_column(Float(53), nullable=True)
    heading_deg: Mapped[float | None] = mapped_column(Float(53), nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float(53), nullable=True)
    # gps | network | ip | manual
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="gps"
    )
    geohash: Mapped[str] = mapped_column(String(12), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_user_locations_user_created", "user_id", text("created_at DESC")),
        Index("ix_user_locations_geohash", "geohash"),
    )

    def __repr__(self) -> str:
        # Sin coordenadas en el repr: que un log casual no filtre ubicación.
        return f"<UserLocation id={self.id} user={self.user_id} source={self.source}>"
