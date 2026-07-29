"""
BugReport model — reportes de error que mandan los usuarios desde
Ayuda → Informar un error.

Cada reporte guarda lo que escribió el usuario (título, descripción, sección
donde le pasó, notas) y el CONTEXTO técnico que el frontend captura solo
(user agent, viewport, URL, versión) — eso es lo que después ahorra el
ida y vuelta de "¿en qué pantalla te pasó?".

Ciclo de vida del `status`: new → in_review → resolved | dismissed.
Los admins lo mueven desde el panel y pueden dejar una `admin_note` interna
(NUNCA se le muestra al usuario: la ruta de usuario no la serializa).

Adjuntos: hoy los reportes son solo texto (decisión de producto para no
inflar la DB). El modelo deja `attachments_count` preparado para cuando se
sumen capturas, sin migración destructiva.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, Identity, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

# Estados válidos (se validan en la ruta; el CHECK vive en la migración).
BUG_STATUSES = ("new", "in_review", "resolved", "dismissed")
# Severidad la elige el usuario; es orientativa, no gobierna nada automático.
BUG_SEVERITIES = ("low", "normal", "high")


class BugReport(Base):
    __tablename__ = "bug_reports"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    # Número corto y legible para hablar con el usuario ("tu reporte #1042").
    # IDENTITY: lo genera Postgres (arranca en 1000); nunca se repite ni se reusa.
    ticket: Mapped[int] = mapped_column(
        Integer, Identity(always=False, start=1000, increment=1),
        nullable=False, unique=True, index=True,
    )

    # ondelete=SET NULL: si el usuario borra su cuenta, el reporte sobrevive
    # (nos sirve para el historial de bugs) pero pierde el vínculo personal.
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Copia del email al momento del reporte: si el usuario se borra, todavía
    # sabemos a quién contestarle.
    reporter_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Sección de la app donde pasó (chat, planos, materiales, …). Texto libre
    # acotado: el front ofrece la lista pero no queremos romper si suma una.
    section: Mapped[str | None] = mapped_column(String(60), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, server_default="normal")

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="new", index=True
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Contexto técnico que captura el frontend (user agent, viewport, url, etc.).
    # JSONB libre a propósito: sumar un campo no necesita migración.
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    attachments_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        # La bandeja del admin filtra por estado y ordena por fecha: un índice
        # compuesto cubre esa query sin scan.
        Index("ix_bug_reports_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<BugReport #{self.ticket} {self.status} {self.title[:30]!r}>"
