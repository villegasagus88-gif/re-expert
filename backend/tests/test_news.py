"""Tests for the news service: parsing + pagination + sort."""
from datetime import date

import pytest
from api.schemas.news import NewsItem
from fastapi.testclient import TestClient
from main import app
from services import news_service

# --------------------------------------------------------------- HTTP --

def test_news_endpoint_requires_auth():
    client = TestClient(app)
    response = client.get("/api/news")
    assert response.status_code == 401


def test_news_endpoint_rejects_post():
    client = TestClient(app)
    response = client.post("/api/news")
    assert response.status_code == 405


# ----------------------------------------------- frontmatter parsing --

def test_build_item_with_full_frontmatter():
    text = """---
title: BCRA baja la tasa
date: 2026-04-25
summary: La decisión bla bla
category: macro
source: Ámbito
impact: Positivo
---

# Cuerpo
Algo más."""
    item = news_service._build_item("2026-04-25-bcra-tasa.md", text)
    assert item is not None
    assert item.title == "BCRA baja la tasa"
    assert item.date == date(2026, 4, 25)
    assert item.summary == "La decisión bla bla"
    assert item.category == "macro"
    assert item.source == "Ámbito"
    assert item.impact == "Positivo"
    assert item.slug == "2026-04-25-bcra-tasa"


def test_build_item_no_frontmatter_uses_filename_and_h1():
    text = """# Cemento subió 17%

El acumulado del trimestre marca presión sobre presupuestos."""
    item = news_service._build_item("2026-04-20-cemento.md", text)
    assert item is not None
    assert item.title == "Cemento subió 17%"
    assert item.date == date(2026, 4, 20)
    assert "presión sobre presupuestos" in item.summary


def test_build_item_no_frontmatter_no_h1_falls_back_to_slug():
    text = "Cuerpo plano sin headers."
    item = news_service._build_item("ventas-pozo-caba.md", text)
    assert item is not None
    assert item.title == "Ventas pozo caba"
    assert item.date is None


def test_build_item_skips_non_md_files():
    assert news_service._build_item("foo.pdf", "ignored") is None


def test_summary_truncates_long_paragraphs():
    long_para = "x " * 500
    text = f"---\ntitle: t\n---\n{long_para}"
    item = news_service._build_item("a.md", text)
    assert item is not None
    assert len(item.summary) <= news_service.SUMMARY_MAX_LEN
    assert item.summary.endswith("…")


# ----------------------------------------------------- list_news --

@pytest.mark.asyncio
async def test_list_news_sorts_desc_and_paginates(monkeypatch):
    items = [
        NewsItem(slug="a", title="A", date=date(2026, 4, 20), summary="", category="macro"),
        NewsItem(slug="b", title="B", date=date(2026, 4, 25), summary="", category="costos"),
        NewsItem(slug="c", title="C", date=None, summary="", category="macro"),
        NewsItem(slug="d", title="D", date=date(2026, 4, 22), summary="", category="macro"),
    ]

    async def fake_list_files(folder=""):
        return [{"name": f"{i.slug}.md", "path": f"noticias/{i.slug}.md"} for i in items]

    async def fake_get_text(path):
        slug = path.rsplit("/", 1)[-1][:-3]
        it = next(i for i in items if i.slug == slug)
        d = f"date: {it.date.isoformat()}\n" if it.date else ""
        return f"---\ntitle: {it.title}\n{d}category: {it.category}\n---\n"

    monkeypatch.setattr(news_service.knowledge_storage, "list_files", fake_list_files)
    monkeypatch.setattr(news_service.knowledge_storage, "get_text_content", fake_get_text)

    page1 = await news_service.list_news(page=1, per_page=2)
    assert page1.total == 4
    assert page1.has_more is True
    assert [i.slug for i in page1.items] == ["b", "d"]  # desc by date

    page2 = await news_service.list_news(page=2, per_page=2)
    assert [i.slug for i in page2.items] == ["a", "c"]  # c (no date) last
    assert page2.has_more is False


@pytest.mark.asyncio
async def test_list_news_filters_by_category(monkeypatch):
    items = [
        NewsItem(slug="a", title="A", date=date(2026, 4, 20), summary="", category="macro"),
        NewsItem(slug="b", title="B", date=date(2026, 4, 25), summary="", category="costos"),
    ]

    async def fake_list_files(folder=""):
        return [{"name": f"{i.slug}.md", "path": f"noticias/{i.slug}.md"} for i in items]

    async def fake_get_text(path):
        slug = path.rsplit("/", 1)[-1][:-3]
        it = next(i for i in items if i.slug == slug)
        return f"---\ntitle: {it.title}\ndate: {it.date.isoformat()}\ncategory: {it.category}\n---\n"

    monkeypatch.setattr(news_service.knowledge_storage, "list_files", fake_list_files)
    monkeypatch.setattr(news_service.knowledge_storage, "get_text_content", fake_get_text)

    res = await news_service.list_news(category="macro")
    assert res.total == 1
    assert res.items[0].slug == "a"
