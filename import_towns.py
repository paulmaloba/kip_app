"""
KIP Geo Data Importer
======================
Run this script whenever you have new town data collected manually.
It merges your CSV entries into zambia_geo.json.

Usage:
    python import_towns.py my_new_towns.csv
"""

import csv
import json
import sys
import os
from pathlib import Path

GEO_FILE = Path(__file__).parent.parent / "data" / "zambia_geo.json"

PROVINCE_MAP = {
    "lusaka":        "lusaka",
    "copperbelt":    "copperbelt",
    "southern":      "southern",
    "eastern":       "eastern",
    "northern":      "northern",
    "luapula":       "luapula",
    "north-western": "north_western",
    "north western": "north_western",
    "northwestern":  "north_western",
    "western":       "western",
    "central":       "central",
    "muchinga":      "muchinga",
}


def csv_to_town(row: dict) -> tuple[str, dict]:
    """Convert a CSV row into (town_key, town_dict)."""
    name = row.get("town_name", "").strip()
    key  = name.lower().replace(" ", "_").replace("-", "_")

    industries = [i.strip() for i in row.get("dominant_industries", "").split(",") if i.strip()]
    employers  = [e.strip() for e in row.get("major_employers", "").split(",") if e.strip()]
    markets    = [m.strip() for m in row.get("major_markets", "").split(",") if m.strip()]
    challenges = [c.strip() for c in row.get("key_challenges", "").split(",") if c.strip()]
    opps       = [o.strip() for o in row.get("unique_opportunities", "").split(",") if o.strip()]
    growing    = [s.strip() for s in row.get("fastest_growing_sectors", "").split(",") if s.strip()]

    def safe_int(val):
        try: return int(str(val).replace(",", "").strip())
        except: return None

    def safe_float(val):
        try: return float(str(val).replace(",", "").strip())
        except: return None

    town = {
        "name":     name,
        "type":     row.get("type", "district_town").strip(),
        "population": safe_int(row.get("population")),
        "economic_profile": {
            "dominant_industries":    industries,
            "major_markets":          markets,
            "major_employers":        employers,
            "average_monthly_income_zmw": safe_int(row.get("avg_monthly_income_zmw")),
            "business_density":       row.get("business_density", "").strip() or None,
            "fastest_growing_sectors": growing,
        },
        "infrastructure": {
            "power_reliability":        row.get("power_reliability", "").strip() or None,
            "load_shedding_hours_per_day": safe_int(row.get("load_shedding_hours")),
            "water_reliability":        row.get("water_reliability", "").strip() or None,
            "internet_quality":         row.get("internet_quality", "").strip() or None,
            "road_quality":             row.get("road_quality", "").strip() or None,
        },
        "business_environment": {
            "rental_cost_commercial_zmw_per_sqm": safe_float(row.get("commercial_rent_zmw_per_sqm")),
            "rental_cost_residential_zmw":        safe_float(row.get("residential_rent_zmw")),
            "key_challenges":    challenges,
            "unique_opportunities": opps,
        },
    }

    # Add cross-border if present
    cb_country = row.get("cross_border_country", "").strip()
    cb_km      = safe_int(row.get("cross_border_km"))
    cb_opps    = [o.strip() for o in row.get("cross_border_opportunities", "").split(",") if o.strip()]
    if cb_country and cb_km:
        town["cross_border"] = {
            f"{cb_country.lower()}_km": cb_km,
            "cross_border_opportunities": cb_opps,
        }

    if row.get("notes"):
        town["notes"] = row["notes"].strip()

    return key, town


def import_csv(csv_path: str):
    with open(GEO_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)

    added   = 0
    updated = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip comment rows
            if row.get("province", "").startswith("#") or not row.get("town_name"):
                continue

            province_raw = row.get("province", "").strip().lower()
            province_key = PROVINCE_MAP.get(province_raw)
            if not province_key:
                print(f"⚠ Unknown province '{province_raw}' for {row.get('town_name')} — skipping")
                continue

            if province_key not in db["provinces"]:
                print(f"⚠ Province key '{province_key}' not in database — skipping")
                continue

            town_key, town_data = csv_to_town(row)
            existing = db["provinces"][province_key].setdefault("towns", {})

            if town_key in existing:
                existing[town_key].update(town_data)
                updated += 1
                print(f"✓ Updated: {town_data['name']} ({province_key})")
            else:
                existing[town_key] = town_data
                added += 1
                print(f"+ Added:   {town_data['name']} ({province_key})")

    with open(GEO_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done — {added} added, {updated} updated → {GEO_FILE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_towns.py <your_towns.csv>")
        sys.exit(1)
    import_csv(sys.argv[1])
