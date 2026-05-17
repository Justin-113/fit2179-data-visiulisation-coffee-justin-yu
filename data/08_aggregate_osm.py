"""
08_aggregate_osm.py
===================
Process the raw OSM Overpass JSONs from 07_fetch_osm_cafes.py into a tiny
clean CSV for Vis 07 (5-city bubble map).

Strategy:
- Load each city's raw JSON
- Count total cafés
- Identify which have a 'brand' tag (chain) vs none (independent)
- Compute a representative geographic centroid for the city (mean lat/lon)
- Output one row per city to data/city_cafes.csv

This CSV powers:
  - Vis 07: 5-city bubble overlay on AU map
  - Vis 12 (later): chain vs independent split

Output:
  - city_cafes.csv  (~5 rows, well under 1 KB)

Run:
  python 08_aggregate_osm.py
"""

from pathlib import Path
import json
import csv

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"
RAW_DIR = DATA_DIR / "raw_osm"

# Pretty display names + ABS 2024 Greater Capital City populations
CITY_META = {
    "melbourne": {"name": "Melbourne", "population": 5_207_145},
    "sydney":    {"name": "Sydney",    "population": 5_450_496},
    "brisbane":  {"name": "Brisbane",  "population": 2_628_083},
    "perth":     {"name": "Perth",     "population": 2_309_338},
    "adelaide":  {"name": "Adelaide",  "population": 1_446_380},
}


def get_coords(elem: dict) -> tuple | None:
    """Extract (lat, lon) from a node or way center."""
    if "lat" in elem and "lon" in elem:
        return (elem["lat"], elem["lon"])
    if "center" in elem:
        return (elem["center"]["lat"], elem["center"]["lon"])
    return None


def process_city(key: str) -> dict:
    """Aggregate one city's raw JSON."""
    raw_file = RAW_DIR / f"{key}.json"
    if not raw_file.exists():
        return None

    with raw_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])

    # Count + classify
    total = 0
    chain = 0
    independent = 0
    lats, lons = [], []

    for el in elements:
        coords = get_coords(el)
        if not coords:
            continue
        total += 1
        lats.append(coords[0])
        lons.append(coords[1])

        tags = el.get("tags", {})
        if "brand" in tags:
            chain += 1
        else:
            independent += 1

    # Geographic centroid (mean) — gives map-friendly anchor point
    centroid_lat = sum(lats) / len(lats) if lats else None
    centroid_lon = sum(lons) / len(lons) if lons else None

    meta = CITY_META[key]
    return {
        "city": meta["name"],
        "city_key": key,
        "lat": round(centroid_lat, 4) if centroid_lat else None,
        "lon": round(centroid_lon, 4) if centroid_lon else None,
        "cafes_total": total,
        "cafes_chain": chain,
        "cafes_independent": independent,
        "chain_pct": round(chain / total * 100, 1) if total else 0,
        "population": meta["population"],
        "per_10k": round(total / meta["population"] * 10000, 2),
    }


def main():
    print(f"Reading from {RAW_DIR.name}/ …\n")

    rows = []
    for key in CITY_META.keys():
        row = process_city(key)
        if row is None:
            print(f"  [{key}] ⚠️  raw file missing, skipping")
            continue
        rows.append(row)
        print(
            f"  [{key:9s}] total={row['cafes_total']:5d}  "
            f"chain={row['cafes_chain']:4d}  "
            f"independent={row['cafes_independent']:5d}  "
            f"per10k={row['per_10k']:.2f}"
        )

    # Sort by total descending (so the CSV reads naturally)
    rows.sort(key=lambda r: -r["cafes_total"])

    out = DATA_DIR / "city_cafes.csv"
    if rows:
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        size = out.stat().st_size
        print(f"\n✓ Saved {out.name} ({size} bytes, {len(rows)} cities)")


if __name__ == "__main__":
    main()
