-- Catch-up migrations: aligns local Supabase DB with backend models (0004..0010).
-- Idempotent — safe to re-run.

-- 0004: conversations.section
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS section VARCHAR(50) NOT NULL DEFAULT 'general';
CREATE INDEX IF NOT EXISTS ix_conversations_section ON conversations(section);

-- 0005: profiles.password_hash
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS password_hash VARCHAR;

-- 0007: projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL DEFAULT 'Mi Proyecto',
    estado VARCHAR(20) NOT NULL DEFAULT 'amarillo',
    estado_texto VARCHAR(255) NOT NULL DEFAULT 'Proyecto en curso',
    presupuesto_base NUMERIC(14, 2) NOT NULL DEFAULT 0,
    costo_real NUMERIC(14, 2) NOT NULL DEFAULT 0,
    avance_real_pct DOUBLE PRECISION NOT NULL DEFAULT 0,
    avance_plan_pct DOUBLE PRECISION NOT NULL DEFAULT 0,
    meses_transcurridos INTEGER NOT NULL DEFAULT 0,
    meses_total INTEGER NOT NULL DEFAULT 0,
    fecha_inicio DATE,
    fecha_entrega_programada DATE,
    fecha_entrega_estimada DATE,
    costos_rubros JSONB NOT NULL DEFAULT '[]'::jsonb,
    alertas JSONB NOT NULL DEFAULT '[]'::jsonb,
    notas TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);

-- 0008: profiles.stripe_customer_id
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

-- 0009: profiles.onboarding_completed
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT false;

-- Stamp alembic version to head (0010)
UPDATE alembic_version SET version_num = '0010_add_ingest_tables';
