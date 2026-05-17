"""
09_prepare_imports_vs_price.py
==============================
Combine Australian coffee import data (UN Comtrade) with international coffee
prices (World Bank Pink Sheet) into a single year-by-year CSV for Vis 08.

Output:
  data/imports_vs_price.csv  (~1 KB, 11 rows)

Fields:
  year                   2015..2025
  au_imports_tonnes      Australia's total coffee imports (HS 0901), all partners
  au_imports_value_usd   Total value, USD
  au_unit_price_usd      Derived: value / tonnes
  arabica_price_usd_kg   Annual average from monthly Pink Sheet ($/kg)
  robusta_price_usd_kg   Annual average from monthly Pink Sheet ($/kg)

Run:
  python 09_prepare_imports_vs_price.py
"""

from pathlib import Path
from collections import defaultdict
import csv
import openpyxl

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent / "data"


def annual_au_imports():
    """Sum up all-country imports from UN Comtrade volume CSV to get year totals."""
    tonnes = defaultdict(float)
    value = defaultdict(float)
    src = DATA_DIR / "au_imports_volume.csv"
    with src.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            y = int(row["year"])
            tonnes[y] += float(row["volume_tonnes"])
            value[y] += float(row["value_usd"])
    return tonnes, value


def annual_pink_sheet_prices():
    """Read monthly Arabica & Robusta from Pink Sheet, return annual averages."""
    src = DATA_DIR / "CMO-Historical-Data-Monthly.xlsx"
    wb = openpyxl.load_workbook(src, data_only=True)
    ws = wb["Monthly Prices"]
    # Row layout:
    # Row 5: commodity names (Coffee Arabica @ col 12, Coffee Robusta @ col 13)
    # Row 6: units
    # Row 7+: data, col 0 = period "YYYY-MM"
    by_year_a = defaultdict(list)
    by_year_r = defaultdict(list)
    for row in ws.iter_rows(min_row=7, values_only=True):
        period = row[0]
        if not period or not isinstance(period, str):
            continue
        if not period.startswith(("2015", "2016", "2017", "2018", "2019",
                                  "2020", "2021", "2022", "2023", "2024", "2025")):
            continue
        year = int(period[:4])
        arabica = row[12]
        robusta = row[13]
        if isinstance(arabica, (int, float)):
            by_year_a[year].append(arabica)
        if isinstance(robusta, (int, float)):
            by_year_r[year].append(robusta)
    # Average per year
    return (
        {y: sum(vals) / len(vals) for y, vals in by_year_a.items()},
        {y: sum(vals) / len(vals) for y, vals in by_year_r.items()},
    )


def main():
    tonnes, value = annual_au_imports()
    arabica, robusta = annual_pink_sheet_prices()

    years = sorted(set(tonnes.keys()) & set(arabica.keys()))

    rows = []
    for y in years:
        t = tonnes[y]
        v = value[y]
        rows.append({
            "year": y,
            "au_imports_tonnes": round(t, 0),
            "au_imports_value_usd": round(v, 0),
            "au_unit_price_usd": round(v / t, 2),
            "arabica_price_usd_kg": round(arabica[y], 2),
            "robusta_price_usd_kg": round(robusta[y], 2),
        })

    # Print summary
    print("Year | Imports(t) | Value(USD M) | Unit($/t) | Arabica($/kg) | Robusta($/kg)")
    for r in rows:
        print(
            f"{r['year']} | {r['au_imports_tonnes']:7,.0f}  | "
            f"${r['au_imports_value_usd']/1e6:7,.0f}     | "
            f"${r['au_unit_price_usd']:6.0f}    | "
            f"${r['arabica_price_usd_kg']:5.2f}        | "
            f"${r['robusta_price_usd_kg']:5.2f}"
        )

    out = DATA_DIR / "imports_vs_price.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✓ Saved {out.name} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
