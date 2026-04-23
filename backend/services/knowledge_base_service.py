"""
KnowledgeBaseService — lee archivos del bucket `knowledge` (Supabase Storage),
parsea .md como texto y .csv como tablas, y expone búsqueda por keywords
con caché TTL en memoria para evitar descargas repetidas.

Uso típico:

    from services.knowledge_base_service import knowledge_base

    context = await knowledge_base.get_context(
        query="costo de construcción por m2 en CABA",
        domain="costos",      # opcional, filtra por subcarpeta
        max_chars=4000,
    )
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

from services.knowledge_storage import knowledge_storage

logger = logging.getLogger(__name__)

DocType = Literal["md", "csv"]

# Stopwords castellano + inglés (breves, suficiente para filtrar ruido en queries)
_STOPWORDS = frozenset(
    """
    a al algo algunos algun alguna algunas ante antes aqui aquel aquella ası asi
    cada como con cual cuando cuanto de del desde donde dos e el ella ellos en
    entre era erase es esa ese eso esta este estos eso fue ha han hasta la las
    le les lo los mas me mi mis muy ni no nos o otra otro para pero por porque
    que quien se si sin sobre solo son su sus tambien tan te ti tu tus un una
    unos unas y ya yo
    and or of to in on at for with by is are was were be been the a an this
    that these those it its it's you your
    """.split()
)

_WORD_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


@dataclass
class Document:
    """Un archivo parseado del knowledge base."""

    path: str
    name: str
    domain: str  # primera carpeta del path (ej: 'costos/foo.md' -> 'costos')
    doc_type: DocType
    content: str  # texto plano (md directo, o csv serializado en filas legibles)
    tokens: frozenset[str] = field(default_factory=frozenset)


@dataclass
class _Cache:
    docs: list[Document]
    loaded_at: float


def _normalize(text: str) -> str:
    """Lowercase + strip acentos para match robusto."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def _tokenize(text: str) -> list[str]:
    """Tokeniza a palabras minúsculas sin acentos ni stopwords."""
    norm = _normalize(text)
    words = _WORD_RE.findall(norm)
    return [w for w in words if w not in _STOPWORDS and len(w) >= 2]


def _domain_from_path(path: str) -> str:
    """Primer segmento del path como dominio; '' si está en la raíz."""
    parts = path.strip("/").split("/", 1)
    return parts[0] if len(parts) > 1 else ""


def parse_md(content: str) -> str:
    """.md se guarda tal cual (ya es texto legible para el LLM)."""
    return content.strip()


def parse_csv(content: str, max_rows: int = 500) -> str:
    """
    Convierte un CSV a un texto tabular legible. Para cada fila:
        col1: val1 | col2: val2 | ...
    Esto es amigable para el LLM y para el keyword search.
    """
    reader = csv.reader(io.StringIO(content))
    try:
        header = next(reader)
    except StopIteration:
        return ""

    header = [h.strip() for h in header]
    lines: list[str] = []
    for i, row in enumerate(reader):
        if i >= max_rows:
            lines.append(f"... ({i}+ filas, truncado)")
            break
        pairs = [
            f"{header[idx] if idx < len(header) else f'col{idx}'}: {val.strip()}"
            for idx, val in enumerate(row)
        ]
        lines.append(" | ".join(pairs))

    return f"Columnas: {', '.join(header)}\n" + "\n".join(lines)


def build_document(path: str, raw_content: str) -> Document | None:
    """Parsea un archivo según su extensión. Devuelve None si no es soportado."""
    lower = path.lower()
    if lower.endswith(".md"):
        text = parse_md(raw_content)
        doc_type: DocType = "md"
    elif lower.endswith(".csv"):
        text = parse_csv(raw_content)
        doc_type = "csv"
    else:
        return None

    name = path.rsplit("/", 1)[-1]
    return Document(
        path=path,
        name=name,
        domain=_domain_from_path(path),
        doc_type=doc_type,
        content=text,
        tokens=frozenset(_tokenize(f"{name}\n{text}")),
    )


