"""Apply password_resets migration to Supabase via the pooler (6543)."""
import asyncio
import asyncpg

# Pooler transaction mode (6543) needs statement_cache_size=0.
DB = (
    "postgresql://postgres.uaiiqjouxlcvleiimokz:lHy3HqVyI77Doy3E"
    "@aws-1-us-east-1.pooler.supabase.com:6543/postgres"
)


async def main():
    c = await asyncpg.connect(DB, statement_cache_size=0)
    try:
        sql = open("/tmp/pr.sql", encoding="utf-8").read()
        # asyncpg.execute on a multi-statement string works in simple mode.
        await c.execute(sql)
        exists = await c.fetchval(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='password_resets'"
        )
        print("password_resets exists:", bool(exists))
        # Stamp Alembic at 0014 (all migrations applied via SQL).
        await c.execute(
            "UPDATE alembic_version SET version_num='0014_add_password_resets'"
        )
        v = await c.fetchval("SELECT version_num FROM alembic_version")
        print("alembic_version:", v)
        se = await c.fetchval(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='stripe_events'"
        )
        print("stripe_events exists:", bool(se))
    finally:
        await c.close()


asyncio.run(main())
