"""
Modelos del sistema de Análisis de Planos (panel inteligente por proyecto).

Jerarquía:
  PlanProject  → proyecto de revisión de planos (independiente de los proyectos
                 del Panel de Proyecto: acá el objeto es la documentación).
  PlanFile     → cada plano subido (PDF/imagen, bytes en Postgres) + clasificación
                 IA editable + versionado (previous_version_id / is_current_version).
  PlanAnalysis → un análisis IA ejecutado sobre un plano (o comparación entre dos):
                 resumen, riesgo general, plan score, checklist, preguntas, etc.
  PlanAlert    → observación accionable (prioridad, estado, pin sobre el plano).
  PlanTask     → tarea creada desde una observación (o manual).

Los archivos se guardan como BYTEA en Postgres (v1): no tenemos permisos para
crear buckets en Supabase Storage desde acá, y el disco de Railway es efímero.
Límite de 15 MB por archivo en el endpoint de upload.
"""
from datetime import datetime
from uuid import UUID, uuid4

from models.base import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class PlanProject(Base):
    __tablename__ = "plan_projects"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    obra_type: Mapped[str] = mapped_column(String(40), nullable=False, server_default="otro")
    location: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    estimated_area: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    stage: Mapped[str] = mapped_column(String(40), nullable=False, server_default="anteproyecto")
    analysis_goal: Mapped[str] = mapped_column(String(60), nullable=False, server_default="entender")
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<PlanProject {self.name}>"


class PlanFile(Base):
    __tablename__ = "plan_files"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf | png | jpg | webp
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Clasificación (IA con edición manual)
    detected_plan_type: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    discipline: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    sheet_number: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    scale: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    plan_date: Mapped[str] = mapped_column(String(40), nullable=False, server_default="")
    floor_level: Mapped[str] = mapped_column(String(80), nullable=False, server_default="")
    classification: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    # Estado y versionado
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="cargado", index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    version_notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    is_current_version: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    previous_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_files.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<PlanFile {self.file_name} v{self.version}>"


class PlanAnalysis(Base):
    __tablename__ = "plan_analyses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(30), nullable=False, server_default="simple")
    profile: Mapped[str] = mapped_column(String(30), nullable=False, server_default="")
    # Para modo comparación: el segundo plano
    compare_plan_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_files.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    detected_data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    general_risk: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medio")
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")  # 0-100
    plan_score: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    strengths: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    missing_info: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    inconsistencies: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    suggested_questions: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    checklist: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<PlanAnalysis {self.mode} plan={self.plan_id}>"


class PlanAlert(Base):
    __tablename__ = "plan_alerts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    category: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    risk: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    impact: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="media", index=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    suggested_action: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pendiente", index=True)
    responsible: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    due_date: Mapped[str] = mapped_column(String(20), nullable=False, server_default="")
    # Pin visual sobre el plano (coordenadas relativas 0-100 sobre la página)
    pin_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pin_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    pin_page: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<PlanAlert [{self.priority}] {self.title[:40]}>"


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid()
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_files.id", ondelete="SET NULL"), nullable=True
    )
    alert_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plan_alerts.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="media")
    responsible: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pendiente", index=True)
    due_date: Mapped[str] = mapped_column(String(20), nullable=False, server_default="")
    comments: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<PlanTask [{self.status}] {self.title[:40]}>"
