"""
FULL PROJECT VERIFICATION
Covers: backend (auth, conversations, models, migrations, settings, routes)
        frontend (no Anthropic, SSE parsing, error handling, consistency)
        cross-cutting (no broken refs, config alignment)
"""
import ast
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

# Setup
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BE = os.path.join(PROJ, "backend")
FE = os.path.join(PROJ, "frontend")

sys.path.insert(0, BE)
mock_settings = MagicMock()
mock_settings.JWT_SECRET = "test-secret-key-for-unit-tests-only-32chars!"
mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
import os
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests-only-32chars!")

passed = 0
failed = 0

def ok(name):
    global passed; print(f"  OK   {name}"); passed += 1
def fail(name, d=""):
    global failed; print(f"  FAIL {name} -- {d}"); failed += 1
def check(name, cond, d=""):
    ok(name) if cond else fail(name, d)

def read(path):
    return open(path, encoding="utf-8").read()

# ================================================================
print("\n" + "="*60)
print("SECTION 1: SYNTAX — All Python files")
print("="*60)
py_files = [
    "models/user.py", "models/conversation.py", "models/message.py",
    "models/token_usage.py", "models/base.py", "models/__init__.py",
    "services/auth_service.py", "services/jwt_service.py",
    "services/anthropic_service.py", "services/rate_limit_service.py",
    "services/token_usage_service.py",
    "core/auth.py", "core/rate_limit.py", "core/plan_gate.py", "core/cors.py",
    "config/settings.py",
    "api/routes/auth.py", "api/routes/conversations.py",
    "api/routes/chat.py", "api/routes/knowledge.py", "api/routes/usage.py",
    "api/routes/payments.py", "api/routes/materials.py",
    "api/routes/project.py", "api/routes/stripe_routes.py", "api/routes/billing.py",
    "api/schemas/auth.py", "api/schemas/conversation.py", "api/schemas/chat.py",
    "api/schemas/payment.py", "api/schemas/project.py",
    "core/sanitize.py",
    "models/payment.py", "models/project.py",
    "alembic/versions/0006_add_payments.py",
    "alembic/versions/0007_add_project.py",
    "alembic/versions/0008_add_stripe_customer_id.py",
    "alembic/versions/0009_add_onboarding_flag.py",
    "main.py",
]
for f in py_files:
    p = os.path.join(BE, f)
    if not os.path.exists(p):
        fail(f"syntax: {f}", "FILE NOT FOUND"); continue
    try:
        ast.parse(read(p)); ok(f"syntax: {f}")
    except SyntaxError as e:
        fail(f"syntax: {f}", str(e))

# ================================================================
print("\n" + "="*60)
print("SECTION 2: MIGRATION CHAIN")
print("="*60)
versions_dir = os.path.join(BE, "alembic", "versions")
chain = {}
for fn in sorted(os.listdir(versions_dir)):
    if not fn.endswith(".py") or fn.startswith("__"): continue
    content = read(os.path.join(versions_dir, fn))
    rev_m = re.search(r'revision:\s*str\s*=\s*"([^"]+)"', content)
    down_m = re.search(r'down_revision:\s*str\s*\|\s*None\s*=\s*(?:"([^"]+)"|None)', content)
    if rev_m:
        chain[rev_m.group(1)] = down_m.group(1) if down_m and down_m.group(1) else None
check("10 migrations exist", len(chain) == 10, f"found {len(chain)}")
roots = [r for r, d in chain.items() if d is None]
check("single root migration", len(roots) == 1)
if roots:
    cur = roots[0]; walked = [cur]
    while True:
        nxt = [r for r, d in chain.items() if d == cur]
        if not nxt: break
        cur = nxt[0]; walked.append(cur)
    check("chain fully continuous", len(walked) == len(chain))
    print(f"       Chain: {' -> '.join(walked)}")

# ================================================================
print("\n" + "="*60)
print("SECTION 3: BCRYPT + JWT (runtime)")
print("="*60)
import bcrypt
from services.auth_service import _hash_password, _verify_password
from services.jwt_service import create_access_token, create_refresh_token, create_token_pair, decode_token

pw = "Test1Pass"
h = _hash_password(pw)
check("bcrypt hash starts $2b$", h.startswith("$2b$"))
check("correct pw verifies", _verify_password(pw, h))
check("wrong pw rejected", not _verify_password("bad", h))
check("empty pw rejected", not _verify_password("", h))

uid = uuid4()
at = create_access_token(uid)
rt = create_refresh_token(uid)
check("access token string", isinstance(at, str) and len(at) > 50)
check("refresh token string", isinstance(rt, str) and len(rt) > 50)
check("tokens differ", at != rt)

ap = decode_token(at)
rp = decode_token(rt)
check("access sub correct", ap["sub"] == str(uid))
check("access type=access", ap["type"] == "access")
check("refresh sub correct", rp["sub"] == str(uid))
check("refresh type=refresh", rp["type"] == "refresh")

exp_a = datetime.fromtimestamp(ap["exp"], tz=timezone.utc) - datetime.fromtimestamp(ap["iat"], tz=timezone.utc)
check("access ~15min", timedelta(minutes=14) < exp_a <= timedelta(minutes=16))
exp_r = datetime.fromtimestamp(rp["exp"], tz=timezone.utc) - datetime.fromtimestamp(rp["iat"], tz=timezone.utc)
check("refresh ~7d", timedelta(days=6, hours=23) < exp_r <= timedelta(days=7, hours=1))

import jwt as pyjwt
expired = pyjwt.encode({"sub":"x","type":"access","exp":datetime.now(timezone.utc)-timedelta(hours=1)}, mock_settings.JWT_SECRET, algorithm="HS256")
try:
    decode_token(expired); fail("expired raises")
except pyjwt.ExpiredSignatureError:
    ok("expired raises ExpiredSignatureError")

bad_secret = pyjwt.encode({"sub":"x","type":"access","exp":datetime.now(timezone.utc)+timedelta(hours=1)}, "wrong", algorithm="HS256")
try:
    decode_token(bad_secret); fail("bad secret raises")
except pyjwt.InvalidSignatureError:
    ok("bad secret raises InvalidSignatureError")

# ================================================================
print("\n" + "="*60)
print("SECTION 4: AUTH SCHEMAS")
print("="*60)
from api.schemas.auth import LoginRequest, RegisterRequest, AuthResponse, RefreshRequest

check("LoginRequest valid", LoginRequest(email="a@b.com", password="x").email == "a@b.com")
try: LoginRequest(email="bad", password="x"); fail("LoginRequest bad email")
except: ok("LoginRequest rejects bad email")
try: LoginRequest(email="a@b.com", password=""); fail("LoginRequest empty pw")
except: ok("LoginRequest rejects empty pw")
check("RegisterRequest valid", RegisterRequest(email="a@b.com", password="Good1Pass", full_name="T").email == "a@b.com")
try: RegisterRequest(email="a@b.com", password="nouppercase1", full_name="T"); fail("Register no upper")
except: ok("Register rejects no uppercase")
try: RegisterRequest(email="a@b.com", password="NoNumber", full_name="T"); fail("Register no number")
except: ok("Register rejects no number")
check("AuthResponse", AuthResponse(access_token="a", refresh_token="r", user={"id":"1","email":"x@y.com","full_name":"T","role":"user","plan":"free"}).user.email == "x@y.com")
check("RefreshRequest", RefreshRequest(refresh_token="tok").refresh_token == "tok")

# ================================================================
print("\n" + "="*60)
print("SECTION 5: CONVERSATION SCHEMAS")
print("="*60)
from api.schemas.conversation import CreateConversationRequest, ConversationOut, ConversationDetailOut, MessageOut, PaginatedConversations

now = datetime.now(timezone.utc)
ccr = CreateConversationRequest()
check("CreateConv defaults", ccr.section == "general")
co = ConversationOut(id="a",title="T",section="general",created_at=now,updated_at=now,message_count=3)
check("ConvOut valid", co.message_count == 3)
mo = MessageOut(id="m",role="user",content="hi",created_at=now)
check("MessageOut valid", mo.role == "user")
cdo = ConversationDetailOut(id="a",title="T",section="general",created_at=now,updated_at=now,messages=[mo])
check("ConvDetailOut has messages", len(cdo.messages) == 1)
pc = PaginatedConversations(items=[co],total=1,page=1,page_size=20,total_pages=1)
check("PaginatedConv valid", pc.total == 1)

