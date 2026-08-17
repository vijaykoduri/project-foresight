"""Demand forecasting engine using scikit-learn."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


MIN_HISTORY_DAYS = 14


def _build_daily_series(sales_records: list[dict[str, Any]]) -> pd.DataFrame:
    if not sales_records:
        return pd.DataFrame(columns=["date", "demand"])

    df = pd.DataFrame(sales_records)
    df["date"] = pd.to_datetime(df["sale_date"]).dt.date
    daily = df.groupby("date")["quantity"].sum().reset_index()
    daily.columns = ["date", "demand"]
    daily["date"] = pd.to_datetime(daily["date"])

    if daily.empty:
        return daily

    full_range = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    daily = daily.set_index("date").reindex(full_range, fill_value=0).reset_index()
    daily.columns = ["date", "demand"]
    return daily


def _fallback_forecast(daily: pd.DataFrame, horizon_days: int) -> dict[str, Any]:
    avg_demand = float(daily["demand"].mean()) if not daily.empty else 0.0
    trend = 0.0
    if len(daily) >= 7:
        recent = daily["demand"].tail(7).mean()
        prior = daily["demand"].head(max(1, len(daily) - 7)).mean()
        trend = (recent - prior) / max(prior, 1)

    start = date.today() + timedelta(days=1)
    results = []
    for i in range(horizon_days):
        d = start + timedelta(days=i)
        predicted = max(0.0, avg_demand * (1 + trend * 0.1))
        results.append(
            {
                "forecast_date": d,
                "predicted_demand": round(predicted, 2),
                "lower_bound": round(max(0, predicted * 0.8), 2),
                "upper_bound": round(predicted * 1.2, 2),
                "is_historical": False,
            }
        )

    historical = []
    for _, row in daily.tail(30).iterrows():
        historical.append(
            {
                "forecast_date": row["date"].date(),
                "predicted_demand": float(row["demand"]),
                "lower_bound": None,
                "upper_bound": None,
                "is_historical": True,
            }
        )

    return {
        "model_type": "historical_average_fallback",
        "confidence_score": 0.5,
        "mae": None,
        "rmse": None,
        "status": "completed",
        "notes": "Insufficient historical data for ML model; using average-based fallback.",
        "results": historical + results,
    }


def generate_forecast(sales_records: list[dict[str, Any]], horizon_days: int = 30) -> dict[str, Any]:
    daily = _build_daily_series(sales_records)

    if len(daily) < MIN_HISTORY_DAYS:
        return _fallback_forecast(daily, horizon_days)

    daily = daily.copy()
    daily["day_index"] = np.arange(len(daily))
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["rolling_7"] = daily["demand"].rolling(window=7, min_periods=1).mean()
    daily["lag_1"] = daily["demand"].shift(1).fillna(daily["demand"].mean())
    daily["lag_7"] = daily["demand"].shift(7).fillna(daily["demand"].mean())

    features = ["day_index", "day_of_week", "rolling_7", "lag_1", "lag_7"]
    X = daily[features].values
    y = daily["demand"].values

    model = LinearRegression()
    model.fit(X, y)

    predictions_in_sample = model.predict(X)
    mae = float(mean_absolute_error(y, predictions_in_sample))
    rmse = float(np.sqrt(mean_squared_error(y, predictions_in_sample)))

    last_row = daily.iloc[-1]
    last_date = last_row["date"]
    last_index = int(last_row["day_index"])
    rolling = float(last_row["rolling_7"])
    lag_1 = float(last_row["demand"])
    lag_7 = float(daily["demand"].tail(7).mean())

    future_results = []
    start = date.today() + timedelta(days=1)
    for i in range(horizon_days):
        d = start + timedelta(days=i)
        day_index = last_index + i + 1
        day_of_week = d.weekday()
        X_pred = np.array([[day_index, day_of_week, rolling, lag_1, lag_7]])
        predicted = max(0.0, float(model.predict(X_pred)[0]))
        std = float(daily["demand"].std()) if len(daily) > 1 else 1.0
        future_results.append(
            {
                "forecast_date": d,
                "predicted_demand": round(predicted, 2),
                "lower_bound": round(max(0, predicted - std), 2),
                "upper_bound": round(predicted + std, 2),
                "is_historical": False,
            }
        )
        lag_7 = (lag_7 * 6 + predicted) / 7
        lag_1 = predicted
        rolling = (rolling * 6 + predicted) / 7

    historical = []
    for idx, row in daily.tail(30).iterrows():
        pred = max(0.0, float(predictions_in_sample[daily.index.get_loc(idx)]))
        historical.append(
            {
                "forecast_date": row["date"].date(),
                "predicted_demand": round(pred, 2),
                "lower_bound": None,
                "upper_bound": None,
                "is_historical": True,
            }
        )

    confidence = max(0.0, min(1.0, 1 - (mae / (daily["demand"].mean() + 1))))

    return {
        "model_type": "linear_regression",
        "confidence_score": round(confidence, 3),
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "status": "completed",
        "notes": None,
        "results": historical + future_results,
    }
