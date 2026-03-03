"""
KIP News Service
================
Auto-fetches live data from:
  1. World Bank Open Data API  — GDP, inflation, poverty, unemployment (free, no key)
  2. Lusaka Times RSS          — lusakatimes.com/feed/
  3. Zambia Daily Mail RSS     — daily-mail.co.zm/feed/
  4. Times of Zambia RSS       — times.co.zm/feed/
  5. Mwebantu RSS              — mwebantu.com/feed/

Caching:
  - World Bank indicators: refreshed every 24 hours
  - News RSS feeds: refreshed every 1 hour
  - Falls back to baked-in data if all fetches fail
"""

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("kip")

# ── Cache store ───────────────────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL_NEWS       = 3600        # 1 hour
CACHE_TTL_INDICATORS = 86400       # 24 hours
FETCH_TIMEOUT        = 8           # seconds per request


# ── World Bank indicator IDs for Zambia ───────────────────────────────────────
WB_INDICATORS = {
    "gdp_growth":        ("NY.GDP.MKTP.KD.ZG",  "GDP Growth Rate (%)",        "World Bank"),
    "inflation":         ("FP.CPI.TOTL.ZG",      "Annual Inflation (%)",       "World Bank"),
    "unemployment":      ("SL.UEM.TOTL.ZS",      "Unemployment Rate (%)",      "World Bank"),
    "poverty_headcount": ("SI.POV.DDAY",          "Poverty Rate (< $2.15/day)", "World Bank"),
    "gni_per_capita":    ("NY.GNP.PCAP.CD",       "GNI Per Capita (USD)",       "World Bank"),
    "exports":           ("NE.EXP.GNFS.ZS",       "Exports (% of GDP)",         "World Bank"),
    "fdi_inflows":       ("BX.KLT.DINV.WD.GD.ZS", "FDI Inflows (% of GDP)",    "World Bank"),
    "rural_pop_pct":     ("SP.RUR.TOTL.ZS",       "Rural Population (%)",       "World Bank"),
}

WB_BASE = "https://api.worldbank.org/v2/country/ZMB/indicator/{indicator}?format=json&mrv=5&per_page=5"

# ── RSS feed sources ───────────────────────────────────────────────────────────
RSS_FEEDS = [
    {"name": "Lusaka Times",    "url": "https://www.lusakatimes.com/feed/",   "category": "General"},
    {"name": "Zambia Daily Mail","url": "https://www.daily-mail.co.zm/feed/", "category": "General"},
    {"name": "Times of Zambia", "url": "https://www.times.co.zm/?feed=rss2",  "category": "General"},
    {"name": "Mwebantu",        "url": "https://www.mwebantu.com/feed/",      "category": "General"},
]

BUSINESS_KEYWORDS = [
    "economy", "inflation", "gdp", "copper", "kwacha", "zambia", "mining",
    "agriculture", "investment", "business", "budget", "finance", "trade",
    "employment", "bank", "ceec", "pacra", "zra", "cdf", "development",
    "forex", "exchange rate", "interest rate", "revenue", "export",
]


# ── Baked-in fallback data ─────────────────────────────────────────────────────
FALLBACK_INDICATORS = [
    {"label": "GDP Growth",          "value": "4.6%",   "trend": "up",   "note": "2024 estimate",         "source": "World Bank", "raw": 4.6},
    {"label": "Annual Inflation",    "value": "13.7%",  "trend": "down", "note": "Dec 2025 ZamStats CPI", "source": "ZamStats",   "raw": 13.7},
    {"label": "USD / ZMW",           "value": "K26.8",  "trend": "down", "note": "Approximate",           "source": "BoZ",        "raw": 26.8},
    {"label": "Copper Price",        "value": "$9,400", "trend": "up",   "note": "LME per tonne",         "source": "LME",        "raw": 9400},
    {"label": "Unemployment Rate",   "value": "12.8%",  "trend": "down", "note": "Labour Force Survey",   "source": "ZamStats",   "raw": 12.8},
    {"label": "Population",          "value": "20.1M",  "trend": "up",   "note": "2024 projection",       "source": "CSO",        "raw": 20.1},
    {"label": "Poverty Rate",        "value": "54.4%",  "trend": "down", "note": "Below $2.15/day",       "source": "World Bank", "raw": 54.4},
    {"label": "Food Inflation",      "value": "12.9%",  "trend": "down", "note": "Annual food CPI",       "source": "ZamStats",   "raw": 12.9},
    {"label": "Maize Floor Price",   "value": "K3,200", "trend": "up",   "note": "FRA per metric tonne",  "source": "FRA",        "raw": 3200},
    {"label": "Mobile Penetration",  "value": "57%",    "trend": "up",   "note": "Active SIM cards",      "source": "ZICTA",      "raw": 57},
    {"label": "Remittances",         "value": "$600M",  "trend": "up",   "note": "Annual inflows 2024",   "source": "BoZ",        "raw": 600},
    {"label": "External Debt",       "value": "$14.7B", "trend": "down", "note": "Post-2023 restructure", "source": "MoF",        "raw": 14.7},
]

