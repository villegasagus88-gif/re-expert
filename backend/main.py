from contextlib import asynccontextmanager

from api.routes.academia import router as academia_router
from api.routes.agent import router as agent_router
from api.routes.auth import router as auth_router
from api.routes.billing import router as billing_router
from api.routes.channels import router as channels_router
from api.routes.chat import router as chat_router
from api.routes.creditos import router as creditos_router
from api.routes.contacts import router as contacts_router
from api.routes.conversations import router as conversations_router
from api.routes.ingest import router as ingest_router
from api.routes.knowledge import router as knowledge_router
from api.routes.materials import router as materials_router
from api.routes.news import router as news_router
from api.routes.payments import router as payments_router
from api.routes.profile import router as profile_router
from api.routes.project import router as project_router
from api.routes.reminders import router as reminders_router
from api.routes.stripe_routes import router as stripe_router
from api.routes.usage import router as usage_router
from api.routes.workspaces import router as workspaces_router
from config.settings import settings
from core.auth import require_admin
from core.plan_gate import require_access
from core.rate_limit import limiter
from fastapi import Depends, FastAPI
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


class _NoCacheAPIMiddleware(BaseHTTPMiddleware):
    """Force `Cache-Control: no-store` on every /api/* response.

    Sin esto, un CDN/proxy intermedio (Cloudflare, Netlify, corporate
    proxies) podría cachear respuestas autenticadas. Como las respuestas
    incluyen datos del user (perfiles, pagos, conversaciones), un user
    podría llegar a ver datos cacheados de otro user que pasó por el
    mismo edge.

    Se aplica solo a /api/* — los assets estáticos (HTML/CSS/JS) los
    sirve Netlify con su propia política de cache.

    Si un handler específico necesita override (ej. SSE chat con
    `no-cache` para streaming), lo setea ANTES y nosotros no pisamos.
    """
    _NO_STORE = "no-store, no-cache, must-revalidate, private"

    async def dispatch(self, request: _Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            # No pisar si el handler ya seteó algo específico (SSE).
            if not response.headers.get("Cache-Control"):
                response.headers["Cache-Control"] = self._NO_STORE
                response.headers.setdefault("Pragma", "no-cache")
        return response


class _HTTPSRedirectExceptHealth:
    """ASGI middleware: HTTPSRedirect but exempt /health* endpoints.

    Railway's internal healthcheck probes over plain HTTP without
    X-Forwarded-Proto, so HTTPSRedirectMiddleware devolvería 307 y
    la healthcheck fallaría. Exemptamos cualquier path bajo /health
    (`/health`, `/health/ready`, `/health/db`).
    """
    def __init__(self, app):
        self._inner = HTTPSRedirectMiddleware(app)
        self._app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path") or ""
        if scope.get("type") == "http" and (
            path == "/health" or path.startswith("/health/")
        ):
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
# No-cache para /api/* — evita que CDNs/proxies cacheen respuestas con
# datos de usuario y los sirvan a otros usuarios. Crítico cuando hay
# proxies intermedios como Netlify Edge o Cloudflare.
app.add_middleware(_NoCacheAPIMiddleware)

# HTTPS enforcement — only in production. In Railway/Vercel/etc. the platform
# proxy terminates TLS and forwards the original scheme via X-Forwarded-Proto;
# Starlette's HTTPSRedirectMiddleware respects that header when uvicorn is
# started with --proxy-headers (see Dockerfile).
if not settings.DEBUG:
    app.add_middleware(_HTTPSRedirectExceptHealth)
    app.add_middleware(_HSTSMiddleware)

# Routes SIN gate de acceso: necesarias para entrar, pagar y operar la cuenta.
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(stripe_router)
app.include_router(usage_router)

# Routes de PRODUCTO: requieren suscripción activa (trial vigente o pro).
# Modelo pago-only — un usuario sin acceso recibe 403 (paywall) en cualquiera.
_paid = [Depends(require_access)]
app.include_router(conversations_router, dependencies=_paid)
app.include_router(chat_router, dependencies=_paid)
# Knowledge base: solo administradores (gestión del KB global). Cierra el agujero
# de escritura/borrado del KB por cualquier usuario autenticado.
app.include_router(knowledge_router, dependencies=[Depends(require_admin)])
app.include_router(materials_router, dependencies=_paid)
app.include_router(academia_router, dependencies=_paid)
app.include_router(creditos_router, dependencies=_paid)
app.include_router(payments_router, dependencies=_paid)
app.include_router(project_router, dependencies=_paid)
app.include_router(profile_router, dependencies=_paid)
app.include_router(ingest_router, dependencies=_paid)
app.include_router(news_router, dependencies=_paid)
app.include_router(workspaces_router, dependencies=_paid)
# SOL agent + reminders + channels
app.include_router(agent_router, dependencies=_paid)
app.include_router(reminders_router, dependencies=_paid)
app.include_router(channels_router, dependencies=_paid)
app.include_router(contacts_router, dependencies=_paid)

# Static files: reportes generados (PDF/DOCX) servidos como fallback de Supabase Storage.
# La carpeta se crea on-demand en services/document_service.py.
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
    """Liveness probe — el proceso está vivo y respondiendo HTTP.
    No verifica dependencias. Railway usa este endpoint.
    """
    return {"status": "ok", "version": settings.VERSION}


@app.get("/health/ready")
async def health_ready():
    """Readiness probe — el proceso está listo para recibir tráfico.
    Verifica conectividad con la DB. Si la DB está caída, devuelve 503
    y un load balancer debería sacar el container de rotación.

    Útil para Kubernetes-style readiness; en Railway hoy usamos solo
    `/health`, pero este endpoint queda disponible para futuros LBs.
    """
    from models.base import get_session_factory
    from sqlalchemy import text as _sa_text

    try:
        async with get_session_factory()() as db:
            res = await db.execute(_sa_text("SELECT 1"))
            row = res.scalar()
            if row != 1:
                raise RuntimeError("SELECT 1 returned unexpected value")
    except Exception as exc:
        return _JSONResponse(
            {"status": "not_ready", "reason": "db_unreachable", "detail": str(exc)[:200]},
            status_code=503,
        )
    return {"status": "ready", "version": settings.VERSION}


@app.get("/health/db")
async def health_db():
    """Alias de /health/ready (más explícito en el nombre).
    Útil para alerting que monitorea específicamente la DB.
    """
    return await health_ready()


@app.get("/health/storage")
async def health_storage():
    """Diagnóstico de Supabase Storage (entregables PDF/Excel).

    Hace una PRUEBA REAL: sube un archivo mínimo al bucket `reports` y lo
    firma. Sirve para confirmar que los links de descarga van a ser durables.
    NO expone secretos: solo si está configurado y si el test funciona.
    Abrí esta URL en el navegador después de cargar las variables en Railway.
    """
    url_set = bool(settings.SUPABASE_URL)
    key_set = bool(settings.SUPABASE_SERVICE_ROLE_KEY)
    out = {"supabase_url_set": url_set, "service_role_set": key_set, "bucket": "reports"}

    if not (url_set and key_set):
        out["status"] = "no_configurado"
        out["detalle"] = (
            "Faltan SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY en Railway. "
            "Mientras tanto los archivos usan disco efímero (no duran 24-48h)."
        )
        return out

    try:
        from services.document_service import _upload_to_supabase

        signed = await _upload_to_supabase("_diag.txt", b"ok", "text/plain", expires_in=600)
        if signed:
            from urllib.parse import urlparse

            out["status"] = "ok"
            out["test_upload"] = "ok"
            out["signed_url_host"] = urlparse(signed).hostname or ""
            out["detalle"] = "Supabase Storage funciona: los entregables tendrán links durables (48h)."
        else:
            out["status"] = "error"
            out["test_upload"] = "fallo"
            out["detalle"] = (
                "Las variables están pero el upload falló. Verificá que exista el "
                "bucket 'reports' y que la key sea la service_role (no la anon)."
            )
    except Exception as e:  # noqa: BLE001
        out["status"] = "error"
        out["detalle"] = f"Excepción en el test: {str(e)[:200]}"
    return out
