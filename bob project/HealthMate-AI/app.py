"""
HealthMate AI — Main Application Entry Point
Run with:  streamlit run app.py
"""
import sys
from pathlib import Path

# Make project root importable when launched from any directory
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import streamlit as st

import database as db
from config import APP_NAME, APP_VERSION

# ── Page configuration (must be first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global font and background */
html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
.stApp { background-color: #f0f7f4; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a6b4a 0%, #2d9b68 100%);
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stSelectbox label { color: #d4edda !important; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #d4edda;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* Section headings */
h1 { color: #1a6b4a; }
h2 { color: #2d7a55; }
h3 { color: #3d8c66; }

/* Buttons */
.stButton > button {
    background: #2d9b68;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}
.stButton > button:hover { background: #1a6b4a; }

/* Progress bars */
.stProgress > div > div > div { background-color: #2d9b68; }

/* Success / info boxes */
.stSuccess { background: #d4edda; border-left: 4px solid #2d9b68; }
.stInfo    { background: #e8f4f8; border-left: 4px solid #3b82d4; }

/* Cards */
.hm-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #d4edda;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.hm-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1a6b4a;
    margin-bottom: 8px;
}
.hm-tag {
    display: inline-block;
    background: #d4edda;
    color: #1a6b4a;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 2px;
}
.hm-muted { color: #6c757d; font-size: 0.88rem; }
</style>
""", unsafe_allow_html=True)

# ── Ensure DB is ready ────────────────────────────────────────────────────────
db.init_db()

# ── Session state defaults ────────────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ── Lazy page imports ─────────────────────────────────────────────────────────
from pages import (
    dashboard, profile, wellness_tracker, mental_wellness,
    ai_assistant, health_education, goals, analytics, settings, about,
)

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h1 style='text-align:center;font-size:1.5rem;margin-bottom:0;'>"
        "🩺 HealthMate AI</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:0.78rem;opacity:0.7;margin-top:4px;'>"
        f"v{APP_VERSION} · SDG 3 Platform</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if st.session_state.user_id:
        st.markdown(
            f"<p style='text-align:center;font-size:0.9rem;'>"
            f"👋 <b>{st.session_state.username}</b></p>",
            unsafe_allow_html=True,
        )

    NAV_ITEMS = [
        ("🏠 Home Dashboard",        "Home"),
        ("👤 My Profile",            "Profile"),
        ("📋 Daily Wellness Tracker", "Tracker"),
        ("🧠 Mood & Mental Wellness", "Mood"),
        ("🤖 AI Wellness Assistant",  "Assistant"),
        ("📚 Health Education",       "Education"),
        ("🎯 My Goals & Reminders",   "Goals"),
        ("📊 Reports & Analytics",    "Analytics"),
        ("⚙️ Privacy & Settings",     "Settings"),
        ("ℹ️ About the Project",      "About"),
    ]

    for label, key in NAV_ITEMS:
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key

    st.markdown("---")
    if st.session_state.user_id:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.page = "Home"
            st.rerun()
    st.markdown(
        "<p style='text-align:center;font-size:0.72rem;opacity:0.6;margin-top:8px;'>"
        "HealthMate AI is an educational wellness tool.<br>"
        "It is not a substitute for professional medical advice.</p>",
        unsafe_allow_html=True,
    )

# ── Route to the selected page ────────────────────────────────────────────────
PAGE_MAP = {
    "Home":       dashboard.render,
    "Profile":    profile.render,
    "Tracker":    wellness_tracker.render,
    "Mood":       mental_wellness.render,
    "Assistant":  ai_assistant.render,
    "Education":  health_education.render,
    "Goals":      goals.render,
    "Analytics":  analytics.render,
    "Settings":   settings.render,
    "About":      about.render,
}

render_fn = PAGE_MAP.get(st.session_state.page, dashboard.render)
render_fn()
