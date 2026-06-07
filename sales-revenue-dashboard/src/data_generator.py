"""
data_generator.py
=================
Creates a realistic 3-year retail sales dataset (Superstore-style) and then
*intentionally* injects real-world data-quality problems into a "raw" copy.

Why synthetic data?
  - It is fully reproducible: anyone who clones the repo gets identical numbers
    (fixed random seed), so the README screenshots always match.
  - It lets us *demonstrate the data-cleaning fix* by injecting the exact issues
    (nulls, duplicates, bad dates, fat-finger prices) that silently break a
    naive dashboard.
  - The pipeline runs unchanged on any real dataset with the same columns
    (e.g. the public "Sample - Superstore" dataset). Just point clean_data()
    at that CSV instead.

Run standalone:
    python -m src.data_generator
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# One seed -> identical data every run (reproducibility matters in analytics).
RNG = np.random.default_rng(42)

# Product catalogue: (category, sub_category, base_price, cost_ratio, base_discount)
#   cost_ratio    = unit_cost / unit_price   (higher  -> thinner margin)
#   base_discount = typical discount level   (higher  -> more margin erosion)
# NOTE: "Tables" and "Bookcases" are deliberately designed as LOSS-MAKING
#       BESTSELLERS - high revenue but negative profit due to deep discounting.
CATALOG = [
    # Technology - high margin, low discount (this is what carries the business)
    ("Technology",      "Phones",       700, 0.62, 0.05),
    ("Technology",      "Accessories",   60, 0.55, 0.05),
    ("Technology",      "Machines",     350, 0.65, 0.10),
    ("Technology",      "Copiers",      450, 0.60, 0.08),
    # Office Supplies - medium margin
    ("Office Supplies", "Binders",       15, 0.60, 0.10),
    ("Office Supplies", "Paper",         25, 0.58, 0.05),
    ("Office Supplies", "Storage",       55, 0.66, 0.08),
    ("Office Supplies", "Art",           30, 0.62, 0.06),
    # Furniture - includes the two deliberate loss-makers
    ("Furniture",       "Chairs",       180, 0.68, 0.12),
    ("Furniture",       "Furnishings",   45, 0.63, 0.10),
    ("Furniture",       "Tables",       300, 0.78, 0.38),   # deep discount -> losses
    ("Furniture",       "Bookcases",    220, 0.80, 0.34),   # deep discount -> losses
]

REGIONS = ["North", "South", "East", "West"]
REGION_WEIGHTS = [0.22, 0.28, 0.20, 0.30]

# Multiplicative seasonal factors: big Nov/Dec holiday peak, mild summer dip.
SEASON = {1: 0.95, 2: 0.90, 3: 1.00, 4: 1.02, 5: 1.05, 6: 0.92,
          7: 0.90, 8: 1.00, 9: 1.08, 10: 1.12, 11: 1.35, 12: 1.45}


def generate(start: str = "2023-01-01", end: str = "2025-12-31") -> pd.DataFrame:
    """Build a clean line-item sales table with trend + seasonality."""
    dates = pd.date_range(start, end, freq="D")
    n_days = len(dates)
    rows = []
    order_seq = 1

    for i, day in enumerate(dates):
        trend = 1.0 + 0.35 * (i / n_days)          # ~35% organic growth over 3 yrs
        lam = 22 * trend * SEASON[day.month]       # expected orders that day
        n_orders = max(1, int(RNG.poisson(lam)))

        for _ in range(n_orders):
            cat, sub, price, cost_ratio, base_disc = CATALOG[RNG.integers(len(CATALOG))]
            qty = int(RNG.integers(1, 8))
            unit_price = round(price * RNG.uniform(0.90, 1.15), 2)
            discount = float(np.clip(RNG.normal(base_disc, 0.05), 0, 0.60))
            sales = round(qty * unit_price * (1 - discount), 2)
            profit = round(sales - qty * unit_price * cost_ratio, 2)
            rows.append([
                f"ORD-{order_seq:06d}", day, RNG.choice(REGIONS, p=REGION_WEIGHTS),
                cat, sub, f"{sub} Item {RNG.integers(1, 50)}",
                qty, unit_price, round(discount, 2), sales, profit,
            ])
            order_seq += 1

    df = pd.DataFrame(rows, columns=[
        "Order ID", "Order Date", "Region", "Category", "Sub-Category",
        "Product Name", "Quantity", "Unit Price", "Discount", "Sales", "Profit",
    ])
    return _inject_anomalies(df)


def _inject_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Add a few sharp, *real* anomalies so the detector has something to find."""
    # Positive spikes: large B2B bulk orders on three specific dates.
    spike_dates = pd.to_datetime(["2024-03-15", "2024-09-20", "2025-07-04"])
    extra, seq = [], 900_000
    for d in spike_dates:
        for _ in range(40):
            sales = round(10 * 480 * 0.95, 2)
            profit = round(sales - 10 * 480 * 0.60, 2)
            extra.append([f"ORD-{seq:06d}", d, "West", "Technology", "Copiers",
                          "Copiers Bulk Order", 10, 480.0, 0.05, sales, profit])
            seq += 1
    df = pd.concat([df, pd.DataFrame(extra, columns=df.columns)], ignore_index=True)

    # Negative anomaly: an "outage" day where ~90% of orders never happened.
    outage = pd.Timestamp("2025-02-10")
    drop_idx = df[df["Order Date"] == outage].sample(frac=0.90, random_state=1).index
    return df.drop(index=drop_idx).reset_index(drop=True)


