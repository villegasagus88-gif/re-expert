"""Tests del KnowledgeBaseService: parseo, búsqueda, caché TTL."""
from __future__ import annotations

import time

import pytest
from services.knowledge_base_service import (
    KnowledgeBaseService,
    _tokenize,
    build_document,
    parse_csv,
    parse_md,
    score_document,
)

SAMPLE_MD = """\
# Costos de obra CABA

El costo promedio por m2 para vivienda multifamiliar en CABA durante 2025
ronda los USD 1200. Incluye estructura, mampostería y terminaciones medias.
"""

SAMPLE_CSV = """\
rubro,porcentaje,notas
Estructura,25,incluye hormigón y acero
Mamposteria,15,ladrillo hueco
Instalaciones,20,sanitario electrico gas
Terminaciones,40,pisos pintura aberturas
"""


# ---------- Parsing ----------

def test_parse_md_preserves_text():
    out = parse_md(SAMPLE_MD)
    assert "Costos de obra CABA" in out
    assert "USD 1200" in out


def test_parse_csv_includes_header_and_rows():
    out = parse_csv(SAMPLE_CSV)
    assert "Columnas: rubro, porcentaje, notas" in out
    assert "rubro: Estructura" in out
    assert "porcentaje: 25" in out
    assert "rubro: Terminaciones" in out


def test_parse_csv_empty_returns_empty():
    assert parse_csv("") == ""


def test_build_document_md():
    doc = build_document("costos/caba.md", SAMPLE_MD)
    assert doc is not None
    assert doc.doc_type == "md"
    assert doc.domain == "costos"
    assert doc.name == "caba.md"
    assert "caba" in doc.tokens
    assert "multifamiliar" in doc.tokens


def test_build_document_csv():
    doc = build_document("rubros/desglose.csv", SAMPLE_CSV)
    assert doc is not None
    assert doc.doc_type == "csv"
    assert doc.domain == "rubros"
    assert "estructura" in doc.tokens


def test_build_document_unsupported_extension():
    assert build_document("whatever.pdf", "ignored") is None


def test_build_document_root_no_domain():
    doc = build_document("top-level.md", "# hi")
    assert doc is not None
    assert doc.domain == ""


# ---------- Tokenize ----------

def test_tokenize_strips_accents_and_stopwords():
    toks = _tokenize("El costo del hormigón en CABA es alto")
    assert "hormigon" in toks  # acento removido
    assert "caba" in toks
    assert "el" not in toks    # stopword
    assert "es" not in toks    # stopword


# ---------- Scoring ----------

def test_score_document_counts_query_overlap():
    doc = build_document("costos/caba.md", SAMPLE_MD)
    assert doc is not None
    q = set(_tokenize("costo de construccion multifamiliar caba"))
    assert score_document(doc, q) >= 2


def test_score_document_empty_query_is_zero():
    doc = build_document("costos/caba.md", SAMPLE_MD)
    assert doc is not None
    assert score_document(doc, set()) == 0


# ---------- Caché TTL ----------

@pytest.mark.asyncio
async def test_cache_ttl_honored(monkeypatch):
    calls = {"n": 0}

    async def fake_list(folder: str = ""):
        calls["n"] += 1
        return [{"name": "x.md", "path": "x.md"}]

    async def fake_get(path: str):
        return "# Hola\n\nContenido de prueba"

    import services.knowledge_base_service as kb_mod
    monkeypatch.setattr(kb_mod.knowledge_storage, "list_files", fake_list)
    monkeypatch.setattr(kb_mod.knowledge_storage, "get_text_content", fake_get)

    svc = KnowledgeBaseService(ttl_seconds=60)
    await svc.load_all()
    await svc.load_all()
    # Second call hits cache.
    assert calls["n"] == 1

    # Force: refetch.
    await svc.load_all(force=True)
    assert calls["n"] == 2

    # Expire TTL manually.
    svc._cache.loaded_at = time.time() - 120
    await svc.load_all()
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_search_ranks_by_overlap(monkeypatch):
    docs_data = [
        ("costos/caba.md", SAMPLE_MD),
        ("rubros/desglose.csv", SAMPLE_CSV),
        ("otros/random.md", "# Otro\n\nTexto sin relacion a nada util"),
    ]

    async def fake_list(folder: str = ""):
        return [{"name": p.rsplit("/", 1)[-1], "path": p} for p, _ in docs_data]

    async def fake_get(path: str):
        return dict(docs_data)[path]

    import services.knowledge_base_service as kb_mod
    monkeypatch.setattr(kb_mod.knowledge_storage, "list_files", fake_list)
    monkeypatch.setattr(kb_mod.knowledge_storage, "get_text_content", fake_get)

    svc = KnowledgeBaseService(ttl_seconds=60)
    hits = await svc.search("costo multifamiliar caba")
    assert hits, "esperaba al menos un match"
    # El MD de costos debería ganar
    assert hits[0][0].path == "costos/caba.md"


@pytest.mark.asyncio
async def test_get_context_filters_by_domain(monkeypatch):
    docs_data = [
        ("costos/caba.md", SAMPLE_MD),
        ("rubros/desglose.csv", SAMPLE_CSV),
    ]

    async def fake_list(folder: str = ""):
        return [{"name": p.rsplit("/", 1)[-1], "path": p} for p, _ in docs_data]

    async def fake_get(path: str):
        return dict(docs_data)[path]

    import services.knowledge_base_service as kb_mod
    monkeypatch.setattr(kb_mod.knowledge_storage, "list_files", fake_list)
    monkeypatch.setattr(kb_mod.knowledge_storage, "get_text_content", fake_get)

    svc = KnowledgeBaseService(ttl_seconds=60)
    ctx = await svc.get_context("estructura", domain="rubros")
    assert "Estructura" in ctx
    assert "Costos de obra CABA" not in ctx  # distinto dominio


@pytest.mark.asyncio
async def test_get_context_truncates_at_max_chars(monkeypatch):
    big = "lorem ipsum " * 1000
    async def fake_list(folder: str = ""):
        return [{"name": "big.md", "path": "big.md"}]
    async def fake_get(path: str):
        return big

    import services.knowledge_base_service as kb_mod
    monkeypatch.setattr(kb_mod.knowledge_storage, "list_files", fake_list)
    monkeypatch.setattr(kb_mod.knowledge_storage, "get_text_content", fake_get)

    svc = KnowledgeBaseService(ttl_seconds=60)
    ctx = await svc.get_context("lorem", max_chars=500)
    assert len(ctx) <= 500
