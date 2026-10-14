"""
HealthMate AI — Goals & Reminders Page
"""
import streamlit as st
import plotly.express as px
import pandas as pd

import database as db
from utils import validate_goal_value, today_str, past_n_days, rows_to_df
from services.wellness_service import get_goal_completion_stats

GOAL_CONFIG = {
    "water_ml":         {"label": "💧 Daily Water Intake",       "unit": "ml",      "default": 2500},
    "activity_minutes": {"label": "🏃 Daily Physical Activity",   "unit": "minutes", "default": 30},
    "steps":            {"label": "👟 Daily Steps",               "unit": "steps",   "default": 8000},
    "sleep_hours":      {"label": "🌙 Sleep Duration",            "unit": "hours",   "default": 8.0},
}


def _auth_guard():
    if not st.session_state.get("user_id"):
        st.info("Please log in from the **My Profile** page to manage your goals.")
        return False
    return True


def _goal_editor(user_id: int):
    st.markdown("### 🎯 Set Personal Goals")
    st.markdown(
        "<p class='hm-muted'>Goals are personal — set values that are realistic and "
        "meaningful for you, not based on generic standards.</p>",
        unsafe_allow_html=True,
    )

    current_goals = {g["goal_type"]: g["target_value"] for g in db.get_goals(user_id)}

    with st.form("goals_form"):
        updated = {}
        for goal_type, cfg in GOAL_CONFIG.items():
            current = current_goals.get(goal_type, cfg["default"])
            val = st.number_input(
                f"{cfg['label']} ({cfg['unit']})",
                min_value=0.0,
                value=float(current),
                step=0.5 if "hours" in cfg["unit"] else 1.0,
                key=f"goal_{goal_type}",
            )
            updated[goal_type] = val

        save = st.form_submit_button("💾 Save Goals", use_container_width=True)

    if save:
        errors = []
        for goal_type, val in updated.items():
            ok, msg = validate_goal_value(goal_type, val)
            if not ok:
                errors.append(f"{GOAL_CONFIG[goal_type]['label']}: {msg}")
        if errors:
            for e in errors:
                st.error(e)
        else:
            for goal_type, val in updated.items():
                db.upsert_goal(user_id, goal_type, val)
            st.success("✅ Goals updated successfully!")
            st.rerun()


def _goal_progress(user_id: int):
    st.markdown("### 📊 Goal Achievement — Last 7 Days")
    stats = get_goal_completion_stats(user_id, 7)

    if not stats:
        st.info("No wellness data available. Start logging to see your goal completion rate.")
        return

    goal_labels = [GOAL_CONFIG[k]["label"] for k in stats]
    goal_pcts = list(stats.values())

    fig = px.bar(
        x=goal_labels,
        y=goal_pcts,
        labels={"x": "Goal", "y": "Days Met (%)"},
        title="% of Days Goal Met (Last 7 Days)",
        color=goal_pcts,
        color_continuous_scale=["#fde8e8", "#fff3cd", "#2d9b68"],
        text=[f"{v:.0f}%" for v in goal_pcts],
    )
    fig.update_layout(height=320, margin=dict(t=40, b=20), coloraxis_showscale=False)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    for goal_type, pct_val in stats.items():
        cfg = GOAL_CONFIG[goal_type]
        color = "🟢" if pct_val >= 80 else "🟡" if pct_val >= 50 else "🔴"
        st.markdown(f"{color} **{cfg['label']}:** {pct_val:.0f}% of days in the last 7 days")


def _reminders_section():
    st.markdown("### 🔔 Reminder Preferences")
    st.info(
        "**In-app reminders:** HealthMate AI displays personalized wellness suggestions on the "
        "Home Dashboard each time you open the app.\n\n"
        "**External notifications** (e.g. phone or email reminders) require additional "
        "infrastructure such as a scheduler service and are not available in the local "
        "Streamlit environment. This is a documented limitation."
    )

    st.markdown("""
**Tips to build reminders into your routine:**
- Set a recurring calendar event for your daily wellness log.
- Place a full water bottle on your desk as a visual cue.
- Use your phone's built-in health app reminders alongside HealthMate AI.
- Set a bedtime alarm to remind you to start your wind-down routine.
""")


def _historical_performance(user_id: int):
    st.markdown("### 📅 Historical Performance")
    n_days = st.select_slider("View last", options=[7, 14, 30, 60, 90], value=30, key="perf_days")
    start = past_n_days(n_days)
    end = today_str()

    rows = db.get_wellness_records(user_id, start, end)
    df = rows_to_df(rows)
    goals_raw = {g["goal_type"]: g["target_value"] for g in db.get_goals(user_id)}

    if df.empty:
        st.info("No data for the selected period. Start logging to see performance trends.")
        return

    col_map = {
        "water_ml": "💧 Water (ml)",
        "activity_minutes": "🏃 Activity (min)",
        "steps": "👟 Steps",
        "sleep_hours": "🌙 Sleep (hrs)",
    }

    for col, label in col_map.items():
        if col not in df.columns:
            continue
        target = goals_raw.get(col)
        if not target:
            continue

        d = df[["record_date", col]].dropna().copy()
        if d.empty:
            continue

        d["record_date"] = pd.to_datetime(d["record_date"])
        d["met"] = d[col] >= target

        fig = px.bar(
            d, x="record_date", y=col,
            title=f"{label} vs Goal ({target})",
            color="met",
            color_discrete_map={True: "#2d9b68", False: "#f87171"},
        )
        fig.add_hline(y=target, line_dash="dash", line_color="#1a6b4a",
                      annotation_text=f"Goal: {target}")
        fig.update_layout(height=260, margin=dict(t=40, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def render():
    st.markdown("# 🎯 My Goals & Reminders")
    st.markdown(
        "<p class='hm-muted'>Set personal wellness goals, track how often you meet them, "
        "and review your historical performance.</p>",
        unsafe_allow_html=True,
    )

    if not _auth_guard():
        return

    user_id = st.session_state.user_id

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Set Goals", "📊 Goal Progress", "📅 Historical", "🔔 Reminders"
    ])
    with tab1:
        _goal_editor(user_id)
    with tab2:
        _goal_progress(user_id)
    with tab3:
        _historical_performance(user_id)
    with tab4:
        _reminders_section()
