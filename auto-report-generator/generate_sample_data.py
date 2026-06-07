"""Generate a small, deterministic synthetic sales dataset for the demo.

Run once:  python generate_sample_data.py
Produces:  data/sample_sales.csv  (monthly sales by region and category)

It is seeded, so it always produces the same data — including a deliberate
loss-making category (Furniture) and an anomalous month, so the report has
something interesting to find.
"""
import csv
import os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_sales.csv")

REGIONS = {"North": 1.1, "South": 0.9, "East": 1.0, "West": 1.2}
# (category, base monthly sales, profit margin) — Furniture loses money on purpose
CATEGORIES = [
    ("Technology", 12000, 0.18),
    ("Office Supplies", 7000, 0.22),
    ("Furniture", 9000, -0.04),
    ("Accessories", 5000, 0.30),
]
MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025) for m in range(1, 13)]  # 24 months


def main():
    rng = np.random.default_rng(42)
    rows = []
    for t, month in enumerate(MONTHS):
        growth = 1 + 0.015 * t                                  # gentle upward trend
        season = 1 + 0.20 * np.sin(2 * np.pi * (t % 12) / 12)   # yearly seasonality
        spike = 1.8 if month == "2025-11" else 1.0              # one anomalous month
        for region, region_factor in REGIONS.items():
            for name, base, margin in CATEGORIES:
                noise = rng.normal(1.0, 0.06)
                sales = round(max(base * growth * season * spike * region_factor * noise, 0), 2)
                profit = round(sales * margin, 2)
                units = int(sales / rng.uniform(40, 80))
                rows.append([month, region, name, units, sales, profit])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "region", "category", "units", "sales", "profit"])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
