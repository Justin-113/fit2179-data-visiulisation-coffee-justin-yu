"""
10_prepare_flow_map.py
======================
Prepare the data for Vis 09's Flow Map: arcs from coffee origin countries
to Australia, sized by 2025 import volume.

Strategy:
- Pick top 12 source countries from UN Comtrade 2025
- Hand-coded centroid lon/lat for each (small number, easier than geocoding)
- Compute a midpoint above the great-circle line for Bezier curves
- Mark Arabica-dominant vs Robusta-dominant origins (from USDA PSD)
- Output a long-format CSV with one row per "arc point" (start, mid, end)

Output:
  data/coffee_flows.csv  — one row per arc waypoint
  data/coffee_origins.csv — one row per origin (for circles)

Run:
  python 10_prepare_flow_map.py
"""

from pathlib import Path
import csv

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"

# Australia destination point (centred over the continent)
AU_LON, AU_LAT = 134.0, -25.0

# Hand-coded centroids for top coffee source countries (lon, lat)
# Centroids approximate to the capital or major coffee-growing region
ORIGINS = {
    "Brazil":           {"lon": -47.9, "lat": -15.8, "species": "Arabica"},   # mostly Arabica
    "Colombia":         {"lon": -74.1, "lat":   4.7, "species": "Arabica"},
    "Viet Nam":         {"lon": 105.8, "lat":  21.0, "species": "Robusta"},
    "Papua New Guinea": {"lon": 147.2, "lat":  -6.3, "species": "Arabica"},
    "Ethiopia":         {"lon":  38.7, "lat":   9.0, "species": "Arabica"},
    "Honduras":         {"lon": -87.2, "lat":  14.1, "species": "Arabica"},
    "India":            {"lon":  77.6, "lat":  12.5, "species": "Robusta"},  # ~62% Robusta
    "Uganda":           {"lon":  32.6, "lat":   0.3, "species": "Robusta"},  # ~80% Robusta
    "Indonesia":        {"lon": 106.8, "lat":  -6.2, "species": "Robusta"},  # ~75% Robusta
    "Peru":             {"lon": -77.0, "lat": -12.0, "species": "Arabica"},
    "Guatemala":        {"lon": -90.5, "lat":  14.6, "species": "Arabica"},
    "Mexico":           {"lon": -99.1, "lat":  19.4, "species": "Arabica"},
}


def read_2025_imports():
    """Get 2025 tonnes per partner from raw Comtrade."""
    imports = {}
    raw = DATA_DIR / "comtrade_au_imports_raw.csv"
    with raw.open("r", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("period", "") != "2025":
                continue
            if r.get("partnerCode", "0") in ("0", "36"):
                continue
            partner = r.get("partnerDesc", "")
            try:
                kg = float(r.get("netWgt", 0) or 0)
            except ValueError:
                continue
            if kg > 0:
                imports[partner] = imports.get(partner, 0) + kg / 1000
    return imports


def compute_midpoint(lon1, lat1, lon2, lat2):
    """Linear midpoint, then lifted up in latitude to make a curving arc."""
    mid_lon = (lon1 + lon2) / 2
    mid_lat = (lat1 + lat2) / 2
    # Lift up by ~20 degrees of latitude so the arc visibly curves
    # (more lift for longer arcs — empirically tune this)
    distance = abs(lon1 - lon2) + abs(lat1 - lat2)
    lift = min(25, distance * 0.20)  # cap lift at 25 degrees
    mid_lat += lift
    return mid_lon, mid_lat


def main():
    imports = read_2025_imports()

    # Build per-origin rows
    origins_rows = []
    flows_rows = []
    for country, meta in ORIGINS.items():
        if country not in imports:
            print(f"  ⚠️  {country} not in 2025 imports — skipping")
            continue
        tonnes = imports[country]
        # Origin point
        origins_rows.append({
            "country": country,
            "lon": meta["lon"],
            "lat": meta["lat"],
            "species": meta["species"],
            "tonnes": round(tonnes, 0)
        })
        # Compute mid waypoint
        mid_lon, mid_lat = compute_midpoint(
            meta["lon"], meta["lat"], AU_LON, AU_LAT
        )
        # 3-point arc: origin → mid → AU
        # The arc id ties all three points together (used in spec to group via "country")
        for order, (lon, lat) in enumerate([
            (meta["lon"], meta["lat"]),
            (mid_lon, mid_lat),
            (AU_LON, AU_LAT),
        ]):
            flows_rows.append({
                "country": country,
                "order": order,
                "lon": round(lon, 2),
                "lat": round(lat, 2),
                "species": meta["species"],
                "tonnes": round(tonnes, 0)
            })

    # Sort origins by tonnes desc
    origins_rows.sort(key=lambda r: -r["tonnes"])
    
    # Write
    out_origins = DATA_DIR / "coffee_origins.csv"
    with out_origins.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=origins_rows[0].keys())
        w.writeheader()
        w.writerows(origins_rows)

    out_flows = DATA_DIR / "coffee_flows.csv"
    with out_flows.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=flows_rows[0].keys())
        w.writeheader()
        w.writerows(flows_rows)

    print(f"✓ {out_origins.name}: {len(origins_rows)} origins")
    print(f"✓ {out_flows.name}: {len(flows_rows)} arc points")
    print()
    print("Top origins by tonnes:")
    for r in origins_rows[:8]:
        print(f"  {r['country']:20s} {r['tonnes']:>8,.0f} t  ({r['species']})")


if __name__ == "__main__":
    main()