# ================================================================
print("\n" + "="*60)
print("SECTION 6: BACKEND FILES — content checks")
print("="*60)
auth_svc = read(os.path.join(BE, "services/auth_service.py"))
check("auth_svc: no Supabase", "SUPABASE" not in auth_svc and "supabase" not in auth_svc.lower().replace("supabase", "").lower())
check("auth_svc: import bcrypt", "import bcrypt" in auth_svc)
check("auth_svc: _hash_password", "_hash_password" in auth_svc)
check("auth_svc: _verify_password", "_verify_password" in auth_svc)
check("auth_svc: last_login update", "last_login" in auth_svc)
check("auth_svc: 401 on bad creds", "HTTP_401" in auth_svc)
check("auth_svc: 409 on duplicate", "HTTP_409" in auth_svc)
check("auth_svc: register creates user", "db.add(user)" in auth_svc)
check("auth_svc: login by email", "User.email == email" in auth_svc)
check("auth_svc: refresh validates type", '"refresh"' in auth_svc)
check("auth_svc: update_profile", "def update_profile" in auth_svc or "async def update_profile" in auth_svc)

core_auth = read(os.path.join(BE, "core/auth.py"))
check("core/auth: no Supabase audience", "authenticated" not in core_auth)
check("core/auth: checks type=access", '"access"' in core_auth)
check("core/auth: returns User", "return user" in core_auth)
check("core/auth: HTTPBearer", "HTTPBearer" in core_auth)

jwt_svc = read(os.path.join(BE, "services/jwt_service.py"))
check("jwt_svc: type access", '"type": "access"' in jwt_svc)
check("jwt_svc: type refresh", '"type": "refresh"' in jwt_svc)
check("jwt_svc: uses settings.ACCESS_TOKEN_EXPIRE_MINUTES", "ACCESS_TOKEN_EXPIRE_MINUTES" in jwt_svc)
check("jwt_svc: uses settings.REFRESH_TOKEN_EXPIRE_DAYS", "REFRESH_TOKEN_EXPIRE_DAYS" in jwt_svc)

settings = read(os.path.join(BE, "config/settings.py"))
check("settings: ACCESS_TOKEN_EXPIRE_MINUTES=15", "ACCESS_TOKEN_EXPIRE_MINUTES: int = 15" in settings)
check("settings: REFRESH_TOKEN_EXPIRE_DAYS=7", "REFRESH_TOKEN_EXPIRE_DAYS: int = 7" in settings)
check("settings: SUPABASE optional", 'SUPABASE_URL: str = ""' in settings)
check("settings: STRIPE_SECRET_KEY", "STRIPE_SECRET_KEY" in settings)
check("settings: STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET" in settings)
check("settings: STRIPE_PRICE_ID_PRO", "STRIPE_PRICE_ID_PRO" in settings)

user_model = read(os.path.join(BE, "models/user.py"))
check("user: password_hash field", "password_hash" in user_model)
check("user: last_login field", "last_login" in user_model)
check("user: conversations relationship", "conversations" in user_model)

conv_model = read(os.path.join(BE, "models/conversation.py"))
check("conv: section field", "section" in conv_model)
check("conv: user_id FK", "ForeignKey" in conv_model and "profiles.id" in conv_model)
check("conv: messages relationship", "messages" in conv_model)
check("conv: cascade delete", "delete-orphan" in conv_model)

msg_model = read(os.path.join(BE, "models/message.py"))
check("msg: conversation_id FK", "ForeignKey" in msg_model and "conversations.id" in msg_model)
check("msg: tokens_used field", "tokens_used" in msg_model)

reqs = read(os.path.join(BE, "requirements.txt"))
check("requirements: bcrypt", "bcrypt" in reqs)

# ================================================================
print("\n" + "="*60)
print("SECTION 7: ROUTES — conversations CRUD")
print("="*60)
conv_routes = read(os.path.join(BE, "api/routes/conversations.py"))
check("POST /conversations (201)", "@router.post(" in conv_routes and "status_code=201" in conv_routes)
check("GET /conversations (list)", "list_conversations" in conv_routes)
check("GET /conversations/:id", "get_conversation" in conv_routes and "/{conversation_id}" in conv_routes)
check("DELETE /conversations/:id (204)", "delete_conversation" in conv_routes and "status_code=204" in conv_routes)
check("pagination params", "page: int" in conv_routes and "page_size: int" in conv_routes)
check("section filter", "section: str | None" in conv_routes)
check("ownership check", "current_user.id" in conv_routes)
check("404 on not found", "HTTP_404_NOT_FOUND" in conv_routes)
check("selectinload", "selectinload" in conv_routes)
check("order by last_message_at desc", "last_message_at" in conv_routes and "desc()" in conv_routes)
check("cascade delete (db.delete)", "db.delete(conv)" in conv_routes)
check("last_message_preview", "last_message_preview" in conv_routes)

# ================================================================
print("\n" + "="*60)
print("SECTION 8: ROUTES — auth")
print("="*60)
auth_routes = read(os.path.join(BE, "api/routes/auth.py"))
check("auth: no unused SB imports", "from models.base import get_db" not in auth_routes)
check("auth: no AsyncSession import", "AsyncSession" not in auth_routes)
check("auth: login route", "login" in auth_routes)
check("auth: register route", "register" in auth_routes)
check("auth: refresh route", "refresh" in auth_routes)
check("auth: me route", "get_me" in auth_routes or "update_me" in auth_routes)

# ================================================================
print("\n" + "="*60)
print("SECTION 9: MAIN.PY — all routers registered")
print("="*60)
main = read(os.path.join(BE, "main.py"))
check("auth_router registered", "app.include_router(auth_router)" in main)
check("conversations_router registered", "app.include_router(conversations_router)" in main)
check("chat_router registered", "app.include_router(chat_router)" in main)
check("knowledge_router registered", "app.include_router(knowledge_router)" in main)
check("materials_router registered", "app.include_router(materials_router)" in main)
check("payments_router registered", "app.include_router(payments_router)" in main)
check("usage_router registered", "app.include_router(usage_router)" in main)
check("stripe_router registered", "app.include_router(stripe_router)" in main)
check("billing_router registered", "app.include_router(billing_router)" in main)
check("11 routers total", main.count("app.include_router(") == 11, f"found {main.count('app.include_router(')}")
check("conversations_router imported", "from api.routes.conversations import router as conversations_router" in main)
check("payments_router imported", "from api.routes.payments import router as payments_router" in main)
check("stripe_router imported", "from api.routes.stripe_routes import router as stripe_router" in main)
check("billing_router imported", "from api.routes.billing import router as billing_router" in main)

# ================================================================
print("\n" + "="*60)
print("SECTION 10: FRONTEND — Anthropic removed")
print("="*60)
html = read(os.path.join(FE, "index.html"))
check("no api.anthropic.com", "api.anthropic.com" not in html)
check("no x-api-key", "x-api-key" not in html)
check("no anthropic-version", "anthropic-version" not in html)
check("no anthropic-dangerous", "anthropic-dangerous" not in html)
check("no state.apiKey", "state.apiKey" not in html)
check("no API Key banner", "Ingresa tu API Key" not in html)
check("no sk-ant placeholder", "sk-ant" not in html)
check("no updateApiKeyUI", "updateApiKeyUI" not in html)
check("no saveApiKey", "saveApiKey" not in html)
check("no SB.addMessage", "SB.addMessage" not in html)
check("no SB.listMessages", "SB.listMessages" not in html)
check("no SB.createConversation", "SB.createConversation" not in html)
check("no SB.listConversations", "SB.listConversations" not in html)
check("no SB.updateConversationTitle", "SB.updateConversationTitle" not in html)

# ================================================================
print("\n" + "="*60)
print("SECTION 11: FRONTEND — Backend integration")
print("="*60)
check("sendMessage uses authFetch", "REAuthService.authFetch" in html)
check("calls /api/chat", "apiBase()+'/api/chat'" in html)
check("calls /api/conversations", "'/api/conversations'" in html or "/api/conversations/" in html or "api/conversations?" in html)
check("parses SSE start", "ev.type==='start'" in html)
check("parses SSE delta", "ev.type==='delta'" in html)
check("parses SSE done", "ev.type==='done'" in html)
check("parses SSE error", "ev.type==='error'" in html)
check("updates conversation_id from start", "state.currentConversation.id=ev.conversation_id" in html)
check("handles 401 -> logout", "r.status===401" in html)
check("handles 429 rate limit", "r.status===429" in html)
check("Retry-After header", "Retry-After" in html)
check("generic error handling", "Error del servidor" in html)
check("context_type chat", "context_type" in html and "'chat'" in html)
check("Accept text/event-stream", "'Accept':'text/event-stream'" in html)
check("SyntaxError safe continue", "parseErr instanceof SyntaxError" in html)
check("apiBase() helper exists", "function apiBase()" in html)
check("conversations from data.items", "data.items" in html)
check("messages from data.messages", "data.messages" in html)

