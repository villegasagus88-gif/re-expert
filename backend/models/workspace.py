"""
Workspace, WorkspaceMemory, UserProfileGlobal models.

Capa 1B — Memoria persistente y workspaces tipo "Proyectos" de ChatGPT.

- Workspace: carpeta que agrupa N conversaciones del usuario. Tiene memoria
  propia que se inyecta como contexto cuando el chat está dentro del workspace.
- WorkspaceMemory: pares key/value scopeados al workspace. Cargados manualmente
  por el usuario (entrega 1) o por el LLM via tool `remember` (entrega 2).
- UserProfileGlobal: pares key/value scopeados al usuario. Viajan a TODOS los
  chats (incluso chats sueltos). Datos estables como rol, zonas, tipologías,
  preferencias de formato.

Convivencia con `Project` (tracker de obra): son conceptos distintos. Project
es un dashboard con CPI/SPI/milestones (uno por usuario). Workspace es un
agrupador de chats con memoria (N por usuario).
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Workspace(Base):
    __tablename__ = "workspaces"

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
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Color hex (#rrggbb) para chip visual en el sidebar. Opcional.
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    # Descripción libre opcional (ej. "Edificio 4 pisos al costo en Palermo Soho").
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="workspaces")
    memory_items: Mapped[list["WorkspaceMemory"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="workspace"
    )

    def __repr__(self) -> str:
        return f"<Workspace id={self.id} name={self.name!r}>"


class WorkspaceMemory(Base):
    __tablename__ = "workspace_memory"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_workspace_memory_workspace_key"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # key corto en snake_case ("lote_usd", "fot", "estructura_juridica").
    # No único globalmente — solo dentro del workspace (uq_workspace_memory_workspace_key).
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    # Valor en texto libre. Limitado para evitar abuso del context window.
    value: Mapped[str] = mapped_column(String(1000), nullable=False)
    # "manual" | "auto-confirmed" | "auto-silent" — entrega 1 solo usa "manual".
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="manual"
    )
    # "high" | "medium" | "low" — la usa la captura híbrida (entrega 2).
    confidence: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="high"
    )
    # Para staleness: prioridad de inyección y recordatorios de revisión.
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="memory_items")

    def __repr__(self) -> str:
        return f"<WorkspaceMemory ws={self.workspace_id} {self.key!r}={self.value!r}>"


class UserProfileGlobal(Base):
    __tablename__ = "user_profile_global"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_profile_global_user_key"),
    )

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
        index=True,
    )
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="manual"
    )
    confidence: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="high"
    )
    # Orden de visualización en el sidebar de "Mi perfil" (drag&drop futuro).
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile_global_items")

    def __repr__(self) -> str:
        return f"<UserProfileGlobal user={self.user_id} {self.key!r}={self.value!r}>"


# Avoid circular imports at type-check time
from models.conversation import Conversation  # noqa: E402
from models.user import User  # noqa: E402
