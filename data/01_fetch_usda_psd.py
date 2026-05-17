"""
01_fetch_usda_psd.py
====================
Download and clean USDA Foreign Agricultural Service PSD coffee data.

Source:  https://apps.fas.usda.gov/psdonline/app/index.html#/app/advQuery
Bulk:    https://apps.fas.usda.gov/psdonline/downloads/psd_coffee_csv.zip
Format:  CSV (zipped)
Account: None required

Outputs (to ../data/):
  - coffee_production.csv      → for Vis 01 (world map), Vis 02 (top 10), Vis 03 (60yr trend)
  - coffee_arabica_robusta.csv → for Vis 04 (Arabica vs Robusta split)

Run:
  pip install pandas requests
  python 01_fetch_usda_psd.py
"""

import io
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
USDA_ZIP_URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_coffee_csv.zip"

# Output directory (relative to this script). Adjust if your repo layout differs.
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Filter to last 10 years to keep files small; charts use 2015–latest.
YEAR_MIN = 2015

# How we map USDA "Attribute_Description" strings to the values we care about.
# (The raw CSV has long attribute names like "Production" / "Arabica Production".)
ATTR_PRODUCTION = "Production"
ATTR_PRODUCTION_ARABICA = "Arabica Production"
ATTR_PRODUCTION_ROBUSTA = "Robusta Production"