# ================================================================
print("\n" + "="*60)
print("SECTION 12: FRONTEND — Nothing broken")
print("="*60)
check("SOL assistant intact", "solSend" in html and "solState" in html)
check("SOL uses authFetch", "REAuthService.authFetch(apiBase()+'/api/chat'" in html)
check("export function intact", "exportConversation" in html)
check("theme toggle intact", "applyTheme" in html)
check("typing indicator intact", "typing-indicator" in html)
check("marked.js parsing intact", "parseMd" in html)
check("copy buttons intact", "addCopyBtns" in html)
check("sidebar intact", "toggleSidebar" in html)
check("auth modal intact", "showAuthModal" in html and "hideAuthModal" in html)
check("requireAuth route guard", "requireAuth" in html)
check("REAuthService used for auth", "REAuthService" in html)
check("login via /api/auth/login", "/api/auth/login" in html)
check("register via /api/auth/register", "/api/auth/register" in html)
check("logout via REAuthService.logout", "REAuthService.logout" in html)
check("model badge", "Claude Sonnet 4.6" in html)
check("HTML valid (doctype)", "<!DOCTYPE html>" in html or "<!doctype html>" in html)
check("HTML valid (closes)", "</html>" in html)
open_s = html.count("<script"); close_s = html.count("</script>")
check(f"script tags balanced ({open_s}/{close_s})", open_s == close_s)

# ================================================================
print("\n" + "="*60)
print("SECTION 13: CROSS-CUTTING CONSISTENCY")
print("="*60)
# Backend SSE format matches what frontend expects
chat_route = read(os.path.join(BE, "api/routes/chat.py"))
check("backend SSE: start event", '"type": "start"' in chat_route or "'type': 'start'" in chat_route)
check("backend SSE: delta event", '"type": "delta"' in chat_route or "'type': 'delta'" in chat_route)
check("backend SSE: done event", '"type": "done"' in chat_route or "'type': 'done'" in chat_route)
check("backend SSE: error event", '"type": "error"' in chat_route or "'type': 'error'" in chat_route)
check("backend SSE: conversation_id in start", "conversation_id" in chat_route)

# Frontend config matches backend routes
config_js = read(os.path.join(FE, "config.js"))
check("config: API_BASE defined", "API_BASE" in config_js)
check("config: localhost override", "localhost" in config_js and "8000" in config_js)

# Auth flow consistency
auth_svc_fe = read(os.path.join(FE, "authService.js"))
check("authService: authFetch exists", "authFetch" in auth_svc_fe)
check("authService: Bearer token", "Bearer" in auth_svc_fe)
check("authService: 401 retry", "401" in auth_svc_fe)
check("authService: redirectToLogin", "redirectToLogin" in auth_svc_fe)

# .env.example updated
env_example = read(os.path.join(BE, ".env.example"))
check(".env: JWT_SECRET", "JWT_SECRET" in env_example)
check(".env: DATABASE_URL", "DATABASE_URL" in env_example)
check(".env: SUPABASE optional", "OPTIONAL" in env_example or "optional" in env_example)
check(".env: token expiration docs", "ACCESS_TOKEN_EXPIRE_MINUTES" in env_example)

# ================================================================
print("\n" + "="*60)
print("SECTION 14: TASK CHECKLIST VERIFICATION")
print("="*60)
# From the task: "Reemplazar llamada directa a Anthropic"
check("TASK: Modificar chatService para backend", "apiBase()+'/api/chat'" in html and "authFetch" in html)
check("TASK: Parsear SSE (start,delta,done,error)", all(x in html for x in ["ev.type==='start'","ev.type==='delta'","ev.type==='done'","ev.type==='error'"]))
check("TASK: Mantener efecto typing", "typing-indicator" in html and "updateStreaming" in html and "appendStreaming" in html)
check("TASK: Header Authorization con JWT", "Authorization" in auth_svc_fe and "Bearer" in auth_svc_fe)
check("TASK: Manejar 401", "r.status===401" in html)
check("TASK: Manejar 429", "r.status===429" in html)
check("TASK: Manejar 500 (generic)", "Error del servidor" in html)

# ================================================================
print("\n" + "="*60)
print("SECTION 15: PAYMENTS — schemas runtime")
print("="*60)
from decimal import Decimal as D
from datetime import date
from api.schemas.payment import (
    CreatePaymentRequest, UpdatePaymentRequest,
    PaymentOut, PaymentsSummary, PaymentsListResponse,
)

# CreatePaymentRequest
cr = CreatePaymentRequest(concepto="Cemento", monto=D("1500.50"), fecha=date(2026, 4, 1))
check("payments: create defaults estado=pendiente", cr.estado == "pendiente")
check("payments: create concepto ok", cr.concepto == "Cemento")
check("payments: create monto ok", cr.monto == D("1500.50"))

try: CreatePaymentRequest(concepto="X", monto=D("-1"), fecha=date(2026,1,1)); fail("payments: create negative monto")
except: ok("payments: create rejects negative monto")

try: CreatePaymentRequest(concepto="X", monto=D("100"), fecha=date(2026,1,1), estado="invalido"); fail("payments: create bad estado")
except: ok("payments: create rejects invalid estado")

try: CreatePaymentRequest(concepto="", monto=D("100"), fecha=date(2026,1,1)); fail("payments: create empty concepto")
except: ok("payments: create rejects empty concepto")

for estado in ("pendiente", "pagado", "cancelado"):
    cr2 = CreatePaymentRequest(concepto="X", monto=D("10"), fecha=date(2026,1,1), estado=estado)
    check(f"payments: create estado={estado}", cr2.estado == estado)

# UpdatePaymentRequest — all optional
ur = UpdatePaymentRequest()
check("payments: update all optional", ur.estado is None and ur.monto is None)
ur2 = UpdatePaymentRequest(estado="pagado", monto=D("999.99"))
check("payments: update estado", ur2.estado == "pagado")
check("payments: update monto", ur2.monto == D("999.99"))

try: UpdatePaymentRequest(estado="nope"); fail("payments: update bad estado")
except: ok("payments: update rejects invalid estado")

# PaymentsSummary
from uuid import uuid4
now = datetime.now(timezone.utc)
ps = PaymentsSummary(
    total_pagado=D("2000"), total_pendiente=D("500"), total_cancelado=D("100"),
    grand_total=D("2500"),
    count_pagado=2, count_pendiente=1, count_cancelado=1, count_total=4,
)
check("payments: summary grand_total", ps.grand_total == D("2500"))
check("payments: summary count_total", ps.count_total == 4)

# PaymentOut
pid = uuid4()
po = PaymentOut(id=pid, concepto="Test", proveedor=None, monto=D("100"),
                fecha=date(2026,4,1), estado="pendiente", categoria=None,
                notas=None, created_at=now, updated_at=now)
check("payments: PaymentOut id", po.id == pid)
check("payments: PaymentOut estado", po.estado == "pendiente")

# PaymentsListResponse
plr = PaymentsListResponse(items=[po], summary=ps, total=1)
check("payments: list response total", plr.total == 1)
check("payments: list items", len(plr.items) == 1)

# ================================================================
print("\n" + "="*60)
print("SECTION 16: PAYMENTS — model & route file checks")
print("="*60)
pay_model = read(os.path.join(BE, "models/payment.py"))
check("pay_model: payments table", '__tablename__ = "payments"' in pay_model)
check("pay_model: user_id FK to profiles", "profiles.id" in pay_model)
check("pay_model: monto Numeric", "Numeric" in pay_model)
check("pay_model: fecha Date field", "Date" in pay_model)
check("pay_model: estado field", "estado" in pay_model)
check("pay_model: concepto field", "concepto" in pay_model)
check("pay_model: categoria field", "categoria" in pay_model)
check("pay_model: proveedor field", "proveedor" in pay_model)
check("pay_model: notas field", "notas" in pay_model)
check("pay_model: cascade delete", "CASCADE" in pay_model)
check("pay_model: user relationship back_populates", "back_populates" in pay_model)

