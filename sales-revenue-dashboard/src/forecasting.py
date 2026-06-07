"""
forecasting.py
==============
Rigorous forecast model selection via **walk-forward back-testing**.

PLAIN ENGLISH
-------------
A weak analyst trains ONE forecasting model and reports its "in-sample" error -
how well it fits data it has already seen. That always looks good (like grading
an exam with the answer key) and is misleading.

This module does what a real analyst does instead:
  1. Hide the most recent few months of sales (the "test set").
  2. Train each model only on the older months (the "train set").
  3. Ask each model to predict the hidden months.
  4. Compare the predictions to what ACTUALLY happened -> true out-of-sample error.
  5. Keep the most accurate model, retrain it on ALL data, and forecast the future.

We compare three classic time-series models:
    1. Holt-Winters (additive)           -> smooths level + trend + seasonality
    2. Holt-Winters on a log transform   -> captures *multiplicative* seasonality
    3. SARIMAX (seasonal ARIMA)          -> classic statistical workhorse

WHERE IT FITS
-------------
Imported by pipeline.forecast_sales(); not run directly. The whole pipeline is
launched with `python main.py`.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

# statsmodels prints "convergence" warnings on short series; hide them for a clean run.
warnings.filterwarnings("ignore")

# The three candidate models we will race against each other.
MODEL_NAMES = ["Holt-Winters", "Holt-Winters (log)", "SARIMAX(1,1,1)(1,1,1,12)"]


def _mape(actual, pred) -> float:
    """MAPE = Mean Absolute Percentage Error.

    On average, how far off (as a %) was the forecast? Lower = better.
    Example: MAPE of 15 means predictions were off by ~15% on average.
    """
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    # |actual - predicted| / actual  -> the % error each month; then average it.
    return float(np.mean(np.abs((actual - pred) / actual)) * 100)


def _fit(name: str, y: pd.Series):
    """Train ONE model on series `y`.

    Returns (results, transform). `transform` converts the model's output back
    to normal sales units - it's the identity for most models, but np.exp for
    the log model (because we trained that one on log(sales)).
    """
    if name == "Holt-Winters":
        # trend="add" + seasonal="add": add a trend slope and a repeating
        # 12-month seasonal pattern. seasonal_periods=12 -> yearly seasonality.
        res = ExponentialSmoothing(y, trend="add", seasonal="add",
                                   seasonal_periods=12,
                                   initialization_method="estimated").fit()
        return res, (lambda v: v)                 # no transform needed

    if name == "Holt-Winters (log)":
        # Train on log(sales). On the log scale, % growth becomes a straight
        # line, so a December that is "+40%" is modelled more naturally.
        res = ExponentialSmoothing(np.log(y), trend="add", seasonal="add",
                                   seasonal_periods=12,
                                   initialization_method="estimated").fit()
        return res, np.exp                        # undo the log with exp()

    # SARIMAX(p,d,q)(P,D,Q,s): seasonal ARIMA. (1,1,1) handles the short-term
    # pattern, (1,1,1,12) the yearly one. enforce_*=False lets it fit freely.
    res = SARIMAX(y, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    return res, (lambda v: v)


def backtest(monthly: pd.Series, horizon: int = 6) -> pd.DataFrame:
    """Score every model on a held-out test set (the heart of the rigour).

    `horizon` = how many recent months to hide and test on (default 6).
    Returns a table of each model's out-of-sample MAPE/RMSE, best first.
    """
    # Split: everything except the last `horizon` months trains; the rest tests.
    train, test = monthly.iloc[:-horizon], monthly.iloc[-horizon:]

    rows = []
    for name in MODEL_NAMES:
        try:
            res, tf = _fit(name, train)                  # train on old months
            pred = np.asarray(tf(res.forecast(horizon)), float)  # predict hidden months
            rows.append({
                "model": name,
                "oos_mape": round(_mape(test.values, pred), 1),          # % error
                # RMSE = typical error in dollars (penalises big misses more).
                "oos_rmse": round(float(np.sqrt(np.mean(
                    (test.values - pred) ** 2))), 0),
            })
        except Exception as exc:                          # a model failed to fit
            rows.append({"model": name, "oos_mape": np.nan, "oos_rmse": np.nan,
                         "error": str(exc)[:50]})

    # Sort so the most accurate (lowest MAPE) model is first; failures go last.
    return (pd.DataFrame(rows)
            .sort_values("oos_mape", na_position="last")
            .reset_index(drop=True))


def best_forecast(monthly: pd.Series, horizon: int = 6) -> dict:
    """Pick the back-test winner, retrain it on ALL data, and forecast ahead.

    Returns a chart-ready dict (the keys the charts expect) plus the comparison
    table, the chosen model's name, and its out-of-sample MAPE.
    """
    comp = backtest(monthly, horizon)                     # race the models
    valid = comp.dropna(subset=["oos_mape"])              # models that didn't crash
    best = valid.iloc[0]["model"] if not valid.empty else "Holt-Winters"
    oos_mape = float(valid.iloc[0]["oos_mape"]) if not valid.empty else float("nan")

    # Now that we know the winner, retrain it on the FULL history (we no longer
    # hide any months) so the real future forecast uses every data point.
    res, tf = _fit(best, monthly)
    fitted = pd.Series(np.asarray(tf(res.fittedvalues), float), index=monthly.index)
    fc_vals = np.asarray(tf(res.forecast(horizon)), float)

    # Build the future month labels (the months AFTER the last one we have).
    future_idx = pd.date_range(monthly.index[-1], periods=horizon + 1, freq="MS")[1:]
    forecast = pd.Series(fc_vals, index=future_idx)

    # Confidence band: forecast +/- 1.96 * (spread of the model's past errors).
    # 1.96 std-devs ~ a 95% interval under a normal assumption.
    resid = (monthly - fitted).dropna()
    ci = 1.96 * float(resid.std())

    return {"monthly": monthly, "fitted": fitted, "forecast": forecast, "ci": ci,
            "oos_mape": oos_mape, "model_name": best, "comparison": comp,
            "next_total": float(forecast.sum()), "periods": horizon}
