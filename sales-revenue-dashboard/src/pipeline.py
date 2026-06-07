"""
pipeline.py
===========
A company-grade sales-analytics pipeline. Each function maps to ONE fix for a
limitation of the typical "pretty charts" sales dashboard:

    clean_data()              -> FIX #3 : robust to messy real-world data
    profitability_analysis()  -> FIX #2 : profit/margin + loss-making bestsellers
    forecast_sales()          -> FIX #1a: forward-looking forecast (back-tested)
    detect_anomalies()        -> FIX #1b: flags sudden sales drops / spikes
    generate_recommendations()-> FIX #1c: turns numbers into business actions

`run()` ties them together and is reused by BOTH entry points:
    - main.py           -> the real "Sample - Superstore" dataset  (USD, $)
    - main_synthetic.py -> a deliberately-broken synthetic dataset (INR, ₹)

HOW TO RUN (this file is a library; launch it through an entry point):
    python main.py            # real Superstore data
    python main_synthetic.py  # synthetic cleaning stress-test

The pipeline is SCHEMA-AWARE: it works whether or not a `unit_price` column
exists, so the same code runs on the real Superstore export and on the
synthetic stress-test data unchanged.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # "Agg" = draw charts straight to image files, no pop-up window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from .forecasting import best_forecast  # the back-tested forecaster (see forecasting.py)

# Currency symbol is a GLOBAL so both the INR and USD runs share one code path.
# main.py / main_synthetic.py overwrite it (via run()) before any output is made.
CURRENCY = "$"

# Use a clean built-in chart style; fall back if this matplotlib version lacks it.
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")

# A small fixed colour palette so every chart looks consistent.
PALETTE = {"blue": "#4C72B0", "green": "#55A868", "red": "#C44E52",
           "orange": "#DD8452", "grey": "#8C8C8C"}


def _money_fmt(x, _pos):
    """Turn a big number on a chart axis into a short money label.

    e.g. 2_300_000 -> "$2.3M",  45_000 -> "$45K". Reads the global CURRENCY.
    """
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e6:                          # millions
        return f"{sign}{CURRENCY}{x / 1e6:.1f}M"
    if x >= 1e3:                          # thousands
        return f"{sign}{CURRENCY}{x / 1e3:.0f}K"
    return f"{sign}{CURRENCY}{x:.0f}"


MONEY = FuncFormatter(_money_fmt)         # wrap it so matplotlib can use it on an axis


def _m(x: float) -> str:
    """Format one number as a full money string for the console/report. e.g. $1,234,567"""
    return f"{CURRENCY}{x:,.0f}"


# ============================================================================
# FIX #3 - DATA CLEANING  (the typical dashboard assumes clean data and breaks)
# ============================================================================
def clean_data(raw_path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Load messy raw data, fix every quality issue, and LOG what was fixed.

    Returns (clean_dataframe, report). The report is a dict that counts each fix
    so the cleaning is *auditable* - a real analyst always shows their working.
    Schema-aware: the price-based repairs only run if a `unit_price` column
    exists, so this handles real Superstore (no unit price) AND synthetic data.
    """
    df = pd.read_csv(raw_path)                  # read the CSV into a table (DataFrame)
    report: dict = {"rows_loaded": len(df)}     # remember how many rows we started with

    # Does this file have a unit-price column? (decides which repairs apply)
    has_price = "unit_price" in (c.strip().lower().replace(" ", "_").replace("-", "_")
                                 for c in df.columns)

    # Rename columns to a tidy snake_case form: "Order Date" -> "order_date".
    # Keeps the rest of the code stable no matter how the CSV labelled things.
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(" ", "_").str.replace("-", "_"))

    # 1) DATES: convert text to real dates. errors="coerce" turns anything
    #    unparseable (or blank) into NaT (Not-a-Time); then we drop those rows.
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    report["invalid_or_blank_dates_dropped"] = int(df["order_date"].isna().sum())
    df = df[df["order_date"].notna()]           # keep only rows with a valid date

    # 2) TEXT: trim spaces and Title-Case so "WEST", " west ", "West" all become
    #    "West" - otherwise groupby would split one region into three.
    for col in ("region", "category", "sub_category"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # 3) DUPLICATES: remove rows that are exact copies of another row.
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)

    # 4) MISSING SALES: if we know unit price we can rebuild sales
    #    (qty x price x (1 - discount)); otherwise we can only drop those rows.
    if has_price:
        missing = df["sales"].isna()
        # only rebuild where we actually have the ingredients to do so
        fixable = missing & df[["quantity", "unit_price", "discount"]].notna().all(axis=1)
        df.loc[fixable, "sales"] = (
            df.loc[fixable, "quantity"] * df.loc[fixable, "unit_price"]
            * (1 - df.loc[fixable, "discount"])
        ).round(2)
        report["sales_recomputed"] = int(fixable.sum())
    else:
        report["sales_recomputed"] = 0
    report["sales_unfixable_dropped"] = int(df["sales"].isna().sum())
    df = df[df["sales"].notna()]                # drop any sales we still couldn't fix

    # 5) BAD QUANTITIES: a sale can't have zero or negative quantity - remove them.
    before = len(df)
    df = df[df["quantity"] > 0]
    report["nonpositive_qty_removed"] = before - len(df)

    # 6) PRICE OUTLIERS: catch fat-finger prices (e.g. 999999) with the IQR rule.
    #    IQR = the middle 50% spread; anything far above it is treated as a typo.
    if has_price:
        q1, q3 = df["unit_price"].quantile([0.25, 0.75])   # 25th & 75th percentiles
        upper = q3 + 3 * (q3 - q1)                          # "too high" threshold
        report["price_outliers_removed"] = int((df["unit_price"] > upper).sum())
        df = df[df["unit_price"] <= upper]
    else:
        report["price_outliers_removed"] = 0

    df = df.reset_index(drop=True)              # tidy the row numbers after dropping
    report["rows_clean"] = len(df)
    report["pct_retained"] = round(100 * len(df) / report["rows_loaded"], 1)
    return df, report


