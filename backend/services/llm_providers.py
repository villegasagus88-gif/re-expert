"""
LLM provider abstraction.

Permite que el agente use Anthropic Claude o Google Gemini sin que el resto
del código se entere. Ambos soportan tool-use (function calling) nativo.

Selección por env var:
  - LLM_PROVIDER=gemini    → Google Gemini 2.5 Flash (FREE tier)
  - LLM_PROVIDER=anthropic → Claude (requiere créditos)
  - LLM_PROVIDER=auto (default) → Si hay GEMINI_API_KEY, Gemini; sino Anthropic.

API unificada (lo que el agente consume):
    response = await provider.generate(system, messages, tools, max_tokens)
    response.content   → list[ContentBlock] con type='text' o type='tool_use'
    response.stop_reason → 'tool_use' | 'end_turn' | 'max_tokens'
    response.usage     → {input_tokens, output_tokens}

Mensajes en formato Anthropic (compatible con el agent_service existente):
    [{"role": "user|assistant", "content": str | list[block]}]
    block puede ser:
      {"type":"text","text":"..."}
      {"type":"tool_use","id":"...","name":"...","input":{...}}
      {"type":"tool_result","tool_use_id":"...","content":"..."}

El adapter Gemini traduce esto a/desde el formato de Google.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ContentBlock:
    type: str  # "text" | "tool_use"
    text: str | None = None
    id: str | None = None  # tool_use only
    name: str | None = None  # tool_use only
    input: dict | None = None  # tool_use only


@dataclass
class LLMResponse:
    content: list[ContentBlock]
    stop_reason: str  # "tool_use" | "end_turn" | "max_tokens"
    usage: dict[str, int] = field(default_factory=dict)


# ════════════════════════════════════════════════════════════════════
# Anthropic provider (la implementación original)
# ════════════════════════════════════════════════════════════════════
class AnthropicProvider:
    name = "anthropic"

    def __init__(self):
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.ANTHROPIC_MODEL

    async def generate(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )
        blocks: list[ContentBlock] = []
        for b in resp.content:
            t = getattr(b, "type", None)
            if t == "text":
                blocks.append(ContentBlock(type="text", text=b.text))
            elif t == "tool_use":
                blocks.append(
                    ContentBlock(
                        type="tool_use",
                        id=b.id,
                        name=b.name,
                        input=b.input or {},
                    )
                )
        return LLMResponse(
            content=blocks,
            stop_reason=resp.stop_reason or "end_turn",
            usage={
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            },
        )


# ════════════════════════════════════════════════════════════════════
# Gemini provider (free tier — usar para desarrollo / planes Free)
# ════════════════════════════════════════════════════════════════════
# Endpoint REST oficial v1beta. Soporta function calling nativo.
# Doc: https://ai.google.dev/gemini-api/docs/function-calling
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _anthropic_tool_to_gemini(tool: dict) -> dict:
    """
    Anthropic tool schema:
        {"name": "...", "description": "...",
         "input_schema": {"type":"object","properties":{...},"required":[...]}}
    Gemini function declaration:
        {"name": "...", "description": "...",
         "parameters": {"type":"OBJECT","properties":{...},"required":[...]}}
    """
    schema = tool.get("input_schema", {}) or {"type": "object"}
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "parameters": _convert_schema_types(schema),
    }


def _convert_schema_types(schema: dict) -> dict:
    """Convierte tipos JSON Schema (lowercase) a Gemini (UPPERCASE) recursivamente."""
    if not isinstance(schema, dict):
        return schema
    out = dict(schema)
    if "type" in out and isinstance(out["type"], str):
        out["type"] = out["type"].upper()
    if "properties" in out and isinstance(out["properties"], dict):
        out["properties"] = {k: _convert_schema_types(v) for k, v in out["properties"].items()}
    if "items" in out and isinstance(out["items"], dict):
        out["items"] = _convert_schema_types(out["items"])
    # Gemini no soporta "default" ni "format" en algunos contextos: los toleramos.
    return out


def _anthropic_msgs_to_gemini(messages: list[dict]) -> list[dict]:
    """
    Traduce historial Anthropic → Gemini.

    Anthropic role = "user"|"assistant"; Gemini role = "user"|"model".
    Bloques Anthropic (text, tool_use, tool_result) → Gemini parts (text,
    functionCall, functionResponse).
    """
    out: list[dict] = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        content = m["content"]
        if isinstance(content, str):
            parts = [{"text": content}]
        else:
            parts = []
            for b in content:
                bt = b.get("type")
                if bt == "text":
                    parts.append({"text": b.get("text", "")})
                elif bt == "tool_use":
                    parts.append(
                        {
                            "functionCall": {
                                "name": b["name"],
                                "args": b.get("input", {}) or {},
                            }
                        }
                    )
                elif bt == "tool_result":
                    # Gemini espera el resultado dentro de functionResponse.response
                    raw = b.get("content", "")
                    if isinstance(raw, str):
                        try:
                            import json

                            parsed = json.loads(raw)
                        except Exception:
                            parsed = {"result": raw}
                    else:
                        parsed = raw if isinstance(raw, dict) else {"result": raw}
                    parts.append(
                        {
                            "functionResponse": {
                                # Gemini matchea por name (no por tool_use_id)
                                "name": parsed.get("__name__") or "tool",
                                "response": parsed,
                            }
                        }
                    )
        if parts:
            out.append({"role": role, "parts": parts})
    return out


class GeminiProvider:
    name = "gemini"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not configured")
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL or "gemini-2.5-flash"

    async def generate(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # Antes de mandar, marcamos cada tool_result con su functionCall name
        # (Anthropic lo identifica por tool_use_id; Gemini por name).
        # Caminamos hacia atrás guardando el último tool_use con id=tool_use_id.
        id_to_name: dict[str, str] = {}
        for m in messages:
            c = m.get("content")
            if isinstance(c, list):
                for b in c:
                    if b.get("type") == "tool_use" and b.get("id"):
                        id_to_name[b["id"]] = b["name"]
                    if b.get("type") == "tool_result":
                        tu_id = b.get("tool_use_id")
                        if tu_id and tu_id in id_to_name:
                            # Inyectar __name__ en el content para el traductor
                            raw = b.get("content")
                            if isinstance(raw, str):
                                try:
                                    import json

                                    parsed = json.loads(raw)
                                except Exception:
                                    parsed = {"result": raw}
                            else:
                                parsed = raw if isinstance(raw, dict) else {"result": raw}
                            parsed["__name__"] = id_to_name[tu_id]
                            import json as _json

                            b["content"] = _json.dumps(parsed, ensure_ascii=False, default=str)

        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": _anthropic_msgs_to_gemini(messages),
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if tools:
            body["tools"] = [
                {"functionDeclarations": [_anthropic_tool_to_gemini(t) for t in tools]}
            ]

        url = f"{GEMINI_API_BASE}/models/{self._model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self._api_key}

        async with httpx.AsyncClient(timeout=60) as cli:
            r = await cli.post(url, headers=headers, json=body)
            data = r.json()
            if r.status_code >= 400:
                raise RuntimeError(f"Gemini error {r.status_code}: {data}")

        candidates = data.get("candidates") or []
        if not candidates:
            return LLMResponse(content=[], stop_reason="end_turn", usage={})
        cand = candidates[0]
        cand_content = cand.get("content") or {}
        parts = cand_content.get("parts") or []
        finish = (cand.get("finishReason") or "STOP").upper()

        blocks: list[ContentBlock] = []
        used_tool = False
        for p in parts:
            if "text" in p:
                blocks.append(ContentBlock(type="text", text=p["text"]))
            elif "functionCall" in p:
                fc = p["functionCall"]
                used_tool = True
                blocks.append(
                    ContentBlock(
                        type="tool_use",
                        id=str(uuid.uuid4()),  # Gemini no devuelve id; sintetizamos
                        name=fc.get("name", "unknown"),
                        input=fc.get("args", {}) or {},
                    )
                )

        # Mapear finishReason → Anthropic-style stop_reason
        if used_tool:
            stop_reason = "tool_use"
        elif finish == "MAX_TOKENS":
            stop_reason = "max_tokens"
        else:
            stop_reason = "end_turn"

        usage_meta = data.get("usageMetadata") or {}
        usage = {
            "input_tokens": usage_meta.get("promptTokenCount", 0),
            "output_tokens": usage_meta.get("candidatesTokenCount", 0),
        }

        return LLMResponse(content=blocks, stop_reason=stop_reason, usage=usage)


# ════════════════════════════════════════════════════════════════════
# Selección
# ════════════════════════════════════════════════════════════════════
_provider: AnthropicProvider | GeminiProvider | None = None


def get_provider() -> AnthropicProvider | GeminiProvider:
    global _provider
    if _provider is not None:
        return _provider

    choice = (settings.LLM_PROVIDER or "auto").lower()
    if choice == "gemini":
        _provider = GeminiProvider()
    elif choice == "anthropic":
        _provider = AnthropicProvider()
    else:  # auto
        # Si hay GEMINI_API_KEY no vacía, lo preferimos (gratis)
        if settings.GEMINI_API_KEY:
            _provider = GeminiProvider()
        else:
            _provider = AnthropicProvider()
    logger.info("LLM provider activo: %s", _provider.name)
    return _provider


def reset_provider() -> None:
    """Útil en tests o después de cambiar settings."""
    global _provider
    _provider = None
