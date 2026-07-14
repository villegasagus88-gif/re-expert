"""Helpers del cache KV persistente (tabla kv_cache).

Best-effort: acelera caches que hoy viven en RAM y mueren en cada redeploy. NO
es fuente de verdad — el caller siempre debe poder regenerar el valor si esto
devuelve None o falla.
"""
from datetime import UTC, datetime, timedelta
from typing import Any

from models.kv_cache import KVCache
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession


async def pcache_get(db: AsyncSession, key: str) -> Any | None:
    """Devuelve el valor si existe y NO está vencido; si venció, lo borra y
    devuelve None (miss)."""
    row = await db.get(KVCache, key)
    if row is None:
        return None
    if row.expires_at <= datetime.now(UTC):
        await db.delete(row)
        await db.commit()
        return None
    return row.value


async def pcache_set(db: AsyncSession, key: str, value: Any, ttl_seconds: int) -> None:
    """Upsert del valor con vencimiento now()+ttl (ON CONFLICT DO UPDATE)."""
    expires = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
    stmt = pg_insert(KVCache).values(key=key, value=value, expires_at=expires)
    stmt = stmt.on_conflict_do_update(
        index_elements=["key"],
        set_={"value": value, "expires_at": expires},
    )
    await db.execute(stmt)
    await db.commit()
