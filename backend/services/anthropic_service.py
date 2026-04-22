"""
Anthropic client service: streams Claude responses and builds system prompt
with optional knowledge base context loaded from Supabase Storage.
"""
import asyncio
import logging
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from config.settings import settings
from services.knowledge_storage import knowledge_storage

logger = logging.getLogger(__name__)

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    """Lazily build the shared async Anthropic client."""
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


BASE_SYSTEM_PROMPT = """Sos RE Expert, un asistente experto en Real Estate argentino.
Ayudas a desarrolladores, inversores e inmobiliarias con preguntas sobre costos de
construcción, rendimientos de inversión, normativa básica y rubros de obra en
Argentina.

Respondés en español rioplatense, de forma clara y concisa. Cuando corresponda,
usá la información de la sección "Base de conocimiento" que se adjunta más abajo
para fundamentar tus respuestas. Si no tenés información suficiente, decilo
directamente en lugar de inventar.
"""


async def load_knowledge_context() -> str:
    """
    Carga todos los archivos .md del bucket 'knowledge' de Supabase Storage
    y los concatena en un único string. Si falla (bucket vacío, red caída, etc.),
    loguea un warning y devuelve "".
    """
    try:
        files = await asyncio.wait_for(knowledge_storage.list_files(), timeout=5)
    except Exception as e:
        logger.warning("No se pudo listar archivos de knowledge: %s", e)
        return ""

    md_files = [f for f in files if f["name"].lower().endswith(".md")]
    chunks: list[str] = []
    for f in md_files:
        try:
            content = await asyncio.wait_for(
                knowledge_storage.get_text_content(f["path"]), timeout=5
            )
            chunks.append(f"# {f['name']}\n\n{content}")
        except Exception as e:
            logger.warning("No se pudo leer %s: %s", f["path"], e)

    return "\n\n---\n\n".join(chunks)


async def build_system_prompt() -> str:
    """Base prompt + knowledge context (si está disponible)."""
    knowledge = await load_knowledge_context()
    if not knowledge:
        return BASE_SYSTEM_PROMPT
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"## Base de conocimiento\n\n"
        f"{knowledge}"
    )


async def stream_chat(
    messages: list[dict],
    system: str,
    max_tokens: int = 4096,
) -> AsyncIterator[str]:
    """
    Streams text tokens from Claude. Yields plain strings as they arrive.
    Raises anthropic exceptions; caller is responsible for handling errors.
    """
    client = get_client()
    async with client.messages.stream(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
