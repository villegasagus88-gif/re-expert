"""Tests del context router: clasificación + selección de contexto."""
from __future__ import annotations

import pytest
from services.context_router import (
    ALL_DOMAINS,
    CHARS_PER_TOKEN,
    DOMAIN_KEYWORDS,
    DOMAIN_TO_FOLDER,
    MAX_CONTEXT_CHARS,
    MAX_CONTEXT_TOKENS,
    META_BUDGET_CHARS,
    classify_query,
    classify_query_multi,
    estimate_tokens,
    select_context_for_message,
)

# ---------- classify_query ----------

@pytest.mark.parametrize(
    "msg, expected",
    [
        ("¿Cuánto sale el m2 de construcción en CABA?", "costos"),
        ("Cuál es el precio del acero y del hormigón?", "arquitectura"),
        ("Qué ordenanza regula la zonificación en Palermo?", "normativa"),
        ("Qué tasa de interés ofrece el crédito hipotecario UVA?", "financiero"),
        ("Cómo armo el waterfall de inversores?", "financiero"),
        ("Qué dice la Ley 27551 de alquileres?", "normativa"),
        ("Cuánto cobra IVA AFIP en obra inmueble propio?", "impuestos"),
        ("Cómo funciona el Distrito Tecnológico CABA?", "estrategia"),
        ("Hola, ¿cómo estás?", "general"),
        ("", "general"),
    ],
)
def test_classify_query_typical(msg, expected):
    assert classify_query(msg) == expected


def test_classify_query_meta_never_selected_as_primary():
    # 'meta' no tiene keywords propias y debería caer en 'general'.
    msg = "indice glosario fuentes"  # palabras que podrían sonar a meta
    result = classify_query(msg)
    assert result != "meta"


def test_classify_query_multi_returns_multiple_domains():
    # Pregunta cross-tema: fideicomiso (impuestos) + pricing (comercial)
    msg = "Cómo estructurar un fideicomiso al costo con pricing pozo y preventa"
    domains = classify_query_multi(msg, top_n=3)
    assert len(domains) > 0
    assert "impuestos" in domains or "comercial" in domains


def test_classify_query_multi_empty_message():
    assert classify_query_multi("") == []


# ---------- multi-word keyword matching ----------

@pytest.mark.parametrize(
    "msg, expected",
    [
        # "cap rate" es keyword multi-word de mercado: antes no matcheaba
        # porque el tokenizer la partía. Debe matchear como substring.
        ("Cap rate promedio multifamiliar en Palermo", "mercado"),
        # "net zero" + "embodied carbon" — triple-impacto
        ("Net zero embodied carbon en obra nueva", "triple-impacto"),
        # "distrito tecnologico" — estrategia (vs general)
        ("Distrito Tecnológico CABA: qué beneficios da", "estrategia"),
        # "customer journey" — comercial (vs general)
        ("Customer journey postcompra: qué incluye", "comercial"),
    ],
)
def test_classify_query_handles_multi_word_keywords(msg, expected):
    assert classify_query(msg) == expected


def test_all_domains_have_keywords_except_meta_and_general():
    for d in ALL_DOMAINS:
        if d in ("general", "meta"):
            assert DOMAIN_KEYWORDS[d] == frozenset()
        else:
            assert len(DOMAIN_KEYWORDS[d]) > 0, f"dominio {d} sin keywords"


def test_all_domains_map_to_folder():
    for d in ALL_DOMAINS:
        assert d in DOMAIN_TO_FOLDER


# ---------- token budget ----------

def test_max_context_chars_matches_max_tokens():
    assert MAX_CONTEXT_CHARS == MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN


def test_meta_budget_is_subset_of_total():
    assert META_BUDGET_CHARS < MAX_CONTEXT_CHARS


def test_estimate_tokens_scales_with_length():
    assert estimate_tokens("a" * 400) == 100
    assert estimate_tokens("") == 0


# ---------- select_context_for_message ----------

@pytest.mark.asyncio
async def test_select_context_includes_meta_baseline(monkeypatch):
    calls: list[dict] = []

    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        calls.append({"query": query, "domain": domain, "max_chars": max_chars})
        if domain == "_meta":
            return "META_BASELINE"
        return "DYNAMIC_CTX"

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    domain, ctx = await select_context_for_message("Cuánto cuesta el m2 en CABA")
    assert domain == "costos"
    # Debe haberse llamado al menos una vez con domain='_meta' (baseline obligatorio).
    assert any(c["domain"] == "_meta" for c in calls)
    # Y debe haberse llamado para la carpeta de costos (14-costos-presupuesto).
    assert any(c["domain"] == "14-costos-presupuesto" for c in calls)
    assert "META_BASELINE" in ctx
    assert "DYNAMIC_CTX" in ctx


@pytest.mark.asyncio
async def test_select_context_general_passes_none_domain_for_dynamic(monkeypatch):
    calls: list[dict] = []

    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        calls.append({"domain": domain})
        return "ctx"

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    domain, _ = await select_context_for_message("hola che qué onda")
    assert domain == "general"
    # Meta siempre se intenta cargar.
    assert any(c["domain"] == "_meta" for c in calls)
    # Para dynamic, al no haber match de keywords, pasamos domain=None (cross-bucket).
    assert any(c["domain"] is None for c in calls)


@pytest.mark.asyncio
async def test_select_context_truncates_oversized_kb_output(monkeypatch):
    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        # devolvemos más chars de los permitidos para probar el safety-net
        return "x" * (max_chars + 500)

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    _, ctx = await select_context_for_message("costo m2")
    assert len(ctx) <= MAX_CONTEXT_CHARS


@pytest.mark.asyncio
async def test_select_context_swallows_kb_errors(monkeypatch):
    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        raise RuntimeError("kb down")

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    domain, ctx = await select_context_for_message("costo m2")
    assert domain == "costos"
    # Si todo el KB falla, devolvemos string vacío (sin romper).
    assert ctx == ""


@pytest.mark.asyncio
async def test_select_context_meta_works_even_if_dynamic_fails(monkeypatch):
    """Si la carga dinámica falla pero meta funciona, devolvemos meta."""
    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        if domain == "_meta":
            return "META_OK"
        raise RuntimeError("dyn down")

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    _, ctx = await select_context_for_message("costo m2")
    assert "META_OK" in ctx
