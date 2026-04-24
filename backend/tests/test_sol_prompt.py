"""Tests for the SOL context system prompt selection."""
import asyncio

from api.schemas.chat import ChatRequest
from services.anthropic_service import (
    BASE_SYSTEM_PROMPT,
    SOL_SYSTEM_PROMPT,
    build_system_prompt,
)


def test_chat_request_defaults_context_to_chat():
    req = ChatRequest(message="hola")
    assert req.context_type == "chat"


def test_chat_request_accepts_sol_context():
    req = ChatRequest(message="pagué 500k al albañil", context_type="sol")
    assert req.context_type == "sol"


def test_chat_request_rejects_unknown_context():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ChatRequest(message="x", context_type="invalid")


def test_sol_prompt_is_used_when_context_is_sol():
    prompt = asyncio.run(build_system_prompt("sol"))
    assert prompt == SOL_SYSTEM_PROMPT
    assert "SOL" in prompt
    assert "CARGADO" in prompt


def test_chat_prompt_is_used_when_context_is_chat_default(monkeypatch):
    # Force knowledge loader to return "" so we get the base prompt unchanged
    # (without needing Supabase credentials during tests).
    from services import anthropic_service

    async def _empty_knowledge():
        return ""

    monkeypatch.setattr(anthropic_service, "load_knowledge_context", _empty_knowledge)
    prompt = asyncio.run(build_system_prompt("chat"))
    assert prompt == BASE_SYSTEM_PROMPT
