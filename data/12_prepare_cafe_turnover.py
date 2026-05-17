"""
12_prepare_cafe_turnover.py
============================
Cafe & restaurant turnover data for Vis 10's heatmap.

Source: ABS Retail Trade, Australia, Series 8501.0, June 2025 release (FINAL).
Industry: "Cafes, restaurants and takeaway food services" (combined supergroup
of cafes, restaurants, catering, and takeaway). Seasonally adjusted monthly $m.

⚠️ Important note: ABS Retail Trade Australia was DISCONTINUED after June 2025
release. The series has been replaced by the Monthly Household Spending
Indicator (MHSI). Data only goes through June 2025.

This script doesn't actually fetch (we hand-copied the data from the ABS web
page since download requires browser). It's archived for reproducibility — the
embedded data was taken from:
https://www.abs.gov.au/statistics/industry/retail-and-wholesale-trade/retail-trade-australia/jun-2025

Output: data/cafe_turnover.csv (61 rows: Jun 2020 - Jun 2025)
"""

from pathlib import Path
import csv

DATA_DIR = Path(__file__).parent.parent / "data"

# Monthly seasonally adjusted turnover, $ millions
# (Hand-copied from ABS Retail Trade June 2025 release)
DATA = """Jun-2020|3239.4
Jul-2020|3410.7
Aug-2020|3215.8
Sep-2020|3299.3
Oct-2020|3479.7
Nov-2020|3710.5
Dec-2020|3871.9
Jan-2021|3868.6
Feb-2021|3865.1
Mar-2021|4007.9
Apr-2021|4104.6
May-2021|4105.8
Jun-2021|3857.7
Jul-2021|3400.7
Aug-2021|3181.0
Sep-2021|3340.9
Oct-2021|3778.0
Nov-2021|4096.6
Dec-2021|4158.6
Jan-2022|4137.5
Feb-2022|4481.1
Mar-2022|4539.4
Apr-2022|4681.7
May-2022|4761.7
Jun-2022|4911.1
Jul-2022|4965.5
Aug-2022|5020.7
Sep-2022|5089.7
Oct-2022|5135.6
Nov-2022|5151.2
Dec-2022|5169.2
Jan-2023|5236.6
Feb-2023|5249.0
Mar-2023|5326.5
Apr-2023|5303.6
May-2023|5351.7
Jun-2023|5347.9
Jul-2023|5408.2
Aug-2023|5413.2
Sep-2023|5383.4
Oct-2023|5364.1
Nov-2023|5371.5
Dec-2023|5267.8
Jan-2024|5364.8
Feb-2024|5393.0
Mar-2024|5387.3
Apr-2024|5404.5
May-2024|5401.8
Jun-2024|5401.4
Jul-2024|5397.9
Aug-2024|5442.0
Sep-2024|5481.8
Oct-2024|5478.8
Nov-2024|5556.5
Dec-2024|5516.7
Jan-2025|5569.3
Feb-2025|5570.5
Mar-2025|5536.7
Apr-2025|5600.3
May-2025|5606.1
Jun-2025|5581.6"""

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main():
    rows = []
    for line in DATA.strip().split("\n"):
        ms, value = line.split("|")
        mon_name, year = ms.split("-")
        rows.append({
            "year": int(year),
            "month": MONTHS.index(mon_name) + 1,
            "month_name": mon_name,
            "turnover_million_aud": round(float(value), 1)
        })

    out = DATA_DIR / "cafe_turnover.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f,
                           fieldnames=["year", "month", "month_name",
                                       "turnover_million_aud"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"✓ {out.name}: {len(rows)} rows, {out.stat().st_size} bytes")
    print(f"  Range: {rows[0]['month_name']} {rows[0]['year']} → "
          f"{rows[-1]['month_name']} {rows[-1]['year']}")
    print(f"  Min: ${min(r['turnover_million_aud'] for r in rows):,.0f}M")
    print(f"  Max: ${max(r['turnover_million_aud'] for r in rows):,.0f}M")


if __name__ == "__main__":
    main()
