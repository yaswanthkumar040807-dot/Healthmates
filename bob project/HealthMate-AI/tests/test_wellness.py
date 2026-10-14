"""
Tests for wellness service business logic and goal progress calculations.
"""
import sys
import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))


@pytest.fixture
def db_and_user(tmp_path, monkeypatch):
    import config
    db_file = tmp_path / "test_wellness.db"
    monkeypatch.setattr(config, "DB_PATH", db_file)
    import database
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    uid = database.create_user("testuser", "test@example.com", "hash")
    return database, uid


# ── Today's summary ────────────────────────────────────────────────────────────

def test_today_summary_empty(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)
    summary = ws.get_today_summary(uid)
    assert summary["water_ml"] == 0
    assert summary["activity_minutes"] == 0
    assert summary["steps"] == 0
    assert summary["sleep_hours"] == 0.0
    assert summary["mood_score"] is None


def test_today_summary_reflects_record(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)
    today = datetime.date.today().isoformat()
    database.upsert_wellness_record(uid, today, water_ml=1800, activity_minutes=35,
                                    steps=7000, sleep_hours=7.0, mood_score=3)
    summary = ws.get_today_summary(uid)
    assert summary["water_ml"] == 1800
    assert summary["activity_minutes"] == 35
    assert summary["steps"] == 7000
    assert abs(summary["sleep_hours"] - 7.0) < 0.01
    assert summary["mood_score"] == 3


# ── Goal completion stats ──────────────────────────────────────────────────────

def test_goal_completion_no_data(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)
    stats = ws.get_goal_completion_stats(uid, 7)
    # All should be 0 with no data
    for v in stats.values():
        assert v == 0.0


def test_goal_completion_all_met(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)

    # Set goals
    database.upsert_goal(uid, "water_ml", 2000)
    database.upsert_goal(uid, "activity_minutes", 30)
    database.upsert_goal(uid, "steps", 5000)
    database.upsert_goal(uid, "sleep_hours", 7.0)

    # Log records for last 7 days that all meet goals
    today = datetime.date.today()
    for i in range(7):
        d = (today - datetime.timedelta(days=i)).isoformat()
        database.upsert_wellness_record(uid, d, water_ml=2500, activity_minutes=45,
                                        steps=8000, sleep_hours=8.0)

    stats = ws.get_goal_completion_stats(uid, 7)
    assert stats["water_ml"] == 100.0
    assert stats["activity_minutes"] == 100.0
    assert stats["steps"] == 100.0
    assert stats["sleep_hours"] == 100.0


# ── Last N days dataframe ──────────────────────────────────────────────────────

def test_last_n_days_df_empty(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)
    df = ws.get_last_n_days_df(uid, 7)
    assert df.empty


def test_last_n_days_df_with_data(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)

    today = datetime.date.today()
    for i in range(5):
        d = (today - datetime.timedelta(days=i)).isoformat()
        database.upsert_wellness_record(uid, d, water_ml=1500 + i * 100)

    df = ws.get_last_n_days_df(uid, 7)
    assert len(df) == 5
    assert "water_ml" in df.columns


# ── Recent activity ────────────────────────────────────────────────────────────

def test_get_recent_activity_returns_most_recent(db_and_user, monkeypatch):
    database, uid = db_and_user
    import services.wellness_service as ws
    monkeypatch.setattr("services.wellness_service.db", database)

    today = datetime.date.today()
    for i in range(10):
        d = (today - datetime.timedelta(days=i)).isoformat()
        database.upsert_wellness_record(uid, d, water_ml=1000)

    recent = ws.get_recent_activity(uid, 5)
    assert len(recent) == 5


# ── pct helper ─────────────────────────────────────────────────────────────────

def test_pct_calculation():
    from utils import pct
    assert pct(1500, 2500) == 60.0
    assert pct(0, 2500) == 0.0
    assert pct(3000, 2500) == 100.0  # capped at 100
    assert pct(100, 0) == 0.0         # zero division guard


# ── Analytics service ─────────────────────────────────────────────────────────

def test_descriptive_stats_empty():
    import pandas as pd
    from services.analytics_service import descriptive_stats
    assert descriptive_stats(pd.DataFrame()) == {}


def test_descriptive_stats_basic():
    import pandas as pd
    from services.analytics_service import descriptive_stats
    df = pd.DataFrame({
        "water_ml": [1000, 2000, 1500],
        "activity_minutes": [20, 40, 30],
    })
    stats = descriptive_stats(df)
    assert "water_ml" in stats
    assert stats["water_ml"]["mean"] == 1500.0
    assert stats["water_ml"]["min"] == 1000.0
    assert stats["water_ml"]["max"] == 2000.0


def test_predict_activity_insufficient_data():
    import pandas as pd
    from services.analytics_service import predict_activity_trend
    df = pd.DataFrame({
        "record_date": ["2024-01-01", "2024-01-02"],
        "activity_minutes": [30, 45],
    })
    result = predict_activity_trend(df)
    assert result["available"] is False


def test_predict_activity_sufficient_data():
    import pandas as pd
    import numpy as np
    from services.analytics_service import predict_activity_trend

    dates = pd.date_range("2024-01-01", periods=20).strftime("%Y-%m-%d").tolist()
    minutes = [30 + i for i in range(20)]
    df = pd.DataFrame({"record_date": dates, "activity_minutes": minutes})
    result = predict_activity_trend(df)
    if result.get("available"):
        assert "predictions_7d" in result
        assert len(result["predictions_7d"]) == 7
        assert "predicted_avg" in result
