from api.routes.auth import router as auth_router
from api.routes.knowledge import router as knowledge_router
from config.settings import settings
from core.rate_limit import limiter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API backend for RE Expert - Real Estate AI Assistant",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(knowledge_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
