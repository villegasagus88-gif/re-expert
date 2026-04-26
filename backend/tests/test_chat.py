"""
Tests for POST /api/chat — streaming SSE endpoint.

Real Anthropic API and database are NOT used. Strategy:
  - stream_chat         → async generator with fake delta+end events
  - build_system_prompt → AsyncMock returning a plain string
  - check_user_rate_limit → AsyncMock returning {} (or raises 429)
  - log_token_usage     → AsyncMock (no-op, inspected in specific tests)
  - get_current_user    → dependency override returning a fake User
  - get_db              → dependency override yielding a thin async stub
"""
import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from core.auth import get_current_user
from main import app
from models.base import get_db
from models.conversation import Conversation
from models.message import Message
from models.user import User


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _make_user(plan: str = "free") -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.plan = plan
    user.role = "user"
    return user


def _parse_sse(content: bytes) -> list[dict]:
    """Parse raw SSE body into a list of event dicts."""
    events = []
    for line in content.decode("utf-8").splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


async def _fake_stream_chat(messages, system, max_tokens=4096):
    """Fake Claude stream: two deltas then usage totals."""
    yield {"type": "delta", "text": "Hola"}
    yield {"type": "delta", "text": " mundo"}
    yield {"type": "end", "input_tokens": 10, "output_tokens": 5}


class _MockDB:
    """Thin async stub for SQLAlchemy AsyncSession."""

    def __init__(self, conversation: Conversation | None = None):
        self.added: list = []
        self._conv = conversation  # returned by db.get(Conversation, ...)

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        # SQLAlchemy applies column defaults at INSERT time; assign UUIDs here
        # so that conv.id is non-None before the stream generator starts.
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    async def commit(self) -> None:
        # Ensure any objects still lacking an id get one (mirrors flush).
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    async def rollback(self) -> None:
        pass

    async def get(self, model, pk):
        if model is Conversation:
            return self._conv
        return None

    async def execute(self, stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        result.scalar.return_value = 0
        result.scalar_one_or_none.return_value = None
        return result


@contextmanager
def _chat_client(
    user: MagicMock | None = None,
    mock_db: _MockDB | None = None,
    rate_limit_headers: dict | None = None,
):
    """
    Context manager that wires up dependency overrides + patches for a chat test.
    Yields (TestClient, mock_db, mock_log_token_usage).
    """
    if user is None:
        user = _make_user()
    if mock_db is None:
        mock_db = _MockDB()
    if rate_limit_headers is None:
        rate_limit_headers = {}

    async def _get_user():
        return user

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db

    mock_log = AsyncMock(return_value=None)

    try:
        with (
            patch("api.routes.chat.stream_chat", side_effect=_fake_stream_chat),
            patch(
                "api.routes.chat.build_system_prompt",
                new=AsyncMock(return_value="test-system-prompt"),
            ),
            patch(
                "api.routes.chat.check_user_rate_limit",
                new=AsyncMock(return_value=rate_limit_headers),
            ),
            patch("api.routes.chat.log_token_usage", mock_log),
        ):
            yield TestClient(app), mock_db, mock_log
    finally:
        app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────
# 1. Smoke tests — no auth
# ─────────────────────────────────────────────────────────────

def test_chat_endpoint_is_registered():
    """POST /api/chat should exist; without auth we expect 401, not 404."""
    client = TestClient(app)
    response = client.post("/api/chat", json={"message": "hola"})
    assert response.status_code == 401


def test_chat_rejects_missing_message():
    """Validation: missing 'message' yields 422 if auth is present, else 401."""
    client = TestClient(app)
    response = client.post("/api/chat", json={})
    assert response.status_code in (401, 422)


def test_chat_method_not_allowed_on_get():
    client = TestClient(app)
    response = client.get("/api/chat")
    assert response.status_code == 405


# ─────────────────────────────────────────────────────────────
# 2. Streaming — SSE format
# ─────────────────────────────────────────────────────────────

def test_streaming_response_is_sse():
    """POST /api/chat returns Content-Type: text/event-stream."""
    with _chat_client() as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "hola"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_streaming_event_order():
    """Events arrive in order: start → delta(s) → done."""
    with _chat_client() as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "hola"})
    events = _parse_sse(resp.content)
    types = [e["type"] for e in events]
    assert types[0] == "start"
    assert types[-1] == "done"
    assert types.count("delta") == 2


