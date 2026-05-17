"""
01b_filter_zeros.py
====================
Filter out non-producing countries from USDA PSD data.

USDA tracks ~93 countries in its coffee database, but only ~44 actually
produce coffee. The rest (Australia, Canada, EU, Japan, etc.) are tracked
because they're large *consumers/importers* — their production rows are
all zeros and would clutter charts.

This script reads the cleaned CSVs from 01_fetch_usda_psd.py and writes
filtered versions that only include actual producing countries.

Run:
  python 01b_filter_zeros.py
"""

from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"


def filter_producers(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Keep only countries whose max production across all years > 0."""
    max_by_country = df.groupby("country")[value_col].max()
    real_producers = max_by_country[max_by_country > 0].index
    filtered = df[df["country"].isin(real_producers)].copy()
    return filtered


def main():
    print("Filtering out countries with zero production…\n")

    # --- coffee_production.csv (2015+) ---
    src = DATA_DIR / "coffee_production.csv"
    df = pd.read_csv(src)
    before = df["country"].nunique()
    df_filtered = filter_producers(df, "production_bags_1000")
    after = df_filtered["country"].nunique()
    out = DATA_DIR / "coffee_production_clean.csv"
    df_filtered.to_csv(out, index=False)
    print(f"  {src.name:35s} {before} → {after} countries ({len(df_filtered)} rows)")
    print(f"     → {out.name}")

    # --- coffee_production_long.csv (1960+) ---
    src = DATA_DIR / "coffee_production_long.csv"
    df = pd.read_csv(src)
    before = df["country"].nunique()
    df_filtered = filter_producers(df, "production_bags_1000")
    after = df_filtered["country"].nunique()
    out = DATA_DIR / "coffee_production_long_clean.csv"
    df_filtered.to_csv(out, index=False)
    print(f"\n  {src.name:35s} {before} → {after} countries ({len(df_filtered)} rows)")
    print(f"     → {out.name}")

    # --- coffee_arabica_robusta.csv ---
    src = DATA_DIR / "coffee_arabica_robusta.csv"
    df = pd.read_csv(src)
    before = df["country"].nunique()
    df_filtered = filter_producers(df, "production_bags_1000")
    after = df_filtered["country"].nunique()
    out = DATA_DIR / "coffee_arabica_robusta_clean.csv"
    df_filtered.to_csv(out, index=False)
    print(f"\n  {src.name:35s} {before} → {after} countries ({len(df_filtered)} rows)")
    print(f"     → {out.name}")

    # Sanity check: top producers in the latest year
    print("\n" + "=" * 60)
    print("SANITY CHECK — Top 15 producers in latest year")
    print("=" * 60)
    df_recent = pd.read_csv(DATA_DIR / "coffee_production_clean.csv")
    latest = df_recent["year"].max()
    top = (
        df_recent[df_recent["year"] == latest]
        .sort_values("production_bags_1000", ascending=False)
        .head(15)[["country", "production_bags_1000", "production_tonnes"]]
    )
    print(top.to_string(index=False))
    print(f"\n(Year: {latest})")
    print("=" * 60)

    print("\n✅ Done. Use the `_clean.csv` files for chart specs.\n")


if __name__ == "__main__":
    main()
