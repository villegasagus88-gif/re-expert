"""Tests del context router: clasificación + selección de contexto."""
from __future__ import annotations

import pytest
from services.context_router import (
    ALL_DOMAINS,
    DOMAIN_KEYWORDS,
    MAX_CONTEXT_CHARS,
    MAX_CONTEXT_TOKENS,
    classify_query,
    estimate_tokens,
    select_context_for_message,
)

# ---------- classify_query ----------

@pytest.mark.parametrize(
    "msg, expected",
    [
        ("¿Cuánto sale el m2 de construcción en CABA?", "costos"),
        ("Cuál es el precio del acero y del hormigón?", "materiales"),
        ("Qué ordenanza regula la zonificación en Palermo?", "normativa"),
        ("Qué tasa de interés ofrece el crédito hipotecario UVA?", "financiero"),
        ("Cuánto dura la etapa de fundaciones en una obra?", "proyecto"),
        ("Hola, ¿cómo estás?", "general"),
        ("", "general"),
    ],
)
def test_classify_query_typical(msg, expected):
    assert classify_query(msg) == expected


def test_classify_query_returns_costos_over_materiales_when_more_costos_terms():
    # Hay 'hormigon' (materiales) pero también 'costo', 'precio', 'm2' (costos)
    msg = "¿Cuál es el costo y el precio por m2 del hormigón?"
    assert classify_query(msg) == "costos"


def test_classify_query_tie_goes_to_first_in_all_domains_order():
    # Si costos y materiales empatan, gana costos por orden en ALL_DOMAINS.
    msg = "costo del ladrillo"  # 'costo' → costos (1); 'ladrillo' → materiales (1)
    assert classify_query(msg) == "costos"


def test_all_domains_have_non_general_keywords():
    for d in ALL_DOMAINS:
        if d == "general":
            assert DOMAIN_KEYWORDS[d] == frozenset()
        else:
            assert len(DOMAIN_KEYWORDS[d]) > 0, f"dominio {d} sin keywords"


# ---------- token budget ----------

def test_max_context_chars_matches_max_tokens():
    assert MAX_CONTEXT_CHARS == MAX_CONTEXT_TOKENS * 4


def test_estimate_tokens_scales_with_length():
    assert estimate_tokens("a" * 400) == 100
    assert estimate_tokens("") == 0


# ---------- select_context_for_message ----------

@pytest.mark.asyncio
async def test_select_context_uses_domain_filter(monkeypatch):
    captured = {}

    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        captured["query"] = query
        captured["domain"] = domain
        captured["max_chars"] = max_chars
        return "fake context"

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    domain, ctx = await select_context_for_message("Cuánto cuesta el m2 en CABA")
    assert domain == "costos"
    assert captured["domain"] == "costos"
    assert captured["max_chars"] == MAX_CONTEXT_CHARS
    assert ctx == "fake context"


@pytest.mark.asyncio
async def test_select_context_general_passes_none_domain(monkeypatch):
    captured = {}

    async def fake_get_context(query, domain=None, max_chars=4000, top_k=5):
        captured["domain"] = domain
        return "ctx"

    import services.context_router as cr
    monkeypatch.setattr(cr.knowledge_base, "get_context", fake_get_context)

    domain, _ = await select_context_for_message("hola che qué onda")
    assert domain == "general"
    assert captured["domain"] is None  # búsqueda cross-bucket


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
    assert ctx == ""