def test_start_event_contains_valid_conversation_id():
    """The start event carries a parseable UUID as conversation_id."""
    with _chat_client() as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "hola"})
    start = _parse_sse(resp.content)[0]
    assert start["type"] == "start"
    UUID(start["conversation_id"])  # raises ValueError if malformed


def test_delta_events_carry_text():
    """Delta events contain the text chunks from the mock stream."""
    with _chat_client() as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "hola"})
    deltas = [e for e in _parse_sse(resp.content) if e["type"] == "delta"]
    assert deltas[0]["text"] == "Hola"
    assert deltas[1]["text"] == " mundo"


def test_done_event_has_tokens_used():
    """The done event reports the sum of input+output tokens."""
    with _chat_client() as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "hola"})
    done = next(e for e in _parse_sse(resp.content) if e["type"] == "done")
    assert done["tokens_used"] == 15  # 10 input + 5 output from fake stream


# ─────────────────────────────────────────────────────────────
# 3. Message persistence
# ─────────────────────────────────────────────────────────────

def test_user_message_persisted_in_db():
    """User message is added to the DB session with correct content."""
    with _chat_client() as (client, mock_db, _mock_log):
        client.post("/api/chat", json={"message": "Test persistence"})

    user_msgs = [
        o for o in mock_db.added
        if isinstance(o, Message) and o.role == "user"
    ]
    assert len(user_msgs) == 1
    assert user_msgs[0].content == "Test persistence"


def test_assistant_message_persisted_in_db():
    """Assistant message is added with the full streamed content and token count."""
    with _chat_client() as (client, mock_db, _mock_log):
        client.post("/api/chat", json={"message": "hola"})

    assistant_msgs = [
        o for o in mock_db.added
        if isinstance(o, Message) and o.role == "assistant"
    ]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0].content == "Hola mundo"
    assert assistant_msgs[0].tokens_used == 15


def test_new_conversation_created_when_no_id_given():
    """When conversation_id is omitted, a new Conversation is created."""
    with _chat_client() as (client, mock_db, _mock_log):
        client.post("/api/chat", json={"message": "primera pregunta"})

    convs = [o for o in mock_db.added if isinstance(o, Conversation)]
    assert len(convs) == 1


def test_new_conversation_title_derived_from_first_message():
    """Title of the auto-created conversation comes from the user's message."""
    with _chat_client() as (client, mock_db, _mock_log):
        client.post("/api/chat", json={"message": "Cuánto cuesta un metro cuadrado en CABA"})

    convs = [o for o in mock_db.added if isinstance(o, Conversation)]
    assert convs
    assert "Cuánto cuesta" in convs[0].title or "metro cuadrado" in convs[0].title


# ─────────────────────────────────────────────────────────────
# 4. Token usage logging
# ─────────────────────────────────────────────────────────────

def test_log_token_usage_called_once():
    """log_token_usage is called exactly once per successful chat request."""
    with _chat_client() as (client, _, mock_log):
        client.post("/api/chat", json={"message": "tokens test"})
    mock_log.assert_called_once()


def test_log_token_usage_correct_counts():
    """log_token_usage receives the exact token counts from the mock stream."""
    with _chat_client() as (client, _, mock_log):
        client.post("/api/chat", json={"message": "tokens test"})

    kwargs = mock_log.call_args.kwargs
    assert kwargs["input_tokens"] == 10
    assert kwargs["output_tokens"] == 5


def test_log_token_usage_bound_to_user():
    """log_token_usage is called with the authenticated user's id."""
    user = _make_user()
    with _chat_client(user=user) as (client, _, mock_log):
        client.post("/api/chat", json={"message": "bind test"})

    kwargs = mock_log.call_args.kwargs
    assert kwargs["user_id"] == user.id


# ─────────────────────────────────────────────────────────────
# 5. Rate limiting
# ─────────────────────────────────────────────────────────────

