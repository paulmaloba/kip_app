"""
KIP Exchange Rate Service
==========================
Fetches live ZMW exchange rates every hour.
Detects significant movements and creates notifications.

Free API: Open Exchange Rates (free tier — 1000 req/month, enough for hourly)
Fallback:  frankfurter.app (completely free, ECB data — no ZMW but useful for cross rates)
Fallback2: hardcoded Bank of Zambia estimates
"""

import asyncio
import logging
import time
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("kip.rates")

# ── Config ────────────────────────────────────────────────────────────────────
# Sign up free at: https://www.exchangerate-api.com/
# Free tier: 1,500 requests/month — hourly polling = 720/month ✓
EXCHANGE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")
EXCHANGE_API_URL = "https://v6.exchangerate-api.com/v6/{key}/latest/USD"

# Fallback: Open Exchange Rates (also free)
OXR_API_KEY = os.getenv("OXR_API_KEY", "")
OXR_URL     = "https://openexchangerates.org/api/latest.json?app_id={key}&base=USD&symbols=ZMW,GBP,EUR,ZAR,CNY,BWP,TZS,MWK,ZWL"

# Alert threshold — notify if ZMW moves more than this % in one hour
ALERT_THRESHOLD_PCT = 0.5   # 0.5% = significant intraday move
MAJOR_ALERT_PCT     = 2.0   # 2%   = major move — urgent notification

FETCH_INTERVAL_SECONDS = 3600  # 1 hour

# ── In-memory state ───────────────────────────────────────────────────────────
_rate_cache: dict = {
    "rates":        None,   # current rates dict
    "previous":     None,   # previous rates for comparison
    "last_fetched": None,   # timestamp
    "changes":      [],     # recent significant changes
    "history":      [],     # last 24 hourly snapshots
}

# Key pairs to track (all vs USD)
TRACKED_PAIRS = {
    "ZMW": "Zambian Kwacha",
    "ZAR": "South African Rand",
    "GBP": "British Pound",
    "EUR": "Euro",
    "CNY": "Chinese Yuan",
    "BWP": "Botswana Pula",
    "TZS": "Tanzanian Shilling",
    "MWK": "Malawian Kwacha",
}

# Fallback rates (Bank of Zambia approximate — March 2026)
FALLBACK_RATES_VS_USD = {
    "ZMW": 27.2,
    "ZAR": 18.4,
    "GBP": 0.79,
    "EUR": 0.92,
    "CNY": 7.24,
    "BWP": 13.6,
    "TZS": 2580,
    "MWK": 1730,
}


async def _fetch_from_exchangerate_api(client: httpx.AsyncClient) -> Optional[dict]:
    """Primary: ExchangeRate-API free tier."""
    if not EXCHANGE_API_KEY:
        return None
    try:
        url  = EXCHANGE_API_URL.format(key=EXCHANGE_API_KEY)
        resp = await client.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") == "success":
            rates = data.get("conversion_rates", {})
            return {k: v for k, v in rates.items() if k in TRACKED_PAIRS}
    except Exception as e:
        logger.debug(f"ExchangeRate-API failed: {e}")
    return None


async def _fetch_from_oxr(client: httpx.AsyncClient) -> Optional[dict]:
    """Fallback: Open Exchange Rates."""
    if not OXR_API_KEY:
        return None
    try:
        url  = OXR_URL.format(key=OXR_API_KEY)
        resp = await client.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        return {k: v for k, v in rates.items() if k in TRACKED_PAIRS}
    except Exception as e:
        logger.debug(f"OXR failed: {e}")
    return None


async def _fetch_from_frankfurter(client: httpx.AsyncClient) -> Optional[dict]:
    """
    Last resort: Frankfurter (ECB data, free, no key needed).
    ECB doesn't publish ZMW, so we only get EUR crosses — limited but better than nothing.
    """
    try:
        symbols = ",".join([k for k in TRACKED_PAIRS if k not in ("ZMW", "TZS", "MWK", "BWP")])
        url  = f"https://api.frankfurter.app/latest?from=USD&to={symbols}"
        resp = await client.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        return data.get("rates", {})
    except Exception as e:
        logger.debug(f"Frankfurter failed: {e}")
    return None


