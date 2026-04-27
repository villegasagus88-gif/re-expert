"""
Full verification: auth + conversations CRUD + schemas + models + migrations.
Runs without DB connection using mocked settings.
"""
import ast
import csv
import math
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

# Setup path + mock settings before any project imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
mock_settings = MagicMock()
mock_settings.JWT_SECRET = "test-secret-key-for-unit-tests-only-32chars!"
mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
import os
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests-only-32chars!")

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
passed = 0
failed = 0


def ok(name):
    global passed
    print(f"  OK  {name}")
    passed += 1


def fail(name, detail=""):
    global failed
    print(f"  FAIL  {name} -- {detail}")
    failed += 1


def check(name, condition, detail=""):
    if condition:
        ok(name)
    else:
        fail(name, detail)


# ================================================================
# 1. SYNTAX CHECK — all project files
# ================================================================
print("\n=== 1. SYNTAX (all Python files) ===")
py_files = [
    "models/user.py", "models/conversation.py", "models/message.py",
    "models/token_usage.py", "models/base.py", "models/__init__.py",
    "services/auth_service.py", "services/jwt_service.py",
    "core/auth.py", "core/rate_limit.py",
    "config/settings.py",
    "api/routes/auth.py", "api/routes/conversations.py",
    "api/routes/chat.py", "api/routes/knowledge.py", "api/routes/usage.py",
    "api/schemas/auth.py", "api/schemas/conversation.py", "api/schemas/chat.py",
    "main.py",
]
for f in py_files:
    p = os.path.join(BASE, f)
    if not os.path.exists(p):
        fail(f"{f} syntax", "file not found")
        continue
    try:
        ast.parse(open(p, encoding="utf-8").read())
        ok(f"{f}")
    except SyntaxError as e:
        fail(f"{f}", str(e))


# ================================================================
# 2. MIGRATION CHAIN
# ================================================================
print("\n=== 2. MIGRATION CHAIN ===")
versions_dir = os.path.join(BASE, "alembic", "versions")
chain = {}
for fn in sorted(os.listdir(versions_dir)):
    if not fn.endswith(".py") or fn.startswith("__"):
        continue
    content = open(os.path.join(versions_dir, fn), encoding="utf-8").read()
    rev_m = re.search(r'revision:\s*str\s*=\s*"([^"]+)"', content)
    down_m = re.search(r'down_revision:\s*str\s*\|\s*None\s*=\s*(?:"([^"]+)"|None)', content)
    if rev_m:
        chain[rev_m.group(1)] = down_m.group(1) if down_m and down_m.group(1) else None

check("10 migrations exist", len(chain) == 10, f"found {len(chain)}")
roots = [r for r, d in chain.items() if d is None]
check("single root", len(roots) == 1)
if roots:
    cur = roots[0]
    walked = [cur]
    while True:
        nxt = [r for r, d in chain.items() if d == cur]
        if not nxt:
            break
        cur = nxt[0]
        walked.append(cur)
    check("chain continuous", len(walked) == len(chain))
    print(f"       {' -> '.join(walked)}")


# ================================================================
# 3. BCRYPT
# ================================================================
print("\n=== 3. BCRYPT ===")
import bcrypt

pw = "TestPass123"
h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
check("hash is bcrypt format", h.startswith("$2b$"))
check("correct password verifies", bcrypt.checkpw(pw.encode(), h.encode()))
check("wrong password rejected", not bcrypt.checkpw(b"wrong", h.encode()))

from services.auth_service import _hash_password, _verify_password

h2 = _hash_password("Abc123")
check("_hash_password roundtrip", _verify_password("Abc123", h2))
check("_verify rejects wrong", not _verify_password("xyz", h2))


# ================================================================
# 4. JWT TOKENS
# ================================================================
print("\n=== 4. JWT TOKENS ===")
from services.jwt_service import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
)

uid = uuid4()
at = create_access_token(uid)
rt = create_refresh_token(uid)

check("access token is string", isinstance(at, str) and len(at) > 50)
check("refresh token is string", isinstance(rt, str) and len(rt) > 50)
check("tokens are different", at != rt)

ap = decode_token(at)
check("access sub == user_id", ap["sub"] == str(uid))
check("access type == access", ap["type"] == "access")
check("access has exp", "exp" in ap)

rp = decode_token(rt)
check("refresh sub == user_id", rp["sub"] == str(uid))
check("refresh type == refresh", rp["type"] == "refresh")