FALLBACK_NEWS = [
    {
        "headline": "Zambia GDP Growth Expected at 4.6% in 2024",
        "summary":  "The World Bank projects sustained growth driven by mining recovery, improved power supply, and agricultural output.",
        "date":     "Q4 2024",
        "category": "Economy",
        "source":   "World Bank",
        "url":      "https://worldbank.org/zambia",
        "fetched":  False,
    },
    {
        "headline": "Inflation Eases to 13.7% — ZamStats CPI December 2025",
        "summary":  "Annual inflation fell from a peak driven by lower food and fuel prices. Mealie meal and tomatoes showed notable price declines.",
        "date":     "Dec 2025",
        "category": "Prices",
        "source":   "ZamStats",
        "url":      "https://zamstats.gov.zm",
        "fetched":  False,
    },
    {
        "headline": "CDF Disbursements Reach K28.3 Billion Nationally",
        "summary":  "CDF disbursements accelerated in 2025 with emphasis on rural electrification, boreholes, and school rehabilitation.",
        "date":     "2025",
        "category": "Development",
        "source":   "Ministry of Finance",
        "url":      "https://mof.gov.zm",
        "fetched":  False,
    },
    {
        "headline": "Copper Production Up 18% in First Half of 2025",
        "summary":  "Mining output rebounds as major mines ramp up operations. Cobalt production also increased 22%, boosting export revenues.",
        "date":     "H1 2025",
        "category": "Mining",
        "source":   "ZCCM-IH",
        "url":      "https://zccm-ih.com.zm",
        "fetched":  False,
    },
    {
        "headline": "CEEC SME Loan Disbursements Hit K2.4 Billion",
        "summary":  "The Citizens Economic Empowerment Commission surpassed its annual target across agriculture, manufacturing, and services.",
        "date":     "2025",
        "category": "Finance",
        "source":   "CEEC",
        "url":      "https://ceec.org.zm",
        "fetched":  False,
    },
    {
        "headline": "Agriculture Sector Grows 7.2% — Strong Harvest Season",
        "summary":  "Favourable rainfall and FISP support drove record maize and soybean production. FRA purchased over 900,000 metric tonnes.",
        "date":     "2025",
        "category": "Agriculture",
        "source":   "Ministry of Agriculture",
        "url":      "https://agri.gov.zm",
        "fetched":  False,
    },
]


# ── Cache helpers ─────────────────────────────────────────────────────────────
def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > entry["ttl"]:
        del _cache[key]
        return None
    return entry["data"]


def _cache_set(key: str, data, ttl: int):
    _cache[key] = {"data": data, "ts": time.time(), "ttl": ttl}


