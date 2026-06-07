"""
sales_dashboard.py
==================
SELF-CONTAINED Sales & Revenue Intelligence Dashboard - the entire project in
ONE runnable file, on the real "Sample - Superstore" dataset.

WHAT IT DOES (one analyst workflow, end to end):
  1. Download + load the real Superstore data (auto, first run only)
  2. Clean it          - fix blank rows, duplicates, bad dates   (FIX #3)
  3. Profitability     - margin + loss-making bestsellers         (FIX #2)
  4. Forecast          - back-test 3 models, pick the best        (FIX #1a)
  5. Anomaly detection - flag unusual days                        (FIX #1b)
  6. Recommendations   - turn numbers into actions                (FIX #1c)
  7. Save charts + a markdown report to ./outputs/

HOW TO RUN
----------
    pip install pandas numpy matplotlib statsmodels tabulate
    python sales_dashboard.py
"""
from __future__ import annotations

import sys
import urllib.request
import warnings
from pathlib import Path

# Force UTF-8 so printing the $ / currency symbols never crashes a Windows console.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import matplotlib
matplotlib.use("Agg")                 # render charts to image files (no pop-up window)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")     # hide statsmodels convergence chatter

# ---- Configuration --------------------------------------------------------
ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "outputs"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
CURRENCY = "$"
URL = ("https://raw.githubusercontent.com/leonism/sample-superstore/"
       "master/data/superstore.csv")
PAL = {"blue": "#4C72B0", "green": "#55A868", "red": "#C44E52",
       "orange": "#DD8452", "grey": "#8C8C8C"}
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


# ---- Small money formatters ----------------------------------------------
def money(x, _pos=None):
    """Short axis label: 2_300_000 -> '$2.3M', 45_000 -> '$45K'."""
    s = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e6:
        return f"{s}{CURRENCY}{x/1e6:.1f}M"
    if x >= 1e3:
        return f"{s}{CURRENCY}{x/1e3:.0f}K"
    return f"{s}{CURRENCY}{x:.0f}"


def m(x):                              # full string, e.g. "$1,234,567"
    return f"{CURRENCY}{x:,.0f}"


MONEY = FuncFormatter(money)


