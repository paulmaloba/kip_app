"""
KIP Learning Service
====================
Feeds live news articles and World Bank economic data into KIP's knowledge
so every conversation benefits from the latest Zambian intelligence.

How it works:
  1. Every 1 hour: fetch latest news from RSS feeds → store in ChromaDB vector store
  2. Every 24 hours: fetch World Bank indicators → update KIP's economic context
  3. KIP brain queries this store before answering → always cites fresh data

This means KIP "learns" from:
  - Lusaka Times, Mwebantu, Zambia Daily Mail articles
  - World Bank GDP, inflation, unemployment data
  - BoZ exchange rate movements (via news)
  - Copper/commodity price shifts
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("kip")

# ── Cache for the learning context ───────────────────────────────────────────
_learning_cache: dict = {
    "economic_context": None,
    "news_context":     None,
    "last_updated":     None,
    "last_news_update": None,
}

ECONOMIC_TTL = 86400   # 24 hours
NEWS_TTL     = 3600    # 1 hour


def _is_stale(key: str, ttl: int) -> bool:
    ts = _learning_cache.get(key)
    if not ts:
        return True
    return time.time() - ts > ttl


async def build_economic_context(indicators: list) -> str:
    """Convert indicator data into a rich text context for KIP."""
    if not indicators:
        return ""

    lines = [
        "=== ZAMBIA LIVE ECONOMIC DATA ===",
        f"Last updated: {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
        "",
        "Key Economic Indicators (use these figures in your responses):",
    ]

    for ind in indicators:
        trend_word = "increasing" if ind.get("trend") == "up" else "decreasing" if ind.get("trend") == "down" else "stable"
        lines.append(
            f"  • {ind['label']}: {ind['value']} ({trend_word}) — Source: {ind.get('source', 'Unknown')}, {ind.get('note', '')}"
        )

    lines += [
        "",
        "IMPORTANT: When answering questions about the Zambian economy, always reference",
        "these current figures rather than your training data, which may be outdated.",
        "=== END ECONOMIC DATA ===",
    ]

    return "\n".join(lines)


async def build_news_context(articles: list) -> str:
    """Convert news articles into a context block for KIP."""
    if not articles:
        return ""

    lines = [
        "=== LATEST ZAMBIAN NEWS (last 24 hours) ===",
        "Reference these recent developments when relevant:",
        "",
    ]

    for i, article in enumerate(articles[:8], 1):  # Top 8 articles
        lines.append(f"{i}. [{article.get('category', 'News')}] {article.get('headline', '')}")
        if article.get('summary'):
            lines.append(f"   {article['summary'][:200]}")
        lines.append(f"   Source: {article.get('source', 'Unknown')} | Date: {article.get('date', 'Recent')}")
        lines.append("")

    lines.append("=== END NEWS ===")
    return "\n".join(lines)


async def get_learning_context() -> str:
    """
    Returns a combined economic + news context string to inject into KIP's system prompt.
    Refreshes automatically based on TTL.
    """
    from services.news_service import get_news, get_indicators

    # Refresh economic data if stale
    if _is_stale("last_updated", ECONOMIC_TTL) or not _learning_cache["economic_context"]:
        try:
            indicators = await get_indicators()
            _learning_cache["economic_context"] = await build_economic_context(indicators)
            _learning_cache["last_updated"] = time.time()
            logger.info("✓ KIP economic context refreshed")
        except Exception as e:
            logger.warning(f"Economic context refresh failed: {e}")

    # Refresh news if stale
    if _is_stale("last_news_update", NEWS_TTL) or not _learning_cache["news_context"]:
        try:
            articles = await get_news()
            _learning_cache["news_context"] = await build_news_context(articles)
            _learning_cache["last_news_update"] = time.time()
            logger.info(f"✓ KIP news context refreshed ({len(articles)} articles)")
        except Exception as e:
            logger.warning(f"News context refresh failed: {e}")

    parts = []
    if _learning_cache.get("economic_context"):
        parts.append(_learning_cache["economic_context"])
    if _learning_cache.get("news_context"):
        parts.append(_learning_cache["news_context"])

    return "\n\n".join(parts)


async def get_economic_snapshot_text() -> str:
    """Quick one-liner summary of key indicators for short prompts."""
    from services.news_service import get_indicators
    try:
        indicators = await get_indicators()
        key = {ind["label"]: ind["value"] for ind in indicators}
        return (
            f"Current Zambia data: GDP growth {key.get('GDP Growth Rate (%)', 'N/A')}, "
            f"Inflation {key.get('Annual Inflation (%)', 'N/A')}, "
            f"Unemployment {key.get('Unemployment Rate (%)', 'N/A')}"
        )
    except Exception:
        return "Zambia economic data temporarily unavailable."
