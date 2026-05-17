"""
04_prepare_au_imports.py
========================
Process UN Comtrade CSV → stacked-share data for Vis 03.

Story: how Australia's coffee source map changed, 2015-2025.

Strategy:
- Identify top N partner countries by total cumulative import volume
- Keep their full year-by-year imports
- Aggregate everyone else into "Other countries"
- Compute SHARE (%) for stacked area chart

Outputs to ../data/:
  - au_imports_share.csv → for Vis 03 (100% stacked area chart)
  - au_imports_volume.csv → backup (raw volumes), for Vis 08/09 later

Input: UN Comtrade CSV downloaded from https://comtradeplus.un.org/
       Saved as `data/comtrade_au_imports_raw.csv`
       (Reporter: Australia, HS 0901, Imports, 2015-2025, All partners)

Run:
  python 04_prepare_au_imports.py
"""

from pathlib import Path
import pandas as pd
import sys

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"
RAW_FILE = DATA_DIR / "comtrade_au_imports_raw.csv"

TOP_N = 6  # Show top 6 individually, rest aggregated


def clean_partner_name(name: str) -> str:
    """Tidy long UN Comtrade country names for chart legibility."""
    mapping = {
        "Viet Nam": "Vietnam",
        "Bolivia (Plurinational State of)": "Bolivia",
        "Venezuela (Bolivarian Republic of)": "Venezuela",
        "Tanzania, United Republic of": "Tanzania",
        "Iran (Islamic Republic of)": "Iran",
        "Republic of Korea": "South Korea",
        "Lao People's Dem. Rep.": "Laos",
        "Russian Federation": "Russia",
        "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
        "United States of America": "United States",
        "Papua New Guinea": "Papua New Guinea",  # OK as-is
    }
    return mapping.get(name, name)


def main():
    if not RAW_FILE.exists():
        sys.exit(
            f"❌ Cannot find {RAW_FILE}.\n"
            f"   Save your UN Comtrade download as 'comtrade_au_imports_raw.csv' "
            f"in the data/ directory."
        )

    print(f"[1/4] Reading {RAW_FILE.name} …")

    # UN Comtrade CSV has a trailing comma → 48 fields per row but 47 headers.
    # Use index_col=False + dtype=str to avoid pandas misalignment.
    df = pd.read_csv(
        RAW_FILE,
        encoding="latin-1",
        dtype=str,
        keep_default_na=False,
        index_col=False,
    )
    # If a 48th empty column slipped in, drop it
    df = df.iloc[:, :47]
    df.columns = df.columns.str.strip()
    print(f"      Loaded {len(df):,} rows")

    # Exclude "World" aggregate rows (partnerCode == "0")
    df = df[df["partnerCode"] != "0"].copy()

    # Convert numeric columns
    df["year"] = df["period"].astype(int)
    df["netWgt"] = pd.to_numeric(df["netWgt"], errors="coerce").fillna(0)
    df["primaryValue"] = pd.to_numeric(df["primaryValue"], errors="coerce").fillna(0)

    # Clean partner names
    df["country"] = df["partnerDesc"].apply(clean_partner_name)

    # Volume in tonnes (kg → tonnes, easier on the eye)
    df["volume_tonnes"] = (df["netWgt"] / 1000).round(0).astype(int)

    print(f"[2/4] Identifying Top {TOP_N} partners by cumulative volume …")
    totals = df.groupby("country")["volume_tonnes"].sum().sort_values(ascending=False)
    top_countries = totals.head(TOP_N).index.tolist()
    print(f"      Top {TOP_N}: {top_countries}")

    # Group: top N keep their name; rest become "Other countries"
    df["group"] = df["country"].where(df["country"].isin(top_countries), "Other countries")

    print("[3/4] Aggregating to year × group …")
    agg = (
        df.groupby(["year", "group"])
        .agg(
            volume_tonnes=("volume_tonnes", "sum"),
            value_usd=("primaryValue", "sum"),
        )
        .reset_index()
    )

    # Compute SHARE within each year
    year_totals = agg.groupby("year")["volume_tonnes"].transform("sum")
    agg["share_pct"] = (agg["volume_tonnes"] / year_totals * 100).round(2)

    # Ensure consistent group order in CSV (top N first by cumulative, then Other)
    group_order = top_countries + ["Other countries"]
    agg["group"] = pd.Categorical(agg["group"], categories=group_order, ordered=True)
    agg = agg.sort_values(["year", "group"]).reset_index(drop=True)

    # Save share CSV (for Vis 03)
    out1 = DATA_DIR / "au_imports_share.csv"
    agg.to_csv(out1, index=False)
    print(f"\n[4/4] ✓ {out1.name}  "
          f"({out1.stat().st_size/1024:.1f} KB, {len(agg)} rows)")

    # Also save the raw aggregated volume (for later viz)
    volume_only = agg[["year", "group", "volume_tonnes", "value_usd"]].copy()
    out2 = DATA_DIR / "au_imports_volume.csv"
    volume_only.to_csv(out2, index=False)
    print(f"      ✓ {out2.name}  "
          f"({out2.stat().st_size/1024:.1f} KB)")

    # Sanity checks — print first / middle / last years
    print("\n" + "=" * 60)
    print("SANITY CHECK")
    print("=" * 60)
    for y in [2015, 2020, 2025]:
        if y in agg["year"].values:
            print(f"\n--- {y} ---")
            sub = agg[agg["year"] == y][["group", "volume_tonnes", "share_pct"]]
            print(sub.to_string(index=False))


if __name__ == "__main__":
    main()