# ---- Step 1: get the data -------------------------------------------------
def get_data() -> Path:
    """Download the real Superstore CSV once; reuse it afterwards."""
    dst = DATA / "superstore.csv"
    if dst.exists():
        print(f"  using cached dataset -> {dst}")
        return dst
    print("  downloading Sample-Superstore ...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    dst.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    print(f"  saved {dst.stat().st_size:,} bytes -> {dst}")
    return dst


# ---- Step 2: clean (FIX #3) ----------------------------------------------
def clean(path: Path):
    """Fix every data-quality issue and log what was done."""
    df = pd.read_csv(path)
    rep = {"rows_loaded": len(df)}
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")   # bad -> NaT
    rep["blank_or_bad_dates_dropped"] = int(df["order_date"].isna().sum())
    df = df[df["order_date"].notna()]

    for c in ("region", "category", "sub_category"):       # tidy text
        df[c] = df[c].astype(str).str.strip().str.title()

    before = len(df)
    df = df.drop_duplicates()
    rep["duplicates_removed"] = before - len(df)

    before = len(df)
    df = df[df["quantity"] > 0]                            # quantities must be positive
    rep["bad_quantity_removed"] = before - len(df)

    df = df.reset_index(drop=True)
    rep["rows_clean"] = len(df)
    rep["pct_retained"] = round(100 * len(df) / rep["rows_loaded"], 1)
    return df, rep


# ---- Step 3: profitability (FIX #2) --------------------------------------
def profitability(df):
    by_cat = (df.groupby("category")
              .agg(sales=("sales", "sum"), profit=("profit", "sum"))
              .assign(margin=lambda x: 100 * x.profit / x.sales)
              .sort_values("sales", ascending=False))
    by_sub = (df.groupby("sub_category")
              .agg(sales=("sales", "sum"), profit=("profit", "sum"))
              .assign(margin=lambda x: 100 * x.profit / x.sales))
    # loss-making bestsellers: above-median revenue, yet negative profit
    hi = by_sub["sales"] >= by_sub["sales"].median()
    losers = by_sub[hi & (by_sub["profit"] < 0)].sort_values("profit")
    band = (df["discount"] * 100 // 10 * 10).astype(int)
    by_disc = df.groupby(band)["profit"].mean()
    return {"by_cat": by_cat, "by_sub": by_sub.sort_values("sales", ascending=False),
            "losers": losers, "by_disc": by_disc,
            "sales": float(df.sales.sum()), "profit": float(df.profit.sum())}


# ---- Step 4: forecast with a back-test (FIX #1a) -------------------------
def _mape(a, p):
    a, p = np.asarray(a, float), np.asarray(p, float)
    return float(np.mean(np.abs((a - p) / a)) * 100)


def _fit(name, y):
    if name == "Holt-Winters":
        return ExponentialSmoothing(y, trend="add", seasonal="add",
                                    seasonal_periods=12,
                                    initialization_method="estimated").fit(), (lambda v: v)
    if name == "Holt-Winters (log)":
        return ExponentialSmoothing(np.log(y), trend="add", seasonal="add",
                                    seasonal_periods=12,
                                    initialization_method="estimated").fit(), np.exp
    return SARIMAX(y, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False), (lambda v: v)


def forecast(df, horizon=6):
    """Hold out the last `horizon` months, score 3 models, keep the best."""
    monthly = df.set_index("order_date").resample("MS")["sales"].sum()
    train, test = monthly.iloc[:-horizon], monthly.iloc[-horizon:]
    rows = []
    for name in ["Holt-Winters", "Holt-Winters (log)", "SARIMAX(1,1,1)(1,1,1,12)"]:
        try:
            res, tf = _fit(name, train)
            rows.append({"model": name,
                         "oos_mape": round(_mape(test.values, tf(res.forecast(horizon))), 1)})
        except Exception:
            rows.append({"model": name, "oos_mape": np.nan})
    comp = pd.DataFrame(rows).sort_values("oos_mape", na_position="last").reset_index(drop=True)
    best = comp.iloc[0]["model"]
    res, tf = _fit(best, monthly)                          # retrain on ALL data
    fitted = pd.Series(np.asarray(tf(res.fittedvalues), float), index=monthly.index)
    idx = pd.date_range(monthly.index[-1], periods=horizon + 1, freq="MS")[1:]
    fc = pd.Series(np.asarray(tf(res.forecast(horizon)), float), index=idx)
    ci = 1.96 * float((monthly - fitted).dropna().std())
    return {"monthly": monthly, "fitted": fitted, "forecast": fc, "ci": ci,
            "comparison": comp, "model": best, "mape": float(comp.iloc[0]["oos_mape"]),
            "next_total": float(fc.sum()), "periods": horizon}


# ---- Step 5: anomalies (FIX #1b) -----------------------------------------
def anomalies(df, window=30, k=3.0):
    daily = df.set_index("order_date").resample("D")["sales"].sum()
    roll = daily.rolling(window, min_periods=window // 2, center=True)
    mean, std = roll.mean(), roll.std()
    upper, lower = mean + k * std, mean - k * std
    flagged = daily[(daily > upper) | (daily < lower)]
    return {"daily": daily, "mean": mean, "upper": upper, "lower": lower,
            "flagged": flagged, "window": window, "k": k}


# ---- Step 6: recommendations (FIX #1c) -----------------------------------
def recommend(prof, fc, anom):
    out = []
    if not prof["losers"].empty:
        w = prof["losers"].iloc[0]
        out.append(f"CAP DISCOUNTS on {', '.join(prof['losers'].index)} - "
                   f"'{prof['losers'].index[0]}' sells well but loses {m(abs(w.profit))} "
                   f"(margin {w.margin:.1f}%).")
    bc = prof["by_cat"].sort_values("profit", ascending=False).iloc[0]
    out.append(f"DOUBLE DOWN on '{bc.name}' - {m(bc.profit)} profit at {bc.margin:.1f}% margin.")
    out.append(f"PLAN AHEAD: {fc['model']} projects {m(fc['next_total'])} next "
               f"{fc['periods']} months (out-of-sample MAPE {fc['mape']:.1f}%).")
    if len(anom["flagged"]):
        out.append(f"INVESTIGATE {len(anom['flagged'])} anomaly day(s) the system flagged.")
    return out


# ---- Step 7: charts -------------------------------------------------------
def charts(prof, fc, anom):
    fig, ax = plt.subplots(2, 2, figsize=(16, 10))

    a = ax[0, 0]                                           # forecast
    a.plot(fc["monthly"].index, fc["monthly"], color=PAL["blue"], label="Actual")
    a.plot(fc["fitted"].index, fc["fitted"], color=PAL["orange"], alpha=.8, label="Fit")
    a.plot(fc["forecast"].index, fc["forecast"], color=PAL["red"], marker="o", label="Forecast")
    a.fill_between(fc["forecast"].index, fc["forecast"] - fc["ci"], fc["forecast"] + fc["ci"],
                   color=PAL["red"], alpha=.15)
    a.set_title(f"Monthly Sales + Forecast ({fc['model']})"); a.legend(fontsize=8)
    a.yaxis.set_major_formatter(MONEY)

    a = ax[0, 1]                                           # category
    x = np.arange(len(prof["by_cat"]))
    a.bar(x - .2, prof["by_cat"].sales, .4, label="Sales", color=PAL["blue"])
    a.bar(x + .2, prof["by_cat"].profit, .4, label="Profit", color=PAL["green"])
    a.set_xticks(x); a.set_xticklabels(prof["by_cat"].index)
    a.set_title("Sales vs Profit by Category"); a.legend(); a.yaxis.set_major_formatter(MONEY)

    a = ax[1, 0]                                           # loss-makers
    s = prof["by_sub"].sort_values("profit")
    a.barh(s.index, s.profit, color=[PAL["red"] if p < 0 else PAL["green"] for p in s.profit])
    a.axvline(0, color=PAL["grey"], lw=.8)
    a.set_title("Profit by Sub-Category (red = loses money)"); a.xaxis.set_major_formatter(MONEY)

    a = ax[1, 1]                                           # anomalies
    a.plot(anom["daily"].index, anom["daily"], lw=.7, color=PAL["blue"], label="Daily")
    a.fill_between(anom["daily"].index, anom["lower"], anom["upper"], color=PAL["grey"], alpha=.2)
    a.scatter(anom["flagged"].index, anom["flagged"], color=PAL["red"], s=25, zorder=5, label="Anomaly")
    a.set_title("Daily Sales with Anomalies"); a.legend(fontsize=8); a.yaxis.set_major_formatter(MONEY)

    fig.suptitle("Sales & Revenue Executive Dashboard", fontsize=16, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "dashboard.png", dpi=120)
    plt.close(fig)


# ---- Main: run all steps in order ----------------------------------------
def main():
    print("=" * 60, "\nSALES & REVENUE DASHBOARD  (real Superstore data)\n", "=" * 60)

    print("\n[1] LOAD")
    df_path = get_data()

    print("\n[2] CLEAN  (FIX #3)")
    df, rep = clean(df_path)
    for k_, v in rep.items():
        print(f"    {k_:<26}: {v}")

    print("\n[3] PROFITABILITY  (FIX #2)")
    prof = profitability(df)
    print(f"    Sales {m(prof['sales'])} | Profit {m(prof['profit'])} | "
          f"Margin {100*prof['profit']/prof['sales']:.1f}%")
    print("    Loss-making bestsellers:")
    for name, r in prof["losers"].iterrows():
        print(f"      - {name:<10} profit {m(r.profit):>10}  (margin {r.margin:5.1f}%)")

    print("\n[4] FORECAST  (FIX #1a - back-tested)")
    fc = forecast(df)
    for _, r in fc["comparison"].iterrows():
        print(f"      {r['model']:<26} out-of-sample MAPE {r['oos_mape']}%")
    print(f"    -> chosen: {fc['model']} | next 6 months {m(fc['next_total'])}")

    print("\n[5] ANOMALIES  (FIX #1b)")
    anom = anomalies(df)
    print(f"    {len(anom['flagged'])} unusual days flagged")

    print("\n[6] RECOMMENDATIONS  (FIX #1c)")
    recs = recommend(prof, fc, anom)
    for i, r in enumerate(recs, 1):
        print(f"    {i}. {r}")

    print("\n[7] SAVE CHARTS")
    charts(prof, fc, anom)
    print(f"    dashboard -> {OUT / 'dashboard.png'}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
