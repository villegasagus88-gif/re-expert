"""
User model - maps to the public.profiles table.

Note: Supabase manages authentication in auth.users (passwords, tokens).
Our app-level User data lives in public.profiles which references auth.users
via the id column. Email is mirrored here for convenience (queries, display).
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from models.base import Base
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), default="user", server_default="user", nullable=False
    )
    # Modelo pago-only: "trial" (evaluación) | "pro" (paga) | "inactive" (sin acceso).
    plan: Mapped[str] = mapped_column(
        String(20), default="trial", server_default="trial", nullable=False
    )
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Fin del trial de evaluación. NULL para usuarios "pro" o "inactive".
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    # Bump cada vez que queremos invalidar todos los JWTs del usuario
    # (password reset, logout global, etc). El claim `tv` del JWT debe
    # coincidir con este valor para que el token sea aceptado.
    token_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # Teléfono del usuario en formato internacional (lo pide SOL en onboarding).
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # ── Cuenta / seguridad (migración 0037) ──────────────────────────────────
    # 2FA: 'totp' (app authenticator) | 'email' | NULL (desactivado).
    twofa_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    twofa_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    # Secret generado pero todavía no confirmado con un primer código válido.
    twofa_pending_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    # Códigos de recuperación de un solo uso, HASHEADOS (sha256 hex).
    twofa_recovery: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Código de un solo uso del método email (login / activación), hasheado.
    twofa_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    twofa_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Intentos fallidos contra el código vigente (throttling POR CUENTA: el rate
    # limit por IP no frena un ataque distribuido).
    twofa_code_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # Cambio de email en dos pasos: el código viaja al correo NUEVO.
    pending_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pending_email_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pending_email_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Baja con gracia: si está seteado, la cuenta espera purga (30 días).
    # El login exitoso lo limpia (cancela la baja).
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # ── Facturación (migración 0038) ─────────────────────────────────────────
    # Próximo cobro de la suscripción, según lo informa Mercado Pago. Se usa
    # para avisar ANTES de renovar, que es lo que prometen los Términos.
    next_charge_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Para qué fecha ya se mandó el aviso: evita repetirlo en cada corrida del
    # scheduler.
    charge_notice_sent_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Importe del próximo cobro, como lo informa MP. Los Términos prometen
    # avisar el importe además de la fecha.
    next_charge_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    # Preferencias de automatización que SOL aprende: qué avisar, por qué canal, etc.
    automation_prefs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    # Capa 1B — Workspaces ("Proyectos" en la UI) y memoria persistente.
    workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    profile_global_items: Mapped[list["UserProfileGlobal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} plan={self.plan}>"


# Avoid circular imports at type-check time
from models.conversation import Conversation  # noqa: E402
from models.payment import Payment  # noqa: E402
from models.project import Project  # noqa: E402
from models.workspace import UserProfileGlobal, Workspace  # noqa: E402
