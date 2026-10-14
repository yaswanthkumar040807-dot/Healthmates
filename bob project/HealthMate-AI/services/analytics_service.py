"""
HealthMate AI — Analytics Service
Statistical trend analysis and optional ML wellness-trend module.
"""
import datetime
import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_MIN_ROWS_FOR_ML = 14  # minimum data points before attempting prediction


def compute_trend(series: pd.Series) -> float:
    """Return the slope of a simple linear regression over the series."""
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series), dtype=float)
    y = series.fillna(series.mean()).values.astype(float)
    if np.std(y) == 0:
        return 0.0
    coeffs = np.polyfit(x, y, 1)
    return float(coeffs[0])


def descriptive_stats(df: pd.DataFrame) -> Dict:
    """Return mean, std, min, max for key wellness columns."""
    cols = ["water_ml", "activity_minutes", "steps", "sleep_hours", "mood_score"]
    stats = {}
    for col in cols:
        if col in df.columns and not df[col].isna().all():
            s = df[col].dropna()
            stats[col] = {
                "mean": round(float(s.mean()), 2),
                "std": round(float(s.std()), 2) if len(s) > 1 else 0.0,
                "min": float(s.min()),
                "max": float(s.max()),
                "count": int(s.count()),
            }
    return stats


def weekly_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily records into ISO-week averages."""
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    if "record_date" not in d.columns:
        return pd.DataFrame()
    d["record_date"] = pd.to_datetime(d["record_date"], errors="coerce")
    d = d.dropna(subset=["record_date"])
    d["week"] = d["record_date"].dt.isocalendar().week.astype(str)
    d["year"] = d["record_date"].dt.isocalendar().year.astype(str)
    d["year_week"] = d["year"] + "-W" + d["week"].str.zfill(2)
    num_cols = ["water_ml", "activity_minutes", "steps", "sleep_hours", "mood_score"]
    available = [c for c in num_cols if c in d.columns]
    return d.groupby("year_week")[available].mean().reset_index()


def predict_activity_trend(df: pd.DataFrame) -> Optional[Dict]:
    """
    Estimate next-7-day average activity_minutes using linear regression on
    the user's own historical data. Returns None when data is insufficient.

    This is a simple educational trend estimator, not a clinical predictor.
    """
    if df.empty or "activity_minutes" not in df.columns:
        return None

    clean = df[["record_date", "activity_minutes"]].dropna()
    if len(clean) < _MIN_ROWS_FOR_ML:
        return {
            "available": False,
            "reason": f"At least {_MIN_ROWS_FOR_ML} days of data are needed. "
                      f"You have {len(clean)} so far.",
        }

    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_absolute_error

        clean = clean.sort_values("record_date").reset_index(drop=True)
        x = clean.index.values.reshape(-1, 1).astype(float)
        y = clean["activity_minutes"].values.astype(float)

        # Simple train/test split (last 20% as test)
        split = max(1, int(len(x) * 0.8))
        x_train, x_test = x[:split], x[split:]
        y_train, y_test = y[:split], y[split:]

        model = LinearRegression()
        model.fit(x_train, y_train)

        mae = mean_absolute_error(y_test, model.predict(x_test)) if len(x_test) > 0 else None

        # Predict next 7 days
        next_x = np.arange(len(x), len(x) + 7, dtype=float).reshape(-1, 1)
        preds = model.predict(next_x).clip(0, 1440).tolist()

        baseline_pred = float(y_train.mean())
        baseline_mae = float(np.abs(y_test - baseline_pred).mean()) if len(y_test) > 0 else None

        return {
            "available": True,
            "predictions_7d": [round(p, 1) for p in preds],
            "predicted_avg": round(float(np.mean(preds)), 1),
            "mae": round(mae, 1) if mae is not None else None,
            "baseline_mae": round(baseline_mae, 1) if baseline_mae is not None else None,
            "slope": round(float(model.coef_[0]), 2),
            "historical_mean": round(float(y.mean()), 1),
            "n_data_points": len(clean),
            "disclaimer": (
                "This is a simple linear trend estimate based solely on your own historical "
                "activity data. It is for educational purposes only and should not be used "
                "for medical or clinical decisions."
            ),
        }
    except ImportError:
        logger.warning("scikit-learn not available; skipping ML prediction.")
        return {
            "available": False,
            "reason": "scikit-learn is not installed. Install it to enable trend analysis.",
        }
    except Exception as exc:
        logger.error("ML prediction error: %s", exc)
        return {
            "available": False,
            "reason": "An error occurred during trend analysis.",
        }