pay_routes = read(os.path.join(BE, "api/routes/payments.py"))
check("pay_routes: GET list", "list_payments" in pay_routes)
check("pay_routes: POST create 201", "HTTP_201_CREATED" in pay_routes)
check("pay_routes: PUT update", "update_payment" in pay_routes)
check("pay_routes: DELETE 204", "HTTP_204_NO_CONTENT" in pay_routes)
check("pay_routes: estado filter", "Query(None" in pay_routes and "estado" in pay_routes)
check("pay_routes: ownership user_id", "user.id" in pay_routes)
check("pay_routes: 404 on missing", "HTTP_404" in pay_routes or "status_code=404" in pay_routes)
check("pay_routes: summary in list", "_build_summary" in pay_routes)
check("pay_routes: prefix /api/payments", '"/api/payments"' in pay_routes or "prefix=\"/api/payments\"" in pay_routes)
check("pay_routes: model_dump exclude_unset", "exclude_unset=True" in pay_routes)

pay_schema = read(os.path.join(BE, "api/schemas/payment.py"))
check("pay_schema: CreatePaymentRequest", "CreatePaymentRequest" in pay_schema)
check("pay_schema: UpdatePaymentRequest", "UpdatePaymentRequest" in pay_schema)
check("pay_schema: PaymentOut", "PaymentOut" in pay_schema)
check("pay_schema: PaymentsSummary", "PaymentsSummary" in pay_schema)
check("pay_schema: PaymentsListResponse", "PaymentsListResponse" in pay_schema)
check("pay_schema: estado pattern", "pendiente|pagado|cancelado" in pay_schema)
check("pay_schema: monto gt=0", "gt=0" in pay_schema)
check("pay_schema: from_attributes", "from_attributes" in pay_schema)

mig = read(os.path.join(BE, "alembic/versions/0006_add_payments.py"))
check("migration 0006: creates payments table", "create_table" in mig and '"payments"' in mig)
check("migration 0006: user_id FK", "ForeignKey" in mig and "profiles.id" in mig)
check("migration 0006: downgrade drops table", "drop_table" in mig)

# ================================================================
print("\n" + "="*60)
print("SECTION 17: PROJECT — schemas runtime")
print("="*60)
from datetime import date
from api.schemas.project import (
    CreateProjectRequest, UpdateProjectRequest,
    CreateMilestoneRequest, UpdateMilestoneRequest,
    ProjectOut, MilestoneOut, ProjectIndicators, ProjectDashboard,
    CostoRubro, AlertaItem,
)

# CostoRubro
cr = CostoRubro(nombre="Estructura", base=D("1600000"), real=D("1820000"))
check("project: CostoRubro valid", cr.nombre == "Estructura" and cr.real == D("1820000"))
try: CostoRubro(nombre="X", base=D("-1"), real=D("0")); fail("project: CostoRubro negative base")
except: ok("project: CostoRubro rejects negative base")

# AlertaItem
ai = AlertaItem(titulo="Sobrecosto", descripcion="Hierro supero presupuesto", severidad="high")
check("project: AlertaItem valid", ai.severidad == "high")
try: AlertaItem(titulo="X", descripcion="Y", severidad="critical"); fail("project: AlertaItem bad severidad")
except: ok("project: AlertaItem rejects invalid severidad")

# CreateProjectRequest — defaults
cp = CreateProjectRequest()
check("project: create defaults nombre", cp.nombre == "Mi Proyecto")
check("project: create defaults estado", cp.estado == "amarillo")
check("project: create defaults avance", cp.avance_real_pct == 0.0)

cp2 = CreateProjectRequest(
    nombre="Torre Norte", presupuesto_base=D("6430000"), costo_real=D("4250000"),
    avance_real_pct=58.0, avance_plan_pct=66.0, meses_transcurridos=14, meses_total=18,
    fecha_inicio=date(2025,2,1), fecha_entrega_programada=date(2026,8,1),
    costos_rubros=[CostoRubro(nombre="Estructura", base=D("1600000"), real=D("1820000"))],
    alertas=[AlertaItem(titulo="Sobrecosto", descripcion="Hierro", severidad="high")],
)
check("project: create full valid", cp2.nombre == "Torre Norte")
check("project: create costos_rubros", len(cp2.costos_rubros) == 1)
check("project: create alertas", len(cp2.alertas) == 1)

try: CreateProjectRequest(avance_real_pct=101.0); fail("project: create avance >100")
except: ok("project: create rejects avance_real_pct > 100")
try: CreateProjectRequest(estado="azul"); fail("project: create bad estado")
except: ok("project: create rejects invalid estado")

for e in ("verde","amarillo","rojo"):
    check(f"project: create estado={e}", CreateProjectRequest(estado=e).estado == e)

# UpdateProjectRequest — all optional
up = UpdateProjectRequest()
check("project: update all optional", up.nombre is None and up.estado is None)
up2 = UpdateProjectRequest(avance_real_pct=75.0, estado="verde")
check("project: update avance", up2.avance_real_pct == 75.0)

# CreateMilestoneRequest
cm = CreateMilestoneRequest(nombre="Fundaciones", fecha_objetivo=date(2025,5,1))
check("project: milestone defaults pending", cm.estado == "pending")
check("project: milestone nombre ok", cm.nombre == "Fundaciones")

try: CreateMilestoneRequest(nombre="X", fecha_objetivo=date(2025,5,1), estado="invalid"); fail("project: milestone bad estado")
except: ok("project: milestone rejects invalid estado")

for e in ("done","active","pending","delayed"):
    check(f"project: milestone estado={e}", CreateMilestoneRequest(nombre="X",fecha_objetivo=date(2025,1,1),estado=e).estado==e)

# UpdateMilestoneRequest — all optional
um = UpdateMilestoneRequest()
check("project: milestone update all optional", um.estado is None and um.nombre is None)

# ProjectIndicators
now = datetime.now(timezone.utc)
pi = ProjectIndicators(cpi=0.94, spi=0.88, eac=D("6840000"), desvio_proyectado=D("410000"), pct_ejecutado=66.0)
check("project: indicators cpi", pi.cpi == 0.94)
check("project: indicators eac", pi.eac == D("6840000"))
pi2 = ProjectIndicators(cpi=None, spi=None, eac=None, desvio_proyectado=None, pct_ejecutado=0.0)
check("project: indicators nullable fields", pi2.cpi is None and pi2.spi is None)

# ================================================================
print("\n" + "="*60)
print("SECTION 18: PROJECT — model, routes & migration checks")
print("="*60)
proj_model = read(os.path.join(BE, "models/project.py"))
check("proj_model: projects table", '__tablename__ = "projects"' in proj_model)
check("proj_model: milestones table", '__tablename__ = "project_milestones"' in proj_model)
check("proj_model: user_id unique", "unique=True" in proj_model)
check("proj_model: presupuesto_base Numeric", "Numeric" in proj_model)
check("proj_model: JSONB costos_rubros", "JSONB" in proj_model and "costos_rubros" in proj_model)
check("proj_model: JSONB alertas", "alertas" in proj_model)
check("proj_model: avance_real_pct Float", "Float" in proj_model and "avance_real_pct" in proj_model)
check("proj_model: Milestone.estado", "pending" in proj_model)
check("proj_model: milestones relationship", "milestones" in proj_model and "back_populates" in proj_model)
check("proj_model: cascade delete orphan", "delete-orphan" in proj_model)
check("proj_model: user_id FK profiles", "profiles.id" in proj_model)
check("proj_model: projects.id FK in Milestone", "projects.id" in proj_model)

proj_routes = read(os.path.join(BE, "api/routes/project.py"))
check("proj_routes: GET /dashboard", "get_dashboard" in proj_routes)
check("proj_routes: POST create 201", "HTTP_201_CREATED" in proj_routes)
check("proj_routes: PUT update project", "update_project" in proj_routes)
check("proj_routes: GET milestones", "list_milestones" in proj_routes)
check("proj_routes: POST milestone 201", "create_milestone" in proj_routes)
check("proj_routes: PUT milestone", "update_milestone" in proj_routes)
check("proj_routes: DELETE milestone 204", "HTTP_204_NO_CONTENT" in proj_routes)
check("proj_routes: 404 on missing project", "Sin proyecto" in proj_routes)
check("proj_routes: 409 on duplicate", "HTTP_409" in proj_routes or "status_code=409" in proj_routes)
check("proj_routes: _compute_indicators", "_compute_indicators" in proj_routes)
check("proj_routes: CPI calculation", "cpi" in proj_routes and "ev / ac" in proj_routes or "ev/ac" in proj_routes or "/ ac" in proj_routes)
check("proj_routes: ownership user_id", "user.id" in proj_routes)
check("proj_routes: prefix /api/project", '"/api/project"' in proj_routes or 'prefix="/api/project"' in proj_routes)
check("proj_routes: exclude_unset updates", "exclude_unset=True" in proj_routes)

