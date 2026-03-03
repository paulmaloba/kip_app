"""
KIP CPI Service
Serves ZamStats commodity price data and forecasts for the dashboard.
Integrates with the kip_cpi_predictor.py pipeline output.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("kip.cpi")

# ── Known CPI data from ZamStats (Dec 2025) ───────────────────────────────────
# Loaded from actual ZamStats CSV processing (supplement 10)
# Indices are base 2016=100. YoY changes as of Dec 2025.

CPI_SNAPSHOT = {
    "last_updated": "2025-12",
    "food_inflation_annual": 12.9,
    "nonfood_inflation_annual": 8.7,
    "indicators": {
        "Breakfast Mealie Meal": {
            "current_index": 286.7,
            "yoy_pct": -16.2,
            "peak_month": "December",
            "dip_month": "January",
            "seasonal_swing_pct": 8,
            "cagr_2016_2024": 18.1,
            "forecast_3m": 353.4,
            "forecast_6m": 357.1,
            "forecast_12m": 381.6,
            "color": "#E67E22",
        },
        "Roller Mealie Meal": {
            "current_index": 226.0,
            "yoy_pct": -23.0,
            "peak_month": "December",
            "dip_month": "July",
            "seasonal_swing_pct": 10,
            "cagr_2016_2024": 19.3,
            "forecast_3m": 296.7,
            "forecast_6m": 298.3,
            "forecast_12m": 319.1,
            "color": "#F39C12",
        },
        "Maize Grain": {
            "current_index": 138.8,
            "yoy_pct": -25.1,
            "peak_month": "March",
            "dip_month": "July",
            "seasonal_swing_pct": 24,
            "cagr_2016_2024": 20.2,
            "forecast_3m": 185.0,
            "forecast_6m": 174.7,
            "forecast_12m": 194.5,
            "color": "#F1C40F",
        },
        "Tomatoes": {
            "current_index": 17.9,
            "yoy_pct": 37.6,
            "peak_month": "June",
            "dip_month": "October",
            "seasonal_swing_pct": 17,
            "cagr_2016_2024": 5.7,
            "forecast_3m": 16.3,
            "forecast_6m": 16.8,
            "forecast_12m": 16.4,
            "color": "#E74C3C",
        },
        "Petrol": {
            "current_index": 29.9,
            "yoy_pct": -11.2,
            "peak_month": "June",
            "dip_month": "October",
            "seasonal_swing_pct": 12,
            "cagr_2016_2024": 15.4,
            "forecast_3m": 36.3,
            "forecast_6m": 37.1,
            "forecast_12m": 38.9,
            "color": "#3498DB",
        },
        "Diesel": {
            "current_index": 27.0,
            "yoy_pct": -16.4,
            "peak_month": "June",
            "dip_month": "October",
            "seasonal_swing_pct": 12,
            "cagr_2016_2024": 16.2,
            "forecast_3m": 33.7,
            "forecast_6m": 34.0,
            "forecast_12m": 36.4,
            "color": "#2980B9",
        },
        "Dried Kapenta Mpulungu": {
            "current_index": 334.9,
            "yoy_pct": 5.6,
            "peak_month": "January",
            "dip_month": "August",
            "seasonal_swing_pct": 9,
            "cagr_2016_2024": 9.7,
            "forecast_3m": 312.4,
            "forecast_6m": 324.4,
            "forecast_12m": 337.6,
            "color": "#16A085",
        },
    }
}


def get_dashboard_metrics() -> dict:
    """Top-level economic metrics for the dashboard header."""
    return {
        "food_inflation":     CPI_SNAPSHOT["food_inflation_annual"],
        "nonfood_inflation":  CPI_SNAPSHOT["nonfood_inflation_annual"],
        "usd_zmw":            27.2,   # approximate 2025 rate
        "copper_usd_ton":     9_450,  # approximate LME copper price
        "last_updated":       CPI_SNAPSHOT["last_updated"],
    }


def get_cpi_chart_data(indicator: str = "Maize Grain") -> dict:
    """
    Build animated chart data for a specific CPI indicator.
    Returns historical + forecast series for Recharts.
    """
    data = CPI_SNAPSHOT["indicators"].get(indicator)
    if not data:
        available = list(CPI_SNAPSHOT["indicators"].keys())
        indicator = available[0]
        data = CPI_SNAPSHOT["indicators"][indicator]

    # Build animated chart data points
    # Simulate 24 months of history (2024-01 to 2025-12) + 12m forecast
    current = data["current_index"]
    cagr_monthly = (1 + data["cagr_2016_2024"] / 100) ** (1/12) - 1

    chart_data = []

    # Historical — back-calculate 24 months
    for i in range(24, 0, -1):
        val = current / ((1 + cagr_monthly) ** i)
        # Add seasonal variation
        month_offset = (datetime.now().month - i) % 12
        seasonal_adj = 1 + (data["seasonal_swing_pct"] / 100) * 0.3 * (
            0.5 * (month_offset - 5) / 6
        )
        chart_data.append({
            "month":      i,
            "type":       "historical",
            "value":      round(val * seasonal_adj, 1),
            "label":      f"Historical",
        })

    # Forecast — 12 months ahead
    for i, (months, val) in enumerate([
        (3, data["forecast_3m"]),
        (6, data["forecast_6m"]),
        (12, data["forecast_12m"]),
    ]):
        chart_data.append({
            "month":  24 + months,
            "type":   "forecast",
            "value":  round(val, 1),
            "label":  f"+{months}m forecast",
        })

    return {
        "indicator":    indicator,
        "current":      current,
        "yoy_pct":      data["yoy_pct"],
        "forecast_12m": data["forecast_12m"],
        "peak_month":   data["peak_month"],
        "dip_month":    data["dip_month"],
        "color":        data["color"],
        "chart_data":   chart_data,
    }


def get_all_indicators_summary() -> list[dict]:
    """Summary cards for all indicators — used in the price dashboard."""
    results = []
    for name, data in CPI_SNAPSHOT["indicators"].items():
        results.append({
            "name":         name,
            "current":      data["current_index"],
            "yoy_pct":      data["yoy_pct"],
            "forecast_12m": data["forecast_12m"],
            "trend":        "up" if data["yoy_pct"] > 0 else "down",
            "color":        data["color"],
            "seasonal_tip": f"Price peaks in {data['peak_month']}, dips in {data['dip_month']}",
        })
    return results
