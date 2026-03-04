"""
KIP News Service — v2
=====================
Fetches live data. Economic indicators strategy:
  - World Bank API: used for HISTORICAL trend data (confirms direction)
  - Fallback figures: current 2025 estimates from ZamStats/IMF/BoZ press releases
  - Display: always show the most recent known figure with clear source dating

World Bank data lags by 1-2 years by design — we use it to confirm trends,
not as the headline figure. Current estimates come from official 2024/2025
ZamStats CPI releases, IMF Article IV, and Bank of Zambia MPC statements.
"""

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("kip")

_cache: dict = {}
CACHE_TTL_NEWS       = 3600
CACHE_TTL_INDICATORS = 86400
FETCH_TIMEOUT        = 8

# ── World Bank indicators (for trend confirmation) ────────────────────────────
WB_INDICATORS = {
    "gdp_growth":   ("NY.GDP.MKTP.KD.ZG", "GDP Growth (%)"),
    "inflation":    ("FP.CPI.TOTL.ZG",    "Inflation (%)"),
    "unemployment": ("SL.UEM.TOTL.ZS",    "Unemployment (%)"),
    "poverty":      ("SI.POV.DDAY",        "Poverty Rate (%)"),
    "exports":      ("NE.EXP.GNFS.ZS",    "Exports (% GDP)"),
    "fdi":          ("BX.KLT.DINV.WD.GD.ZS", "FDI Inflows (% GDP)"),
}

WB_BASE = "https://api.worldbank.org/v2/country/ZMB/indicator/{indicator}?format=json&mrv=3&per_page=3"

# ── RSS feeds ─────────────────────────────────────────────────────────────────
RSS_FEEDS = [
    {"name": "Lusaka Times",     "url": "https://www.lusakatimes.com/feed/"},
    {"name": "Zambia Daily Mail","url": "https://www.daily-mail.co.zm/feed/"},
    {"name": "Times of Zambia",  "url": "https://www.times.co.zm/?feed=rss2"},
    {"name": "Mwebantu",         "url": "https://www.mwebantu.com/feed/"},
]

BUSINESS_KEYWORDS = [
    "economy","inflation","gdp","copper","kwacha","zambia","mining",
    "agriculture","investment","business","budget","finance","trade",
    "employment","bank","ceec","pacra","zra","cdf","development",
    "forex","exchange rate","interest rate","revenue","export","price",
]

# ── CURRENT 2025 figures — sourced from latest official releases ───────────────
# These are the HEADLINE figures shown to users.
# World Bank API figures are used only to show historical trend direction.
CURRENT_INDICATORS = [
    {
        "label":  "GDP Growth",
        "value":  "4.6%",
        "trend":  "up",
        "note":   "2024 estimate — IMF/World Bank",
        "source": "IMF Article IV 2024",
        "raw":    4.6,
    },
    {
        "label":  "Annual Inflation",
        "value":  "16.0%",
        "trend":  "down",
        "note":   "Feb 2025 — ZamStats CPI release",
        "source": "ZamStats",
        "raw":    16.0,
    },
    {
        "label":  "USD / ZMW Rate",
        "value":  "K27.2",
        "trend":  "down",
        "note":   "Approximate — Mar 2025",
        "source": "Bank of Zambia",
        "raw":    27.2,
    },
    {
        "label":  "Copper Price",
        "value":  "$9,650/t",
        "trend":  "up",
        "note":   "LME spot — Mar 2025",
        "source": "London Metal Exchange",
        "raw":    9650,
    },
    {
        "label":  "Unemployment",
        "value":  "12.8%",
        "trend":  "down",
        "note":   "2023 Labour Force Survey",
        "source": "ZamStats",
        "raw":    12.8,
    },
    {
        "label":  "Population",
        "value":  "20.6M",
        "trend":  "up",
        "note":   "2025 projection",
        "source": "CSO Zambia",
        "raw":    20.6,
    },
    {
        "label":  "Poverty Rate",
        "value":  "54.4%",
        "trend":  "down",
        "note":   "Below $2.15/day",
        "source": "World Bank 2023",
        "raw":    54.4,
    },
    {
        "label":  "Food Inflation",
        "value":  "17.2%",
        "trend":  "down",
        "note":   "Feb 2025 — ZamStats",
        "source": "ZamStats",
        "raw":    17.2,
    },
    {
        "label":  "Maize Floor Price",
        "value":  "K3,200/t",
        "trend":  "up",
        "note":   "2024/25 season — FRA",
        "source": "Food Reserve Agency",
        "raw":    3200,
    },
    {
        "label":  "Mobile Penetration",
        "value":  "58%",
        "trend":  "up",
        "note":   "Active SIMs 2024",
        "source": "ZICTA",
        "raw":    58,
    },
    {
        "label":  "Remittances",
        "value":  "$640M",
        "trend":  "up",
        "note":   "Annual inflows 2024",
        "source": "Bank of Zambia",
        "raw":    640,
    },
    {
        "label":  "External Debt",
        "value":  "$13.4B",
        "trend":  "down",
        "note":   "Post-restructure 2024",
        "source": "Ministry of Finance",
        "raw":    13.4,
    },
]