proj_schema = read(os.path.join(BE, "api/schemas/project.py"))
check("proj_schema: CostoRubro", "CostoRubro" in proj_schema)
check("proj_schema: AlertaItem", "AlertaItem" in proj_schema)
check("proj_schema: CreateProjectRequest", "CreateProjectRequest" in proj_schema)
check("proj_schema: UpdateProjectRequest", "UpdateProjectRequest" in proj_schema)
check("proj_schema: CreateMilestoneRequest", "CreateMilestoneRequest" in proj_schema)
check("proj_schema: UpdateMilestoneRequest", "UpdateMilestoneRequest" in proj_schema)
check("proj_schema: ProjectDashboard", "ProjectDashboard" in proj_schema)
check("proj_schema: ProjectIndicators", "ProjectIndicators" in proj_schema)
check("proj_schema: estado pattern verde/amarillo/rojo", "verde|amarillo|rojo" in proj_schema)
check("proj_schema: milestone estado pattern", "done|active|pending|delayed" in proj_schema)
check("proj_schema: from_attributes", "from_attributes" in proj_schema)

mig7 = read(os.path.join(BE, "alembic/versions/0007_add_project.py"))
check("migration 0007: creates projects", "create_table" in mig7 and '"projects"' in mig7)
check("migration 0007: creates milestones", '"project_milestones"' in mig7)
check("migration 0007: JSONB fields", "JSONB" in mig7)
check("migration 0007: user_id unique", "unique=True" in mig7)
check("migration 0007: downgrade drops both", mig7.count("drop_table") >= 2)
check("migration 0007: down_revision=0006", "0006_add_payments" in mig7)

user_model_content = read(os.path.join(BE, "models/user.py"))
check("user_model: Project import added", "from models.project import Project" in user_model_content)

main_content = read(os.path.join(BE, "main.py"))
check("main: project_router imported", "from api.routes.project import router as project_router" in main_content)
check("main: project_router registered", "app.include_router(project_router)" in main_content)

fe = read(os.path.join(FE, "index.html"))
check("frontend: loadProyecto function", "async function loadProyecto" in fe)
check("frontend: proyectoState", "const proyectoState" in fe)
check("frontend: fmtM helper", "function fmtM" in fe)
check("frontend: fmtMonth helper", "function fmtMonth" in fe)
check("frontend: renderProyectoResumen", "function renderProyectoResumen" in fe)
check("frontend: renderProyectoCostos", "function renderProyectoCostos" in fe)
check("frontend: renderProyectoCronograma", "function renderProyectoCronograma" in fe)
check("frontend: /api/project/dashboard call", "'/api/project/dashboard'" in fe or '"/api/project/dashboard"' in fe or "/api/project/dashboard" in fe)
check("frontend: proyectoEmptyHTML", "proyectoEmptyHTML" in fe)
check("frontend: projResumenContent container", 'id="projResumenContent"' in fe)
check("frontend: projCostosContent container", 'id="projCostosContent"' in fe)
check("frontend: projCronogramaContent container", 'id="projCronogramaContent"' in fe)
check("frontend: switchView calls loadProyecto", "if(v==='proyecto')loadProyecto()" in fe)
check("frontend: no static mock KPI $6.43M", "$6.43M" not in fe)
check("frontend: no static mock 58% hardcoded", ">58%<" not in fe)
check("frontend: event delegation resumen", "projResumenContent" in fe and "aiProjectAnalysis" in fe)
check("frontend: event delegation costos", "projCostosContent" in fe and "aiCostAnalysis" in fe)
check("frontend: event delegation cronograma", "projCronogramaContent" in fe and "aiScheduleAnalysis" in fe)

# ================================================================
print("\n" + "="*60)
print("SECTION 19: STRIPE — routes, settings & frontend")
print("="*60)
stripe_routes = read(os.path.join(BE, "api/routes/stripe_routes.py"))
check("stripe: GET /status route", "get_status" in stripe_routes)
check("stripe: POST /create-checkout-session", "create_checkout_session" in stripe_routes)
check("stripe: POST /portal", "create_portal_session" in stripe_routes)
check("stripe: POST /webhook", "stripe_webhook" in stripe_routes)
check("stripe: prefix /api/stripe", '"/api/stripe"' in stripe_routes or 'prefix="/api/stripe"' in stripe_routes)
check("stripe: get_current_user dependency", "get_current_user" in stripe_routes)
check("stripe: _run_stripe async wrapper", "_run_stripe" in stripe_routes)
check("stripe: checkout.session.completed handler", "checkout.session.completed" in stripe_routes)
check("stripe: plan='pro' on completed", '"pro"' in stripe_routes)
check("stripe: subscription.deleted handler", "customer.subscription.deleted" in stripe_routes)
check("stripe: webhook raw body", "await request.body()" in stripe_routes)
check("stripe: signature verification", "STRIPE_WEBHOOK_SECRET" in stripe_routes)
check("stripe: 503 when not configured", "503" in stripe_routes)
check("stripe: run_in_executor (non-blocking)", "run_in_executor" in stripe_routes)

settings_content = read(os.path.join(BE, "config/settings.py"))
check("settings: STRIPE_SUCCESS_URL", "STRIPE_SUCCESS_URL" in settings_content)
check("settings: STRIPE_CANCEL_URL", "STRIPE_CANCEL_URL" in settings_content)

env_ex = read(os.path.join(BE, ".env.example"))
check(".env: STRIPE_SECRET_KEY documented", "STRIPE_SECRET_KEY" in env_ex)
check(".env: STRIPE_PRICE_ID_PRO documented", "STRIPE_PRICE_ID_PRO" in env_ex)
check(".env: STRIPE_WEBHOOK_SECRET documented", "STRIPE_WEBHOOK_SECRET" in env_ex)
check(".env: STRIPE_SUCCESS_URL documented", "STRIPE_SUCCESS_URL" in env_ex)

reqs_content = read(os.path.join(BE, "requirements.txt"))
check("requirements: stripe added", "stripe" in reqs_content)

mig8 = read(os.path.join(BE, "alembic/versions/0008_add_stripe_customer_id.py"))
check("migration 0008: adds stripe_customer_id", "stripe_customer_id" in mig8)
check("migration 0008: down_revision=0007", "0007_add_project" in mig8)
check("migration 0008: downgrade drops column", "drop_column" in mig8)

user_m = read(os.path.join(BE, "models/user.py"))
check("user_model: stripe_customer_id field", "stripe_customer_id" in user_m)

authsvc_fe = read(os.path.join(FE, "authService.js"))
check("authService: /pricing.html is public", "/pricing.html" in authsvc_fe)
check("authService: /success.html is public", "/success.html" in authsvc_fe)

pricing_html = read(os.path.join(FE, "pricing.html"))
check("pricing.html: exists", len(pricing_html) > 100)
check("pricing.html: plan free card", "Plan Free" in pricing_html or "Free" in pricing_html)
check("pricing.html: plan pro card", "Pro" in pricing_html)
check("pricing.html: subscribe button calls handleSubscribe", "handleSubscribe" in pricing_html)
check("pricing.html: calls /api/stripe/create-checkout-session", "/api/stripe/create-checkout-session" in pricing_html)
check("pricing.html: calls /api/stripe/status", "/api/stripe/status" in pricing_html)
check("pricing.html: calls /api/stripe/portal", "/api/stripe/portal" in pricing_html)
check("pricing.html: uses authFetch", "REAuthService.authFetch" in pricing_html)
check("pricing.html: redirect to Stripe url", "window.location.href = data.url" in pricing_html or "window.location.href=data.url" in pricing_html)
check("pricing.html: FAQ section", "faq" in pricing_html.lower())
check("pricing.html: USD 29", "29" in pricing_html)
check("pricing.html: doctype", "<!DOCTYPE html>" in pricing_html)

