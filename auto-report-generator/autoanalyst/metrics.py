"""Compute the numbers the report talks about. Pure pandas, no surprises."""
import pandas as pd


def load(path, date_col="date"):
    """Load the CSV and parse the date column so we can sort/group by month."""
    df = pd.read_csv(path)
    df[date_col] = pd.to_datetime(df[date_col])
    return df


def kpis(df, value="sales", profit="profit", date_col="date"):
    total_sales = float(df[value].sum())
    total_profit = float(df[profit].sum())
    return {
        "rows": len(df),
        "total_sales": total_sales,
        "total_profit": total_profit,
        "margin": (total_profit / total_sales) if total_sales else 0.0,
        "start": df[date_col].min(),
        "end": df[date_col].max(),
    }


def monthly_trend(df, value="sales", date_col="date"):
    return df.groupby(date_col)[value].sum().sort_index()


def latest_change(monthly):
    """Percentage change between the last two periods."""
    if len(monthly) < 2:
        return None
    last, prev = float(monthly.iloc[-1]), float(monthly.iloc[-2])
    return {
        "last_period": monthly.index[-1],
        "last": last,
        "prev": prev,
        "pct": (last - prev) / prev if prev else 0.0,
    }


def top_by(df, group, value="sales"):
    return df.groupby(group)[value].sum().sort_values(ascending=False)


def loss_makers(df, group="category", profit="profit"):
    """Categories (or any group) whose total profit is negative."""
    totals = df.groupby(group)[profit].sum().sort_values()
    return totals[totals < 0]


def anomalies(monthly, z_threshold=2.0):
    """Flag months whose total is a statistical outlier (|z| >= threshold)."""
    mean, std = monthly.mean(), monthly.std()
    if not std:
        return []
    out = []
    for idx, val in monthly.items():
        z = (val - mean) / std
        if abs(z) >= z_threshold:
            out.append((idx, float(val), float(z)))
    return out
