"""
Tests for input validation and authentication logic.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))


# ── Wellness input validation ──────────────────────────────────────────────────

from utils import validate_wellness_input, validate_goal_value, pct, bmi, bmi_category


class TestWellnessInputValidation:

    def test_valid_input_passes(self):
        ok, errors = validate_wellness_input(2000, 30, 8000, 7.5, 4)
        assert ok is True
        assert errors == []

    def test_zero_values_valid(self):
        ok, errors = validate_wellness_input(0, 0, 0, 0.0, 1)
        assert ok is True

    def test_water_negative_invalid(self):
        ok, errors = validate_wellness_input(-100, 30, 8000, 7.0, 3)
        assert ok is False
        assert any("water" in e.lower() for e in errors)

    def test_water_too_large_invalid(self):
        ok, errors = validate_wellness_input(99999, 30, 8000, 7.0, 3)
        assert ok is False

    def test_activity_too_large(self):
        ok, errors = validate_wellness_input(2000, 2000, 8000, 7.0, 3)
        assert ok is False

    def test_sleep_out_of_range(self):
        ok, errors = validate_wellness_input(2000, 30, 8000, 30.0, 3)
        assert ok is False
        assert any("sleep" in e.lower() for e in errors)

    def test_mood_out_of_range(self):
        ok, errors = validate_wellness_input(2000, 30, 8000, 7.0, 6)
        assert ok is False

    def test_mood_zero_invalid(self):
        ok, errors = validate_wellness_input(2000, 30, 8000, 7.0, 0)
        assert ok is False

    def test_non_numeric_water(self):
        ok, errors = validate_wellness_input("abc", 30, 8000, 7.0, 3)
        assert ok is False

    def test_mood_none_skips_validation(self):
        ok, errors = validate_wellness_input(2000, 30, 8000, 7.0, None)
        assert ok is True

    def test_steps_too_large(self):
        ok, errors = validate_wellness_input(2000, 30, 200000, 7.0, 3)
        assert ok is False


class TestGoalValidation:

    def test_valid_water_goal(self):
        ok, msg = validate_goal_value("water_ml", 2500)
        assert ok is True

    def test_water_goal_too_low(self):
        ok, msg = validate_goal_value("water_ml", 50)
        assert ok is False

    def test_water_goal_too_high(self):
        ok, msg = validate_goal_value("water_ml", 50000)
        assert ok is False

    def test_valid_sleep_goal(self):
        ok, msg = validate_goal_value("sleep_hours", 8.0)
        assert ok is True

    def test_sleep_goal_too_low(self):
        ok, msg = validate_goal_value("sleep_hours", 1.0)
        assert ok is False

    def test_non_numeric_goal(self):
        ok, msg = validate_goal_value("water_ml", "abc")
        assert ok is False


# ── BMI helpers ────────────────────────────────────────────────────────────────

class TestBMI:

    def test_bmi_calculation(self):
        result = bmi(70.0, 175.0)
        assert result is not None
        assert abs(result - 22.9) < 0.2

    def test_bmi_zero_height(self):
        assert bmi(70.0, 0.0) is None

    def test_bmi_none_weight(self):
        assert bmi(None, 175.0) is None

    def test_bmi_categories(self):
        assert bmi_category(17.0) == "Underweight"
        assert bmi_category(22.0) == "Healthy weight"
        assert bmi_category(27.0) == "Overweight"
        assert bmi_category(32.0) == "Obese"


# ── Authentication ─────────────────────────────────────────────────────────────

class TestAuthValidation:

    def test_valid_registration(self):
        from auth import validate_registration
        ok, msg = validate_registration("alice", "alice@example.com", "password123", "password123")
        assert ok is True

    def test_username_too_short(self):
        from auth import validate_registration
        ok, msg = validate_registration("ab", "a@b.com", "password123", "password123")
        assert ok is False
        assert "username" in msg.lower()

    def test_username_invalid_chars(self):
        from auth import validate_registration
        ok, msg = validate_registration("alice smith", "a@b.com", "password123", "password123")
        assert ok is False

    def test_invalid_email(self):
        from auth import validate_registration
        ok, msg = validate_registration("alice", "not-an-email", "password123", "password123")
        assert ok is False
        assert "email" in msg.lower()

    def test_password_too_short(self):
        from auth import validate_registration
        ok, msg = validate_registration("alice", "alice@example.com", "short", "short")
        assert ok is False
        assert "password" in msg.lower()

    def test_passwords_do_not_match(self):
        from auth import validate_registration
        ok, msg = validate_registration("alice", "alice@example.com", "password123", "different456")
        assert ok is False
        assert "match" in msg.lower()

    def test_empty_login_fails(self):
        from auth import login_user
        ok, msg, uid = login_user("", "")
        assert ok is False
        assert uid is None


class TestPasswordHashing:

    def test_hash_is_not_plaintext(self):
        from auth import hash_password
        h = hash_password("mysecretpassword")
        assert h != "mysecretpassword"
        assert len(h) > 20

    def test_verify_correct_password(self):
        from auth import hash_password, verify_password
        h = hash_password("correcthorse")
        assert verify_password("correcthorse", h) is True

    def test_verify_wrong_password(self):
        from auth import hash_password, verify_password
        h = hash_password("correcthorse")
        assert verify_password("wrongpassword", h) is False

    def test_hash_salted_uniquely(self):
        from auth import hash_password
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses a unique salt each time


# ── Date utilities ─────────────────────────────────────────────────────────────

class TestDateUtils:

    def test_today_str_format(self):
        from utils import today_str
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", today_str())

    def test_past_n_days(self):
        import datetime
        from utils import past_n_days, today_str
        start = past_n_days(7)
        end = today_str()
        d_start = datetime.date.fromisoformat(start)
        d_end = datetime.date.fromisoformat(end)
        assert (d_end - d_start).days == 6

    def test_week_start_is_monday(self):
        from utils import week_start
        import datetime
        s = datetime.date.fromisoformat(week_start())
        assert s.weekday() == 0  # Monday

    def test_date_range_length(self):
        from utils import date_range
        r = date_range("2024-01-01", "2024-01-07")
        assert len(r) == 7
        assert r[0] == "2024-01-01"
        assert r[-1] == "2024-01-07"

    def test_date_range_empty_when_reversed(self):
        from utils import date_range
        r = date_range("2024-01-07", "2024-01-01")
        assert r == []


# ── CSV export ─────────────────────────────────────────────────────────────────

class TestCSVExport:

    def test_wellness_csv_empty(self):
        from utils import wellness_records_to_csv
        assert wellness_records_to_csv([]) == ""

    def test_mood_csv_empty(self):
        from utils import mood_entries_to_csv
        assert mood_entries_to_csv([]) == ""

    def test_wellness_csv_with_data(self, tmp_path, monkeypatch):
        from utils import wellness_records_to_csv

        import config
        db_file = tmp_path / "csv_test.db"
        monkeypatch.setattr(config, "DB_PATH", db_file)
        import database
        monkeypatch.setattr(database, "DB_PATH", db_file)
        database.init_db()
        uid = database.create_user("csvuser", "csv@test.com", "hash")
        database.upsert_wellness_record(uid, "2024-03-01", water_ml=1800)
        rows = database.get_all_wellness_records(uid)
        csv = wellness_records_to_csv(rows)
        assert "record_date" in csv
        assert "1800" in csv
