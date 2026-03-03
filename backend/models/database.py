"""
KIP Database Models
===================
Tables:
  users, refresh_tokens, business_profiles,
  conversations, messages, business_logs, forecast_cache
"""

import os
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Enum as SAEnum, JSON, Boolean,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
import enum

logger = logging.getLogger("kip")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://kip:kip_password@localhost:5432/kip_db"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────
class BusinessStage(str, enum.Enum):
    idea       = "idea"
    planning   = "planning"
    launched   = "launched"
    growing    = "growing"
    struggling = "struggling"


class MessageRole(str, enum.Enum):
    user      = "user"
    assistant = "assistant"


class ResponseType(str, enum.Enum):
    business_idea      = "business_idea"
    economic_analysis  = "economic_analysis"
    crisis             = "crisis"
    regulatory         = "regulatory"
    general            = "general"


class LogType(str, enum.Enum):
    revenue   = "revenue"
    expense   = "expense"
    challenge = "challenge"
    milestone = "milestone"
    customer  = "customer"
    supplier  = "supplier"
    staff     = "staff"
    general   = "general"


class Channel(str, enum.Enum):
    web      = "web"
    whatsapp = "whatsapp"


# ── Tables ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String(120), nullable=False)
    email           = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)   # ← NEW
    phone           = Column(String(30), unique=True, nullable=True)
    location        = Column(String(120), nullable=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    businesses    = relationship("BusinessProfile", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation",    back_populates="user", cascade="all, delete-orphan")
    refresh_tokens= relationship("RefreshToken",    back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):                          # ← NEW TABLE
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token      = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="refresh_tokens")


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name            = Column(String(200), nullable=False)
    sector          = Column(String(80), nullable=True)
    stage           = Column(SAEnum(BusinessStage), default=BusinessStage.idea)
    location        = Column(String(120), nullable=True)
    start_capital   = Column(Float, nullable=True)
    monthly_revenue = Column(Float, nullable=True)
    employees       = Column(Integer, default=0)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))

    user  = relationship("User",         back_populates="businesses")
    logs  = relationship("BusinessLog",  back_populates="business", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id     = Column(Integer, ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True)
    channel         = Column(SAEnum(Channel), default=Channel.web)
    session_token   = Column(String(64), unique=True, nullable=True, index=True)
    title           = Column(String(200), nullable=True)
    started_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_message_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user     = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation",
                            cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role            = Column(SAEnum(MessageRole), nullable=False)
    content         = Column(Text, nullable=False)
    response_type   = Column(SAEnum(ResponseType), nullable=True)
    structured_data = Column(JSON, nullable=True)
    tokens_used     = Column(Integer, nullable=True)
    latency_ms      = Column(Integer, nullable=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")


class BusinessLog(Base):
    __tablename__ = "business_logs"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    business_id     = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date        = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    log_type        = Column(SAEnum(LogType), default=LogType.general)
    title           = Column(String(200), nullable=False)
    description     = Column(Text, nullable=True)
    amount_zmw      = Column(Float, nullable=True)
    kip_analysis    = Column(Text, nullable=True)
    kip_suggestions = Column(JSON, nullable=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    business = relationship("BusinessProfile", back_populates="logs")


class ForecastCache(Base):
    __tablename__ = "forecast_cache"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    indicator     = Column(String(80), nullable=False, unique=True)
    generated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    forecast_json = Column(JSON, nullable=False)
    expires_at    = Column(DateTime(timezone=True), nullable=True)


# ── Session dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ── DB init ───────────────────────────────────────────────────────────────────
async def init_db():
    logger.info("Initialising database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✓ Database ready")
