"""Add email, plan, last_login to profiles table

Revision ID: 0002_add_user_fields
Revises: 0001_initial_schema
Create Date: 2026-04-16 22:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_user_fields"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email column (nullable first, then backfill, then set NOT NULL)
    op.add_column("profiles", sa.Column("email", sa.String(255), nullable=True))

    # Backfill email from auth.users for existing rows
    op.execute("""
        UPDATE public.profiles p
        SET email = u.email
        FROM auth.users u
        WHERE p.id = u.id
    """)

    # Now set NOT NULL + unique index
    op.alter_column("profiles", "email", nullable=False)
    op.create_index("ix_profiles_email", "profiles", ["email"], unique=True)

    # Add plan column
    op.add_column(
        "profiles",
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
    )

    # Add last_login column
    op.add_column(
        "profiles",
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    )

    # Update trigger to include email on new user signup
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO public.profiles (id, email, full_name)
            VALUES (
                NEW.id,
                NEW.email,
                NEW.raw_user_meta_data->>'full_name'
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)


def downgrade() -> None:
    # Restore original trigger (without email)
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO public.profiles (id, full_name)
            VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.drop_column("profiles", "last_login")
    op.drop_column("profiles", "plan")
    op.drop_index("ix_profiles_email", table_name="profiles")
    op.drop_column("profiles", "email")
