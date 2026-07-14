"""Stale-while-revalidate del feed de noticias (news_live).

Garantiza que la optimización sea de pura latencia: sirve el feed cacheado al
instante y refresca en background, pero NUNCA sirve algo más viejo que ~2× TTL
(más allá de eso recomputa sincrónico) — la frescura del contenido se mantiene.
"""
import time

import pytest

import services.news_live as nl


@pytest.mark.asyncio
async def test_feed_fresco_devuelve_sin_refrescar(monkeypatch):
    sched = []
    monkeypatch.setattr(nl, "_schedule_feed_refresh", lambda c: sched.append(c))
    fresh = [{"title": "x"}]
    nl._cache["ranked::economia"] = (time.time() + 300, fresh)
    out = await nl._ranked_items("economia")
    assert out is fresh and sched == []  # fresco → sin refresh


@pytest.mark.asyncio
async def test_feed_stale_sirve_viejo_y_agenda_refresh(monkeypatch):
    sched = []
    monkeypatch.setattr(nl, "_schedule_feed_refresh", lambda c: sched.append(c))
    stale = [{"title": "vieja"}]
    # Vencido hace 60s, dentro de la ventana SWR (≤ _FEED_TTL extra).
    nl._cache["ranked::economia"] = (time.time() - 60, stale)
    out = await nl._ranked_items("economia")
    assert out is stale            # sirve el viejo AL INSTANTE
    assert sched == ["economia"]   # y agenda el refresh en background


@pytest.mark.asyncio
async def test_feed_muy_viejo_recomputa_no_sirve_stale(monkeypatch):
    sched = []
    monkeypatch.setattr(nl, "_schedule_feed_refresh", lambda c: sched.append(c))
    called = {"rss": 0}

    async def fake_rss(refresh=False):
        called["rss"] += 1
        return []

    monkeypatch.setattr(nl, "_fetch_all_rss", fake_rss)
    stale = [{"title": "muy vieja"}]
    # Vencido hace más de 2× TTL → NO se sirve viejo: recomputa sincrónico (fresco).
    nl._cache["ranked::economia"] = (time.time() - (nl._FEED_TTL + 10), stale)
    out = await nl._ranked_items("economia")
    assert called["rss"] == 1  # recomputó
    assert sched == []         # no hubo SWR
    assert out is not stale    # no devolvió el viejo
