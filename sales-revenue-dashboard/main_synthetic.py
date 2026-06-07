"""
main_synthetic.py
=================
BONUS entry point. Runs the SAME pipeline on a deliberately-broken synthetic
dataset to stress-test the cleaning layer (FIX #3) with injected nulls,
duplicates, bad dates and fat-finger prices that the pristine real data lacks.

Writes to `outputs_synthetic/` so it never clobbers the real-data charts.

Usage:
    python main_synthetic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from src import pipeline
from src.data_generator import build_and_save

ROOT = Path(__file__).parent


def main() -> None:
    print("\nSALES & REVENUE DASHBOARD  -  synthetic cleaning stress-test")
    raw_path, n = build_and_save(ROOT / "data")
    print(f"  generated {n:,} intentionally-messy rows -> {raw_path}")
    pipeline.run(
        raw_path,
        currency="₹",
        out_dir=ROOT / "outputs_synthetic",
        source_label="synthetic data with injected quality issues",
    )
    print("\nDone. Charts written to outputs_synthetic/.")


if __name__ == "__main__":
    main()
