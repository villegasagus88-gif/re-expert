"""
RevocationRequest — pedidos del Botón de Arrepentimiento.

La Resolución 424/2020 exige un botón visible en la home que inicie la
revocación **sin exigirle al usuario ningún otro trámite ni justificación**.
Eso tiene una consecuencia de diseño que conviene dejar escrita:

- **No se pide sesión.** Obligar a loguearse ES un trámite adicional, y quien
  quiere arrepentirse puede no acordarse de la contraseña. Se identifica por el
  email que declara.
- **Por eso NO se cancela ni se reembolsa automáticamente.** Sin sesión, un
  formulario público que cancele suscripciones ajenas con sólo escribir un email
  sería un vector de abuso trivial. El pedido queda registrado y se procesa; el
  plazo de respuesta es el de la normativa, no el de un click.
- **Se persiste en tabla, no se confía en el mail.** El aviso al titular es
  best-effort (hoy `RESEND_API_KEY` puede no estar configurada en producción):
  si el pedido viviera sólo en un email, un proveedor caído lo haría desaparecer
  y perderíamos la constancia de algo que la ley obliga a atender.

`processed_at` + `admin_note` son la trazabilidad de que se atendió, que es lo
que hay que poder mostrar si alguien reclama.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Identity, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class RevocationRequest(Base):
    __tablename__ = "revocation_requests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    # Número corto para referirse al pedido ("tu solicitud #100"). Mismo criterio
    # que los reportes de error: lo genera Postgres, nunca se repite.
    numero: Mapped[int] = mapped_column(
        Integer, Identity(always=False, start=100, increment=1), nullable=False, unique=True
    )
    # Email que declaró la persona. NO se valida contra una sesión a propósito
    # (ver el docstring del módulo): es el dato de contacto del pedido.
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Si el email coincide con una cuenta, se guarda para no tener que buscarla
    # a mano después. SET NULL: el pedido sobrevive a la baja de la cuenta —
    # justamente es la constancia de que se pidió.
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    # Opcionales: la ley prohíbe exigir justificación, así que se piden como
    # "si querés contarnos" y nunca bloquean el envío.
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    motivo: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    admin_note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        # La bandeja se ordena por "sin atender primero, más viejo primero".
        Index("ix_revocation_requests_pendientes", "processed", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RevocationRequest #{self.numero} {self.email} procesado={self.processed}>"
