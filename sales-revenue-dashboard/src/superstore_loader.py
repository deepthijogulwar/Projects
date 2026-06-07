"""
superstore_loader.py
====================
Fetches the real "Sample - Superstore" dataset so the project runs out of the
box. If the CSV is already on disk it is used as-is; otherwise it is downloaded
once from a public mirror.

Dataset: 10,800 rows, 2015-2018, columns:
    Order Date, Region, Category, Sub-Category, Sales, Quantity, Discount,
    Profit, ... (standard Superstore schema; note: NO unit-price column, and
    profit is provided directly).

NOTE: this particular public mirror is a *deliberately messy* version (it
contains ~806 blank rows and ~504 duplicate rows), which is perfect for
showcasing the cleaning step on genuinely real data.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

# Public mirror of the Sample - Superstore dataset.
SUPERSTORE_URL = (
    "https://raw.githubusercontent.com/leonism/sample-superstore/"
    "master/data/superstore.csv"
)


def ensure_dataset(dst: str | Path) -> Path:
    """Return a local path to the Superstore CSV, downloading it if needed."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() and dst.stat().st_size > 0:
        print(f"  using cached dataset -> {dst}")
        return dst

    print(f"  downloading Sample-Superstore -> {dst}")
    req = urllib.request.Request(SUPERSTORE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dst.write_bytes(resp.read())
    print(f"  downloaded {dst.stat().st_size:,} bytes")
    return dst


if __name__ == "__main__":
    ensure_dataset("data/superstore.csv")