def score_document(doc: Document, query_tokens: set[str]) -> int:
    """
    Score = cantidad de tokens de la query que aparecen en el doc.
    Simple y suficiente para un KB chico. Reemplazable por BM25 más adelante.
    """
    if not query_tokens:
        return 0
    return len(query_tokens & doc.tokens)


class KnowledgeBaseService:
    """
    Orquesta carga + parseo + búsqueda sobre los archivos del bucket `knowledge`.

    El caché guarda la lista completa de Documents parseados por TTL segundos
    (default 1 hora). Un lock asyncio evita que múltiples requests concurrentes
    dispare N cargas simultáneas al iniciar.
    """

    DEFAULT_TTL = 3600  # 1 hora

    def __init__(self, ttl_seconds: int = DEFAULT_TTL):
        self._ttl = ttl_seconds
        self._cache: _Cache | None = None
        self._lock = asyncio.Lock()

    def _is_fresh(self) -> bool:
        if self._cache is None:
            return False
        return (time.time() - self._cache.loaded_at) < self._ttl

    async def load_all(self, force: bool = False) -> list[Document]:
        """
        Lee todos los archivos .md y .csv del bucket, los parsea y cachea.
        Si el caché está fresco y `force=False`, devuelve el caché.
        Si falla la carga, devuelve el último caché válido (aunque esté viejo)
        o lista vacía.
        """
        if not force and self._is_fresh():
            return self._cache.docs  # type: ignore[union-attr]

        async with self._lock:
            # Re-check dentro del lock (double-checked locking)
            if not force and self._is_fresh():
                return self._cache.docs  # type: ignore[union-attr]

            try:
                files = await knowledge_storage.list_files()
            except Exception as e:
                logger.warning("KB: list_files falló: %s", e)
                return self._cache.docs if self._cache else []

            supported = [
                f for f in files
                if f["name"].lower().endswith((".md", ".csv"))
            ]

            docs: list[Document] = []
            for f in supported:
                try:
                    raw = await knowledge_storage.get_text_content(f["path"])
                except Exception as e:
                    logger.warning("KB: no pude leer %s: %s", f["path"], e)
                    continue
                doc = build_document(f["path"], raw)
                if doc is not None:
                    docs.append(doc)

            self._cache = _Cache(docs=docs, loaded_at=time.time())
            logger.info("KB: cargados %s documentos", len(docs))
            return docs

    async def search(
        self,
        query: str,
        domain: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[Document, int]]:
        """Devuelve los top_k documentos ordenados por score desc (score > 0)."""
        docs = await self.load_all()
        if domain:
            docs = [d for d in docs if d.domain == domain]

        query_tokens = set(_tokenize(query))
        scored = [
            (doc, score_document(doc, query_tokens))
            for doc in docs
        ]
        scored = [s for s in scored if s[1] > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    async def get_context(
        self,
        query: str,
        domain: str | None = None,
        max_chars: int = 4000,
        top_k: int = 5,
    ) -> str:
        """
        Devuelve contenido relevante concatenado, truncado a `max_chars`.
        Cada fragmento va precedido por `# <nombre>` como separador.
        Si no hay matches, cae a devolver los primeros N docs del dominio.
        """
        hits = await self.search(query, domain=domain, top_k=top_k)

        if not hits:
            # Fallback: devolver los primeros docs del dominio (sin scoring).
            docs = await self.load_all()
            if domain:
                docs = [d for d in docs if d.domain == domain]
            hits = [(d, 0) for d in docs[:top_k]]

        if not hits:
            return ""

        chunks: list[str] = []
        remaining = max_chars
        for doc, _score in hits:
            header = f"# {doc.name}\n\n"
            body = doc.content
            block = header + body
            if len(block) > remaining:
                block = block[: max(0, remaining)]
            chunks.append(block)
            remaining -= len(block)
            if remaining <= 0:
                break

        return "\n\n---\n\n".join(c for c in chunks if c)

    def invalidate_cache(self) -> None:
        """Fuerza recarga en el próximo acceso."""
        self._cache = None


# Singleton para uso en routes/services
knowledge_base = KnowledgeBaseService()
