"""Tests para inyección de perfil global + memoria de workspace en el system prompt.

Capa 1B — Verifica que build_system_prompt arme los bloques de memoria con
formato esperado, respete los caps de chars, y los muestre tanto en chat
general como en SOL.
"""
import asyncio
from unittest.mock import AsyncMock, patch

from services.anthropic_service import (
    PROFILE_MEMORY_MAX_CHARS,
    WORKSPACE_MEMORY_MAX_CHARS,
    _format_memory_block,
    build_system_prompt,
)


def _stub_knowledge(monkey=None):
    """Stub load_knowledge_context para que no toque Supabase Storage en tests."""
    return patch(
        "services.anthropic_service.load_knowledge_context",
        new=AsyncMock(return_value=""),
    )


def _stub_router():
    """Stub del router para que devuelva "" y no requiera red."""
    async def _empty(_msg):
        return ""

    return patch("services.anthropic_service._load_routed_knowledge", new=_empty)


def test_format_block_empty_returns_empty():
    assert _format_memory_block("Título", [], 1000) == ""


def test_format_block_with_items():
    block = _format_memory_block(
        "Sobre el usuario",
        [("rol", "desarrollador"), ("zona", "Palermo")],
        1000,
    )
    assert block.startswith("## Sobre el usuario")
    assert "- **rol**: desarrollador" in block
    assert "- **zona**: Palermo" in block


def test_format_block_truncates_when_over_cap():
    items = [("key" + str(i), "valor que ocupa varios chars") for i in range(100)]
    block = _format_memory_block("Título", items, 200)
    assert "omitidos por límite" in block
    assert len(block) <= 260  # un poquito de margen por el sufijo


def test_chat_prompt_includes_profile_block():
    with _stub_knowledge(), _stub_router():
        prompt = asyncio.run(
            build_system_prompt(
                "chat",
                user_message="hola",
                profile_items=[("rol", "desarrollador"), ("zonas", "Palermo, Núñez")],
            )
        )
    assert "## Sobre el usuario (perfil)" in prompt
    assert "**rol**: desarrollador" in prompt
    assert "**zonas**: Palermo, Núñez" in prompt


def test_chat_prompt_includes_workspace_block_with_name():
    with _stub_knowledge(), _stub_router():
        prompt = asyncio.run(
            build_system_prompt(
                "chat",
                user_message="hola",
                workspace_memory=[
                    ("lote_usd", "850000"),
                    ("estructura_juridica", "fideicomiso al costo"),
                ],
                workspace_name="Edificio Soler 4500",
            )
        )
    assert "## Contexto del proyecto activo: Edificio Soler 4500" in prompt
    assert "**lote_usd**: 850000" in prompt
    assert "**estructura_juridica**: fideicomiso al costo" in prompt


def test_sol_prompt_includes_profile_block():
    prompt = asyncio.run(
        build_system_prompt(
            "sol",
            profile_items=[("rol", "desarrollador")],
        )
    )
    assert "## Sobre el usuario (perfil)" in prompt
    assert "**rol**: desarrollador" in prompt


def test_chat_prompt_without_memory_has_no_memory_section():
    with _stub_knowledge(), _stub_router():
        prompt = asyncio.run(
            build_system_prompt("chat", user_message="hola")
        )
    assert "## Sobre el usuario" not in prompt
    assert "## Contexto del proyecto activo" not in prompt


def test_caps_are_reasonable():
    # Sanity check: ~1 token ≈ 4 chars, perfil ~400 tk, ws ~800 tk.
    assert 1000 <= PROFILE_MEMORY_MAX_CHARS <= 3000
    assert 2000 <= WORKSPACE_MEMORY_MAX_CHARS <= 6000
