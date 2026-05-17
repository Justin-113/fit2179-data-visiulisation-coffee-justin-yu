"""
11_prepare_cpi.py — Prep ABS CPI Table 3 for Vis 11
Source: ABS Consumer Price Index, Australia, March 2026, Table 3 (640103.xlsx)
Series:
  - A130393720C: All groups CPI ; Australia ; (col 1)
  - A130395477A: Food and non-alcoholic beverages ; Australia ; (col 2)
  - A130390640X: Coffee, tea and cocoa ; Australia ; (col 30)
Output: data/cpi_inflation.csv (36 rows = 12 months × 3 series, Apr 2025 - Mar 2026)
"""

from pathlib import Path
import csv
import openpyxl

DATA_DIR = Path(__file__).parent.parent / "data"
COLS = {"All groups CPI": 1, "Food": 2, "Coffee, tea & cocoa": 30}
SAFE_NAMES = {
    "All groups CPI": "All groups CPI",
    "Food": "Food and beverages",
    "Coffee, tea & cocoa": "Coffee tea & cocoa",  # remove comma for CSV safety
}


def main():
    wb = openpyxl.load_workbook(DATA_DIR / "640103.xlsx", data_only=True)
    ws = wb["Data1"]

    raw = []
    for row in ws.iter_rows(min_row=12, values_only=True):
        date = row[0]
        if not date or (date.year, date.month) < (2024, 4):
            continue
        d = date.strftime("%Y-%m")
        for orig_name, col in COLS.items():
            v = row[col]
            if v is not None:
                raw.append({"date": d, "series": SAFE_NAMES[orig_name], "index": round(float(v), 2)})

    # YoY %
    lookup = {(r["date"], r["series"]): r["index"] for r in raw}
    final = []
    for r in raw:
        y, m = r["date"].split("-")
        prev = lookup.get((f"{int(y)-1}-{m}", r["series"]))
        if prev and r["index"]:
            final.append({**r, "yoy_pct": round((r["index"] / prev - 1) * 100, 1)})

    out = DATA_DIR / "cpi_inflation.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "series", "index", "yoy_pct"], lineterminator="\n")
        w.writeheader()
        w.writerows(final)
    print(f"✓ {out.name}: {len(final)} rows, {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
