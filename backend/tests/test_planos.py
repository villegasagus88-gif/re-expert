"""
Tests for POST /api/planos/analyze — multimodal (vision) streaming SSE endpoint.

Real Anthropic API and database are NOT used. Strategy mirrors test_chat.py:
  - stream_chat         → async generator that captures the `messages` it
                          receives (so we can assert the vision content blocks)
  - build_system_prompt → AsyncMock returning a plain string
  - check_user_rate_limit → AsyncMock returning {}
  - log_token_usage     → AsyncMock (inspected)
  - get_current_user / get_db → dependency overrides
  - limiter.enabled = False so the 6/minute cap doesn't make tests flaky
"""
import base64
import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from core.auth import get_current_user
from core.rate_limit import limiter
from main import app
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User

# 1x1 px PNG (transparent) — smallest valid image payload for the upload.
_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture(autouse=True)
def _disable_limiter():
    """The route is @limiter.limit('6/minute'); disable it so repeated test
    posts don't trip the shared in-memory bucket."""
    prev = limiter.enabled
    limiter.enabled = False
    try:
        yield
    finally:
        limiter.enabled = prev


def _make_user(plan: str = "free") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.plan = plan
    user.role = "user"
    return user


def _parse_sse(content: bytes) -> list[dict]:
    return [
        json.loads(line[6:])
        for line in content.decode("utf-8").splitlines()
        if line.startswith("data: ")
    ]


class _MockDB:
    """Thin async stub for SQLAlchemy AsyncSession (same shape as test_chat)."""

    def __init__(self, conversation: Conversation | None = None):
        self.added: list = []
        self._conv = conversation

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    async def commit(self) -> None:
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    async def rollback(self) -> None:
        pass

    async def get(self, model, pk):
        if model is Conversation:
            return self._conv
        return None


@contextmanager
def _planos_client(user: MagicMock | None = None, mock_db: _MockDB | None = None):
    """Wire dependency overrides + patches. Yields (client, mock_db, mock_log, captured)."""
    if user is None:
        user = _make_user()
    if mock_db is None:
        mock_db = _MockDB()

    captured: dict = {}

    async def _fake_stream(messages, system, max_tokens=4096):
        captured["messages"] = messages
        captured["system"] = system
        captured["max_tokens"] = max_tokens
        yield {"type": "delta", "text": "Estim"}
        yield {"type": "delta", "text": "ación"}
        yield {"type": "end", "input_tokens": 12, "output_tokens": 7}

    async def _get_user():
        return user

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db
    mock_log = AsyncMock(return_value=None)

    try:
        with (
            patch("api.routes.planos.stream_chat", side_effect=_fake_stream),
            patch(
                "api.routes.planos.build_system_prompt",
                new=AsyncMock(return_value="test-system-prompt"),
            ),
            patch(
                "api.routes.planos.check_user_rate_limit",
                new=AsyncMock(return_value={}),
            ),
            patch("api.routes.planos.log_token_usage", mock_log),
        ):
            yield TestClient(app), mock_db, mock_log, captured
    finally:
        app.dependency_overrides.clear()


# ── registration / auth ──────────────────────────────────────────────

def test_planos_endpoint_registered():
    """Valid multipart but no auth → 401 (endpoint exists, not 404).

    Override only get_db (with the stub) so the real async session — which
    needs a live DB/greenlet — is never entered; get_current_user stays real
    so it raises 401 on the missing token.
    """
    mock_db = _MockDB()

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _get_db
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code in (401, 422)


# ── streaming / happy path ───────────────────────────────────────────

def test_streaming_response_is_sse():
    with _planos_client() as (client, _db, _log, _cap):
        resp = client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_event_order_start_delta_done():
    with _planos_client() as (client, _db, _log, _cap):
        resp = client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
        )
    types = [e["type"] for e in _parse_sse(resp.content)]
    assert types[0] == "start"
    assert types[-1] == "done"
    assert types.count("delta") == 2


def test_start_event_has_valid_conversation_id():
    with _planos_client() as (client, _db, _log, _cap):
        resp = client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
        )
    start = _parse_sse(resp.content)[0]
    UUID(start["conversation_id"])  # raises if malformed


# ── the core fix: real file bytes reach the model ────────────────────

