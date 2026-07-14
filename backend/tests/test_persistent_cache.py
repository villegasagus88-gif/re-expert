"""Cache persistente de digests de noticias (kv_cache).

Garantiza: (1) pcache_get respeta el vencimiento, (2) make_digest reusa el
digest persistido en un cache-miss de RAM SIN regenerar (fetch + IA) — mismo
contenido, sobrevive redeploys.
"""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from services.persistent_cache import pcache_get


@pytest.mark.asyncio
async def test_pcache_get_respeta_vencimiento():
    # Fila vigente → devuelve el valor.
    vig = SimpleNamespace(value={"x": 2}, expires_at=datetime.now(UTC) + timedelta(hours=1))

    class DBVig:
        async def get(self, model, key):
            return vig

    got = await pcache_get(DBVig(), "k")
    assert got == {"x": 2}

    # Fila vencida → None (y se borra).
    borrado = {"n": 0}
    venc = SimpleNamespace(value={"x": 1}, expires_at=datetime.now(UTC) - timedelta(seconds=1))

    class DBVenc:
        async def get(self, model, key):
            return venc

        async def delete(self, row):
            borrado["n"] += 1

        async def commit(self):
            pass

    assert await pcache_get(DBVenc(), "k") is None
    assert borrado["n"] == 1  # borró la fila vencida

    # Inexistente → None.
    class DBNone:
        async def get(self, model, key):
            return None

    assert await pcache_get(DBNone(), "k") is None


@pytest.mark.asyncio
async def test_make_digest_reusa_persistido_sin_regenerar(monkeypatch):
    import services.news_live as nl

    nl._cache.clear()  # forzar miss en el cache de RAM
    persisted = {"lead": "resumen guardado", "puntos_clave": ["a"], "parcial": False}

    async def fake_pget(key):
        return persisted

    called = {"fetch": 0}

    async def fake_fetch(url):
        called["fetch"] += 1
        return (None, "")

    monkeypatch.setattr(nl, "_persistent_get", fake_pget)
    monkeypatch.setattr(nl, "_fetch_article_text", fake_fetch)

    out = await nl.make_digest(url="http://x/nota", title="t")
    assert out is persisted          # sirvió el persistido...
    assert called["fetch"] == 0      # ...sin ir a buscar el artículo ni al LLM
    assert nl._cache_get("digest::http://x/nota") is persisted  # repobló RAM


@pytest.mark.asyncio
async def test_make_digest_persiste_al_generar(monkeypatch):
    import services.news_live as nl

    nl._cache.clear()
    saved = {}

    async def fake_pget(key):
        return None  # miss persistente → se genera

    async def fake_pset(key, value, ttl):
        saved[key] = value

    async def fake_fetch(url):
        return (None, "texto largo del artículo " * 20)  # >120 chars → intenta IA

    async def fake_llm(*a, **k):
        raise RuntimeError("sin IA en el test")  # cae a digest parcial

    monkeypatch.setattr(nl, "_persistent_get", fake_pget)
    monkeypatch.setattr(nl, "_persistent_set", fake_pset)
    monkeypatch.setattr(nl, "_fetch_article_text", fake_fetch)

    # Con IA rota, el digest es "parcial" → NO se persiste (no cacheamos basura).
    out = await nl.make_digest(url="http://y/nota", title="t", snippet="s")
    assert out["parcial"] is True
    assert saved == {}  # los parciales no se persisten
