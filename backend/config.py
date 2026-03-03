"""
KIP Platform Configuration
All environment variables in one place.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────
    APP_NAME: str = "KIP — Kwacha Intelligence Platform"
    APP_ENV: str = "development"
    SECRET_KEY: str = "kip-secret-change-in-production"

    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://kip:kip_password@localhost:5432/kip_db"

    # ── Redis (optional — falls back to in-memory) ────────────────
    REDIS_URL: str = ""
    USE_REDIS: bool = False

    # ── Claude API ────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    CLAUDE_SMART_MODEL: str = "claude-sonnet-4-5"   # for complex responses

    # ── ChromaDB (KIP knowledge base) ─────────────────────────────
    CHROMA_DB_PATH: str = "./kip_corpus/chroma_db"
    CHROMA_COLLECTION: str = "kip_knowledge"

    # ── LSTM Models ───────────────────────────────────────────────
    LSTM_GDP_MODEL_PATH: str = "./ml/gdp_growth_lstm_model.h5"
    LSTM_INFLATION_MODEL_PATH: str = "./ml/inflation_lstm_model.h5"

    # ── CPI Data ──────────────────────────────────────────────────
    CPI_CSV_PATH: str = "./data/consumer-price_index.csv"

    # ── Twilio / WhatsApp ─────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    # ── CORS ──────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # React alternative
        "http://127.0.0.1:5173",
        "https://kip.railway.app",  # production
    ]

    # ── Forecast Cache (seconds) ───────────────────────────────────
    FORECAST_CACHE_TTL: int = 604800   # 1 week

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
