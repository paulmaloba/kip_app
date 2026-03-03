"""
KIP News Router
===============
GET /news/feed        — latest Zambian news articles (RSS + fallback)
GET /news/indicators  — economic indicators (World Bank API + fallback)
GET /news/all         — both combined (used by landing page)
"""

import logging
from fastapi import APIRouter, BackgroundTasks

from services.news_service import get_news, get_indicators, get_news_and_indicators

logger = logging.getLogger("kip")
router = APIRouter(prefix="/news", tags=["news"])


@router.get("/all")
async def all_data():
    """Single endpoint for landing page — returns news + indicators in parallel."""
    return await get_news_and_indicators()


@router.get("/feed")
async def news_feed():
    return {"articles": await get_news()}


@router.get("/indicators")
async def indicators():
    return {"indicators": await get_indicators()}