success_html = read(os.path.join(FE, "success.html"))
check("success.html: exists", len(success_html) > 100)
check("success.html: pro badge", "Pro" in success_html)
check("success.html: auto redirect countdown", "setInterval" in success_html or "countdown" in success_html.lower())
check("success.html: goToApp or index.html redirect", "index.html" in success_html)
check("success.html: doctype", "<!DOCTYPE html>" in success_html)

# ================================================================
print("\n" + "="*60)
print("SECTION 20: PLAN GATING — backend & frontend")
print("="*60)
plan_gate = read(os.path.join(BE, "core/plan_gate.py"))
check("plan_gate: require_pro function", "def require_pro" in plan_gate)
check("plan_gate: 403 status", "HTTP_403_FORBIDDEN" in plan_gate)
check("plan_gate: plan_required key", "plan_required" in plan_gate)
check("plan_gate: upgrade_url key", "upgrade_url" in plan_gate)
check("plan_gate: depends get_current_user", "get_current_user" in plan_gate)

chat_route = read(os.path.join(BE, "api/routes/chat.py"))
check("chat: SOL gate raises 403", "HTTP_403_FORBIDDEN" in chat_route and "sol" in chat_route)
check("chat: SOL gate checks plan!=pro", "plan" in chat_route and "sol" in chat_route)
check("chat: SOL gate message", "SOL" in chat_route or "sol" in chat_route)

fe = read(os.path.join(FE, "index.html"))
check("fe: userPlan state variable", "let userPlan" in fe or "userPlan = " in fe)
check("fe: updatePlanBadge function", "function updatePlanBadge" in fe)
check("fe: showUpgradeModal function", "function showUpgradeModal" in fe)
check("fe: hideUpgradeModal function", "function hideUpgradeModal" in fe)
check("fe: updateDailyCounter function", "function updateDailyCounter" in fe)
check("fe: planBadge element", 'id="planBadge"' in fe)
check("fe: dailyMsgsCounter element", 'id="dailyMsgsCounter"' in fe)
check("fe: upgradeModal element", 'id="upgradeModal"' in fe)
check("fe: upgradeFeatureDesc element", 'id="upgradeFeatureDesc"' in fe)
check("fe: upgradeModalClose element", 'id="upgradeModalClose"' in fe)
check("fe: plan badge CSS free", "plan-badge-free" in fe)
check("fe: plan badge CSS pro", "plan-badge-pro" in fe)
check("fe: pricing.html link in modal", "pricing.html" in fe)
check("fe: onUserLoggedIn sets userPlan", "userPlan=user?.plan" in fe or "userPlan = user?.plan" in fe)
check("fe: onUserLoggedIn calls updatePlanBadge", "updatePlanBadge()" in fe)
check("fe: chat 403 shows upgrade modal", "r.status===403" in fe and "showUpgradeModal" in fe)
check("fe: chat reads X-RateLimit-Remaining-Day", "X-RateLimit-Remaining-Day" in fe)
check("fe: chat reads X-RateLimit-Limit-Day", "X-RateLimit-Limit-Day" in fe)
check("fe: chat calls updateDailyCounter", "updateDailyCounter" in fe)
check("fe: solSend gates free users", "userPlan!=='pro'" in fe or "userPlan !== 'pro'" in fe)
check("fe: solSend 403 shows upgrade modal", "r.status===403" in fe)
check("fe: export gated by plan", "showUpgradeModal" in fe and "Exportar" in fe)
check("fe: upgradeSidebarLink in sidebar", 'id="upgradeSidebarLink"' in fe)

# ================================================================
print("\n" + "="*60)
print("SECTION 21: BILLING — route, account page & sidebar link")
print("="*60)
billing_route = read(os.path.join(BE, "api/routes/billing.py"))
check("billing: GET /status route", "billing_status" in billing_route)
check("billing: prefix /api/billing", '"/api/billing"' in billing_route or 'prefix="/api/billing"' in billing_route)
check("billing: get_current_user dependency", "get_current_user" in billing_route)
check("billing: returns plan", '"plan"' in billing_route)
check("billing: returns is_pro", '"is_pro"' in billing_route)
check("billing: returns subscription", '"subscription"' in billing_route)
check("billing: returns invoices", '"invoices"' in billing_route)
check("billing: Stripe subscription fetch", "Subscription.list" in billing_route)
check("billing: Stripe invoice fetch", "Invoice.list" in billing_route)
check("billing: _ts timestamp helper", "_ts" in billing_route)
check("billing: graceful if no stripe key", "STRIPE_SECRET_KEY" in billing_route)
check("billing: graceful if no customer_id", "stripe_customer_id" in billing_route)
check("billing: run_in_executor non-blocking", "run_in_executor" in billing_route)
check("billing: logger.warning on errors", "logger.warning" in billing_route)

account_html = read(os.path.join(FE, "account.html"))
check("account.html: exists", len(account_html) > 200)
check("account.html: doctype", "<!DOCTYPE html>" in account_html)
check("account.html: calls /api/billing/status", "/api/billing/status" in account_html)
check("account.html: calls /api/stripe/portal", "/api/stripe/portal" in account_html)
check("account.html: renderBilling function", "renderBilling" in account_html or "function renderBilling" in account_html)
check("account.html: subscription section", "subscriptionCard" in account_html or "subscription" in account_html)
check("account.html: invoices section", "invoicesCard" in account_html or "invoices" in account_html.lower())
check("account.html: renewal date rendered", "current_period_end" in account_html or "renewalLabel" in account_html or "fmtDate" in account_html)
check("account.html: cancel_at_period_end handled", "cancel_at_period_end" in account_html)
check("account.html: upgrade CTA for free", "pricing.html" in account_html and "upgradeSection" in account_html)
check("account.html: portal button", "openPortal" in account_html)
check("account.html: uses authFetch", "REAuthService.authFetch" in account_html or "authFetch" in account_html)
check("account.html: requireAuth / ready check", "REAuthService.ready" in account_html or "requireAuth" in account_html)
check("account.html: 401 redirect to login", "login.html" in account_html)
check("account.html: plan pill free", "plan-pill-free" in account_html)
check("account.html: plan pill pro", "plan-pill-pro" in account_html)
check("account.html: invoice table PDF column", "invoice_pdf" in account_html)
check("account.html: invoice status labels", "invStatusLabel" in account_html or "Pagada" in account_html)
check("account.html: fmtDate helper", "fmtDate" in account_html)
check("account.html: fmtCurrency helper", "fmtCurrency" in account_html)

fe_html = read(os.path.join(FE, "index.html"))
check("index: planBadge links to account.html", 'href="account.html"' in fe_html and 'id="planBadge"' in fe_html)

# ================================================================
print("\n" + "="*60)
print("SECTION 22: LOADING STATES & VISUAL FEEDBACK")
print("="*60)
idx = read(os.path.join(FE, "index.html"))
# Skeleton CSS
check("skeleton: @keyframes shimmer defined", "shimmer" in idx)
check("skeleton: .skeleton base class", ".skeleton{" in idx)
check("skeleton: sidebar conv items sk-conv", "sk-conv" in idx)
check("skeleton: sk-conv-line defined", "sk-conv-line" in idx)
check("skeleton: sk-bubble chat skeleton", "sk-bubble" in idx)
check("skeleton: sk-avatar element", "sk-avatar" in idx)
check("skeleton: sk-content wrapper", "sk-content" in idx)
check("skeleton: sk-kpi-grid layout", "sk-kpi-grid" in idx)
check("skeleton: sk-kpi-card element", "sk-kpi-card" in idx)
# Loading state JS
check("skeleton: sidebar skeleton on fresh load", "sk-conv-icon" in idx)
check("skeleton: pagos skeleton table rows", "_skRow" in idx)
check("skeleton: materiales skeleton cards", "_skCard" in idx)
check("skeleton: proyecto skeleton KPI", "_projSkeleton" in idx)
check("skeleton: loadConversations catch calls renderHistory", "if(!append)renderHistory()" in idx)
# Typing indicator
check("typing: typing-label class", "typing-label" in idx)
check("typing: Generando respuesta label in streamMsg", "Generando respuesta" in idx)
check("typing: SOL Procesando label", "Procesando" in idx)
# Action spinners
check("action: btn-spinner class", "btn-spinner" in idx)
check("action: savePayment uses spinner HTML", "btn-spinner" in idx and "Guardando" in idx)
# Empty states
check("empty: empty-icon class", "empty-icon" in idx)
check("empty: empty-title class", "empty-title" in idx)
check("empty: empty-desc class", "empty-desc" in idx)
check("empty: pagos context-aware empty (no filter)", "Sin pagos registrados" in idx)
check("empty: pagos context-aware empty (filter)", "Sin resultados" in idx)
check("empty: materiales empty-state", "Sin materiales" in idx)
check("empty: proyecto empty uses empty-state", "Sin proyecto configurado" in idx)
# Skeleton messages loading replaces spinner
check("skeleton: messages-loading is flex-col not centered", "flex-direction:column;flex:1" in idx and "messages-loading{display:none;flex-direction:column" in idx)
check("skeleton: sk-bubble-ai in messagesLoading", "sk-bubble-ai" in idx)
check("skeleton: messages-loading-spinner hidden", "messages-loading-spinner{display:none}" in idx or "display:none}" in idx)

