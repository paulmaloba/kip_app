"""
KIP Platform — FastAPI Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import init_db
from api.chat      import router as chat_router
from api.forecast  import router as forecast_router
from api.business  import router as business_router
from api.users     import router as users_router
from api.whatsapp  import router as whatsapp_router
from api.auth      import router as auth_router       # ← NEW
from api.news      import router as news_router       # ← NEW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kip")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 KIP Platform starting...")
    await init_db()
    logger.info("✓ KIP ready")
    yield
    logger.info("KIP shutting down")


app = FastAPI(
    title="KIP — Kwacha Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,     prefix="/api")
app.include_router(news_router,     prefix="/api")
# app.include_router(chat_router,     prefix="/api")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(forecast_router, prefix="/api/forecast")
app.include_router(business_router, prefix="/api/business")
app.include_router(users_router,    prefix="/api/users")
app.include_router(whatsapp_router, prefix="/api/whatsapp")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "KIP v2.0"}
