-- Idempotent: crea la tabla password_resets para el flujo de recuperación
-- de contraseña. Equivalente al migration 0014_add_password_resets.py.
-- Aplicar en Supabase SQL Editor si Alembic no corre automáticamente.

CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_password_resets_user_id ON password_resets(user_id);
CREATE INDEX IF NOT EXISTS ix_password_resets_expires_at ON password_resets(expires_at);

-- Stamp Alembic if not already at 0014
-- (Skip if running fresh; uncomment if needed)
-- UPDATE alembic_version SET version_num = '0014_add_password_resets';