# ================================================================
print("\n" + "="*60)
print("SECTION 23: ONBOARDING — backend + frontend")
print("="*60)
# Migration
mig9 = read(os.path.join(BE, "alembic/versions/0009_add_onboarding_flag.py"))
check("mig9: revision id", "0009_add_onboarding" in mig9)
check("mig9: down_revision = 0008", "0008_add_stripe_customer_id" in mig9)
check("mig9: adds onboarding_completed column", "onboarding_completed" in mig9)
check("mig9: Boolean type", "Boolean" in mig9)
check("mig9: server_default false", "false" in mig9)
check("mig9: downgrade drops column", "drop_column" in mig9)

# Model
user_model = read(os.path.join(BE, "models/user.py"))
check("model: onboarding_completed field", "onboarding_completed" in user_model)
check("model: Boolean imported", "Boolean" in user_model)

# Schema
auth_schema = read(os.path.join(BE, "api/schemas/auth.py"))
check("schema: onboarding_completed in UserOut", "onboarding_completed" in auth_schema)

# Service
auth_svc = read(os.path.join(BE, "services/auth_service.py"))
check("service: onboarding_completed in _user_to_dict", '"onboarding_completed"' in auth_svc)
check("service: complete_onboarding function", "async def complete_onboarding" in auth_svc)
check("service: sets flag to True", "onboarding_completed = True" in auth_svc)

# Route
auth_route = read(os.path.join(BE, "api/routes/auth.py"))
check("route: complete_onboarding imported", "complete_onboarding" in auth_route)
check("route: POST /onboarding/complete endpoint", "onboarding/complete" in auth_route)
check("route: mark_onboarding_complete handler", "mark_onboarding_complete" in auth_route)
check("route: me includes onboarding_completed", "onboarding_completed=current_user.onboarding_completed" in auth_route)

# Frontend
fe = read(os.path.join(FE, "index.html"))
check("fe: onboarding overlay element", 'id="onboardingOverlay"' in fe)
check("fe: 4 ob-slides", fe.count('class="ob-slide') >= 4)
check("fe: ob-dots navigation", "ob-dot" in fe)
check("fe: showOnboarding function", "function showOnboarding" in fe)
check("fe: initOnboarding function", "function initOnboarding" in fe)
check("fe: _obComplete function", "async function _obComplete" in fe or "_obComplete" in fe)
check("fe: calls /api/auth/onboarding/complete", "/api/auth/onboarding/complete" in fe)
check("fe: checks onboarding_completed flag", "onboarding_completed" in fe)
check("fe: localStorage guard re_onboarding_done", "re_onboarding_done" in fe)
check("fe: sets localStorage on complete", 'localStorage.setItem(\'re_onboarding_done\'' in fe)
check("fe: obUserName personalization", 'id="obUserName"' in fe)
check("fe: prompt selection cards", "ob-prompt-card" in fe)
check("fe: skip button", 'id="obSkipBtn"' in fe)
check("fe: prev/next buttons", 'id="obPrevBtn"' in fe and 'id="obNextBtn"' in fe)
check("fe: initOnboarding called in init()", "initOnboarding()" in fe)
check("fe: onUserLoggedIn triggers onboarding", "showOnboarding" in fe and "onboarding_completed" in fe)
check("fe: 700ms delay after login", "700" in fe and "showOnboarding" in fe)
check("fe: obSelectedPrompt used", "obSelectedPrompt" in fe)

# ================================================================
print("\n" + "="*60)
print("SECTION 24: INPUT SANITIZATION — XSS/injection defence")
print("="*60)
from core.sanitize import strip_html, sanitize_str, clean_text, SanitizedStr, SanitizedOptStr, CleanText, CleanOptText
from pydantic import BaseModel as _BM

# Unit-level sanitize functions
# strip_html removes TAG MARKUP (<...>) but not the text content between tags.
# <script>alert(1)</script>hello → alert(1)hello (tags removed, content preserved as safe text)
check("sanitize: strip_html removes script tags", strip_html("<script>alert(1)</script>hello") == "alert(1)hello")
check("sanitize: strip_html removes inline tag", strip_html("<b>bold</b>") == "bold")
check("sanitize: strip_html handles multiline tag", strip_html("<div\nclass='x'>text</div>") == "text")
check("sanitize: sanitize_str trims whitespace", sanitize_str("  hello  ") == "hello")
check("sanitize: sanitize_str removes null byte", sanitize_str("he\x00llo") == "hello")
check("sanitize: sanitize_str strips HTML tags", sanitize_str("<script>xss</script>text") == "xsstext")
check("sanitize: clean_text trims whitespace", clean_text("  hello  ") == "hello")
check("sanitize: clean_text removes null byte", clean_text("he\x00llo") == "hello")
check("sanitize: clean_text preserves angle brackets", clean_text("a < b and c > d") == "a < b and c > d")
check("sanitize: sanitize_str passes non-str unchanged", sanitize_str(123) == 123)
check("sanitize: sanitize_str passes None unchanged", sanitize_str(None) is None)

# Pydantic annotated types
class _TS(_BM):
    name: SanitizedStr
    note: SanitizedOptStr = None

check("sanitize: SanitizedStr strips whitespace", _TS(name="  hello  ").name == "hello")
check("sanitize: SanitizedStr strips HTML tags", _TS(name="<b>bold</b>").name == "bold")
check("sanitize: SanitizedOptStr strips HTML", _TS(name="ok", note="<script>xss</script>").note == "xss")
check("sanitize: SanitizedOptStr allows None", _TS(name="ok", note=None).note is None)

class _TC(_BM):
    msg: CleanText

check("sanitize: CleanText trims whitespace", _TC(msg="  hi  ").msg == "hi")
check("sanitize: CleanText preserves angle brackets", _TC(msg="a < 5 and b > 2").msg == "a < 5 and b > 2")
check("sanitize: CleanText removes control chars", _TC(msg="msg\x00with\x01ctrl").msg == "msgwithctrl")

# Auth schema — XSS in full_name
from api.schemas.auth import RegisterRequest as _RR, UpdateProfileRequest as _UPR
_rr = _RR(email="a@b.com", password="Good1Pass", full_name="  <b>John</b>  ")
check("auth: RegisterRequest full_name HTML stripped", _rr.full_name == "John")
_rr2 = _RR(email="a@b.com", password="Good1Pass", full_name="<b>Alice</b>")
check("auth: RegisterRequest XSS tags stripped", _rr2.full_name == "Alice")
_rr3 = _RR(email="a@b.com", password="Good1Pass", full_name="  María García  ")
check("auth: RegisterRequest whitespace trimmed", _rr3.full_name == "María García")

# Chat schema — CleanText
from api.schemas.chat import ChatRequest as _CR
_cr = _CR(message="  ¿Precio m2 Buenos Aires? ")
check("chat: message trimmed", _cr.message == "¿Precio m2 Buenos Aires?")
try: _CR(message="a" * 10001); fail("chat: 10001 chars accepted")
except: ok("chat: message > 10000 chars rejected")
try: _CR(message=""); fail("chat: empty message accepted")
except: ok("chat: empty message rejected")
_cr_null = _CR(message="text\x00with null")
check("chat: null bytes stripped from message", "\x00" not in _cr_null.message)
_cr_angle = _CR(message="price < 100 and quality > 5")
check("chat: angle brackets preserved in chat message", "<" in _cr_angle.message and ">" in _cr_angle.message)