def test_image_sent_as_vision_block_with_base64():
    """The uploaded PNG must reach Claude as an image block with base64 data —
    this is the whole point of the fix (previously only filenames were sent)."""
    with _planos_client() as (client, _db, _log, captured):
        client.post(
            "/api/planos/analyze",
            files=[("files", ("plano-planta.png", _PNG_BYTES, "image/png"))],
        )
    content = captured["messages"][0]["content"]
    assert isinstance(content, list)
    # First block is the instruction text, then the image.
    assert content[0]["type"] == "text"
    img = next(b for b in content if b["type"] == "image")
    assert img["source"]["type"] == "base64"
    assert img["source"]["media_type"] == "image/png"
    # Round-trips back to the exact bytes we uploaded.
    assert base64.b64decode(img["source"]["data"]) == _PNG_BYTES


def test_pdf_sent_as_document_block():
    with _planos_client() as (client, _db, _log, captured):
        client.post(
            "/api/planos/analyze",
            files=[("files", ("plano.pdf", b"%PDF-1.4 fake-bytes", "application/pdf"))],
        )
    content = captured["messages"][0]["content"]
    doc = next(b for b in content if b["type"] == "document")
    assert doc["source"]["media_type"] == "application/pdf"


def test_custom_prompt_used_as_text_block():
    with _planos_client() as (client, _db, _log, captured):
        client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
            data={"prompt": "¿Cuántos ladrillos necesito?"},
        )
    text_block = captured["messages"][0]["content"][0]
    assert text_block["type"] == "text"
    assert "ladrillos" in text_block["text"]


# ── validation ───────────────────────────────────────────────────────

def test_unsupported_file_type_rejected():
    with _planos_client() as (client, _db, _log, _cap):
        resp = client.post(
            "/api/planos/analyze",
            files=[("files", ("notas.txt", b"hello", "text/plain"))],
        )
    assert resp.status_code == 400


def test_too_many_files_rejected():
    with _planos_client() as (client, _db, _log, _cap):
        resp = client.post(
            "/api/planos/analyze",
            files=[
                ("files", (f"p{i}.png", _PNG_BYTES, "image/png")) for i in range(9)
            ],
        )
    assert resp.status_code == 400


def test_oversized_file_rejected():
    """A single file over MAX_FILE_BYTES → 413 (patch the cap low to avoid a big payload)."""
    with _planos_client() as (client, _db, _log, _cap):
        with patch("api.routes.planos.MAX_FILE_BYTES", 4):
            resp = client.post(
                "/api/planos/analyze",
                files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
            )
    assert resp.status_code == 413


# ── persistence + usage ──────────────────────────────────────────────

def test_user_and_assistant_messages_persisted():
    with _planos_client() as (client, mock_db, _log, _cap):
        client.post(
            "/api/planos/analyze",
            files=[("files", ("planta.png", _PNG_BYTES, "image/png"))],
        )
    msgs = [o for o in mock_db.added if isinstance(o, Message)]
    user_msgs = [m for m in msgs if m.role == "user"]
    asst_msgs = [m for m in msgs if m.role == "assistant"]
    assert len(user_msgs) == 1
    assert "planta.png" in user_msgs[0].content  # filenames recorded in history
    assert len(asst_msgs) == 1
    assert asst_msgs[0].content == "Estimación"
    assert asst_msgs[0].tokens_used == 19  # 12 + 7


def test_token_usage_logged_once_with_counts():
    with _planos_client() as (client, _db, mock_log, _cap):
        client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
        )
    mock_log.assert_called_once()
    kwargs = mock_log.call_args.kwargs
    assert kwargs["input_tokens"] == 12
    assert kwargs["output_tokens"] == 7


def test_other_users_conversation_returns_404():
    user = _make_user()
    foreign = MagicMock(spec=Conversation)
    foreign.id = uuid4()
    foreign.user_id = uuid4()  # different owner
    with _planos_client(user=user, mock_db=_MockDB(conversation=foreign)) as (
        client,
        _db,
        _log,
        _cap,
    ):
        resp = client.post(
            "/api/planos/analyze",
            files=[("files", ("plan.png", _PNG_BYTES, "image/png"))],
            data={"conversation_id": str(foreign.id)},
        )
    assert resp.status_code == 404
