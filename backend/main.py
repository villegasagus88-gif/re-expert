from contextlib import asynccontextmanager
from pathlib import Path as _Path

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
from api.routes.planos import router as planos_router
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
from starlette.requests import Request as _Request
from starlette.responses import JSONResponse as _JSONResponse


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
    """Reject oversized request bodies before they are read.

    Default cap is 1 MB for the JSON APIs. Multimodal upload routes (planos)
    need more room, so paths under those prefixes get a higher cap — the
    handler still validates per-file and total size.
    """
    _MAX_BYTES = 1_048_576  # 1 MB
    _UPLOAD_MAX_BYTES = 16_777_216  # 16 MB
    _UPLOAD_PREFIXES = ("/api/planos/",)

    async def dispatch(self, request: _Request, call_next):
        cl = request.headers.get("content-length")
        if cl:
            limit = (
                self._UPLOAD_MAX_BYTES
                if request.url.path.startswith(self._UPLOAD_PREFIXES)
                else self._MAX_BYTES
            )
            try:
                too_big = int(cl) > limit
            except ValueError:
                too_big = False
            if too_big:
                return _JSONResponse(
                    {"detail": "Request body too large"},
                    status_code=413,
                )
        return await call_next(request)


# CORS — environment-aware, never wildcard in production (see core/cors.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(_BodySizeLimitMiddleware)

# Routes
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(materials_router)
app.include_router(payments_router)
app.include_router(planos_router)
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
