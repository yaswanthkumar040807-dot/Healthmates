"""
HealthMate AI — Home Dashboard Page
"""
import streamlit as st
import plotly.graph_objects as go

from config import MOOD_EMOJIS, MOOD_LABELS
from utils import today_str, mood_emoji, mood_label
import database as db
from services.wellness_service import get_today_summary, get_recent_activity


def _gauge(pct_val: float, title: str, color: str = "#2d9b68") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct_val,
        number={"suffix": "%", "font": {"size": 20}},
        title={"text": title, "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "bgcolor": "#f0f7f4",
            "borderwidth": 1,
            "bordercolor": "#d4edda",
            "steps": [
                {"range": [0, 50], "color": "#fde8e8"},
                {"range": [50, 80], "color": "#fff3cd"},
                {"range": [80, 100], "color": "#d4edda"},
            ],
        },
    ))
    fig.update_layout(height=160, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="white")
    return fig


def _login_prompt():
    st.markdown("""
<div class="hm-card" style="text-align:center;padding:40px;">
  <h2 style="color:#1a6b4a;">Welcome to 🩺 HealthMate AI</h2>
  <p style="font-size:1.05rem;color:#444;max-width:600px;margin:0 auto 16px;">
    An intelligent health and well-being platform aligned with
    <strong>United Nations Sustainable Development Goal 3</strong> —
    <em>Good Health and Well-Being</em>.
  </p>
  <p style="color:#666;">Track your daily wellness, explore health education, chat with the
  AI assistant, and gain insights through interactive analytics.</p>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="hm-card" style="text-align:center;">
            <div style="font-size:2rem;">💧</div>
            <div class="hm-card-title">Hydration Tracking</div>
            <p class="hm-muted">Log daily water intake and monitor progress toward your hydration goal.</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="hm-card" style="text-align:center;">
            <div style="font-size:2rem;">🧠</div>
            <div class="hm-card-title">Mental Wellness</div>
            <p class="hm-muted">Check in with your mood, write in your journal, and explore mindfulness exercises.</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="hm-card" style="text-align:center;">
            <div style="font-size:2rem;">🤖</div>
            <div class="hm-card-title">AI Wellness Assistant</div>
            <p class="hm-muted">Get evidence-informed wellness guidance on nutrition, sleep, exercise, and more.</p>
        </div>""", unsafe_allow_html=True)

    st.info("👈 Please **log in or register** using the **My Profile** section in the sidebar to get started.")

    st.markdown("""
---
### 🌍 About UN SDG 3 — Good Health and Well-Being

SDG 3 aims to *"ensure healthy lives and promote well-being for all at all ages."*
HealthMate AI supports this goal by empowering individuals with accessible wellness education,
self-monitoring tools, and preventive health awareness — entirely free and locally hosted.

**Key features:**
- Daily wellness tracking (water, activity, steps, sleep, mood)
- Interactive AI wellness assistant with evidence-based guidance
- Searchable health education library
- Personal goal setting and progress visualization
- Privacy-first: all data stored locally on your device
""")