FALLBACK_NEWS = [
    {
        "headline": "Zambia GDP Growth Projected at 4.6% for 2024",
        "summary":  "IMF and World Bank project sustained growth driven by mining recovery and improved power supply.",
        "date":     "2024",
        "category": "Economy",
        "source":   "IMF Article IV",
        "url":      "https://imf.org/zambia",
        "fetched":  False,
    },
    {
        "headline": "Inflation Rises to 16.0% — ZamStats February 2025",
        "summary":  "Annual inflation increased driven by food prices and Kwacha depreciation. Food inflation at 17.2%.",
        "date":     "Feb 2025",
        "category": "Prices",
        "source":   "ZamStats",
        "url":      "https://zamstats.gov.zm",
        "fetched":  False,
    },
    {
        "headline": "CDF Disbursements Reach K28.3 Billion Nationally",
        "summary":  "CDF disbursements accelerated in 2025 with emphasis on rural electrification and school rehabilitation.",
        "date":     "2025",
        "category": "Development",
        "source":   "Ministry of Finance",
        "url":      "https://mof.gov.zm",
        "fetched":  False,
    },
    {
        "headline": "Copper Rebounds to $9,650/tonne on LME",
        "summary":  "Copper prices strengthened on Chinese demand recovery. Zambia's mining revenue expected to increase.",
        "date":     "Mar 2025",
        "category": "Mining",
        "source":   "LME",
        "url":      "https://lme.com",
        "fetched":  False,
    },
    {
        "headline": "CEEC SME Loan Disbursements Hit K2.4 Billion",
        "summary":  "The Citizens Economic Empowerment Commission surpassed its annual target across key sectors.",
        "date":     "2025",
        "category": "Finance",
        "source":   "CEEC",
        "url":      "https://ceec.org.zm",
        "fetched":  False,
    },
    {
        "headline": "Agriculture Sector Records Strong 2024/25 Harvest",
        "summary":  "Favourable rainfall and FISP support drove record maize production. FRA purchased over 900,000MT.",
        "date":     "2025",
        "category": "Agriculture",
        "source":   "Ministry of Agriculture",
        "url":      "https://agri.gov.zm",
        "fetched":  False,
    },
]


# ── Cache helpers ─────────────────────────────────────────────────────────────
def _cache_get(key):
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > entry["ttl"]:
        del _cache[key]
        return None
    return entry["data"]

def _cache_set(key, data, ttl):
    _cache[key] = {"data": data, "ts": time.time(), "ttl": ttl}