# ---------------------------------------------------------------------------
# Step 1 — Download the bulk ZIP
# ---------------------------------------------------------------------------
def download_usda_zip() -> pd.DataFrame:
    """Download USDA PSD coffee CSV (zipped) and return raw DataFrame."""
    print(f"[1/3] Downloading {USDA_ZIP_URL} …")
    resp = requests.get(USDA_ZIP_URL, timeout=60)
    resp.raise_for_status()
    print(f"      Got {len(resp.content)/1024:.0f} KB")

    print("[1/3] Unzipping…")
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        # The ZIP contains one CSV — find it.
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("No CSV found inside USDA ZIP")
        csv_name = csv_names[0]
        print(f"      Found: {csv_name}")
        with zf.open(csv_name) as f:
            df = pd.read_csv(f)

    print(f"      Raw rows: {len(df):,}")
    print(f"      Columns: {list(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# Step 2 — Clean & filter
# ---------------------------------------------------------------------------
def clean_production(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Extract total green-bean production (1000 60-kg bags) per country per year.

    Output columns:
        country, year, production_bags_1000, production_tonnes
    """
    print("[2/3] Cleaning total production …")

    # USDA columns of interest (the bulk CSV has long names):
    # 'Country_Name', 'Market_Year', 'Attribute_Description', 'Value', 'Unit_Description'
    df = df_raw.copy()

    # Some bulk dumps use slightly different column names — normalise.
    rename = {}
    for col in df.columns:
        cl = col.strip().lower()
        if cl in ("country_name", "country"):
            rename[col] = "country"
        elif cl in ("market_year", "year", "marketyear"):
            rename[col] = "year"
        elif cl in ("attribute_description", "attribute"):
            rename[col] = "attribute"
        elif cl in ("value",):
            rename[col] = "value"
        elif cl in ("unit_description", "unit"):
            rename[col] = "unit"
    df = df.rename(columns=rename)

    # Drop rows with missing essentials
    needed = ["country", "year", "attribute", "value"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"Expected columns {needed}, got {list(df.columns)}. "
            "USDA may have changed schema — inspect df_raw."
        )

    df = df.dropna(subset=needed)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

    # Keep only Production rows
    prod = df[df["attribute"].str.strip() == ATTR_PRODUCTION].copy()

    # USDA reports in "1000 60-kg bags" — convert to tonnes for human-readable charts
    # 1 bag = 60 kg, so 1000 bags = 60 tonnes
    prod["production_bags_1000"] = prod["value"]
    prod["production_tonnes"] = prod["value"] * 60

    # Filter recent years for the small-files version
    prod_recent = prod[prod["year"] >= YEAR_MIN].copy()

    out = (
        prod_recent[["country", "year", "production_bags_1000", "production_tonnes"]]
        .sort_values(["country", "year"])
        .reset_index(drop=True)
    )

    # Also keep a long-history version for the "60 years of trade" chart (Vis 03)
    out_long = (
        prod[["country", "year", "production_bags_1000", "production_tonnes"]]
        .sort_values(["country", "year"])
        .reset_index(drop=True)
    )

    print(f"      Recent rows ({YEAR_MIN}+): {len(out):,}")
    print(f"      Long-history rows: {len(out_long):,}")
    return out, out_long


def clean_arabica_robusta(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Extract Arabica vs Robusta production split per country per year.
    Not every country reports both — that's fine.

    Output columns:
        country, year, species, production_bags_1000
    """
    print("[2/3] Cleaning Arabica/Robusta split …")

    df = df_raw.copy()
    rename = {}
    for col in df.columns:
        cl = col.strip().lower()
        if cl in ("country_name", "country"):
            rename[col] = "country"
        elif cl in ("market_year", "year"):
            rename[col] = "year"
        elif cl in ("attribute_description", "attribute"):
            rename[col] = "attribute"
        elif cl in ("value",):
            rename[col] = "value"
    df = df.rename(columns=rename)

    df = df.dropna(subset=["country", "year", "attribute", "value"])
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

    mask = df["attribute"].isin([ATTR_PRODUCTION_ARABICA, ATTR_PRODUCTION_ROBUSTA])
    split = df[mask].copy()

    # Map attribute → species name for cleaner charts
    split["species"] = split["attribute"].map(
        {ATTR_PRODUCTION_ARABICA: "Arabica", ATTR_PRODUCTION_ROBUSTA: "Robusta"}
    )
    split["production_bags_1000"] = split["value"]

    split = split[split["year"] >= YEAR_MIN]

    out = (
        split[["country", "year", "species", "production_bags_1000"]]
        .sort_values(["country", "year", "species"])
        .reset_index(drop=True)
    )

    print(f"      Arabica/Robusta rows ({YEAR_MIN}+): {len(out):,}")
    return out


# ---------------------------------------------------------------------------
# Step 3 — Write outputs
# ---------------------------------------------------------------------------
def write_outputs(prod_recent, prod_long, arabica_robusta):
    print(f"[3/3] Writing CSVs to {DATA_DIR} …")

    f1 = DATA_DIR / "coffee_production.csv"
    prod_recent.to_csv(f1, index=False)
    print(f"      ✓ {f1.name}  ({f1.stat().st_size/1024:.1f} KB, {len(prod_recent)} rows)")

    f2 = DATA_DIR / "coffee_production_long.csv"
    prod_long.to_csv(f2, index=False)
    print(f"      ✓ {f2.name}  ({f2.stat().st_size/1024:.1f} KB, {len(prod_long)} rows)")

    f3 = DATA_DIR / "coffee_arabica_robusta.csv"
    arabica_robusta.to_csv(f3, index=False)
    print(f"      ✓ {f3.name}  ({f3.stat().st_size/1024:.1f} KB, {len(arabica_robusta)} rows)")


# ---------------------------------------------------------------------------
# Sanity checks — print sample data so you can eyeball it
# ---------------------------------------------------------------------------
def sanity_check(prod_recent, prod_long, arabica_robusta):
    print("\n" + "=" * 70)
    print("SANITY CHECK — sample data")
    print("=" * 70)

    print("\n--- Top 10 producers (latest year) ---")
    latest = prod_recent["year"].max()
    top10 = (
        prod_recent[prod_recent["year"] == latest]
        .sort_values("production_bags_1000", ascending=False)
        .head(10)[["country", "production_bags_1000", "production_tonnes"]]
    )
    print(top10.to_string(index=False))

    print("\n--- Arabica vs Robusta (latest year, top 5 countries by total) ---")
    ar_latest = arabica_robusta[arabica_robusta["year"] == latest]
    pivot = (
        ar_latest.pivot_table(
            index="country", columns="species", values="production_bags_1000", aggfunc="sum"
        )
        .fillna(0)
    )
    pivot["total"] = pivot.sum(axis=1)
    print(pivot.sort_values("total", ascending=False).head(5).to_string())

    print(f"\nLatest year in data: {latest}")
    print(f"Year range (long): {prod_long['year'].min()} – {prod_long['year'].max()}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    raw = download_usda_zip()
    prod_recent, prod_long = clean_production(raw)
    arabica_robusta = clean_arabica_robusta(raw)
    write_outputs(prod_recent, prod_long, arabica_robusta)
    sanity_check(prod_recent, prod_long, arabica_robusta)
    print("\n✅ Done. Send me the three CSVs and I'll write the Vega-Lite specs.\n")


if __name__ == "__main__":
    main()
