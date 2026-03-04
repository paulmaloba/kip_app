"""
KIP Geo Intelligence Service
=============================
Detects Zambian location mentions in user queries and injects
the relevant town/district profile into KIP's context.

This is what makes KIP answer:
  "Should I open a hardware shop in Solwezi?" with Solwezi-specific
  data about mining supply chain, population, rental costs, etc.
  instead of generic Zambia advice.
"""

import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger("kip.geo")

# ── Load the geo database ─────────────────────────────────────────────────────
_GEO_DB: Optional[dict] = None
_LOCATION_INDEX: Optional[dict] = None   # flat name → town data


def _load_geo_db() -> dict:
    global _GEO_DB
    if _GEO_DB:
        return _GEO_DB
    path = os.path.join(os.path.dirname(__file__), "..", "data", "zambia_geo.json")
    path = os.path.abspath(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            _GEO_DB = json.load(f)
        logger.info(f"✓ Geo database loaded from {path}")
    except FileNotFoundError:
        logger.warning(f"Geo database not found at {path} — geo features disabled")
        _GEO_DB = {"provinces": {}}
    return _GEO_DB


def _build_location_index() -> dict:
    """Build a flat name → town_data index for fast lookup."""
    global _LOCATION_INDEX
    if _LOCATION_INDEX:
        return _LOCATION_INDEX

    db = _load_geo_db()
    index = {}

    for province_key, province in db.get("provinces", {}).items():
        province_name = province.get("name", "")
        # Add province itself
        index[province_name.lower()] = {"type": "province", "data": province}
        index[province_key.lower()] = {"type": "province", "data": province}

        for town_key, town in province.get("towns", {}).items():
            town_name = town.get("name", "").lower()
            index[town_name] = {
                "type":     "town",
                "data":     town,
                "province": province_name,
            }
            # Also index by key
            index[town_key.lower().replace("_", " ")] = {
                "type":     "town",
                "data":     town,
                "province": province_name,
            }

    _LOCATION_INDEX = index
    logger.info(f"✓ Location index built: {len(index)} entries")
    return index


def detect_locations(text: str) -> list[dict]:
    """
    Scan text for Zambian location mentions.
    Returns list of matched town/province data objects.
    """
    index = _build_location_index()
    text_lower = text.lower()
    found = []
    seen_names = set()

    # Sort by length descending so "North-Western Province" matches before "Western"
    sorted_names = sorted(index.keys(), key=len, reverse=True)

    for name in sorted_names:
        if name in seen_names:
            continue
        # Word boundary match
        pattern = r'\b' + re.escape(name) + r'\b'
        if re.search(pattern, text_lower):
            entry = index[name]
            found.append(entry)
            seen_names.add(name)
            # Mark sub-names as seen to avoid double-matching
            for sub in sorted_names:
                if sub != name and sub in name:
                    seen_names.add(sub)

    return found[:3]  # Max 3 locations per query


def build_geo_context(locations: list[dict]) -> str:
    """Convert matched location data into a context string for KIP."""
    if not locations:
        return ""

    parts = ["=== ZAMBIAN LOCATION INTELLIGENCE ==="]

    for loc in locations:
        data    = loc["data"]
        loc_type = loc["type"]
        province = loc.get("province", "")

        if loc_type == "town":
            t = data
            name = t.get("name", "Unknown")
            parts.append(f"\n📍 {name} ({province})")
            parts.append(f"Type: {t.get('type', '').replace('_', ' ').title()}")
            parts.append(f"Population: {t.get('population', 'Unknown'):,}" if isinstance(t.get('population'), int) else f"Population: {t.get('population', 'Unknown')}")

            ep = t.get("economic_profile", {})
            if ep:
                if ep.get("dominant_industries"):
                    parts.append(f"Main industries: {', '.join(ep['dominant_industries'][:5])}")
                if ep.get("average_monthly_income_zmw"):
                    parts.append(f"Average monthly income: K{ep['average_monthly_income_zmw']:,}")
                if ep.get("business_density"):
                    parts.append(f"Business density: {ep['business_density'].replace('_', ' ')}")
                if ep.get("fastest_growing_sectors"):
                    parts.append(f"Fastest growing sectors: {', '.join(ep['fastest_growing_sectors'][:4])}")
                if ep.get("notable"):
                    parts.append(f"Key note: {ep['notable']}")

            infra = t.get("infrastructure", {})
            if infra:
                parts.append(f"Power: {infra.get('power_reliability', 'unknown')} "
                              f"(~{infra.get('load_shedding_hours_per_day', '?')} hrs load shedding/day)")
                parts.append(f"Internet: {infra.get('internet_quality', 'unknown')}")
                parts.append(f"Roads: {infra.get('road_quality', 'unknown')}")
                if infra.get("airport"):
                    parts.append(f"Airport: {infra['airport']}")

            be = t.get("business_environment", {})
            if be:
                if be.get("rental_cost_commercial_zmw_per_sqm"):
                    parts.append(f"Commercial rent: ~K{be['rental_cost_commercial_zmw_per_sqm']}/sqm/month")
                if be.get("rental_cost_residential_zmw"):
                    parts.append(f"Residential rent: ~K{be['rental_cost_residential_zmw']}/month")
                if be.get("key_challenges"):
                    parts.append(f"Key challenges: {', '.join(be['key_challenges'][:3])}")
                if be.get("unique_opportunities"):
                    parts.append(f"Best opportunities: {', '.join(be['unique_opportunities'][:4])}")
                if be.get("banks_present"):
                    parts.append(f"Banks available: {', '.join(be['banks_present'][:4])}")

            cb = t.get("cross_border", {})
            if cb and any(cb.get(k) for k in ["drc_proximity_km", "malawi_km", "tanzania_km", "zimbabwe_km", "zambia_km", "namibia_km", "angola_km"]):
                for country_key in ["drc", "malawi", "tanzania", "zimbabwe", "namibia", "angola", "botswana"]:
                    km_key = f"{country_key}_km"
                    if cb.get(km_key):
                        parts.append(f"Border: {country_key.upper()} — {cb[km_key]}km away")
                if cb.get("cross_border_opportunities"):
                    parts.append(f"Cross-border opportunities: {', '.join(cb['cross_border_opportunities'][:3])}")

            ci = t.get("consumer_insights", {})
            if ci:
                if ci.get("spending_power"):
                    parts.append(f"Consumer spending power: {ci['spending_power']}")
                if ci.get("notable"):
                    parts.append(f"Consumer note: {ci['notable']}")

        elif loc_type == "province":
            p = data
            parts.append(f"\n🗺️  {p.get('name', 'Unknown Province')}")
            parts.append(f"Key sectors: {', '.join(p.get('key_sectors', []))}")
            parts.append(f"GDP contribution: ~{p.get('gdp_contribution_pct', '?')}% of national GDP")
            if p.get("population"):
                parts.append(f"Population: ~{p['population']:,}")

    parts.append("\n=== Use this local data to give highly specific, accurate advice ===")
    return "\n".join(parts)


def get_geo_context_for_query(query: str) -> str:
    """
    Main entry point: given a user query, return geo context string.
    Returns empty string if no Zambian location is detected.
    """
    locations = detect_locations(query)
    if not locations:
        return ""
    context = build_geo_context(locations)
    detected = [loc["data"].get("name", "") for loc in locations]
    logger.info(f"Geo context injected for: {detected}")
    return context


def get_all_towns() -> list[str]:
    """Return all known town names — for autocomplete or validation."""
    index = _build_location_index()
    return [name for name, entry in index.items() if entry["type"] == "town"]


def get_town_data(town_name: str) -> Optional[dict]:
    """Get full data for a specific town."""
    index = _build_location_index()
    return index.get(town_name.lower())
