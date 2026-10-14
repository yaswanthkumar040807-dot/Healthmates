"""
Tests for database initialization and CRUD operations.
"""
import os
import sys
import tempfile
import datetime
from pathlib import Path

import pytest

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Point the database module to a fresh temp database for each test."""
    db_file = tmp_path / "test_healthmate.db"
    import config
    monkeypatch.setattr(config, "DB_PATH", db_file)
    import database
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    return database


# ── Init ──────────────────────────────────────────────────────────────────────

def test_init_db_creates_tables(tmp_db):
    db = tmp_db
    with db.get_connection() as conn:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert "users" in tables
    assert "user_profiles" in tables
    assert "wellness_records" in tables
    assert "mood_entries" in tables
    assert "wellness_goals" in tables
    assert "chat_history" in tables


def test_init_db_is_idempotent(tmp_db):
    """Calling init_db twice should not raise or destroy data."""
    db = tmp_db
    db.init_db()
    db.init_db()
    with db.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 0


# ── User creation and retrieval ───────────────────────────────────────────────

def test_create_and_retrieve_user(tmp_db):
    db = tmp_db
    uid = db.create_user("alice", "alice@example.com", "hashed_pw")
    assert isinstance(uid, int)
    assert uid > 0

    user = db.get_user_by_username("alice")
    assert user is not None
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"


def test_username_case_insensitive_lookup(tmp_db):
    db = tmp_db
    db.create_user("Bob", "bob@example.com", "hash")
    assert db.get_user_by_username("bob") is not None
    assert db.get_user_by_username("BOB") is not None


def test_duplicate_username_raises(tmp_db):
    db = tmp_db
    db.create_user("carol", "carol@example.com", "hash")
    with pytest.raises(Exception):
        db.create_user("carol", "carol2@example.com", "hash")


def test_create_user_creates_profile_and_goals(tmp_db):
    db = tmp_db
    uid = db.create_user("dave", "dave@example.com", "hash")
    profile = db.get_profile(uid)
    assert profile is not None
    goals = db.get_goals(uid)
    goal_types = {g["goal_type"] for g in goals}
    assert "water_ml" in goal_types
    assert "activity_minutes" in goal_types
    assert "steps" in goal_types
    assert "sleep_hours" in goal_types


def test_get_user_by_id(tmp_db):
    db = tmp_db
    uid = db.create_user("eve", "eve@example.com", "hash")
    user = db.get_user_by_id(uid)
    assert user["id"] == uid


def test_get_nonexistent_user_returns_none(tmp_db):
    db = tmp_db
    assert db.get_user_by_username("nobody") is None
    assert db.get_user_by_id(99999) is None


# ── Profile update ────────────────────────────────────────────────────────────

def test_update_profile(tmp_db):
    db = tmp_db
    uid = db.create_user("frank", "frank@example.com", "hash")
    db.update_profile(uid, full_name="Frank Smith", age=30, height_cm=175.0, weight_kg=72.0)
    profile = db.get_profile(uid)
    assert profile["full_name"] == "Frank Smith"
    assert profile["age"] == 30


# ── Wellness records ──────────────────────────────────────────────────────────

def test_upsert_and_retrieve_wellness_record(tmp_db):
    db = tmp_db
    uid = db.create_user("gina", "gina@example.com", "hash")
    today = datetime.date.today().isoformat()

    db.upsert_wellness_record(uid, today, water_ml=2000, activity_minutes=45,
                              steps=8500, sleep_hours=7.5, mood_score=4)
    record = db.get_wellness_record(uid, today)
    assert record is not None
    assert record["water_ml"] == 2000
    assert record["activity_minutes"] == 45
    assert record["steps"] == 8500
    assert abs(record["sleep_hours"] - 7.5) < 0.01
    assert record["mood_score"] == 4


def test_upsert_updates_existing_record(tmp_db):
    db = tmp_db
    uid = db.create_user("hank", "hank@example.com", "hash")
    today = datetime.date.today().isoformat()

    db.upsert_wellness_record(uid, today, water_ml=1000)
    db.upsert_wellness_record(uid, today, water_ml=2500)
    record = db.get_wellness_record(uid, today)
    assert record["water_ml"] == 2500


def test_get_wellness_records_date_range(tmp_db):
    db = tmp_db
    uid = db.create_user("iris", "iris@example.com", "hash")

    db.upsert_wellness_record(uid, "2024-01-01", water_ml=1500)
    db.upsert_wellness_record(uid, "2024-01-05", water_ml=2000)
    db.upsert_wellness_record(uid, "2024-01-10", water_ml=2500)

    rows = db.get_wellness_records(uid, "2024-01-01", "2024-01-05")
    assert len(rows) == 2

    rows_all = db.get_wellness_records(uid, "2024-01-01", "2024-01-10")
    assert len(rows_all) == 3


def test_wellness_records_user_isolation(tmp_db):
    db = tmp_db
    uid1 = db.create_user("user1", "u1@example.com", "hash")
    uid2 = db.create_user("user2", "u2@example.com", "hash")
    today = datetime.date.today().isoformat()

    db.upsert_wellness_record(uid1, today, water_ml=1000)
    record = db.get_wellness_record(uid2, today)
    assert record is None


# ── Mood entries ──────────────────────────────────────────────────────────────

def test_add_and_retrieve_mood_entry(tmp_db):
    db = tmp_db
    uid = db.create_user("jack", "jack@example.com", "hash")
    today = datetime.date.today().isoformat()

    db.add_mood_entry(uid, today, mood_score=4, emotions="Happy, Calm", journal="Good day.")
    rows = db.get_mood_entries(uid, today, today)
    assert len(rows) == 1
    assert rows[0]["mood_score"] == 4
    assert rows[0]["emotions"] == "Happy, Calm"
    assert rows[0]["journal"] == "Good day."


# ── Goals ─────────────────────────────────────────────────────────────────────

def test_upsert_goal(tmp_db):
    db = tmp_db
    uid = db.create_user("kate", "kate@example.com", "hash")
    db.upsert_goal(uid, "water_ml", 3000)
    goals = {g["goal_type"]: g["target_value"] for g in db.get_goals(uid)}
    assert goals["water_ml"] == 3000


def test_upsert_goal_updates_existing(tmp_db):
    db = tmp_db
    uid = db.create_user("leo", "leo@example.com", "hash")
    db.upsert_goal(uid, "steps", 10000)
    db.upsert_goal(uid, "steps", 12000)
    goals = {g["goal_type"]: g["target_value"] for g in db.get_goals(uid)}
    assert goals["steps"] == 12000


# ── Chat history ──────────────────────────────────────────────────────────────

def test_add_and_retrieve_chat(tmp_db):
    db = tmp_db
    uid = db.create_user("mia", "mia@example.com", "hash")
    db.add_chat_message(uid, "user", "How much water?", "user")
    db.add_chat_message(uid, "assistant", "About 2 litres.", "fallback")
    history = db.get_chat_history(uid)
    assert len(history) == 2


def test_clear_chat_history(tmp_db):
    db = tmp_db
    uid = db.create_user("ned", "ned@example.com", "hash")
    db.add_chat_message(uid, "user", "Hello", "user")
    db.clear_chat_history(uid)
    assert db.get_chat_history(uid) == []


# ── Data deletion ─────────────────────────────────────────────────────────────

def test_delete_user_data_keeps_account(tmp_db):
    db = tmp_db
    uid = db.create_user("oliver", "oliver@example.com", "hash")
    today = datetime.date.today().isoformat()
    db.upsert_wellness_record(uid, today, water_ml=1000)
    db.delete_user_data(uid)
    rows = db.get_all_wellness_records(uid)
    assert len(rows) == 0
    # Account still exists
    assert db.get_user_by_id(uid) is not None


def test_delete_user_account(tmp_db):
    db = tmp_db
    uid = db.create_user("pam", "pam@example.com", "hash")
    db.delete_user_account(uid)
    assert db.get_user_by_id(uid) is None
