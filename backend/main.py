from contextlib import asynccontextmanager

from api.routes.agent import router as agent_router
from api.routes.auth import router as auth_router
from api.routes.billing import router as billing_router
from api.routes.channels import router as channels_router
from api.routes.chat import router as chat_router
from api.routes.contacts import router as contacts_router
from api.routes.conversations import router as conversations_router
from api.routes.ingest import router as ingest_router
from api.routes.knowledge import router as knowledge_router
from api.routes.materials import router as materials_router
from api.routes.news import router as news_router
from api.routes.payments import router as payments_router
from api.routes.project import router as project_router
from api.routes.reminders import router as reminders_router
from api.routes.stripe_routes import router as stripe_router
from api.routes.usage import router as usage_router
from config.settings import settings
from core.rate_limit import limiter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.scheduler_service import start_scheduler, stop_scheduler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.requests import Request as _Request
from starlette.responses import JSONResponse as _JSONResponse

# Sentry — init BEFORE the FastAPI app is created so middleware auto-wraps.
# Disabled when SENTRY_DSN is empty (default), which is the case in tests
# and local dev without explicit opt-in.
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        release=settings.VERSION,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # Don't include request bodies — they can contain user prompts / PII.
        send_default_pii=False,
        max_request_body_size="never",
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            AsyncioIntegration(),
        ],
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: arrancar el scheduler de recordatorios
    start_scheduler()
    try:
        yield
    finally:
        # Shutdown
        await stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API backend for RE Expert - Real Estate AI Assistant",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class _BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose body exceeds 10 MB.

    10 MB para soportar attachments multimodales en /api/chat (planos):
    hasta 4 imágenes x ~6 MB binarios. El schema ya capea por imagen,
    este middleware es la barrera dura a nivel transport.

    Defensa contra Transfer-Encoding: chunked (que no manda Content-Length):
    rechazamos métodos con body sin CL para no permitir bypass del cap.
    """
    _MAX_BYTES = 10_485_760  # 10 MB
    _METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}

    async def dispatch(self, request: _Request, call_next):
        if request.method in self._METHODS_WITH_BODY:
            cl = request.headers.get("content-length")
            if cl is None:
                # Sin Content-Length no podemos garantizar el cap antes
                # de leer el body. Rechazamos para evitar bypass por
                # chunked transfer encoding o streaming malicioso.
                return _JSONResponse(
                    {"detail": "Falta Content-Length (chunked no soportado)"},
                    status_code=411,  # Length Required
                )
            try:
                size = int(cl)
            except ValueError:
                return _JSONResponse(
                    {"detail": "Content-Length inválido"},
                    status_code=400,
                )
            if size > self._MAX_BYTES:
                return _JSONResponse(
                    {"detail": "Request body too large (max 10 MB)"},
                    status_code=413,
                )
        return await call_next(request)


class _HSTSMiddleware(BaseHTTPMiddleware):
    """Add Strict-Transport-Security header on every response (production only).

    HSTS instructs browsers to only contact this host over HTTPS for the next
    `max-age` seconds. `includeSubDomains` extends the policy to subdomains.
    `preload` is opt-in to the HSTS preload list maintained by the browser
    vendors — only enable when you've already verified all subdomains serve
    HTTPS, since it is hard to reverse.
    """
    _HEADER_VALUE = "max-age=31536000; includeSubDomains"

    async def dispatch(self, request: _Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = self._HEADER_VALUE
        return response


class _HTTPSRedirectExceptHealth:
    """ASGI middleware: HTTPSRedirect but exempt /health.

    Railway's internal healthcheck probes /health over plain HTTP without
    X-Forwarded-Proto, so HTTPSRedirectMiddleware would return 307 and the
    healthcheck would fail. We skip the redirect for /health only.
    """
    def __init__(self, app):
        self._inner = HTTPSRedirectMiddleware(app)
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path") == "/health":
            await self._app(scope, receive, send)
        else:
            await self._inner(scope, receive, send)


# CORS — environment-aware, never wildcard in production (see core/cors.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(_BodySizeLimitMiddleware)

# HTTPS enforcement — only in production. In Railway/Vercel/etc. the platform
# proxy terminates TLS and forwards the original scheme via X-Forwarded-Proto;
# Starlette's HTTPSRedirectMiddleware respects that header when uvicorn is
# started with --proxy-headers (see Dockerfile).
if not settings.DEBUG:
    app.add_middleware(_HTTPSRedirectExceptHealth)
    app.add_middleware(_HSTSMiddleware)

# Routes
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(materials_router)
app.include_router(payments_router)
app.include_router(project_router)
app.include_router(stripe_router)
app.include_router(usage_router)
app.include_router(ingest_router)
app.include_router(news_router)
# SOL agent + reminders + channels
app.include_router(agent_router)
app.include_router(reminders_router)
app.include_router(channels_router)
app.include_router(contacts_router)

# Static files: reportes generados (PDF/DOCX) servidos como fallback de Supabase Storage.
# La carpeta se crea on-demand en services/document_service.py.
import os as _os
from pathlib import Path as _Path

_reports_dir = _Path(__file__).resolve().parent / "data" / "reports"
_reports_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/static/reports",
    StaticFiles(directory=str(_reports_dir)),
    name="reports",
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
