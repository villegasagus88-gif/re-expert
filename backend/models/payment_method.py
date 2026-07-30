"""
Medios de pago guardados del usuario (tarjetas de crédito/débito).

⚠️ ACÁ NO SE GUARDA NINGÚN DATO DE TARJETA.

El número, el vencimiento completo y el código de seguridad **nunca pasan por
nuestro backend**: el navegador los envía directo a Mercado Pago mediante su
SDK, que devuelve un token de un solo uso. Con ese token le pedimos a MP que
guarde la tarjeta en su bóveda y nos devuelve un identificador (`mp_card_id`).

Lo único que persistimos es ese identificador y los datos que sirven para que el
usuario reconozca su tarjeta en pantalla: marca y últimos cuatro dígitos. Los
últimos cuatro NO son dato de tarjeta en el sentido de PCI-DSS (es lo que
imprime cualquier ticket) y por sí solos no permiten ninguna operación.

Esto es lo que sostiene la afirmación de los Términos y de la Política de
Privacidad: "el Titular no recibe, almacena ni procesa los datos completos de tu
tarjeta". Si alguna vez se agrega una columna con el número, esa declaración
pasa a ser falsa y el proyecto entra en alcance PCI-DSS completo.

Roles:
  - `principal`: la tarjeta con la que Mercado Pago cobra la suscripción.
  - `respaldo`:  la alternativa que se le ofrece al usuario si el cobro falla.
                 MP exige el código de seguridad para usarla, así que el cambio
                 lo confirma la persona con un clic; no es automático.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # Identificadores en la bóveda de Mercado Pago. Sin ellos no se puede operar,
    # pero por sí solos tampoco: requieren nuestro access token.
    mp_customer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mp_card_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # Para que el usuario reconozca la tarjeta. NO son datos operables.
    brand: Mapped[str] = mapped_column(String(30), nullable=False, server_default="")
    last_four: Mapped[str] = mapped_column(String(4), nullable=False, server_default="")
    exp_month: Mapped[int | None] = mapped_column(nullable=True)
    exp_year: Mapped[int | None] = mapped_column(nullable=True)
    holder_name: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")

    # 'principal' | 'respaldo'
    role: Mapped[str] = mapped_column(String(12), nullable=False, server_default="principal")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        # Una tarjeta no puede estar guardada dos veces para el mismo usuario.
        Index("ix_payment_methods_user_card", "user_id", "mp_card_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<PaymentMethod {self.brand} ****{self.last_four} ({self.role})>"


class BillingIssue(Base):
    """
    Un cobro que falló y todavía no se resolvió.

    Existe para no cortarle el acceso a alguien por un rechazo transitorio (sin
    fondos ese día, tarjeta vencida, límite). Mientras hay un issue abierto, la
    app le avisa al usuario y le ofrece pagar con su tarjeta de respaldo.
    """

    __tablename__ = "billing_issues"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # Motivo que devolvió MP (status_detail), para poder explicarlo en criollo.
    reason: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    mp_payment_id: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # Hasta cuándo se mantiene el acceso mientras el usuario resuelve el pago.
    grace_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Mercado Pago ya pausó la suscripción, pero el corte de acceso está
    # diferido hasta que venza la gracia. El scheduler lo aplica al vencer.
    # Sin esto, la gracia sería un cartel: MP pausa y el acceso se corta igual.
    pending_downgrade: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    # Cuándo el usuario pidió reintentar con otra tarjeta. Sirve para mostrar
    # "reintento en curso" en vez del mismo cartel rojo mientras MP procesa.
    retry_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_billing_issues_user_open", "user_id", "resolved"),
        # Un solo cobro pendiente por usuario: convierte la carrera entre dos
        # entregas del webhook en un IntegrityError en vez de dos carteles.
        Index(
            "ix_billing_issues_uno_abierto", "user_id",
            unique=True, postgresql_where=text("resolved = false"),
        ),
    )

    def __repr__(self) -> str:
        return f"<BillingIssue {self.reason} resuelto={self.resolved}>"
