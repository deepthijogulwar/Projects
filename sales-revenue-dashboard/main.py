"""
main.py
=======
Runs the company-grade sales-analytics pipeline on the REAL
"Sample - Superstore" dataset (auto-downloaded on first run).

    raw Superstore CSV -> clean -> profitability -> forecast
                       -> anomalies -> recommendations -> charts + report

Usage:
    python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows consoles default to cp1252; force UTF-8 so currency glyphs never crash.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from src import pipeline
from src.superstore_loader import ensure_dataset

ROOT = Path(__file__).parent


def main() -> None:
    print("\nSALES & REVENUE DASHBOARD  -  real Sample-Superstore dataset")

    # 1) Make sure we have the data (downloads the CSV the first time only).
    csv_path = ensure_dataset(ROOT / "data" / "superstore.csv")

    # 2) Run the whole pipeline (clean -> profit -> forecast -> anomaly ->
    #    recommend -> save charts + report). currency="$" because it's US data.
    pipeline.run(
        csv_path,
        currency="$",
        out_dir=ROOT / "outputs",
        source_label="real Sample-Superstore dataset (2015-2018)",
    )
    print("\nDone. Open outputs/dashboard.png and outputs/insights_report.md")


if __name__ == "__main__":
    main()
