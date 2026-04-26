"""
Budget model - maps to public.budgets.

Item de presupuesto, gasto extra o desvío de obra (carga típica vía SOL).
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(200), nullable=False)  # rubro
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="ARS")
    kind: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="planned"
    )  # planned | extra | actual
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default="sol")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<Budget id={self.id} category={self.category!r} "
            f"amount={self.amount} {self.currency} kind={self.kind}>"
        )
