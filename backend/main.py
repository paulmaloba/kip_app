"""
KIP Platform — FastAPI Entry Point
Updated to include exchange rate poller and notifications
"""

import asyncio
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
from api.auth      import router as auth_router
from api.news      import router as news_router
from api.rates     import router as rates_router       # ← NEW

from services.exchange_service import start_rate_poller, fetch_rates
from services.notification_service import notify_rate_change

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kip")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 KIP Platform starting...")
    await init_db()

    # Initial rate fetch on startup
    try:
        result = await fetch_rates()
        logger.info(f"✓ Initial rates loaded: USD/ZMW = {result['rates'].get('ZMW', '?')}")
    except Exception as e:
        logger.warning(f"Initial rate fetch failed: {e}")

    # Start background rate poller
    poller_task = asyncio.create_task(_rate_poller_with_notifications())
    logger.info("✓ KIP ready")

    yield

    poller_task.cancel()
    logger.info("KIP shutting down")


async def _rate_poller_with_notifications():
    """Rate poller that also triggers notifications on significant changes."""
    import asyncio
    from services.exchange_service import fetch_rates, FETCH_INTERVAL_SECONDS
    logger.info("✓ Exchange rate poller started")
    while True:
        try:
            await asyncio.sleep(FETCH_INTERVAL_SECONDS)
            result = await fetch_rates()
            if result.get("changes"):
                notify_rate_change(result["changes"])
                logger.info(f"⚡ {len(result['changes'])} rate alert(s) sent")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Rate poller error: {e}")


app = FastAPI(
    title="KIP — Kwacha Intelligence Platform",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,     prefix="/api")
app.include_router(news_router,     prefix="/api")
app.include_router(chat_router,     prefix="/api/chat")     # ← fixed prefix
app.include_router(rates_router,    prefix="/api")          # ← NEW
app.include_router(forecast_router, prefix="/api/forecast")
app.include_router(business_router, prefix="/api/business")
app.include_router(users_router,    prefix="/api/users")
app.include_router(whatsapp_router, prefix="/api/whatsapp")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "KIP v2.1"}
