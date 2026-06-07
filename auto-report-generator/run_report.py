"""Automated report generator: a sales CSV in -> a Markdown report + charts out.

    python run_report.py                          # uses the bundled sample data
    python run_report.py --data path\to\file.csv  # your own data
    python run_report.py --out reports            # choose where output goes

One command runs the whole pipeline. Schedule it (see schedule_weekly.ps1) and
the report regenerates itself on a cadence — that's the "automation".
"""
import argparse
import os

from autoanalyst import metrics, charts, narrative, report

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(HERE, "data", "sample_sales.csv")
DEFAULT_OUT = os.path.join(HERE, "outputs")


def main():
    parser = argparse.ArgumentParser(description="Automatically turn a sales CSV into a report.")
    parser.add_argument("--data", default=DEFAULT_DATA, help="path to the input CSV")
    parser.add_argument("--out", default=DEFAULT_OUT, help="output folder for the report + charts")
    args = parser.parse_args()

    df = metrics.load(args.data)
    k = metrics.kpis(df)
    monthly = metrics.monthly_trend(df)
    by_category = metrics.top_by(df, "category")
    by_region = metrics.top_by(df, "region")
    profit_by_category = df.groupby("category")["profit"].sum()
    anomaly_list = metrics.anomalies(monthly)

    facts = {
        "months": int(monthly.shape[0]),
        "start": k["start"],
        "end": k["end"],
        "total_sales": k["total_sales"],
        "total_profit": k["total_profit"],
        "margin": k["margin"],
        "top_region": by_region.index[0],
        "top_category": by_category.index[0],
        "change": metrics.latest_change(monthly),
        "loss_makers": metrics.loss_makers(df).to_dict(),
        "anomaly": ({"month": anomaly_list[0][0], "value": anomaly_list[0][1], "z": anomaly_list[0][2]}
                    if anomaly_list else None),
    }
    summary = narrative.write_summary(facts)

    os.makedirs(args.out, exist_ok=True)
    chart_files = [
        ("Monthly sales trend", charts.save_trend(monthly, args.out)),
        ("Sales by category", charts.save_sales_by_category(by_category, args.out)),
        ("Profit by category", charts.save_profit_by_category(profit_by_category, args.out)),
    ]
    markdown = report.build_markdown(k, summary, chart_files, facts["top_region"], facts["top_category"])

    out_md = os.path.join(args.out, "report.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Report written to: {out_md}")
    print(f"Charts written:    {[c for _, c in chart_files]}")
    print("\n--- Executive summary ---")
    print(summary)


if __name__ == "__main__":
    main()