def inject_quality_issues(clean: pd.DataFrame) -> pd.DataFrame:
    """Return a dirty copy that mimics messy real-world exports."""
    df = clean.copy()
    n = len(df)

    # 1) ~2% missing Sales values
    df.loc[RNG.choice(n, int(0.02 * n), replace=False), "Sales"] = np.nan

    # 2) ~1% duplicated rows
    dup = df.iloc[RNG.choice(n, int(0.01 * n), replace=False)]
    df = pd.concat([df, dup], ignore_index=True)

    # 3) ~0.5% negative quantities (data-entry sign errors)
    neg = RNG.choice(len(df), int(0.005 * len(df)), replace=False)
    df.loc[neg, "Quantity"] = -df.loc[neg, "Quantity"]

    # 4) ~5% inconsistent Region casing / stray whitespace
    variants = {"North": " north ", "South": "SOUTH", "East": "east", "West": " West "}
    case = RNG.choice(len(df), int(0.05 * len(df)), replace=False)
    df.loc[case, "Region"] = df.loc[case, "Region"].map(lambda r: variants.get(r, r))

    # 5) ~0.2% absurd fat-finger unit prices
    out = RNG.choice(len(df), max(5, int(0.002 * len(df))), replace=False)
    df.loc[out, "Unit Price"] = 999_999.0

    # 6) 20 invalid / unparseable dates.
    #    (pandas 3.0 forbids writing a string into a datetime column, so first
    #     render dates as plain strings - exactly how a messy CSV export looks.)
    df["Order Date"] = pd.to_datetime(df["Order Date"]).dt.strftime("%Y-%m-%d")
    df.loc[RNG.choice(len(df), 20, replace=False), "Order Date"] = "not_a_date"

    # Shuffle so the problems are spread throughout the file.
    return df.sample(frac=1.0, random_state=7).reset_index(drop=True)


def build_and_save(out_dir: str | Path = "data") -> tuple[Path, int]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = inject_quality_issues(generate())
    raw_path = out / "raw_sales.csv"
    raw.to_csv(raw_path, index=False)
    return raw_path, len(raw)


if __name__ == "__main__":
    path, n = build_and_save()
    print(f"Wrote {n:,} rows of (intentionally messy) raw data -> {path}")
