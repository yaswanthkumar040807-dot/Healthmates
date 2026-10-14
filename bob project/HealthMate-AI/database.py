"""
HealthMate AI — Database Layer
Handles SQLite initialization and all parameterized queries.
"""
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple

from config import DB_PATH

logger = logging.getLogger(__name__)


def get_db_path() -> Path:
    return DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield an auto-closing, row-factory-enabled SQLite connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not already exist. Safe to call repeatedly."""
    with get_connection() as conn:
        conn.executescript("""
        -- ── Users ──────────────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT  NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

        -- ── User profiles ──────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS user_profiles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            full_name       TEXT    DEFAULT '',
            age             INTEGER,
            gender          TEXT    DEFAULT '',
            height_cm       REAL,
            weight_kg       REAL,
            activity_level  TEXT    DEFAULT 'moderate',
            health_notes    TEXT    DEFAULT '',
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- ── Wellness records ───────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS wellness_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            record_date     TEXT    NOT NULL,
            water_ml        INTEGER NOT NULL DEFAULT 0,
            activity_minutes INTEGER NOT NULL DEFAULT 0,
            steps           INTEGER NOT NULL DEFAULT 0,
            sleep_hours     REAL    NOT NULL DEFAULT 0.0,
            mood_score      INTEGER CHECK(mood_score BETWEEN 1 AND 5),
            notes           TEXT    DEFAULT '',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, record_date)
        );
        CREATE INDEX IF NOT EXISTS idx_wellness_user_date ON wellness_records(user_id, record_date);

        -- ── Mood entries ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS mood_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            entry_date  TEXT    NOT NULL,
            mood_score  INTEGER NOT NULL CHECK(mood_score BETWEEN 1 AND 5),
            emotions    TEXT    DEFAULT '',
            journal     TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_mood_user_date ON mood_entries(user_id, entry_date);

        -- ── Wellness goals ─────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS wellness_goals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            goal_type       TEXT    NOT NULL,
            target_value    REAL    NOT NULL,
            period          TEXT    NOT NULL DEFAULT 'daily',
            active          INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, goal_type)
        );

        -- ── Chat history ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role        TEXT    NOT NULL CHECK(role IN ('user','assistant')),
            content     TEXT    NOT NULL,
            source      TEXT    NOT NULL DEFAULT 'fallback',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id, created_at);
        """)
    logger.info("Database initialized at %s", DB_PATH)


# ── User helpers ───────────────────────────────────────────────────────────────

def create_user(username: str, email: str, password_hash: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username.strip(), email.strip().lower(), password_hash),
        )
        user_id = cur.lastrowid
        conn.execute(
            "INSERT INTO user_profiles (user_id) VALUES (?)",
            (user_id,),
        )
        conn.execute(
            """INSERT OR IGNORE INTO wellness_goals
               (user_id, goal_type, target_value, period)
               VALUES
               (?, 'water_ml',          2500, 'daily'),
               (?, 'activity_minutes',  30,   'daily'),
               (?, 'steps',             8000, 'daily'),
               (?, 'sleep_hours',       8.0,  'daily')""",
            (user_id, user_id, user_id, user_id),
        )
    return user_id


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_profile(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()


def update_profile(user_id: int, **fields) -> None:
    allowed = {"full_name", "age", "gender", "height_cm", "weight_kg",
               "activity_level", "health_notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id]
    with get_connection() as conn:
        conn.execute(
            f"UPDATE user_profiles SET {set_clause}, updated_at = datetime('now') WHERE user_id = ?",
            values,
        )


def delete_user_data(user_id: int) -> None:
    """Delete all records for a user but keep the account."""
    with get_connection() as conn:
        conn.execute("DELETE FROM wellness_records WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM mood_entries WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE wellness_goals SET target_value = target_value WHERE user_id = ?",
            (user_id,),
        )


def delete_user_account(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ── Wellness records ───────────────────────────────────────────────────────────

def upsert_wellness_record(user_id: int, record_date: str, **fields) -> None:
    allowed = {"water_ml", "activity_minutes", "steps", "sleep_hours", "mood_score", "notes"}
    data = {k: v for k, v in fields.items() if k in allowed}
    if not data:
        return
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    updates = ", ".join(f"{k} = excluded.{k}" for k in data)
    sql = f"""
        INSERT INTO wellness_records (user_id, record_date, {cols})
        VALUES (?, ?, {placeholders})
        ON CONFLICT(user_id, record_date) DO UPDATE SET {updates},
            updated_at = datetime('now')
    """
    with get_connection() as conn:
        conn.execute(sql, [user_id, record_date] + list(data.values()))


def get_wellness_record(user_id: int, record_date: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM wellness_records WHERE user_id = ? AND record_date = ?",
            (user_id, record_date),
        ).fetchone()


def get_wellness_records(user_id: int, start_date: str, end_date: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM wellness_records
               WHERE user_id = ? AND record_date BETWEEN ? AND ?
               ORDER BY record_date ASC""",
            (user_id, start_date, end_date),
        ).fetchall()


def get_all_wellness_records(user_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM wellness_records WHERE user_id = ? ORDER BY record_date ASC",
            (user_id,),
        ).fetchall()


# ── Mood entries ───────────────────────────────────────────────────────────────

def add_mood_entry(user_id: int, entry_date: str, mood_score: int,
                   emotions: str = "", journal: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO mood_entries (user_id, entry_date, mood_score, emotions, journal)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, entry_date, mood_score, emotions, journal),
        )


def get_mood_entries(user_id: int, start_date: str, end_date: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM mood_entries
               WHERE user_id = ? AND entry_date BETWEEN ? AND ?
               ORDER BY entry_date ASC""",
            (user_id, start_date, end_date),
        ).fetchall()


def get_all_mood_entries(user_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM mood_entries WHERE user_id = ? ORDER BY entry_date ASC",
            (user_id,),
        ).fetchall()


# ── Goals ──────────────────────────────────────────────────────────────────────

def get_goals(user_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM wellness_goals WHERE user_id = ? AND active = 1",
            (user_id,),
        ).fetchall()


def upsert_goal(user_id: int, goal_type: str, target_value: float, period: str = "daily") -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO wellness_goals (user_id, goal_type, target_value, period)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, goal_type) DO UPDATE SET
                   target_value = excluded.target_value,
                   period = excluded.period,
                   updated_at = datetime('now')""",
            (user_id, goal_type, target_value, period),
        )


# ── Chat history ───────────────────────────────────────────────────────────────

def add_chat_message(user_id: int, role: str, content: str, source: str = "fallback") -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content, source) VALUES (?,?,?,?)",
            (user_id, role, content, source),
        )


def get_chat_history(user_id: int, limit: int = 50) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM chat_history WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()


def clear_chat_history(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