def render():
    if not st.session_state.get("user_id"):
        _login_prompt()
        return

    user_id = st.session_state.user_id
    username = st.session_state.username
    today = today_str()

    st.markdown(f"# 🏠 Good day, **{username}**!")
    st.markdown(f"<p class='hm-muted'>Today is {today} · Your daily wellness overview</p>",
                unsafe_allow_html=True)

    # ── Today's summary ────────────────────────────────────────────────────────
    summary = get_today_summary(user_id)

    st.markdown("### 📊 Today's Progress")
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(_gauge(summary["water_pct"], "💧 Hydration"), use_container_width=True)
    with g2:
        st.plotly_chart(_gauge(summary["activity_pct"], "🏃 Activity", "#3b82d4"), use_container_width=True)
    with g3:
        st.plotly_chart(_gauge(summary["steps_pct"], "👟 Steps", "#f59e0b"), use_container_width=True)
    with g4:
        st.plotly_chart(_gauge(summary["sleep_pct"], "🌙 Sleep", "#7c5cd8"), use_container_width=True)

    # ── Metric quick-view ──────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💧 Water", f"{summary['water_ml']} ml",
              delta=f"Goal: {int(summary['goals'].get('water_ml', 2500))} ml")
    m2.metric("🏃 Activity", f"{summary['activity_minutes']} min",
              delta=f"Goal: {int(summary['goals'].get('activity_minutes', 30))} min")
    m3.metric("👟 Steps", f"{summary['steps']:,}",
              delta=f"Goal: {int(summary['goals'].get('steps', 8000)):,}")
    m4.metric("🌙 Sleep", f"{summary['sleep_hours']} hrs",
              delta=f"Goal: {summary['goals'].get('sleep_hours', 8.0)} hrs")
    if summary["mood_score"]:
        m5.metric("😊 Mood", f"{mood_emoji(summary['mood_score'])} {mood_label(summary['mood_score'])}",
                  delta=f"Score: {summary['mood_score']}/5")
    else:
        m5.metric("😊 Mood", "Not logged", delta="Log today's mood")

    # ── Wellness suggestions ───────────────────────────────────────────────────
    st.markdown("### 💡 Personalized Wellness Suggestions")
    suggestions = []
    if summary["water_pct"] < 50:
        suggestions.append("💧 You've logged less than half your daily water goal — grab a glass now!")
    if summary["activity_pct"] < 50:
        suggestions.append("🏃 Your activity goal is less than halfway met. Even a 10-minute walk helps.")
    if summary["steps_pct"] < 30:
        suggestions.append("👟 Take the stairs or walk during a break to boost your step count.")
    if summary["sleep_hours"] and summary["sleep_hours"] < 6:
        suggestions.append("🌙 You logged under 6 hours of sleep. Prioritize rest tonight.")
    if summary["mood_score"] and summary["mood_score"] <= 2:
        suggestions.append("🧠 Your mood is low today. Try a short breathing exercise in the Mood section.")
    if not summary["mood_score"]:
        suggestions.append("😊 Don't forget to log your mood today — it takes just 10 seconds!")
    if not suggestions:
        suggestions.append("🌟 Great work! You're making solid progress toward your wellness goals today.")

    for s in suggestions:
        st.success(s)

    # ── Quick actions ──────────────────────────────────────────────────────────
    st.markdown("### ⚡ Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("📋 Log Today's Wellness", use_container_width=True):
            st.session_state.page = "Tracker"
            st.rerun()
    with qa2:
        if st.button("😊 Check In Mood", use_container_width=True):
            st.session_state.page = "Mood"
            st.rerun()
    with qa3:
        if st.button("🤖 Ask the AI Assistant", use_container_width=True):
            st.session_state.page = "Assistant"
            st.rerun()
    with qa4:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "Analytics"
            st.rerun()

    # ── Recent activity ────────────────────────────────────────────────────────
    st.markdown("### 📅 Recent Wellness Activity")
    recent = get_recent_activity(user_id, 5)
    if recent:
        import pandas as pd
        df_display = pd.DataFrame(recent)
        cols_show = ["record_date", "water_ml", "activity_minutes", "steps", "sleep_hours", "mood_score"]
        df_display = df_display[[c for c in cols_show if c in df_display.columns]]
        df_display.columns = [c.replace("_", " ").title() for c in df_display.columns]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No wellness records yet. Use the Daily Wellness Tracker to log your first entry!")

    # ── SDG 3 reminder ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div class='hm-card'>"
        "<div class='hm-card-title'>🌍 UN SDG 3 — Good Health and Well-Being</div>"
        "<p class='hm-muted'>HealthMate AI supports SDG Target 3.4 by promoting mental health "
        "and physical well-being, and Target 3.8 by improving access to health education and "
        "preventive wellness information — available to everyone, free of charge.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
