"""Add credits catalog + review pipeline (Fase 2)

Mueve el catálogo de créditos del JSON estático a la DB para que el pipeline de
actualización persista:
  - credits: catálogo publicable (sembrado desde data/creditos/creditos.json).
  - credit_proposals: cola de validación humana (pending_review → approved/rejected).
  - credit_change_log: historial inmutable de cambios aplicados (auditoría).

Aditivo: no toca tablas existentes. El seed lo hace el route on-demand (tabla
vacía → carga el JSON), no la migración, para no acoplar el deploy al archivo.

Revision ID: 0018_add_credits_pipeline
Revises: 0017_add_trial_and_paid_model
Create Date: 2026-06-23
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_add_credits_pipeline"
down_revision: str | None = "0017_add_trial_and_paid_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMPTY_JSONB = sa.text("'[]'::jsonb")


def upgrade() -> None:
    op.create_table(
        "credits",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("country", sa.String(60), nullable=False, server_default="Argentina"),
        sa.Column("province", sa.String(60), nullable=False, server_default="Nacional"),
        sa.Column("bank_name", sa.String(120), nullable=False),
        sa.Column("bank_emoji", sa.String(8), nullable=False, server_default="🏦"),
        sa.Column("credit_name", sa.String(160), nullable=False),
        sa.Column("audience", sa.String(20), nullable=False, server_default="comprador"),
        sa.Column("credit_type", sa.String(30), nullable=False, server_default="compra"),
        sa.Column("rate_type", sa.String(12), nullable=False, server_default="UVA"),
        sa.Column("interest_rate_tna", sa.Float, nullable=True),
        sa.Column("interest_rate_note", sa.Text, nullable=False, server_default=""),
        sa.Column("max_term_years", sa.Integer, nullable=False, server_default="20"),
        sa.Column("max_financing_percent", sa.Float, nullable=False, server_default="75"),
        sa.Column("min_income_ars", sa.Float, nullable=False, server_default="0"),
        sa.Column("min_employment_seniority_months", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_age", sa.Integer, nullable=True),
        sa.Column("property_value_limit_ars", sa.Float, nullable=True),
        sa.Column("relacion_cuota_ingreso_max", sa.Float, nullable=True, server_default="25"),
        sa.Column("required_savings_note", sa.Text, nullable=False, server_default=""),
        sa.Column("requirements", postgresql.JSONB, nullable=False, server_default=_EMPTY_JSONB),
        sa.Column("documents", postgresql.JSONB, nullable=False, server_default=_EMPTY_JSONB),
        sa.Column("pros", postgresql.JSONB, nullable=False, server_default=_EMPTY_JSONB),
        sa.Column("cons", postgresql.JSONB, nullable=False, server_default=_EMPTY_JSONB),
        sa.Column("extra_costs", postgresql.JSONB, nullable=False, server_default=_EMPTY_JSONB),
        sa.Column("official_url", sa.Text, nullable=False, server_default=""),
        sa.Column("source_urls", postgresql.JSONB, nullable=False, server_default=_EMPTY_JSONB),
        sa.Column("last_checked_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("last_updated_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="approved"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credits_validation_status", "credits", ["validation_status"])
    op.create_index("ix_credits_status", "credits", ["status"])

    op.create_table(
        "credit_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("credit_id", sa.String(80), sa.ForeignKey("credits.id", ondelete="CASCADE"), nullable=True),
        sa.Column("change_type", sa.String(20), nullable=False, server_default="field_update"),
        sa.Column("field", sa.String(60), nullable=False, server_default=""),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("proposed_payload", postgresql.JSONB, nullable=True),
        sa.Column("source_url", sa.Text, nullable=False, server_default=""),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending_review"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text, nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_proposals_credit_id", "credit_proposals", ["credit_id"])
    op.create_index("ix_credit_proposals_status", "credit_proposals", ["status"])

    op.create_table(
        "credit_change_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("credit_id", sa.String(80), nullable=False),
        sa.Column("field", sa.String(60), nullable=False, server_default=""),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("source", sa.Text, nullable=False, server_default=""),
        sa.Column("change_type", sa.String(20), nullable=False, server_default="manual_edit"),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_change_log_credit_id", "credit_change_log", ["credit_id"])


def downgrade() -> None:
    op.drop_index("ix_credit_change_log_credit_id", table_name="credit_change_log")
    op.drop_table("credit_change_log")
    op.drop_index("ix_credit_proposals_status", table_name="credit_proposals")
    op.drop_index("ix_credit_proposals_credit_id", table_name="credit_proposals")
    op.drop_table("credit_proposals")
    op.drop_index("ix_credits_status", table_name="credits")
    op.drop_index("ix_credits_validation_status", table_name="credits")
    op.drop_table("credits")
