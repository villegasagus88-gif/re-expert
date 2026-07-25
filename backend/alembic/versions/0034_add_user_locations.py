"""Add user location tables: user_location_settings + user_locations

Módulo de geolocalización (capacidad de plataforma, consumida después por
las features que la necesiten — ver docs/LOCATION_MODULE.md):

- `user_location_settings`: 1 fila por usuario con el estado de consentimiento
  (unset/granted/denied) y la precisión elegida (exact/coarse). Fail-safe:
  sin fila o consent != granted, el backend NO acepta ni guarda fixes.
- `user_locations`: fixes de ubicación append-only con geohash indexado
  (consultas de proximidad por prefijo sin PostGIS) y retención acotada
  (el service poda por cantidad y por edad en cada insert).

Revision ID: 0034_add_user_locations
Revises: 0033_add_material_list
Create Date: 2026-07-25 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0034_add_user_locations"
down_revision: str | None = "0033_add_material_list"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ─── user_location_settings (consentimiento, 1 fila por usuario) ──────
    op.create_table(
        "user_location_settings",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # unset | granted | denied — fail-safe: solo 'granted' habilita fixes.
        sa.Column("consent", sa.String(10), nullable=False, server_default="unset"),
        # exact (~centímetros, lo que dé el device) | coarse (~1 km, redondeado
        # server-side ANTES de persistir — la coordenada exacta nunca se guarda).
        sa.Column("precision", sa.String(10), nullable=False, server_default="exact"),
        sa.Column("consent_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ─── user_locations (fixes append-only) ───────────────────────────────
    op.create_table(
        "user_locations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # double precision — estándar GIS (PostGIS usa lo mismo). 6 decimales
        # de precisión útil ≈ 0.11 m.
        sa.Column("lat", sa.Float(53), nullable=False),
        sa.Column("lon", sa.Float(53), nullable=False),
        # Metadatos que reporta el device (Geolocation API). Todos opcionales.
        sa.Column("accuracy_m", sa.Float(53), nullable=True),
        sa.Column("altitude_m", sa.Float(53), nullable=True),
        sa.Column("heading_deg", sa.Float(53), nullable=True),
        sa.Column("speed_mps", sa.Float(53), nullable=True),
        # gps | network | ip | manual
        sa.Column("source", sa.String(16), nullable=False, server_default="gps"),
        # Geohash base32 (precisión 9 ≈ celda de 4.8 m; en modo coarse, 5 ≈ 4.9 km).
        # Permite proximidad por prefijo (WHERE geohash LIKE '69y7p%') sin PostGIS.
        sa.Column("geohash", sa.String(12), nullable=False),
        # Cuándo el device tomó el fix (clampeado a now() si viene del futuro).
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # "última ubicación de X" y poda por antigüedad — ambas O(log n).
    op.create_index(
        "ix_user_locations_user_created",
        "user_locations",
        ["user_id", sa.text("created_at DESC")],
    )
    # Proximidad por prefijo de geohash (features futuras: "cerca de la obra").
    op.create_index("ix_user_locations_geohash", "user_locations", ["geohash"])


def downgrade() -> None:
    op.drop_index("ix_user_locations_geohash", table_name="user_locations")
    op.drop_index("ix_user_locations_user_created", table_name="user_locations")
    op.drop_table("user_locations")
    op.drop_table("user_location_settings")
