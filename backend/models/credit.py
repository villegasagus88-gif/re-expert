"""
Modelos de la sección Créditos — Capa Créditos, Fase 2 (mantenimiento).

Fase 1 servía el catálogo desde un JSON estático (efímero en Railway). La Fase 2
mueve el catálogo a la DB para que el pipeline de actualización **persista**:

- Credit: el catálogo publicable. Sembrado desde `data/creditos/creditos.json`
  la primera vez (tabla vacía). A partir de ahí, la DB es la fuente de verdad.
- CreditProposal: cola de validación humana. El monitor (IA) detecta un cambio
  en la fuente oficial y escribe una propuesta `pending_review`. Un admin la
  aprueba (se aplica al Credit + se registra en el log) o la rechaza.
- CreditChangeLog: historial inmutable de cambios aplicados (auditoría).

Solo se expone al público lo que tiene validation_status='approved' y
status='active'. Todo el resto del pipeline vive en estas tablas.

No tocamos el dominio del chat (Capa 2 / system prompt): el monitor usa su
propia llamada a Claude en `services/creditos_monitor.py`.
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Credit(Base):
    """Un crédito del catálogo (hipotecario / construcción / desarrollo)."""

    __tablename__ = "credits"

    # id = slug estable del JSON (ej. "nacion-uva-compra"). PK natural.
    id: Mapped[str] = mapped_column(String(80), primary_key=True)

    # Identidad / clasificación
    country: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Argentina")
    province: Mapped[str] = mapped_column(String(60), nullable=False, server_default="Nacional")
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    bank_emoji: Mapped[str] = mapped_column(String(8), nullable=False, server_default="🏦")
    credit_name: Mapped[str] = mapped_column(String(160), nullable=False)
    audience: Mapped[str] = mapped_column(String(20), nullable=False, server_default="comprador")
    credit_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="compra")
    rate_type: Mapped[str] = mapped_column(String(12), nullable=False, server_default="UVA")

    # Condiciones financieras
    interest_rate_tna: Mapped[float | None] = mapped_column(Float, nullable=True)
    interest_rate_note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    max_term_years: Mapped[int] = mapped_column(Integer, nullable=False, server_default="20")
    max_financing_percent: Mapped[float] = mapped_column(Float, nullable=False, server_default="75")
    min_income_ars: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    min_employment_seniority_months: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    property_value_limit_ars: Mapped[float | None] = mapped_column(Float, nullable=True)
    relacion_cuota_ingreso_max: Mapped[float | None] = mapped_column(
        Float, nullable=True, server_default="25"
    )
    required_savings_note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    # Listas (JSONB) — requisitos, documentos, pros, contras, costos extra
    requirements: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    documents: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    pros: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    cons: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    extra_costs: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    # Fuentes y trazabilidad (Fase 2)
    official_url: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    source_urls: Mapped[Any] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    last_checked_at: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    last_updated_at: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")

    # Estado de publicación
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="approved", index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="active", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Campos que el catálogo expone pero NO son columnas escalares persistidas
    # como tales: change_history se arma desde CreditChangeLog en el route admin.
    def to_item_dict(self) -> dict:
        """Mapea la fila al shape de `CreditItem` (schema público)."""
        return {
            "id": self.id,
            "country": self.country,
            "province": self.province,
            "bank_name": self.bank_name,
            "bank_emoji": self.bank_emoji,
            "credit_name": self.credit_name,
            "audience": self.audience,
            "credit_type": self.credit_type,
            "rate_type": self.rate_type,
            "interest_rate_tna": self.interest_rate_tna,
            "interest_rate_note": self.interest_rate_note,
            "max_term_years": self.max_term_years,
            "max_financing_percent": self.max_financing_percent,
            "min_income_ars": self.min_income_ars,
            "min_employment_seniority_months": self.min_employment_seniority_months,
            "max_age": self.max_age,
            "property_value_limit_ars": self.property_value_limit_ars,
            "relacion_cuota_ingreso_max": self.relacion_cuota_ingreso_max,
            "required_savings_note": self.required_savings_note,
            "requirements": self.requirements or [],
            "documents": self.documents or [],
            "pros": self.pros or [],
            "cons": self.cons or [],
            "extra_costs": self.extra_costs or [],
            "official_url": self.official_url,
            "source_urls": self.source_urls or [],
            "last_checked_at": self.last_checked_at,
            "last_updated_at": self.last_updated_at,
            "validation_status": self.validation_status,
            "change_history": [],
            "status": self.status,
        }


# Campos del Credit que el monitor IA puede proponer cambiar (whitelist).
# Evita que una propuesta toque id, timestamps o estado de publicación.
MONITORABLE_FIELDS: tuple[str, ...] = (
    "interest_rate_tna",
    "interest_rate_note",
    "max_term_years",
    "max_financing_percent",
    "min_income_ars",
    "min_employment_seniority_months",
    "max_age",
    "property_value_limit_ars",
    "required_savings_note",
    "status",
)


class CreditProposal(Base):
    """Cambio detectado por el monitor, a la espera de validación humana."""

    __tablename__ = "credit_proposals"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    # Crédito afectado. NULL = propuesta de crédito NUEVO (no existe todavía).
    credit_id: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("credits.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # field_update | new_credit | discontinued
    change_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="field_update")
    field: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Para new_credit: el item completo propuesto. Para field_update: opcional.
    proposed_payload: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    # Confianza del modelo 0..1 (ayuda a priorizar la revisión).
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Razón / cita textual de la fuente que justifica el cambio.
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # pending_review | approved | rejected
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending_review", index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CreditChangeLog(Base):
    """Historial inmutable de cambios aplicados al catálogo (auditoría)."""

    __tablename__ = "credit_change_log"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    # Sin FK estricta: el log sobrevive aunque el crédito se elimine.
    credit_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    # seed | new_credit | auto_approved | manual_edit | discontinued | rejected
    change_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="manual_edit")
    changed_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    proposal_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
