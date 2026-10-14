"""
HealthMate AI — Daily Wellness Tracker Page
"""
import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import database as db
from utils import today_str, validate_wellness_input, pct, rows_to_df
from services.wellness_service import get_today_summary, get_last_n_days_df


def _auth_guard():
    if not st.session_state.get("user_id"):
        st.info("Please log in from the **My Profile** page to use the wellness tracker.")
        return False
    return True


def _log_form(user_id: int):
    st.markdown("### 📋 Log Today's Wellness")
    goals = {g["goal_type"]: g["target_value"] for g in db.get_goals(user_id)}

    # Allow choosing a date (default = today)
    log_date = st.date_input(
        "Date",
        value=datetime.date.today(),
        max_value=datetime.date.today(),
        min_value=datetime.date.today() - datetime.timedelta(days=365),
    )
    date_str = log_date.isoformat()

    # Pre-fill with existing record if available
    existing = db.get_wellness_record(user_id, date_str)

    with st.form("wellness_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            water = st.number_input(
                f"💧 Water intake (ml) — Goal: {int(goals.get('water_ml', 2500))} ml",
                min_value=0, max_value=10000, step=50,
                value=int(existing["water_ml"]) if existing and existing["water_ml"] else 0,
            )
            activity = st.number_input(
                f"🏃 Physical activity (minutes) — Goal: {int(goals.get('activity_minutes', 30))} min",
                min_value=0, max_value=1440, step=5,
                value=int(existing["activity_minutes"]) if existing and existing["activity_minutes"] else 0,
            )
            steps = st.number_input(
                f"👟 Steps walked — Goal: {int(goals.get('steps', 8000)):,}",
                min_value=0, max_value=100000, step=100,
                value=int(existing["steps"]) if existing and existing["steps"] else 0,
            )
        with col2:
            sleep = st.number_input(
                f"🌙 Sleep duration (hours) — Goal: {goals.get('sleep_hours', 8.0)} hrs",
                min_value=0.0, max_value=24.0, step=0.25,
                value=float(existing["sleep_hours"]) if existing and existing["sleep_hours"] else 7.0,
            )
            mood = st.select_slider(
                "😊 Daily mood (1 = Very Low → 5 = Excellent)",
                options=[1, 2, 3, 4, 5],
                value=int(existing["mood_score"]) if existing and existing["mood_score"] else 3,
            )
            notes = st.text_area(
                "📝 Optional notes",
                value=existing["notes"] if existing and existing["notes"] else "",
                max_chars=500, height=100,
            )

        save = st.form_submit_button("💾 Save Record", use_container_width=True)

    if save:
        ok, errors = validate_wellness_input(water, activity, steps, sleep, mood)
        if not ok:
            for e in errors:
                st.error(e)
            return

        db.upsert_wellness_record(
            user_id, date_str,
            water_ml=water, activity_minutes=activity, steps=steps,
            sleep_hours=sleep, mood_score=mood, notes=notes,
        )
        st.success(f"✅ Wellness record saved for {date_str}!")
        st.rerun()


def _progress_bars(user_id: int):
    st.markdown("### 📈 Today's Progress")
    summary = get_today_summary(user_id)
    goals = summary["goals"]

    metrics = [
        ("💧 Water", summary["water_ml"], goals.get("water_ml", 2500), "ml"),
        ("🏃 Activity", summary["activity_minutes"], goals.get("activity_minutes", 30), "min"),
        ("👟 Steps", summary["steps"], goals.get("steps", 8000), "steps"),
        ("🌙 Sleep", summary["sleep_hours"], goals.get("sleep_hours", 8.0), "hrs"),
    ]
    for label, value, goal, unit in metrics:
        p = pct(value, goal)
        st.markdown(f"**{label}** — {value} / {goal:.0f} {unit} ({p:.0f}%)")
        st.progress(min(p / 100, 1.0))


def _weekly_charts(user_id: int):
    st.markdown("### 📊 Last 7 Days")
    df = get_last_n_days_df(user_id, 7)

    if df.empty:
        st.info("No records in the last 7 days. Start logging to see charts.")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df, x="record_date", y="water_ml",
                     title="Daily Water Intake (ml)",
                     color_discrete_sequence=["#2d9b68"])
        fig.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.line(df, x="record_date", y="sleep_hours",
                       title="Sleep Duration (hours)", markers=True,
                       color_discrete_sequence=["#7c5cd8"])
        fig2.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        fig3 = px.bar(df, x="record_date", y="activity_minutes",
                      title="Physical Activity (minutes)",
                      color_discrete_sequence=["#3b82d4"])
        fig3.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig3, use_container_width=True)

        if "mood_score" in df.columns and df["mood_score"].notna().any():
            fig4 = px.line(df, x="record_date", y="mood_score",
                           title="Mood Score Trend", markers=True,
                           color_discrete_sequence=["#f59e0b"])
            fig4.update_yaxes(range=[0.5, 5.5])
            fig4.update_layout(height=280, margin=dict(t=40, b=20))
            st.plotly_chart(fig4, use_container_width=True)


def _history_table(user_id: int):
    st.markdown("### 🗓️ Historical Records")
    col1, col2 = st.columns(2)
    start = col1.date_input("From", value=datetime.date.today() - datetime.timedelta(days=30),
                             key="hist_start")
    end = col2.date_input("To", value=datetime.date.today(), key="hist_end")

    if start > end:
        st.error("Start date must be before end date.")
        return

    rows = db.get_wellness_records(user_id, start.isoformat(), end.isoformat())
    df = rows_to_df(rows)

    if df.empty:
        st.info("No records found for the selected date range.")
        return

    display_cols = ["record_date", "water_ml", "activity_minutes", "steps",
                    "sleep_hours", "mood_score", "notes"]
    df_show = df[[c for c in display_cols if c in df.columns]]
    df_show.columns = [c.replace("_", " ").title() for c in df_show.columns]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # CSV export
    csv_data = df_show.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        data=csv_data,
        file_name=f"healthmate_wellness_{start}_{end}.csv",
        mime="text/csv",
    )


def render():
    st.markdown("# 📋 Daily Wellness Tracker")
    st.markdown(
        "<p class='hm-muted'>Log your daily water intake, physical activity, "
        "steps, sleep, and mood. Track your progress against personal goals.</p>",
        unsafe_allow_html=True,
    )

    if not _auth_guard():
        return

    user_id = st.session_state.user_id

    tab1, tab2, tab3 = st.tabs(["📝 Log Entry", "📈 Progress", "🗓️ History"])
    with tab1:
        _log_form(user_id)
    with tab2:
        _progress_bars(user_id)
        _weekly_charts(user_id)
    with tab3:
        _history_table(user_id)