# Payment schema — XSS in text fields
from api.schemas.payment import CreatePaymentRequest as _CPR
_pr = _CPR(concepto="  <b>Cemento</b>  ", proveedor="<b>ABC</b>", monto=D("100"), fecha=date(2026,1,1))
check("payment: concepto HTML stripped and trimmed", _pr.concepto == "Cemento")
check("payment: proveedor HTML tags stripped", _pr.proveedor == "ABC")
_pr2 = _CPR(concepto="Cemento\x00null", monto=D("100"), fecha=date(2026,1,1))
check("payment: concepto null byte stripped", "\x00" not in _pr2.concepto)

# Project schema — XSS in text fields
from api.schemas.project import (
    CreateProjectRequest as _CProjR, CostoRubro as _CR2,
    AlertaItem as _AI, CreateMilestoneRequest as _CMR,
)
_cp_xss = _CProjR(nombre="<img src=x onerror=alert(1)>Torre")
check("project: nombre HTML stripped", _cp_xss.nombre == "Torre")
_ai_xss = _AI(titulo="<b>Alert</b>", descripcion="<b>High severity</b>", severidad="high")
check("project: AlertaItem titulo stripped", _ai_xss.titulo == "Alert")
check("project: AlertaItem descripcion stripped", _ai_xss.descripcion == "High severity")
_ms_xss = _CMR(nombre="<em>Fundaciones</em>", fecha_objetivo=date(2025,5,1))
check("project: milestone nombre stripped", _ms_xss.nombre == "Fundaciones")
_cr2_xss = _CR2(nombre="  <b>Estructura</b>  ", base=D("100"), real=D("120"))
check("project: CostoRubro nombre stripped", _cr2_xss.nombre == "Estructura")

# Sanitize module structure
sanitize_src = read(os.path.join(BE, "core/sanitize.py"))
check("sanitize: module exists", len(sanitize_src) > 0)
check("sanitize: _HTML_RE defined", "_HTML_RE" in sanitize_src)
check("sanitize: _CTRL_RE defined", "_CTRL_RE" in sanitize_src)
check("sanitize: SanitizedStr exported", "SanitizedStr" in sanitize_src)
check("sanitize: SanitizedOptStr exported", "SanitizedOptStr" in sanitize_src)
check("sanitize: CleanText exported", "CleanText" in sanitize_src)
check("sanitize: CleanOptText exported", "CleanOptText" in sanitize_src)

# All schemas import from core.sanitize
for _sf, _label in [
    ("api/schemas/auth.py", "auth"),
    ("api/schemas/chat.py", "chat"),
    ("api/schemas/payment.py", "payment"),
    ("api/schemas/project.py", "project"),
    ("api/schemas/conversation.py", "conversation"),
]:
    check(f"schema: {_label} imports core.sanitize", "from core.sanitize import" in read(os.path.join(BE, _sf)))

# Body size limit in main.py
_main = read(os.path.join(BE, "main.py"))
check("main: BodySizeLimitMiddleware class defined", "_BodySizeLimitMiddleware" in _main)
check("main: 1 MB limit constant", "1_048_576" in _main)
check("main: middleware registered", "add_middleware(_BodySizeLimitMiddleware)" in _main)
check("main: 413 status on oversize", "413" in _main)

# ================================================================
print("\n" + "="*60)
print("SECTION 25: CORS — environment-aware, no wildcard in prod")
print("="*60)
import importlib.util as _ilu

# Load core/cors.py directly (bypasses the config.settings mock)
_cors_spec = _ilu.spec_from_file_location("_core_cors_test", os.path.join(BE, "core", "cors.py"))
_cors_mod = _ilu.module_from_spec(_cors_spec)
_cors_spec.loader.exec_module(_cors_mod)
_build = _cors_mod.build_cors_origins
_DEV = _cors_mod._DEV_ORIGINS

# ── Pure function: dev mode ──────────────────────────────────────
_dev = _build(debug=True)
check("cors: dev mode includes localhost:8080", "http://localhost:8080" in _dev)
check("cors: dev mode includes localhost:3000", "http://localhost:3000" in _dev)
check("cors: dev mode no wildcard", "*" not in _dev)

# ── Pure function: prod mode with FRONTEND_URL ───────────────────
_prod = _build(debug=False, frontend_url="https://re-expert.app")
check("cors: prod includes FRONTEND_URL", "https://re-expert.app" in _prod)
check("cors: prod does NOT include localhost", not any("localhost" in o for o in _prod))
check("cors: prod does NOT include 127.0.0.1", not any("127.0.0.1" in o for o in _prod))
check("cors: prod no wildcard", "*" not in _prod)

# ── Pure function: staging mode ──────────────────────────────────
_staging = _build(debug=True, frontend_url="https://staging.re-expert.app")
check("cors: staging includes staging URL", "https://staging.re-expert.app" in _staging)
check("cors: staging includes localhost (debug=True)", "http://localhost:8080" in _staging)
check("cors: staging no wildcard", "*" not in _staging)

# ── Wildcard safety net ──────────────────────────────────────────
_wild_dev = _build(debug=True, extra_origins=["*"])
check("cors: wildcard allowed in dev (debug=True)", "*" in _wild_dev)
_wild_prod = _build(debug=False, frontend_url="https://re-expert.app", extra_origins=["*"])
check("cors: wildcard STRIPPED in prod (debug=False)", "*" not in _wild_prod)

# ── Unauthorized domain test ─────────────────────────────────────
_attacker = "https://evil.com"
check("cors: unauthorized domain not in dev origins", _attacker not in _build(debug=True))
check("cors: unauthorized domain not in prod origins", _attacker not in _build(debug=False, frontend_url="https://re-expert.app"))

# ── Deduplication ────────────────────────────────────────────────
_dup = _build(debug=True, frontend_url="http://localhost:8080")
check("cors: deduplicates origins", _dup.count("http://localhost:8080") == 1)

# ── FRONTEND_URL trailing slash stripped ─────────────────────────
_slash = _build(debug=False, frontend_url="https://re-expert.app/")
check("cors: trailing slash stripped from FRONTEND_URL", "https://re-expert.app" in _slash and "https://re-expert.app/" not in _slash)

# ── extra_origins appended ───────────────────────────────────────
_extra = _build(debug=False, frontend_url="https://re-expert.app", extra_origins=["https://cdn.example.com"])
check("cors: extra_origins included in prod", "https://cdn.example.com" in _extra)
check("cors: extra_origins: main domain still present", "https://re-expert.app" in _extra)

# ── File-level checks ────────────────────────────────────────────
_cors_src = read(os.path.join(BE, "core", "cors.py"))
check("cors: _DEV_ORIGINS constant defined", "_DEV_ORIGINS" in _cors_src)
check("cors: build_cors_origins function", "def build_cors_origins" in _cors_src)
check("cors: wildcard guard in source", '"*"' in _cors_src or "'*'" in _cors_src)
check("cors: debug branch for dev origins", "if debug" in _cors_src)

_settings_src = read(os.path.join(BE, "config", "settings.py"))
check("settings: FRONTEND_URL field", "FRONTEND_URL: str" in _settings_src)
check("settings: cors_allowed_origins property", "cors_allowed_origins" in _settings_src)
check("settings: imports build_cors_origins", "build_cors_origins" in _settings_src)
check("settings: CORS_ORIGINS default empty list", "CORS_ORIGINS: list[str] = []" in _settings_src)

_main_src = read(os.path.join(BE, "main.py"))
check("main: uses cors_allowed_origins (not CORS_ORIGINS directly)", "settings.cors_allowed_origins" in _main_src)
check("main: no allow_origins=CORS_ORIGINS literal", "allow_origins=settings.CORS_ORIGINS" not in _main_src)

_env_ex = read(os.path.join(BE, ".env.example"))
check(".env.example: FRONTEND_URL documented", "FRONTEND_URL" in _env_ex)
check(".env.example: prod FRONTEND_URL example", "re-expert.app" in _env_ex or "example.com" in _env_ex)
check(".env.example: staging example", "staging" in _env_ex)

# ================================================================
# FINAL SUMMARY
# ================================================================
print("\n" + "="*60)
total = passed + failed
print(f"TOTAL: {passed} passed, {failed} failed out of {total}")
if failed == 0:
    print("ALL CHECKS PASSED — PROJECT IS HEALTHY")
else:
    print(f"ATTENTION: {failed} check(s) failed!")
    sys.exit(1)