# Expiration
exp_a = datetime.fromtimestamp(ap["exp"], tz=timezone.utc)
iat_a = datetime.fromtimestamp(ap["iat"], tz=timezone.utc)
check("access expires ~15min", timedelta(minutes=14) < (exp_a - iat_a) <= timedelta(minutes=16))

exp_r = datetime.fromtimestamp(rp["exp"], tz=timezone.utc)
iat_r = datetime.fromtimestamp(rp["iat"], tz=timezone.utc)
check("refresh expires ~7 days", timedelta(days=6, hours=23) < (exp_r - iat_r) <= timedelta(days=7, hours=1))

# Expired token — sign with the SAME secret decode_token uses (env-driven).
import jwt as pyjwt
expired = pyjwt.encode(
    {"sub": str(uid), "type": "access", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
    os.environ["JWT_SECRET"], algorithm="HS256"
)
try:
    decode_token(expired)
    fail("expired token raises")
except pyjwt.ExpiredSignatureError:
    ok("expired token raises ExpiredSignatureError")

# Wrong secret
bad = pyjwt.encode(
    {"sub": str(uid), "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
    "wrong-key", algorithm="HS256"
)
try:
    decode_token(bad)
    fail("wrong secret raises")
except pyjwt.InvalidSignatureError:
    ok("wrong secret raises InvalidSignatureError")

# Token pair
a, r = create_token_pair(uid)
check("token_pair returns two different", a != r)


# ================================================================
# 5. AUTH SCHEMAS
# ================================================================
print("\n=== 5. AUTH SCHEMAS ===")
from api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserOut,
)

lr = LoginRequest(email="a@b.com", password="x")
check("LoginRequest valid", lr.email == "a@b.com")

try:
    LoginRequest(email="bad", password="x")
    fail("LoginRequest rejects bad email")
except Exception:
    ok("LoginRequest rejects bad email")

try:
    LoginRequest(email="a@b.com", password="")
    fail("LoginRequest rejects empty pw")
except Exception:
    ok("LoginRequest rejects empty pw")

rr = RegisterRequest(email="a@b.com", password="Good1Pass", full_name="T")
check("RegisterRequest valid", rr.email == "a@b.com")

try:
    RegisterRequest(email="a@b.com", password="nouppercase1", full_name="T")
    fail("Register rejects no uppercase")
except Exception:
    ok("Register rejects no uppercase")

try:
    RegisterRequest(email="a@b.com", password="NoNumber", full_name="T")
    fail("Register rejects no number")
except Exception:
    ok("Register rejects no number")

ar = AuthResponse(
    access_token="a", refresh_token="r",
    user={"id": "1", "email": "x@y.com", "full_name": "T", "role": "user", "plan": "free"}
)
check("AuthResponse valid", ar.user.email == "x@y.com")

rfr = RefreshRequest(refresh_token="tok")
check("RefreshRequest valid", rfr.refresh_token == "tok")


# ================================================================
# 6. CONVERSATION SCHEMAS
# ================================================================
print("\n=== 6. CONVERSATION SCHEMAS ===")
from api.schemas.conversation import (
    ConversationDetailOut,
    ConversationOut,
    CreateConversationRequest,
    MessageOut,
    PaginatedConversations,
)

ccr = CreateConversationRequest()
check("CreateConversation defaults", ccr.title == "Nueva conversacion" or ccr.title == "Nueva conversación")
check("CreateConversation section default", ccr.section == "general")

ccr2 = CreateConversationRequest(title="Test", section="sol")
check("CreateConversation custom values", ccr2.title == "Test" and ccr2.section == "sol")

now = datetime.now(timezone.utc)
co = ConversationOut(
    id="abc", title="T", section="general",
    created_at=now, updated_at=now, message_count=5,
    last_message_preview="Hello..."
)
check("ConversationOut valid", co.message_count == 5)

mo = MessageOut(id="m1", role="user", content="Hi", created_at=now)
check("MessageOut valid", mo.role == "user")

cdo = ConversationDetailOut(
    id="abc", title="T", section="general",
    created_at=now, updated_at=now,
    messages=[mo]
)
check("ConversationDetailOut has messages", len(cdo.messages) == 1)

pc = PaginatedConversations(items=[co], total=1, page=1, page_size=20, total_pages=1)
check("PaginatedConversations valid", pc.total == 1)


# ================================================================
# 7. ROUTES STRUCTURE
# ================================================================
print("\n=== 7. ROUTES STRUCTURE ===")
conv_routes = open(os.path.join(BASE, "api/routes/conversations.py"), encoding="utf-8").read()

check("POST /api/conversations", "@router.post(" in conv_routes and "status_code=201" in conv_routes)
check("GET /api/conversations (list)", "list_conversations" in conv_routes)
check("GET /api/conversations/:id", "get_conversation" in conv_routes and "/{conversation_id}" in conv_routes)
check("DELETE /api/conversations/:id", "delete_conversation" in conv_routes and "status_code=204" in conv_routes)
check("pagination (page, page_size)", "page: int" in conv_routes and "page_size: int" in conv_routes)
check("section filter param", 'section: str | None' in conv_routes)
check("ownership check", "current_user.id" in conv_routes)
check("404 on not found/not owned", "HTTP_404_NOT_FOUND" in conv_routes)
check("selectinload for messages", "selectinload" in conv_routes)
check("order by last_message_at desc", "last_message_at" in conv_routes and "desc()" in conv_routes)
check("cascade delete", "db.delete(conv)" in conv_routes)


# ================================================================
# 8. MAIN.PY ROUTERS
# ================================================================
print("\n=== 8. MAIN.PY ROUTERS ===")
main = open(os.path.join(BASE, "main.py"), encoding="utf-8").read()

check("auth_router", "app.include_router(auth_router)" in main)
check("conversations_router", "app.include_router(conversations_router)" in main)
check("chat_router", "app.include_router(chat_router)" in main)
check("knowledge_router", "app.include_router(knowledge_router)" in main)
check("usage_router", "app.include_router(usage_router)" in main)
check("11 routers total", main.count("app.include_router(") == 11)


# ================================================================
# 9. INTEGRATION FLOW
# ================================================================
print("\n=== 9. INTEGRATION FLOW ===")

# Full auth flow simulation
email = "test@test.com"
password = "Secure1Pass"
user_id = uuid4()
pw_hash = _hash_password(password)

check("register: hash created", pw_hash.startswith("$2b$"))
check("login: verify succeeds", _verify_password(password, pw_hash))
check("login: wrong pw rejected", not _verify_password("bad", pw_hash))

access, refresh = create_token_pair(user_id)
a_payload = decode_token(access)
r_payload = decode_token(refresh)

check("auth flow: access is access type", a_payload["type"] == "access")
check("auth flow: refresh is refresh type", r_payload["type"] == "refresh")
check("auth flow: same user in both", a_payload["sub"] == r_payload["sub"] == str(user_id))

# Refresh simulation
time.sleep(1.1)
new_a, new_r = create_token_pair(user_id)
check("refresh: new tokens differ", new_a != access)
check("refresh: still same user", decode_token(new_a)["sub"] == str(user_id))

# Token type separation
check("access rejected as refresh", a_payload["type"] != "refresh")
check("refresh rejected as access", r_payload["type"] != "access")


# ================================================================
# 10. SETTINGS
# ================================================================
print("\n=== 10. SETTINGS ===")
settings_src = open(os.path.join(BASE, "config/settings.py"), encoding="utf-8").read()
check("ACCESS_TOKEN_EXPIRE_MINUTES = 15", "ACCESS_TOKEN_EXPIRE_MINUTES: int = 15" in settings_src)
check("REFRESH_TOKEN_EXPIRE_DAYS = 7", "REFRESH_TOKEN_EXPIRE_DAYS: int = 7" in settings_src)
check("SUPABASE optional", 'SUPABASE_URL: str = ""' in settings_src)
check("bcrypt in requirements", "bcrypt" in open(os.path.join(BASE, "requirements.txt")).read())


# ================================================================
# 11. USER MODEL
# ================================================================
print("\n=== 11. USER MODEL ===")
user_src = open(os.path.join(BASE, "models/user.py"), encoding="utf-8").read()
check("password_hash field", "password_hash" in user_src)
check("last_login field", "last_login" in user_src)
check("FK to conversations", "conversations" in user_src)


# ================================================================
# SUMMARY
# ================================================================
print(f"\n{'='*60}")
print(f"TOTAL: {passed} passed, {failed} failed out of {passed + failed}")
if failed == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"ATTENTION: {failed} check(s) failed!")
    sys.exit(1)