# ── World Bank: fetch trend direction only ────────────────────────────────────
async def _fetch_wb_trends(client: httpx.AsyncClient) -> dict:
    """Returns {indicator_label: 'up'|'down'|'flat'} from WB historical data."""
    trends = {}
    for key, (ind_id, label) in WB_INDICATORS.items():
        try:
            url  = WB_BASE.format(indicator=ind_id)
            resp = await client.get(url, timeout=FETCH_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if data and len(data) > 1:
                entries = [e for e in data[1] if e.get("value") is not None]
                if len(entries) >= 2:
                    trend = "up" if entries[0]["value"] > entries[1]["value"] else "down"
                    trends[label] = trend
        except Exception:
            pass
    return trends


async def get_indicators() -> list:
    cached = _cache_get("indicators")
    if cached:
        return cached

    # Start with our current 2025 estimates
    result = [dict(ind) for ind in CURRENT_INDICATORS]

    # Try to update trend directions from World Bank
    try:
        async with httpx.AsyncClient() as client:
            wb_trends = await _fetch_wb_trends(client)

        # Update trend direction from WB where available
        wb_label_map = {ind["label"]: ind for ind in result}
        for wb_label, trend in wb_trends.items():
            # Match by partial label
            for ind in result:
                if any(word in ind["label"].lower() for word in wb_label.lower().split()):
                    ind["trend"] = trend
                    break

        logger.info(f"WB trend data applied to {len(wb_trends)} indicators")
    except Exception as e:
        logger.debug(f"WB trend fetch skipped: {e}")

    _cache_set("indicators", result, CACHE_TTL_INDICATORS)
    return result


# ── RSS ───────────────────────────────────────────────────────────────────────
def _classify_category(text: str) -> str:
    text = text.lower()
    if any(w in text for w in ["copper","mining","cobalt","mine","konkola","mopani"]):
        return "Mining"
    if any(w in text for w in ["maize","farm","agricult","harvest","crop","fra","food reserve"]):
        return "Agriculture"
    if any(w in text for w in ["inflation","cpi","price","kwacha","exchange","forex"]):
        return "Prices"
    if any(w in text for w in ["loan","bank","ceec","finance","investment","bond"]):
        return "Finance"
    if any(w in text for w in ["gdp","growth","economy","trade","export","imf","world bank"]):
        return "Economy"
    if any(w in text for w in ["school","hospital","borehole","road","cdf","electri"]):
        return "Development"
    if any(w in text for w in ["start","sme","business","entrepreneur","pacra","company"]):
        return "Business"
    return "General"


def _parse_rss(xml_text: str, source_name: str) -> list:
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.iter("item"):
            title   = item.findtext("title", "").strip()
            desc    = item.findtext("description", "").strip()
            link    = item.findtext("link", "").strip()
            pubdate = item.findtext("pubDate", "").strip()

            if not title or not link:
                continue
            combined = (title + " " + desc).lower()
            if not any(kw in combined for kw in BUSINESS_KEYWORDS):
                continue

            summary = re.sub(r"<[^>]+>", "", desc).strip()
            summary = re.sub(r"\s+", " ", summary)[:280]

            try:
                dt = datetime.strptime(pubdate[:25], "%a, %d %b %Y %H:%M:%S")
                date_str = dt.strftime("%d %b %Y")
            except Exception:
                date_str = pubdate[:16] if pubdate else "Recent"

            items.append({
                "headline": title[:120],
                "summary":  summary or title,
                "date":     date_str,
                "category": _classify_category(title + " " + desc),
                "source":   source_name,
                "url":      link,
                "fetched":  True,
            })
            if len(items) >= 5:
                break
    except Exception as e:
        logger.debug(f"RSS parse error ({source_name}): {e}")
    return items


async def _fetch_rss(client: httpx.AsyncClient, feed: dict) -> list:
    try:
        resp = await client.get(feed["url"], timeout=FETCH_TIMEOUT, follow_redirects=True,
                                headers={"User-Agent": "KIP-NewsBot/2.0"})
        resp.raise_for_status()
        items = _parse_rss(resp.text, feed["name"])
        logger.info(f"RSS {feed['name']}: {len(items)} articles")
        return items
    except Exception as e:
        logger.debug(f"RSS failed ({feed['name']}): {e}")
        return []


async def get_news() -> list:
    cached = _cache_get("news")
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(*[_fetch_rss(client, f) for f in RSS_FEEDS], return_exceptions=True)

        items = []
        for r in results:
            if isinstance(r, list):
                items.extend(r)

        if items:
            items = items[:20]
            _cache_set("news", items, CACHE_TTL_NEWS)
            logger.info(f"News: {len(items)} live articles")
            return items
    except Exception as e:
        logger.warning(f"News fetch error: {e}")

    return FALLBACK_NEWS


async def get_news_and_indicators() -> dict:
    news, indicators = await asyncio.gather(get_news(), get_indicators())
    return {
        "news":         news,
        "indicators":   indicators,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "live":         any(n.get("fetched") for n in news),
    }
