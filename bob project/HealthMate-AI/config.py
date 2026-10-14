"""
HealthMate AI — Central Configuration
Loads settings from environment variables with safe defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project root (one level above this file)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Load .env if present
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

# ── Database ──────────────────────────────────────────────────────────────────
_db_path_env = os.getenv("DB_PATH", "").strip()
DB_PATH: Path = Path(_db_path_env) if _db_path_env else PROJECT_ROOT / "data" / "healthmate.db"

# ── LLM / AI assistant ────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip()
AI_AVAILABLE: bool = bool(OPENAI_API_KEY)

# ── App ───────────────────────────────────────────────────────────────────────
APP_NAME = "HealthMate AI"
APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-me-in-production")
APP_VERSION = "1.0.0"

# ── Wellness defaults ─────────────────────────────────────────────────────────
DEFAULT_GOALS = {
    "water_ml": 2500,
    "activity_minutes": 30,
    "steps": 8000,
    "sleep_hours": 8.0,
}

MOOD_LABELS = {
    1: "Very Low",
    2: "Low",
    3: "Neutral",
    4: "Good",
    5: "Excellent",
}

MOOD_EMOJIS = {
    1: "😞",
    2: "😕",
    3: "😐",
    4: "🙂",
    5: "😄",
}

EMOTION_TAGS = [
    "Calm", "Happy", "Energetic", "Grateful", "Anxious",
    "Stressed", "Tired", "Lonely", "Motivated", "Sad",
    "Focused", "Overwhelmed", "Content", "Irritable", "Hopeful",
]
