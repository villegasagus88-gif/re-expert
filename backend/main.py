from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API backend for RE Expert - Real Estate AI Assistant",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
