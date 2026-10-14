"""
HealthMate AI — Reports & Analytics Page
"""
import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import database as db
from utils import today_str, past_n_days, rows_to_df, wellness_records_to_csv, mood_entries_to_csv
from services.analytics_service import (
    descriptive_stats, weekly_averages, predict_activity_trend, compute_trend,
)
from services.wellness_service import get_last_n_days_df


def _auth_guard():
    if not st.session_state.get("user_id"):
        st.info("Please log in from the **My Profile** page to view analytics.")
        return False
    return True


def _overview_charts(user_id: int, df: pd.DataFrame):
    st.markdown("### 📊 Wellness Overview")

    if df.empty:
        st.info("No records in the selected period. Start logging to see charts.")
        return

    col1, col2 = st.columns(2)
    with col1:
        # Water intake
        fig = px.bar(df, x="record_date", y="water_ml",
                     title="Daily Water Intake (ml)",
                     color_discrete_sequence=["#2d9b68"])
        fig.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # Sleep
        fig3 = px.line(df, x="record_date", y="sleep_hours",
                       title="Sleep Duration (hours)", markers=True,
                       color_discrete_sequence=["#7c5cd8"])
        fig3.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # Activity
        fig2 = px.bar(df, x="record_date", y="activity_minutes",
                      title="Physical Activity (minutes)",
                      color_discrete_sequence=["#3b82d4"])
        fig2.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig2, use_container_width=True)

        # Steps
        fig4 = px.line(df, x="record_date", y="steps",
                       title="Daily Steps", markers=True,
                       color_discrete_sequence=["#f59e0b"])
        fig4.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig4, use_container_width=True)

    # Mood
    mood_df = df.dropna(subset=["mood_score"]) if "mood_score" in df.columns else pd.DataFrame()
    if not mood_df.empty:
        fig5 = px.line(mood_df, x="record_date", y="mood_score",
                       title="Mood Score History", markers=True,
                       color_discrete_sequence=["#ef4444"])
        fig5.update_yaxes(range=[0.5, 5.5])
        fig5.update_layout(height=280, margin=dict(t=40, b=20))
        st.plotly_chart(fig5, use_container_width=True)


def _descriptive_stats(df: pd.DataFrame):
    st.markdown("### 📋 Summary Statistics")
    stats = descriptive_stats(df)
    if not stats:
        st.info("Insufficient data for statistics.")
        return

    label_map = {
        "water_ml": "💧 Water (ml)",
        "activity_minutes": "🏃 Activity (min)",
        "steps": "👟 Steps",
        "sleep_hours": "🌙 Sleep (hrs)",
        "mood_score": "😊 Mood",
    }

    rows_list = []
    for col, s in stats.items():
        rows_list.append({
            "Metric": label_map.get(col, col),
            "Average": s["mean"],
            "Std Dev": s["std"],
            "Min": s["min"],
            "Max": s["max"],
            "Days Logged": s["count"],
        })

    st.dataframe(pd.DataFrame(rows_list), use_container_width=True, hide_index=True)


def _weekly_summary(df: pd.DataFrame):
    st.markdown("### 📅 Weekly Averages")
    w_df = weekly_averages(df)
    if w_df.empty:
        st.info("Not enough data for weekly averages.")
        return

    fig = px.line(w_df, x="year_week",
                  y=[c for c in ["water_ml", "activity_minutes", "sleep_hours"] if c in w_df.columns],
                  title="Weekly Average Trends",
                  markers=True)
    fig.update_layout(height=320, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _ml_module(df: pd.DataFrame):
    st.markdown("### 🤖 Activity Trend Analysis (Educational ML Module)")
    result = predict_activity_trend(df)

    if result is None:
        st.info("No activity data available for trend analysis.")
        return

    if not result.get("available"):
        st.warning(f"⚠️ {result.get('reason', 'Insufficient data.')}")
        return

    st.success(
        f"**Trend analysis based on {result['n_data_points']} days of your own activity data.**\n\n"
        f"- Historical average: {result['historical_mean']} min/day\n"
        f"- Predicted next-7-day average: **{result['predicted_avg']} min/day**\n"
        f"- Trend slope: {result['slope']} min/day (positive = improving)\n"
        + (f"- Model MAE: {result['mae']} min vs baseline MAE: {result['baseline_mae']} min"
           if result.get("mae") is not None else "")
    )

    pred_days = [f"Day +{i+1}" for i in range(len(result["predictions_7d"]))]
    fig = px.bar(x=pred_days, y=result["predictions_7d"],
                 title="Predicted Activity for Next 7 Days (minutes)",
                 color_discrete_sequence=["#3b82d4"],
                 labels={"x": "Day", "y": "Predicted Minutes"})
    fig.add_hline(y=result["historical_mean"], line_dash="dash", line_color="#1a6b4a",
                  annotation_text=f"Historical avg: {result['historical_mean']} min")
    fig.update_layout(height=280, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.caption(result.get("disclaimer", ""))


def _export_section(user_id: int):
    st.markdown("### 📥 Export Your Data")

    rows = db.get_all_wellness_records(user_id)
    mood_rows = db.get_all_mood_entries(user_id)

    col1, col2 = st.columns(2)
    with col1:
        csv_wellness = wellness_records_to_csv(rows)
        if csv_wellness:
            st.download_button(
                "📥 Download Wellness Records (CSV)",
                data=csv_wellness,
                file_name=f"healthmate_wellness_{today_str()}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("No wellness records to export yet.")
    with col2:
        csv_mood = mood_entries_to_csv(mood_rows)
        if csv_mood:
            st.download_button(
                "📥 Download Mood Data (CSV)",
                data=csv_mood,
                file_name=f"healthmate_mood_{today_str()}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("No mood entries to export yet.")


def render():
    st.markdown("# 📊 Reports & Analytics")
    st.markdown(
        "<p class='hm-muted'>Interactive charts, statistical summaries, trend analysis, "
        "and data export for your wellness records.</p>",
        unsafe_allow_html=True,
    )
    st.caption(
        "⚠️ Wellness trends shown here are patterns in your own data. "
        "They do not constitute medical analysis or prove causation."
    )

    if not _auth_guard():
        return

    user_id = st.session_state.user_id

    # ── Date range selector ────────────────────────────────────────────────────
    st.markdown("### 📅 Select Date Range")
    col1, col2 = st.columns(2)
    start_date = col1.date_input(
        "From",
        value=datetime.date.today() - datetime.timedelta(days=29),
        key="analytics_start",
    )
    end_date = col2.date_input(
        "To",
        value=datetime.date.today(),
        key="analytics_end",
    )

    if start_date > end_date:
        st.error("Start date must be before end date.")
        return

    rows = db.get_wellness_records(user_id, start_date.isoformat(), end_date.isoformat())
    df = rows_to_df(rows)
    if not df.empty:
        df["record_date"] = pd.to_datetime(df["record_date"])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Charts", "📋 Statistics", "📅 Weekly", "🤖 Trend Analysis", "📥 Export"
    ])
    with tab1:
        _overview_charts(user_id, df)
    with tab2:
        _descriptive_stats(df)
    with tab3:
        _weekly_summary(df)
    with tab4:
        _ml_module(df)
    with tab5:
        _export_section(user_id)
