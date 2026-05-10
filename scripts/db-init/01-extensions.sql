-- ─────────────────────────────────────────────────────────────────
-- Bootstrap del Postgres LOCAL (solo dev — no usar este SQL en prod).
--
-- En Supabase, varias cosas vienen pre-creadas: extensiones
-- pgcrypto/uuid-ossp/citext, y el schema `auth` con tablas como
-- `auth.users`. Algunas migraciones del proyecto referencian
-- `auth.users`. Para que Alembic corra contra un Postgres vainilla,
-- creamos los stubs necesarios ANTES de las migraciones.
-- ─────────────────────────────────────────────────────────────────

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "citext";    -- email case-insensitive

-- Schema y tablas stub que imitan a Supabase Auth.
-- Quedan vacías; las migraciones que hacen UPDATE … FROM auth.users
-- simplemente no actualizan filas (lo cual es correcto en una DB
-- recién inicializada sin usuarios).
CREATE SCHEMA IF NOT EXISTS auth;

CREATE TABLE IF NOT EXISTS auth.users (
    id              UUID PRIMARY KEY,
    email           VARCHAR(255),
    raw_user_meta_data JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Permisos amplios para el usuario de la app local.
GRANT USAGE ON SCHEMA auth TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO PUBLIC;
