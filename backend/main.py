from api.routes.auth import router as auth_router
from api.routes.billing import router as billing_router
from api.routes.chat import router as chat_router
from api.routes.conversations import router as conversations_router
from api.routes.knowledge import router as knowledge_router
from api.routes.materials import router as materials_router
from api.routes.payments import router as payments_router
from api.routes.project import router as project_router
from api.routes.stripe_routes import router as stripe_router
from api.routes.usage import router as usage_router
from config.settings import settings
from core.rate_limit import limiter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as _Request
from starlette.responses import JSONResponse as _JSONResponse

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API backend for RE Expert - Real Estate AI Assistant",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class _BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds 1 MB before they are read."""
    _MAX_BYTES = 1_048_576  # 1 MB

    async def dispatch(self, request: _Request, call_next):
        cl = request.headers.get("content-length")
        if cl and int(cl) > self._MAX_BYTES:
            return _JSONResponse(
                {"detail": "Request body too large (max 1 MB)"},
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
app.include_router(project_router)
app.include_router(stripe_router)
app.include_router(usage_router)
app.include_router(ingest_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
