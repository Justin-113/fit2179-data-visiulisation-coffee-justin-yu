"""
02_prepare_world_map.py
========================
Prepare Vis 01 (world choropleth) data.

The world TopoJSON we'll use (Vega's `world-110m.json`) identifies countries
by **numeric ISO codes** (Brazil = 76, Vietnam = 704, etc.). Our USDA data
uses country names ("Brazil", "Vietnam"). We need to attach numeric ISO codes
to each row so Vega-Lite's `lookup` transform can join them.

Outputs to ../data/:
  - coffee_world_map.csv → for Vis 01 (world choropleth)

Run:
  python 02_prepare_world_map.py
"""

from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"

# USDA country name → numeric ISO 3166-1 code (matches world-110m.json `id` field)
# Only included countries are those actually producing coffee in our data.
USDA_TO_ISO = {
    "Angola": 24,
    "Bolivia": 68,
    "Brazil": 76,
    "Burundi": 108,
    "Cameroon": 120,
    "Central African Republic": 140,
    "China": 156,
    "Colombia": 170,
    "Congo (Kinshasa)": 180,        # DR Congo
    "Costa Rica": 188,
    "Cote d'Ivoire": 384,
    "Cuba": 192,
    "Dominican Republic": 214,
    "Ecuador": 218,
    "El Salvador": 222,
    "Ethiopia": 231,
    "Ghana": 288,
    "Guatemala": 320,
    "Guinea": 324,
    "Honduras": 340,
    "India": 356,
    "Indonesia": 360,
    "Jamaica": 388,
    "Kenya": 404,
    "Laos": 418,
    "Madagascar": 450,
    "Malawi": 454,
    "Malaysia": 458,
    "Mexico": 484,
    "Nicaragua": 558,
    "Nigeria": 566,
    "Panama": 591,
    "Papua New Guinea": 598,
    "Peru": 604,
    "Philippines": 608,
    "Rwanda": 646,
    "Sierra Leone": 694,
    "Tanzania": 834,
    "Thailand": 764,
    "Togo": 768,
    "Uganda": 800,
    "United States": 840,
    "Venezuela": 862,
    "Vietnam": 704,
}


def main():
    src = DATA_DIR / "coffee_production_clean.csv"
    df = pd.read_csv(src)

    # Keep latest year only for the map snapshot
    latest = df["year"].max()
    df_latest = df[df["year"] == latest].copy()
    print(f"Latest year: {latest}, {len(df_latest)} country rows")

    # Add ISO numeric code
    df_latest["iso_id"] = df_latest["country"].map(USDA_TO_ISO)

    # Sanity check — any countries we missed?
    missing = df_latest[df_latest["iso_id"].isna()]["country"].tolist()
    if missing:
        print(f"⚠️  Missing ISO codes for: {missing}")
        print("   Add them to USDA_TO_ISO and rerun.")
    else:
        print("✓ All countries mapped to ISO codes.")

    # Drop missing and convert to integer
    df_latest = df_latest.dropna(subset=["iso_id"])
    df_latest["iso_id"] = df_latest["iso_id"].astype(int)

    # Only keep producing countries (filter out zero-production rows)
    df_latest = df_latest[df_latest["production_bags_1000"] > 0]

    # Round tonnes to whole numbers for tooltips
    df_latest["production_tonnes"] = df_latest["production_tonnes"].astype(int)

    out = df_latest[["iso_id", "country", "year", "production_bags_1000", "production_tonnes"]]
    out_path = DATA_DIR / "coffee_world_map.csv"
    out.to_csv(out_path, index=False)
    print(f"\n✓ Saved {out_path.name} ({len(out)} rows, "
          f"{out_path.stat().st_size/1024:.1f} KB)")

    # Preview
    print("\n--- Preview (Top 15) ---")
    print(
        out.sort_values("production_bags_1000", ascending=False)
        .head(15)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
