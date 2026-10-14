"""
HealthMate AI — Wellness Service
Business logic for wellness records and goal progress.
"""
import datetime
from typing import Dict, List, Optional

import pandas as pd

import database as db
from utils import rows_to_df, pct, today_str, past_n_days, week_start, week_end


def get_today_summary(user_id: int) -> Dict:
    """Return today's wellness values and goal progress."""
    today = today_str()
    record = db.get_wellness_record(user_id, today)
    goals = {g["goal_type"]: g["target_value"] for g in db.get_goals(user_id)}

    water = record["water_ml"] if record and record["water_ml"] else 0
    activity = record["activity_minutes"] if record and record["activity_minutes"] else 0
    steps = record["steps"] if record and record["steps"] else 0
    sleep = record["sleep_hours"] if record and record["sleep_hours"] else 0.0
    mood = record["mood_score"] if record and record["mood_score"] else None
    notes = record["notes"] if record and record["notes"] else ""

    return {
        "water_ml": water,
        "activity_minutes": activity,
        "steps": steps,
        "sleep_hours": sleep,
        "mood_score": mood,
        "notes": notes,
        "water_pct": pct(water, goals.get("water_ml", 2500)),
        "activity_pct": pct(activity, goals.get("activity_minutes", 30)),
        "steps_pct": pct(steps, goals.get("steps", 8000)),
        "sleep_pct": pct(sleep, goals.get("sleep_hours", 8.0)),
        "goals": goals,
    }


def get_weekly_df(user_id: int, reference_date: Optional[str] = None) -> pd.DataFrame:
    start = week_start(reference_date)
    end = week_end(reference_date)
    rows = db.get_wellness_records(user_id, start, end)
    df = rows_to_df(rows)
    if df.empty:
        return df
    df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def get_last_n_days_df(user_id: int, n: int = 30) -> pd.DataFrame:
    start = past_n_days(n)
    end = today_str()
    rows = db.get_wellness_records(user_id, start, end)
    df = rows_to_df(rows)
    if df.empty:
        return df
    df["record_date"] = pd.to_datetime(df["record_date"])
    return df


def get_goal_completion_stats(user_id: int, n_days: int = 7) -> Dict:
    """Return % of days in the last n_days each goal was met."""
    start = past_n_days(n_days)
    end = today_str()
    rows = db.get_wellness_records(user_id, start, end)
    df = rows_to_df(rows)
    goals = {g["goal_type"]: g["target_value"] for g in db.get_goals(user_id)}

    if df.empty:
        return {k: 0.0 for k in goals}

    stats = {}
    for goal_type, target in goals.items():
        col_map = {
            "water_ml": "water_ml",
            "activity_minutes": "activity_minutes",
            "steps": "steps",
            "sleep_hours": "sleep_hours",
        }
        col = col_map.get(goal_type)
        if col and col in df.columns:
            met = (df[col] >= target).sum()
            stats[goal_type] = round(met / n_days * 100, 1)
        else:
            stats[goal_type] = 0.0
    return stats


def save_wellness_record(user_id: int, record_date: str, **fields) -> None:
    db.upsert_wellness_record(user_id, record_date, **fields)


def get_recent_activity(user_id: int, n: int = 5) -> List[Dict]:
    """Return the n most recent days that have any wellness data."""
    rows = db.get_wellness_records(user_id, "2000-01-01", today_str())
    if not rows:
        return []
    df = rows_to_df(rows).tail(n)
    return df.to_dict("records")
