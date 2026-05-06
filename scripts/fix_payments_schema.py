"""Idempotent payments schema repair."""
import asyncio
import asyncpg

DB_URL = (
    "postgresql://postgres.uaiiqjouxlcvleiimokz:lHy3HqVyI77Doy3E"
    "@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
)

# Map of "if this English column exists, rename to this Spanish one"
RENAMES = {
    "concept":  "concepto",
    "provider": "proveedor",
    "amount":   "monto",
    "paid_at":  "fecha",
    "notes":    "notas",
}

DROPS = ["currency", "source"]


async def main():
    c = await asyncpg.connect(DB_URL)
    try:
        cols = {
            r["column_name"]: r["is_nullable"]
            for r in await c.fetch(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name='payments'"
            )
        }
        print("before:", sorted(cols.keys()))

        for old, new in RENAMES.items():
            if old in cols and new not in cols:
                await c.execute(f"ALTER TABLE payments RENAME COLUMN {old} TO {new}")
                print(f"renamed {old} -> {new}")

        for col in DROPS:
            if col in cols:
                await c.execute(f"ALTER TABLE payments DROP COLUMN {col}")
                print(f"dropped {col}")

        # Make sure required columns exist with correct types/nullability
        await c.execute(
            "ALTER TABLE payments "
            "ADD COLUMN IF NOT EXISTS estado VARCHAR(20) NOT NULL DEFAULT 'pendiente'"
        )
        await c.execute(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS categoria VARCHAR(100)"
        )
        await c.execute(
            "ALTER TABLE payments "
            "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
        )

        # Force types (TEXT) and NOT NULL on key columns where appropriate
        await c.execute("ALTER TABLE payments ALTER COLUMN concepto TYPE TEXT")
        await c.execute("ALTER TABLE payments ALTER COLUMN concepto SET NOT NULL")
        await c.execute("ALTER TABLE payments ALTER COLUMN fecha SET NOT NULL")
        await c.execute("ALTER TABLE payments ALTER COLUMN notas TYPE TEXT")

        cols2 = sorted(
            r["column_name"]
            for r in await c.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name='payments'"
            )
        )
        print("after:", cols2)
    finally:
        await c.close()


asyncio.run(main())