def _detect_changes(current: dict, previous: dict) -> list[dict]:
    """Compare current vs previous rates and return significant changes."""
    if not previous:
        return []

    changes = []
    for currency, label in TRACKED_PAIRS.items():
        curr_rate = current.get(currency)
        prev_rate = previous.get(currency)
        if not curr_rate or not prev_rate:
            continue

        # Calculate % change
        pct_change = ((curr_rate - prev_rate) / prev_rate) * 100

        if abs(pct_change) >= ALERT_THRESHOLD_PCT:
            direction = "weakened" if (currency == "ZMW" and pct_change > 0) else \
                        "strengthened" if (currency == "ZMW" and pct_change < 0) else \
                        "up" if pct_change > 0 else "down"

            severity = "major" if abs(pct_change) >= MAJOR_ALERT_PCT else "normal"

            # Human-readable message
            if currency == "ZMW":
                if pct_change > 0:
                    msg = f"🔴 Kwacha weakened — USD now K{curr_rate:.2f} (was K{prev_rate:.2f}, {abs(pct_change):.1f}% drop)"
                    impact = "Imports and fuel will cost more. Consider buying USD-priced inputs now."
                else:
                    msg = f"🟢 Kwacha strengthened — USD now K{curr_rate:.2f} (was K{prev_rate:.2f}, {abs(pct_change):.1f}% gain)"
                    impact = "Good time to import or pay USD-denominated loans."
            else:
                msg = f"{label} moved {abs(pct_change):.1f}% — now {curr_rate:.4f} vs USD"
                impact = f"Cross rate: 1 {currency} = K{(curr_rate * current.get('ZMW', 27.2) / curr_rate if currency != 'ZMW' else curr_rate):.2f}"

            changes.append({
                "currency":    currency,
                "label":       label,
                "prev_rate":   round(prev_rate, 4),
                "curr_rate":   round(curr_rate, 4),
                "pct_change":  round(pct_change, 2),
                "direction":   direction,
                "severity":    severity,
                "message":     msg,
                "impact":      impact,
                "timestamp":   datetime.now(timezone.utc).isoformat(),
            })

    return changes


def _build_rate_summary(rates: dict) -> dict:
    """Build the display-ready rate summary."""
    zmw = rates.get("ZMW", FALLBACK_RATES_VS_USD["ZMW"])
    summary = {
        "base":      "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zmw_per_usd": round(zmw, 2),
        "pairs": []
    }

    # ZMW pairs vs major currencies
    for currency, label in TRACKED_PAIRS.items():
        rate_vs_usd = rates.get(currency, FALLBACK_RATES_VS_USD.get(currency))
        if not rate_vs_usd:
            continue

        if currency == "ZMW":
            display = f"1 USD = K{zmw:.2f}"
            zmw_per_unit = None
        else:
            zmw_per_unit = round(zmw / rate_vs_usd, 2)
            display = f"1 {currency} = K{zmw_per_unit:.2f}"

        summary["pairs"].append({
            "currency":      currency,
            "label":         label,
            "rate_vs_usd":   round(rate_vs_usd, 4),
            "zmw_per_unit":  zmw_per_unit,
            "display":       display,
        })

    return summary


async def fetch_rates() -> dict:
    """Fetch current rates from best available source."""
    async with httpx.AsyncClient() as client:
        rates = None

        # Try sources in order
        rates = await _fetch_from_exchangerate_api(client)
        if not rates:
            rates = await _fetch_from_oxr(client)
        if not rates:
            rates = await _fetch_from_frankfurter(client)

        if not rates:
            logger.warning("All rate APIs failed — using fallback rates")
            rates = dict(FALLBACK_RATES_VS_USD)
            return {
                "rates":   rates,
                "source":  "fallback",
                "summary": _build_rate_summary(rates),
                "changes": [],
            }

        source = "live"
        logger.info(f"Rates fetched: USD/ZMW = {rates.get('ZMW', '?')}")

    # Detect changes
    changes = _detect_changes(rates, _rate_cache.get("previous"))

    # Update cache
    _rate_cache["previous"] = _rate_cache["rates"]
    _rate_cache["rates"]    = rates
    _rate_cache["last_fetched"] = time.time()

    # Keep 24h history
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rates":     dict(rates),
    }
    _rate_cache["history"].append(snapshot)
    if len(_rate_cache["history"]) > 24:
        _rate_cache["history"].pop(0)

    # Store recent changes (keep last 20)
    if changes:
        _rate_cache["changes"] = (changes + _rate_cache.get("changes", []))[:20]
        for c in changes:
            logger.info(f"Rate alert: {c['message']}")

    return {
        "rates":   rates,
        "source":  source,
        "summary": _build_rate_summary(rates),
        "changes": changes,
    }


async def get_current_rates() -> dict:
    """Return cached rates, refreshing if stale (>1 hour)."""
    last = _rate_cache.get("last_fetched")
    if not last or time.time() - last > FETCH_INTERVAL_SECONDS:
        return await fetch_rates()

    rates = _rate_cache["rates"] or FALLBACK_RATES_VS_USD
    return {
        "rates":   rates,
        "source":  "cache",
        "summary": _build_rate_summary(rates),
        "changes": _rate_cache.get("changes", []),
    }


def get_recent_alerts() -> list[dict]:
    """Return recent rate change alerts."""
    return _rate_cache.get("changes", [])


def get_rate_history() -> list[dict]:
    """Return last 24 hourly snapshots."""
    return _rate_cache.get("history", [])


async def start_rate_poller():
    """
    Background task — call this from FastAPI lifespan.
    Fetches rates every hour and logs any significant moves.
    """
    logger.info("✓ Exchange rate poller started (1hr interval)")
    while True:
        try:
            result = await fetch_rates()
            if result["changes"]:
                logger.info(f"⚡ {len(result['changes'])} rate alert(s) generated")
        except Exception as e:
            logger.error(f"Rate poller error: {e}")
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)