# ============================================================================
# FIX #2 - PROFITABILITY  (revenue lies; margin tells the truth)
# ============================================================================
def profitability_analysis(df: pd.DataFrame) -> dict:
    """Compute profit/margin views and surface loss-making bestsellers."""
    total_sales = float(df["sales"].sum())
    total_profit = float(df["profit"].sum())

    # Group every row by category, then SUM sales & profit per category.
    # .assign(...) adds a margin% column;  margin% = profit / sales * 100.
    by_cat = (df.groupby("category")
              .agg(sales=("sales", "sum"), profit=("profit", "sum"))
              .assign(margin_pct=lambda x: 100 * x.profit / x.sales)
              .sort_values("sales", ascending=False))

    # Same idea but per sub-category, and also count how many orders each had.
    by_sub = (df.groupby("sub_category")
              .agg(sales=("sales", "sum"), profit=("profit", "sum"),
                   orders=("order_id", "count"))
              .assign(margin_pct=lambda x: 100 * x.profit / x.sales))

    # LOSS-MAKING BESTSELLERS = high revenue (top half by sales) BUT negative profit.
    # .median() splits sub-categories into the high-revenue half and the low half.
    hi_rev = by_sub["sales"] >= by_sub["sales"].median()
    loss_makers = by_sub[hi_rev & (by_sub["profit"] < 0)].sort_values("profit")

    # The "why": bucket orders into discount bands (0-10%, 10-20%, ...) and look
    # at the AVERAGE profit in each band - profit usually turns negative as
    # discount rises. (//10*10 rounds a discount down to the nearest 10.)
    band = (df["discount"] * 100 // 10 * 10).astype(int)
    profit_by_discount = df.groupby(band)["profit"].mean()

    return {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "overall_margin_pct": 100 * total_profit / total_sales,
        "by_category": by_cat,
        "by_sub": by_sub.sort_values("sales", ascending=False),
        "loss_makers": loss_makers,
        "profit_by_discount": profit_by_discount,
    }


# ============================================================================
# FIX #1a - FORECAST  (look forward, not just backward)
# ============================================================================
def forecast_sales(df: pd.DataFrame, periods: int = 6) -> dict:
    """Forecast monthly sales using the best back-tested model.

    Step 1: roll the daily rows up into MONTHLY totals (resample "MS" = Month Start).
    Step 2: hand that series to forecasting.best_forecast(), which races three
            models on a held-out test set and returns the most accurate one.
    """
    monthly = df.set_index("order_date").resample("MS")["sales"].sum()
    return best_forecast(monthly, horizon=periods)


# ============================================================================
# FIX #1b - ANOMALY DETECTION  (catch sudden drops/spikes automatically)
# ============================================================================
def detect_anomalies(df: pd.DataFrame, window: int = 30, k: float = 3.0) -> dict:
    """Flag days where sales fall outside a rolling mean +/- k*std band.

    Idea: for each day, look at a moving 30-day window. If a day's sales are
    more than k=3 standard deviations away from that window's average, it's
    unusual (a spike or a slump) and worth investigating.
    """
    daily = df.set_index("order_date").resample("D")["sales"].sum()   # daily totals
    roll = daily.rolling(window, min_periods=window // 2, center=True) # 30-day window
    mean, std = roll.mean(), roll.std()           # local average & spread
    upper, lower = mean + k * std, mean - k * std  # the "normal" band edges
    anomalies = daily[(daily > upper) | (daily < lower)]  # days outside the band
    return {"daily": daily, "mean": mean, "upper": upper, "lower": lower,
            "anomalies": anomalies, "window": window, "k": k}


# ============================================================================
# FIX #1c - RECOMMENDATIONS  (numbers are useless without an action)
# ============================================================================
def generate_recommendations(prof: dict, fc: dict, anom: dict) -> list[str]:
    """Translate the analysis into concrete, quantified business actions."""
    recs: list[str] = []

    # 1) If we found products that sell well but lose money -> recommend a fix.
    lm = prof["loss_makers"]
    if not lm.empty:
        names = ", ".join(lm.index)
        worst = lm.iloc[0]                         # the single biggest loser
        recs.append(
            f"CAP DISCOUNTS on loss-making bestsellers ({names}). "
            f"'{lm.index[0]}' sells well but LOSES {_m(abs(worst.profit))} "
            f"(margin {worst.margin_pct:.1f}%). Capping discount near the "
            f"break-even band turns these from a drain into profit."
        )

    # 2) Point the business at its most profitable category.
    best_cat = prof["by_category"].sort_values("profit", ascending=False).iloc[0]
    recs.append(
        f"DOUBLE DOWN on '{best_cat.name}' - it drives {_m(best_cat.profit)} "
        f"profit at {best_cat.margin_pct:.1f}% margin. Prioritise its inventory "
        f"and marketing spend."
    )

    # 3) Use the forecast to plan ahead (and quote the honest out-of-sample error).
    recs.append(
        f"PLAN FOR THE PEAK: the best back-tested model ({fc['model_name']}) "
        f"projects {_m(fc['next_total'])} in sales over the next {fc['periods']} "
        f"months (out-of-sample MAPE {fc['oos_mape']:.1f}%). Pre-stock and add "
        f"staff before the seasonal surge."
    )

    # 4) Tell them to investigate whatever the anomaly detector flagged.
    n = len(anom["anomalies"])
    if n:
        recs.append(
            f"INVESTIGATE {n} ANOMALY DAY(S) the system flagged automatically "
            f"(e.g. {anom['anomalies'].index.max():%d %b %Y}). Sudden swings are "
            f"usually a stock-out, pricing bug, or a one-off bulk order worth "
            f"understanding - not guessing."
        )

    return recs


# ============================================================================
# CHARTING  (each _ax_* helper draws ONE chart onto a given Axes `ax`, so the
#            same code powers both the standalone PNGs and the 2x2 dashboard)
# ============================================================================
def _ax_category(ax, by_cat):
    """Side-by-side Sales vs Profit bars, one pair per category."""
    x = np.arange(len(by_cat))                          # bar positions 0,1,2,...
    ax.bar(x - 0.2, by_cat["sales"], 0.4, label="Sales", color=PALETTE["blue"])
    ax.bar(x + 0.2, by_cat["profit"], 0.4, label="Profit", color=PALETTE["green"])
    ax.axhline(0, color=PALETTE["grey"], lw=0.8)        # zero line
    ax.set_xticks(x)
    ax.set_xticklabels(by_cat.index)
    ax.yaxis.set_major_formatter(MONEY)                 # show $/₹ on the axis
    ax.set_title("Sales vs Profit by Category")
    ax.legend()


def _ax_lossmakers(ax, by_sub):
    """Horizontal profit bars per sub-category; red where profit is negative."""
    s = by_sub.sort_values("profit")
    colors = [PALETTE["red"] if p < 0 else PALETTE["green"] for p in s["profit"]]
    ax.barh(s.index, s["profit"], color=colors)
    ax.axvline(0, color=PALETTE["grey"], lw=0.8)
    ax.xaxis.set_major_formatter(MONEY)
    ax.set_title("Profit by Sub-Category (red = loses money)")


def _ax_discount(ax, profit_by_discount):
    """Line of average profit per order against discount band (the 'why')."""
    g = profit_by_discount
    ax.plot(g.index, g.values, marker="o", color=PALETTE["orange"])
    ax.axhline(0, color=PALETTE["red"], ls="--", lw=1)  # break-even line
    ax.yaxis.set_major_formatter(MONEY)
    ax.set_xlabel("Discount band (%)")
    ax.set_title("Avg Profit per Order vs Discount (the 'why')")


def _ax_forecast(ax, fc):
    """History (actual + model fit) plus the future forecast and its 95% band."""
    ax.plot(fc["monthly"].index, fc["monthly"].values, label="Actual",
            color=PALETTE["blue"])
    ax.plot(fc["fitted"].index, fc["fitted"].values, label="Model fit",
            color=PALETTE["orange"], alpha=0.8)
    ax.plot(fc["forecast"].index, fc["forecast"].values, label="Forecast",
            color=PALETTE["red"], marker="o")
    # shaded confidence band = forecast +/- ci
    ax.fill_between(fc["forecast"].index, fc["forecast"] - fc["ci"],
                    fc["forecast"] + fc["ci"], color=PALETTE["red"], alpha=0.15,
                    label="95% CI")
    ax.yaxis.set_major_formatter(MONEY)
    ax.set_title(f"Monthly Sales + {fc['periods']}-Month Forecast ({fc['model_name']})")
    ax.legend(fontsize=8)


def _ax_anomalies(ax, an):
    """Daily sales, the rolling average, the normal band, and red anomaly dots."""
    ax.plot(an["daily"].index, an["daily"].values, lw=0.7, color=PALETTE["blue"],
            label="Daily sales")
    ax.plot(an["mean"].index, an["mean"].values, color=PALETTE["orange"],
            label=f"{an['window']}-day avg")
    ax.fill_between(an["daily"].index, an["lower"], an["upper"],
                    color=PALETTE["grey"], alpha=0.20, label=f"+/-{an['k']:g}σ")
    ax.scatter(an["anomalies"].index, an["anomalies"].values, color=PALETTE["red"],
               zorder=5, s=25, label="Anomaly")
    ax.yaxis.set_major_formatter(MONEY)
    ax.set_title("Daily Sales with Auto-Detected Anomalies")
    ax.legend(fontsize=8)


def save_all_charts(prof: dict, fc: dict, anom: dict, out_dir: str | Path) -> None:
    """Write the four standalone charts plus one combined executive dashboard."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)              # create the folder if needed

    # (filename, drawing function, data) for each standalone chart.
    singles = [
        ("profit_by_category.png", _ax_category, prof["by_category"]),
        ("loss_making_products.png", _ax_lossmakers, prof["by_sub"]),
        ("discount_vs_profit.png", _ax_discount, prof["profit_by_discount"]),
        ("sales_forecast.png", _ax_forecast, fc),
        ("anomaly_detection.png", _ax_anomalies, anom),
    ]
    for fname, fn, data in singles:
        fig, ax = plt.subplots(figsize=(9, 5))          # new blank canvas
        fn(ax, data)                                    # draw onto it
        fig.tight_layout()
        fig.savefig(out / fname, dpi=120)               # save as PNG
        plt.close(fig)                                  # free memory

    # Combined 2x2 "hero" dashboard reusing the same four helpers.
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    _ax_forecast(axes[0, 0], fc)
    _ax_category(axes[0, 1], prof["by_category"])
    _ax_lossmakers(axes[1, 0], prof["by_sub"])
    _ax_anomalies(axes[1, 1], anom)
    fig.suptitle("Sales & Revenue Executive Dashboard", fontsize=16, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out / "dashboard.png", dpi=120)
    plt.close(fig)


# ============================================================================
# REPORT WRITER  (turns the results into a recruiter-facing markdown summary)
# ============================================================================
def write_report(prof, fc, anom, clean_report, recs, out_dir, source_label) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def _pretty(frame):
        """Format a sales/profit/margin table nicely for markdown."""
        d = frame.copy()
        for col in ("sales", "profit"):
            if col in d:
                d[col] = d[col].map(lambda v: f"{CURRENCY}{v:,.0f}")
        if "margin_pct" in d:
            d["margin_pct"] = d["margin_pct"].map(lambda v: f"{v:.1f}%")
        return d.to_markdown()

    # Build the report as a list of lines, then join them with newlines.
    lines = ["# Sales & Revenue Dashboard - Insights Report\n",
             f"_Auto-generated by the pipeline. Data source: **{source_label}**._\n",
             "## Key Performance Indicators\n",
             f"- **Total sales:** {_m(prof['total_sales'])}",
             f"- **Total profit:** {_m(prof['total_profit'])}",
             f"- **Overall margin:** {prof['overall_margin_pct']:.1f}%",
             f"- **Next-{fc['periods']}-month forecast:** {_m(fc['next_total'])} "
             f"via {fc['model_name']} (out-of-sample MAPE {fc['oos_mape']:.1f}%)",
             f"- **Anomaly days flagged:** {len(anom['anomalies'])}\n",
             "## Data Quality (cleaning audit)\n",
             f"Loaded {clean_report['rows_loaded']:,} raw rows; kept "
             f"{clean_report['rows_clean']:,} ({clean_report['pct_retained']}%) "
             "after fixing:\n"]
    for key in ("invalid_or_blank_dates_dropped", "duplicates_removed",
                "sales_recomputed", "sales_unfixable_dropped",
                "nonpositive_qty_removed", "price_outliers_removed"):
        lines.append(f"- `{key}`: {clean_report[key]:,}")

    lines.append("\n## Profit by Category\n")
    lines.append(_pretty(prof["by_category"]))
    lines.append("\n## Loss-Making Bestsellers (the headline finding)\n")
    lines.append(_pretty(prof["loss_makers"])
                 if not prof["loss_makers"].empty else "_None found._")
    lines.append("\n## Forecast model selection (walk-forward back-test)\n")
    lines.append(f"Models scored on a held-out test set; **{fc['model_name']}** won.\n")
    lines.append(fc["comparison"].to_markdown(index=False))
    lines.append("\n## Recommendations\n")
    lines += [f"{i}. {r}" for i, r in enumerate(recs, 1)]

    path = out / "insights_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ============================================================================
# ORCHESTRATOR  (runs steps 1-6 in order; shared by both entry points)
# ============================================================================
def _rule(title: str) -> None:
    """Print a titled separator line so the console output is easy to read."""
    print("\n" + "=" * 64 + f"\n{title}\n" + "=" * 64)


def run(raw_path, *, currency: str, out_dir, source_label: str) -> dict:
    """Run the full pipeline on one CSV and write all charts + the report.

    `currency` is "$" or "₹"; `out_dir` is where charts/report are saved;
    `source_label` is a human description of the data source for the report.
    """
    global CURRENCY
    CURRENCY = currency                      # set the money symbol for this run

    # --- STEP 1: clean ---
    _rule(f"STEP 1  Clean data  [FIX #3]   source: {source_label}")
    df, creport = clean_data(raw_path)
    for key, val in creport.items():         # print the cleaning audit
        print(f"  {key:<32}: {val}")

    # --- STEP 2: profitability ---
    _rule("STEP 2  Profitability  [FIX #2: margin, not vanity revenue]")
    prof = profitability_analysis(df)
    print(f"  Total sales : {_m(prof['total_sales'])}")
    print(f"  Total profit: {_m(prof['total_profit'])}")
    print(f"  Margin      : {prof['overall_margin_pct']:.1f}%")
    print("  Loss-making bestsellers:")
    if prof["loss_makers"].empty:
        print("    (none)")
    for name, row in prof["loss_makers"].iterrows():
        print(f"    - {name:<11} sales {_m(row.sales):>13}  "
              f"profit {_m(row.profit):>13}  ({row.margin_pct:5.1f}%)")

    # --- STEP 3: forecast (with the model back-test) ---
    _rule("STEP 3  Forecast  [FIX #1a: back-tested model selection]")
    fc = forecast_sales(df, periods=6)
    print("  Model back-test (out-of-sample MAPE):")
    for _, r in fc["comparison"].iterrows():
        print(f"    - {r['model']:<26} {r['oos_mape']}%")
    print(f"  Chosen model           : {fc['model_name']}")
    print(f"  Next 6 months projected: {_m(fc['next_total'])}")
    print(f"  Out-of-sample MAPE     : {fc['oos_mape']:.1f}%")

    # --- STEP 4: anomalies ---
    _rule("STEP 4  Anomaly detection  [FIX #1b]")
    anom = detect_anomalies(df)
    print(f"  Anomaly days flagged: {len(anom['anomalies'])}")
    for dt, val in anom["anomalies"].items():
        print(f"    - {dt:%Y-%m-%d}: {_m(val)}")

    # --- STEP 5: recommendations ---
    _rule("STEP 5  Recommendations  [FIX #1c]")
    recs = generate_recommendations(prof, fc, anom)
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r}\n")

    # --- STEP 6: save outputs ---
    _rule("STEP 6  Save charts + written report")
    save_all_charts(prof, fc, anom, out_dir)
    report = write_report(prof, fc, anom, creport, recs, out_dir, source_label)
    print(f"  charts  -> {out_dir}")
    print(f"  report  -> {report}")

    # Hand everything back to the caller (also handy for the notebook).
    return {"df": df, "clean_report": creport, "prof": prof, "fc": fc,
            "anom": anom, "recs": recs}