def test_rate_limit_exceeded_returns_429():
    """When check_user_rate_limit raises 429, the endpoint returns 429."""
    user = _make_user()
    mock_db = _MockDB()

    async def _get_user():
        return user

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db

    try:
        with patch(
            "api.routes.chat.check_user_rate_limit",
            new=AsyncMock(
                side_effect=HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Límite horario excedido: 5 msgs/hora. Plan actual: free.",
                    headers={"Retry-After": "3600"},
                )
            ),
        ):
            client = TestClient(app)
            resp = client.post("/api/chat", json={"message": "too many"})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 429
    assert "Límite" in resp.json().get("detail", "")


def test_rate_limit_headers_included_in_streaming_response():
    """X-RateLimit-* headers returned by check_user_rate_limit are forwarded."""
    rl_headers = {
        "X-RateLimit-Limit-Hour": "5",
        "X-RateLimit-Remaining-Hour": "3",
        "X-RateLimit-Reset-Hour": "9999999999",
    }
    with _chat_client(rate_limit_headers=rl_headers) as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "header test"})

    assert resp.headers.get("X-RateLimit-Limit-Hour") == "5"
    assert resp.headers.get("X-RateLimit-Remaining-Hour") == "3"


# ─────────────────────────────────────────────────────────────
# 6. Conversation ownership
# ─────────────────────────────────────────────────────────────

def test_accessing_other_users_conversation_returns_404():
    """Requesting a conversation owned by another user yields 404."""
    user = _make_user()
    other_user_id = uuid4()

    foreign_conv = MagicMock(spec=Conversation)
    foreign_conv.id = uuid4()
    foreign_conv.user_id = other_user_id  # different from user.id

    mock_db = _MockDB(conversation=foreign_conv)

    async def _get_user():
        return user

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db

    try:
        with (
            patch("api.routes.chat.stream_chat", side_effect=_fake_stream_chat),
            patch(
                "api.routes.chat.build_system_prompt",
                new=AsyncMock(return_value="prompt"),
            ),
            patch(
                "api.routes.chat.check_user_rate_limit",
                new=AsyncMock(return_value={}),
            ),
        ):
            client = TestClient(app)
            resp = client.post(
                "/api/chat",
                json={"message": "hack", "conversation_id": str(foreign_conv.id)},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert "Conversación" in resp.json().get("detail", "")


def test_accessing_nonexistent_conversation_returns_404():
    """Requesting a conversation_id that doesn't exist yields 404."""
    user = _make_user()
    mock_db = _MockDB(conversation=None)  # db.get returns None

    async def _get_user():
        return user

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db

    try:
        with (
            patch("api.routes.chat.check_user_rate_limit", new=AsyncMock(return_value={})),
        ):
            client = TestClient(app)
            resp = client.post(
                "/api/chat",
                json={"message": "gone", "conversation_id": str(uuid4())},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────
# 7. Plan gating (SOL context)
# ─────────────────────────────────────────────────────────────

def test_sol_context_blocked_for_free_user():
    """context_type='sol' returns 403 for users on the free plan."""
    user = _make_user(plan="free")
    mock_db = _MockDB()

    async def _get_user():
        return user

    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_db] = _get_db

    try:
        with patch(
            "api.routes.chat.check_user_rate_limit", new=AsyncMock(return_value={})
        ):
            client = TestClient(app)
            resp = client.post(
                "/api/chat",
                json={"message": "cargame un pago", "context_type": "sol"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 403
    body = resp.json()
    assert body["detail"]["plan_required"] == "pro"
    assert "upgrade_url" in body["detail"]


def test_sol_context_allowed_for_pro_user():
    """context_type='sol' streams normally for pro-plan users."""
    pro_user = _make_user(plan="pro")
    with _chat_client(user=pro_user) as (client, _, _mock_log):
        resp = client.post(
            "/api/chat",
            json={"message": "cargame un pago", "context_type": "sol"},
        )

    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    assert events[0]["type"] == "start"
    assert any(e["type"] == "done" for e in events)


def test_chat_context_allowed_for_free_user():
    """Default context_type='chat' is available to free-plan users."""
    with _chat_client(user=_make_user(plan="free")) as (client, _, _mock_log):
        resp = client.post("/api/chat", json={"message": "hola"})
    assert resp.status_code == 200
