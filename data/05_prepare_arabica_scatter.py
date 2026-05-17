"""
05_prepare_arabica_scatter.py
==============================
Prepare Vis 04 data — Arabica vs Robusta scatter plot.

For each coffee-producing country in the latest marketing year:
- Total production (1000 bags) → X axis (log scale)
- Arabica share (%)            → Y axis
- Total production              → bubble size
- Variety category              → color

Output:
  - coffee_species_scatter.csv → for Vis 04 (scatter plot)

Run:
  python 05_prepare_arabica_scatter.py
"""

from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"

# Minimum production to include — filter out tiny producers that would clutter
MIN_PRODUCTION = 200  # 1000 × 60-kg bags (≈ 12,000 tonnes)


def categorize(arabica_pct: float) -> str:
    """Bucket countries by their Arabica/Robusta mix."""
    if arabica_pct >= 95:
        return "Pure Arabica"
    elif arabica_pct >= 60:
        return "Arabica-dominant"
    elif arabica_pct >= 40:
        return "Mixed"
    elif arabica_pct >= 5:
        return "Robusta-dominant"
    else:
        return "Pure Robusta"


def main():
    src = DATA_DIR / "coffee_arabica_robusta_clean.csv"
    df = pd.read_csv(src)

    latest = df["year"].max()
    print(f"Using latest year: {latest}")

    df_latest = df[df["year"] == latest]

    # Pivot wide: one row per country with Arabica and Robusta columns
    pivot = (
        df_latest.pivot_table(
            index="country",
            columns="species",
            values="production_bags_1000",
            aggfunc="sum",
        )
        .fillna(0)
        .reset_index()
    )

    # Make sure both species columns exist (avoid KeyError if data is missing)
    if "Arabica" not in pivot.columns:
        pivot["Arabica"] = 0
    if "Robusta" not in pivot.columns:
        pivot["Robusta"] = 0

    # Compute total and Arabica percentage
    pivot["total"] = pivot["Arabica"] + pivot["Robusta"]
    pivot = pivot[pivot["total"] >= MIN_PRODUCTION].copy()
    pivot["arabica_pct"] = (pivot["Arabica"] / pivot["total"] * 100).round(1)

    # Categorise
    pivot["variety_mix"] = pivot["arabica_pct"].apply(categorize)

    # Round / cast for cleaner display
    pivot["Arabica"] = pivot["Arabica"].astype(int)
    pivot["Robusta"] = pivot["Robusta"].astype(int)
    pivot["total"] = pivot["total"].astype(int)

    # Sort: large producers first (annotations look nicer in this order)
    pivot = pivot.sort_values("total", ascending=False).reset_index(drop=True)

    # Final columns
    out_df = pivot[
        ["country", "Arabica", "Robusta", "total", "arabica_pct", "variety_mix"]
    ].rename(columns={"Arabica": "arabica_bags", "Robusta": "robusta_bags"})

    out = DATA_DIR / "coffee_species_scatter.csv"
    out_df.to_csv(out, index=False)
    print(f"\n✓ Saved {out.name} "
          f"({out.stat().st_size/1024:.1f} KB, {len(out_df)} countries)")

    # Preview
    print("\n--- Preview (sorted by total production) ---")
    print(out_df.to_string(index=False))

    # Category distribution
    print("\n--- Distribution by category ---")
    print(out_df["variety_mix"].value_counts().to_string())


if __name__ == "__main__":
    main()
