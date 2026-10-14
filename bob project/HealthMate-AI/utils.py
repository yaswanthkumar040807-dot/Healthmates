"""
HealthMate AI — Utility Functions
"""
import csv
import io
import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from config import MOOD_LABELS, MOOD_EMOJIS


# ── Date helpers ───────────────────────────────────────────────────────────────

def today_str() -> str:
    return datetime.date.today().isoformat()


def date_range(start: str, end: str) -> List[str]:
    """Return a list of ISO date strings from start to end inclusive."""
    s = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    days = (e - s).days + 1
    return [(s + datetime.timedelta(days=i)).isoformat() for i in range(max(days, 0))]


def week_start(reference: Optional[str] = None) -> str:
    """ISO date of the Monday of the week containing *reference* (default today)."""
    d = datetime.date.fromisoformat(reference) if reference else datetime.date.today()
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def week_end(reference: Optional[str] = None) -> str:
    s = datetime.date.fromisoformat(week_start(reference))
    return (s + datetime.timedelta(days=6)).isoformat()


def past_n_days(n: int) -> str:
    return (datetime.date.today() - datetime.timedelta(days=n - 1)).isoformat()


# ── Wellness helpers ───────────────────────────────────────────────────────────

def pct(value: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return min(100.0, round(value / target * 100, 1))


def mood_label(score: int) -> str:
    return MOOD_LABELS.get(score, "Unknown")


def mood_emoji(score: int) -> str:
    return MOOD_EMOJIS.get(score, "❓")


def bmi(weight_kg: float, height_cm: float) -> Optional[float]:
    if weight_kg and height_cm and height_cm > 0:
        h = height_cm / 100
        return round(weight_kg / (h * h), 1)
    return None


def bmi_category(bmi_val: float) -> str:
    if bmi_val < 18.5:
        return "Underweight"
    if bmi_val < 25:
        return "Healthy weight"
    if bmi_val < 30:
        return "Overweight"
    return "Obese"


# ── DataFrame helpers ─────────────────────────────────────────────────────────

def rows_to_df(rows) -> pd.DataFrame:
    """Convert a list of sqlite3.Row objects to a DataFrame."""
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


# ── CSV export ────────────────────────────────────────────────────────────────

def wellness_records_to_csv(rows) -> str:
    """Serialise wellness records to a UTF-8 CSV string."""
    df = rows_to_df(rows)
    if df.empty:
        return ""
    cols = ["record_date", "water_ml", "activity_minutes", "steps",
            "sleep_hours", "mood_score", "notes"]
    df = df[[c for c in cols if c in df.columns]]
    return df.to_csv(index=False)


def mood_entries_to_csv(rows) -> str:
    df = rows_to_df(rows)
    if df.empty:
        return ""
    cols = ["entry_date", "mood_score", "emotions", "journal"]
    df = df[[c for c in cols if c in df.columns]]
    return df.to_csv(index=False)


# ── Input validation ──────────────────────────────────────────────────────────

def validate_wellness_input(water_ml: Any, activity_min: Any, steps: Any,
                             sleep_h: Any, mood: Any) -> tuple:
    errors = []
    try:
        water_ml = int(water_ml)
        if not (0 <= water_ml <= 10000):
            errors.append("Water intake must be between 0 and 10 000 ml.")
    except (TypeError, ValueError):
        errors.append("Water intake must be a whole number.")

    try:
        activity_min = int(activity_min)
        if not (0 <= activity_min <= 1440):
            errors.append("Activity minutes must be between 0 and 1 440.")
    except (TypeError, ValueError):
        errors.append("Activity minutes must be a whole number.")

    try:
        steps = int(steps)
        if not (0 <= steps <= 100000):
            errors.append("Steps must be between 0 and 100 000.")
    except (TypeError, ValueError):
        errors.append("Steps must be a whole number.")

    try:
        sleep_h = float(sleep_h)
        if not (0.0 <= sleep_h <= 24.0):
            errors.append("Sleep hours must be between 0 and 24.")
    except (TypeError, ValueError):
        errors.append("Sleep hours must be a number.")

    if mood is not None:
        try:
            mood = int(mood)
            if not (1 <= mood <= 5):
                errors.append("Mood score must be between 1 and 5.")
        except (TypeError, ValueError):
            errors.append("Mood score must be a number.")

    return (not errors), errors


def validate_goal_value(goal_type: str, value: Any) -> tuple:
    limits = {
        "water_ml":          (100, 10000),
        "activity_minutes":  (5, 480),
        "steps":             (500, 50000),
        "sleep_hours":       (4, 12),
    }
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, f"Goal value must be a number."
    lo, hi = limits.get(goal_type, (0, 1e9))
    if not (lo <= v <= hi):
        return False, f"Value must be between {lo} and {hi} for this goal type."
    return True, ""
