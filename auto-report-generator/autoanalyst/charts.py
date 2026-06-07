"""Render the report's charts as PNG files."""
import os
import matplotlib
matplotlib.use("Agg")  # headless backend — important for automation / servers
import matplotlib.pyplot as plt


def save_trend(monthly, out_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    monthly.plot(ax=ax, marker="o", color="#4c72b0")
    ax.set_title("Monthly sales trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Sales ($)")
    return _save(fig, out_dir, "trend.png")


def save_sales_by_category(by_cat, out_dir):
    fig, ax = plt.subplots(figsize=(8, 4))
    by_cat.sort_values().plot(kind="barh", ax=ax, color="#4c72b0")
    ax.set_title("Sales by category")
    ax.set_xlabel("Sales ($)")
    return _save(fig, out_dir, "sales_by_category.png")


def save_profit_by_category(profit_by_cat, out_dir):
    ordered = profit_by_cat.sort_values()
    colors = ["#d62728" if v < 0 else "#2ca02c" for v in ordered]  # red = loss
    fig, ax = plt.subplots(figsize=(8, 4))
    ordered.plot(kind="barh", ax=ax, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Profit by category (red = losing money)")
    ax.set_xlabel("Profit ($)")
    return _save(fig, out_dir, "profit_by_category.png")


def _save(fig, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, name), dpi=120)
    plt.close(fig)
    return name  # filename, for embedding in the Markdown report
