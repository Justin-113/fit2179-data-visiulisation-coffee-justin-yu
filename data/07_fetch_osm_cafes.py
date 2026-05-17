"""
07_fetch_osm_cafes.py
=====================
Fetch cafe locations from OpenStreetMap (via the Overpass API) for the five
largest Australian capital cities.

Strategy:
- One Overpass query per city, using a metropolitan bounding box
- Each query returns nodes AND ways tagged amenity=cafe with their center coords
- Save the raw result as JSON (one file per city) for reproducibility
- A second pass (08_aggregate_osm.py) will summarise → city_cafes.csv

Output (in ../data/raw_osm/):
  - melbourne.json, sydney.json, brisbane.json, perth.json, adelaide.json
  - osm_query_log.txt (timestamps + query strings — for the AI/data audit)

Run:
  python 07_fetch_osm_cafes.py

API: https://overpass-api.de/api/interpreter (no auth needed; please respect
fair-use limits — this script throttles 10s between requests to be polite).
"""

from pathlib import Path
from datetime import datetime
import json
import time
import requests

SCRIPT_DIR = Path(__file__).parent.resolve()
RAW_DIR = SCRIPT_DIR.parent / "data" / "raw_osm"
RAW_DIR.mkdir(parents=True, exist_ok=True)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT = 180  # seconds
THROTTLE = 10  # seconds between requests (be polite)

# Greater metropolitan bounding boxes (south, west, north, east)
# Sourced from Wikipedia/ABS Greater Capital City Statistical Area definitions
CITIES = {
    "melbourne":  (-38.30, 144.50, -37.40, 145.60),
    "sydney":     (-34.30, 150.50, -33.50, 151.45),
    "brisbane":   (-27.80, 152.70, -27.10, 153.40),
    "perth":      (-32.30, 115.60, -31.60, 116.20),
    "adelaide":   (-35.20, 138.40, -34.60, 138.85),
}


def build_query(south: float, west: float, north: float, east: float) -> str:
    """Build an Overpass QL query for amenity=cafe within a bbox.

    Returns nodes (point cafes) and ways (cafes with footprints) with their
    center coordinates and key tags (name, brand, opening_hours, takeaway).
    """
    bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:{TIMEOUT}];
(
  node["amenity"="cafe"]({bbox});
  way["amenity"="cafe"]({bbox});
);
out center tags;
""".strip()


def fetch_city(name: str, bbox: tuple) -> dict:
    """Hit Overpass for one city. Returns the raw JSON response."""
    query = build_query(*bbox)
    print(f"  [{name}] querying bbox {bbox} …")

    headers = {
        # Polite User-Agent — Overpass requires identification
        "User-Agent": "FIT2179-coffee-vis/1.0 (Monash University student project)"
    }
    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers=headers,
        timeout=TIMEOUT + 10,
    )
    response.raise_for_status()
    data = response.json()
    print(f"  [{name}] ✓ {len(data.get('elements', [])):,} elements returned")
    return data, query


def main():
    log_lines = [f"# OSM Overpass query log — {datetime.now().isoformat()}\n"]

    for i, (name, bbox) in enumerate(CITIES.items()):
        if i > 0:
            print(f"  (throttling {THROTTLE}s) …")
            time.sleep(THROTTLE)

        try:
            data, query = fetch_city(name, bbox)
        except Exception as e:
            print(f"  [{name}] ❌ FAILED: {e}")
            log_lines.append(f"\n## {name}: FAILED — {e}\n")
            continue

        # Save raw JSON
        out = RAW_DIR / f"{name}.json"
        with out.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        size_kb = out.stat().st_size / 1024
        print(f"  [{name}] saved {out.name} ({size_kb:.1f} KB)")

        # Log the query for reproducibility
        log_lines.append(
            f"\n## {name}\n"
            f"- bbox: {bbox}\n"
            f"- elements: {len(data.get('elements', [])):,}\n"
            f"- file: {out.name} ({size_kb:.1f} KB)\n"
            f"- query:\n```\n{query}\n```\n"
        )

    # Write log
    log_file = RAW_DIR / "osm_query_log.txt"
    with log_file.open("w", encoding="utf-8") as f:
        f.write("".join(log_lines))
    print(f"\n✓ Log saved to {log_file.name}")

    print("\nNext step: run 08_aggregate_osm.py to produce city_cafes.csv")


if __name__ == "__main__":
    main()