# ── World Bank fetcher ────────────────────────────────────────────────────────
async def fetch_wb_indicator(client: httpx.AsyncClient, key: str, ind_id: str, label: str, source: str) -> Optional[dict]:
    try:
        url  = WB_BASE.format(indicator=ind_id)
        resp = await client.get(url, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if not data or len(data) < 2:
            return None

        entries = [e for e in data[1] if e.get("value") is not None]
        if not entries:
            return None

        latest   = entries[0]
        previous = entries[1] if len(entries) > 1 else None
        val      = latest["value"]
        year     = latest["date"]

        trend = "flat"
        if previous and previous.get("value") is not None:
            trend = "up" if val > previous["value"] else "down"

        # Format value nicely
        if "GNP.PCAP" in ind_id:
            formatted = f"${val:,.0f}"
        elif "SP.POP" in ind_id or "SP.RUR" in ind_id:
            formatted = f"{val:.1f}%"
        else:
            formatted = f"{val:.1f}%"

        return {
            "label":  label,
            "value":  formatted,
            "trend":  trend,
            "note":   f"Latest data: {year}",
            "source": source,
            "raw":    val,
        }
    except Exception as e:
        logger.debug(f"WB fetch failed for {key}: {e}")
        return None


async def get_indicators() -> list:
    cached = _cache_get("indicators")
    if cached:
        return cached

    results = []
    try:
        async with httpx.AsyncClient() as client:
            tasks = [
                fetch_wb_indicator(client, k, v[0], v[1], v[2])
                for k, v in WB_INDICATORS.items()
            ]
            fetched = await asyncio.gather(*tasks, return_exceptions=True)

        # Map WB results by label
        wb_map = {}
        for item in fetched:
            if isinstance(item, dict):
                wb_map[item["label"]] = item

        # Merge with fallback (WB wins if available)
        merged = []
        for fb in FALLBACK_INDICATORS:
            if fb["label"] in wb_map:
                merged.append(wb_map[fb["label"]])
            else:
                merged.append(fb)

        _cache_set("indicators", merged, CACHE_TTL_INDICATORS)
        logger.info(f"Indicators: {len([x for x in fetched if isinstance(x, dict)])} live from World Bank, rest from fallback")
        return merged

    except Exception as e:
        logger.warning(f"Indicator fetch error: {e} — using fallback")
        return FALLBACK_INDICATORS


# ── RSS fetcher ───────────────────────────────────────────────────────────────
def _parse_rss(xml_text: str, source_name: str, default_category: str) -> list:
    """Parse RSS XML into news items, filtering for Zambia/business relevance."""
    items = []
    try:
        root = ET.fromstring(xml_text)
        ns   = {"content": "http://purl.org/rss/1.0/modules/content/"}

        for item in root.iter("item"):
            title       = item.findtext("title", "").strip()
            description = item.findtext("description", "").strip()
            link        = item.findtext("link", "").strip()
            pub_date    = item.findtext("pubDate", "").strip()
            category_el = item.find("category")
            category    = category_el.text.strip() if category_el is not None and category_el.text else default_category

            if not title or not link:
                continue

            # Filter for relevance (business/economy keywords)
            combined = (title + " " + description).lower()
            if not any(kw in combined for kw in BUSINESS_KEYWORDS):
                continue

            # Trim description
            summary = description[:280] + "..." if len(description) > 280 else description
            # Strip HTML tags simply
            import re
            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = re.sub(r"\s+", " ", summary).strip()

            # Format date
            try:
                dt = datetime.strptime(pub_date[:25], "%a, %d %b %Y %H:%M:%S")
                date_str = dt.strftime("%d %b %Y")
            except Exception:
                date_str = pub_date[:16] if pub_date else "Recent"

            items.append({
                "headline": title[:120],
                "summary":  summary[:300] if summary else title,
                "date":     date_str,
                "category": _classify_category(title + " " + description),
                "source":   source_name,
                "url":      link,
                "fetched":  True,
            })

            if len(items) >= 5:   # Max 5 per source
                break

    except Exception as e:
        logger.debug(f"RSS parse error ({source_name}): {e}")

    return items


def _classify_category(text: str) -> str:
    text = text.lower()
    if any(w in text for w in ["copper", "mining", "cobalt", "mine", "konkola", "mopani"]):
        return "Mining"
    if any(w in text for w in ["maize", "farm", "agricult", "harvest", "crop", "food reserve", "fra"]):
        return "Agriculture"
    if any(w in text for w in ["inflation", "cpi", "price", "kwacha", "exchange", "forex"]):
        return "Prices"
    if any(w in text for w in ["loan", "bank", "ceec", "finance", "investment", "stock", "bond"]):
        return "Finance"
    if any(w in text for w in ["gdp", "growth", "economy", "trade", "export", "imf", "world bank"]):
        return "Economy"
    if any(w in text for w in ["school", "hospital", "borehole", "road", "cdf", "constituency", "electri"]):
        return "Development"
    if any(w in text for w in ["start", "sme", "business", "entrepreneur", "pacra", "company"]):
        return "Business"
    return "General"


async def fetch_rss_feed(client: httpx.AsyncClient, feed: dict) -> list:
    try:
        resp = await client.get(feed["url"], timeout=FETCH_TIMEOUT, follow_redirects=True,
                                headers={"User-Agent": "KIP-NewsBot/1.0 (+https://kip.zm)"})
        resp.raise_for_status()
        items = _parse_rss(resp.text, feed["name"], feed["category"])
        logger.info(f"RSS {feed['name']}: {len(items)} relevant articles")
        return items
    except Exception as e:
        logger.debug(f"RSS fetch failed ({feed['name']}): {e}")
        return []


async def get_news() -> list:
    cached = _cache_get("news")
    if cached:
        return cached

    all_items = []
    try:
        async with httpx.AsyncClient() as client:
            tasks   = [fetch_rss_feed(client, feed) for feed in RSS_FEEDS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, list):
                all_items.extend(r)

        if all_items:
            # Sort by recency (fetched items first, then fallback)
            all_items = all_items[:20]   # Cap at 20
            _cache_set("news", all_items, CACHE_TTL_NEWS)
            logger.info(f"News: {len(all_items)} live articles fetched")
            return all_items

    except Exception as e:
        logger.warning(f"News fetch error: {e}")

    # Fallback
    logger.info("News: using fallback articles")
    return FALLBACK_NEWS


async def get_news_and_indicators() -> dict:
    """Fetch both in parallel for the landing page."""
    news, indicators = await asyncio.gather(get_news(), get_indicators())
    return {
        "news":         news,
        "indicators":   indicators,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "live":         any(n.get("fetched") for n in news),
    }
