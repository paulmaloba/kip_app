"""
KIP Forecast API Router
Serves LSTM GDP/Inflation forecasts and CPI commodity data.
"""

import logging
from fastapi import APIRouter
from services.lstm_service import get_gdp_forecast, get_inflation_forecast
from services.cpi_service import (
    get_dashboard_metrics, get_cpi_chart_data, get_all_indicators_summary
)

logger = logging.getLogger("kip.forecast")
router = APIRouter()

# In-memory cache (Redis upgrade path ready)
_cache: dict = {}


def cached(key: str, ttl_seconds: int = 3600):
    """Simple in-memory cache decorator."""
    import time
    def decorator(func):
        async def wrapper(*args, **kwargs):
            now = time.time()
            if key in _cache:
                val, exp = _cache[key]
                if now < exp:
                    return val
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            _cache[key] = (result, now + ttl_seconds)
            return result
        return wrapper
    return decorator


@router.get("/gdp")
async def gdp_forecast():
    """GDP growth rate forecast — 12 months ahead."""
    if "gdp" in _cache:
        return _cache["gdp"]
    data = get_gdp_forecast()
    _cache["gdp"] = data
    return data


@router.get("/inflation")
async def inflation_forecast():
    """Annual inflation rate forecast — 12 months ahead."""
    if "inflation" in _cache:
        return _cache["inflation"]
    data = get_inflation_forecast()
    _cache["inflation"] = data
    return data


@router.get("/metrics")
async def dashboard_metrics():
    """Top-level dashboard metrics — inflation rates, USD/ZMW, copper price."""
    return get_dashboard_metrics()


@router.get("/cpi")
async def cpi_summary():
    """All CPI indicator summary cards."""
    return get_all_indicators_summary()


@router.get("/cpi/{indicator}")
async def cpi_indicator(indicator: str):
    """
    Detailed chart data for a specific CPI indicator.
    indicator: 'Maize Grain', 'Petrol', 'Tomatoes', etc.
    """
    # URL decode
    indicator = indicator.replace("-", " ").replace("%20", " ")
    return get_cpi_chart_data(indicator)


@router.get("/all")
async def all_forecasts():
    """All forecast data in one call — for dashboard initial load."""
    gdp        = get_gdp_forecast()
    inflation  = get_inflation_forecast()
    metrics    = get_dashboard_metrics()
    cpi        = get_all_indicators_summary()

    return {
        "gdp":       gdp,
        "inflation": inflation,
        "metrics":   metrics,
        "cpi":       cpi,
    }
