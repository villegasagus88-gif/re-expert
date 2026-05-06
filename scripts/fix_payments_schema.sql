-- Align payments table with the SQLAlchemy Payment model (Spanish names).
-- Idempotent — safe to re-run.

-- Rename English -> Spanish columns
ALTER TABLE payments RENAME COLUMN concept   TO concepto;
ALTER TABLE payments RENAME COLUMN provider  TO proveedor;
ALTER TABLE payments RENAME COLUMN amount    TO monto;
ALTER TABLE payments RENAME COLUMN paid_at   TO fecha;
ALTER TABLE payments RENAME COLUMN notes     TO notas;

-- Drop columns the model does not use
ALTER TABLE payments DROP COLUMN IF EXISTS currency;
ALTER TABLE payments DROP COLUMN IF EXISTS source;

-- Add columns the model expects
ALTER TABLE payments
    ALTER COLUMN concepto SET NOT NULL,
    ALTER COLUMN concepto TYPE TEXT;
ALTER TABLE payments
    ALTER COLUMN fecha SET NOT NULL;
ALTER TABLE payments
    ALTER COLUMN notas TYPE TEXT;
ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    ADD COLUMN IF NOT EXISTS categoria VARCHAR(100),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
