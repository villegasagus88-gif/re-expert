"""
AcademiaInterest — eventos de interés en cursos (medición de demanda por tema).

Cada vez que un usuario abre el detalle de un curso o toca "Solicitar información" /
"Inscribirme" se registra un evento. Sirve para que el dueño sepa qué temas/cursos
interesan más (datos de demanda).
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class AcademiaInterest(Base):
    __tablename__ = "academia_interest"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    course_title: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    topic: Mapped[str] = mapped_column(String(40), nullable=False, server_default="", index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False, server_default="view")  # view | info | inscribir
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AcademiaInterest course={self.course_id} action={self.action}>"
