"""
HealthMate AI — Mood & Mental Wellness Page
"""
import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import database as db
from config import EMOTION_TAGS, MOOD_LABELS, MOOD_EMOJIS
from utils import today_str, rows_to_df, mood_emoji, mood_label, past_n_days


BREATHING_EXERCISES = [
    {
        "name": "4-7-8 Breathing",
        "emoji": "🌬️",
        "description": "A relaxation technique that calms the nervous system.",
        "steps": [
            "Sit comfortably with your back straight.",
            "Exhale completely through your mouth.",
            "Close your mouth and inhale through your nose for **4 seconds**.",
            "Hold your breath for **7 seconds**.",
            "Exhale completely through your mouth for **8 seconds**.",
            "Repeat the cycle 3–4 times.",
        ],
    },
    {
        "name": "Box Breathing",
        "emoji": "📦",
        "description": "Used by athletes and first responders to reduce acute stress.",
        "steps": [
            "Inhale slowly through your nose for **4 counts**.",
            "Hold your breath for **4 counts**.",
            "Exhale slowly through your mouth for **4 counts**.",
            "Hold for **4 counts**.",
            "Repeat 4–6 times.",
        ],
    },
    {
        "name": "Diaphragmatic Breathing",
        "emoji": "🫁",
        "description": "Deep belly breathing to activate the relaxation response.",
        "steps": [
            "Place one hand on your chest, one on your belly.",
            "Breathe in slowly through your nose — your belly should rise, not your chest.",
            "Exhale slowly through pursed lips.",
            "Repeat for 5–10 minutes.",
        ],
    },
]

MINDFULNESS_ACTIVITIES = [
    {
        "name": "5-4-3-2-1 Grounding",
        "emoji": "🌿",
        "description": "A sensory grounding technique to anchor you in the present moment.",
        "steps": [
            "Name **5 things** you can see around you.",
            "Name **4 things** you can physically feel (e.g. your feet on the floor).",
            "Name **3 things** you can hear.",
            "Name **2 things** you can smell (or like the smell of).",
            "Name **1 thing** you can taste.",
        ],
    },
    {
        "name": "Body Scan",
        "emoji": "🧘",
        "description": "Progressive awareness of each part of the body, releasing tension.",
        "steps": [
            "Lie down or sit comfortably. Close your eyes.",
            "Bring attention to your feet — notice any sensations without judgment.",
            "Slowly move your awareness upward: legs → stomach → chest → arms → neck → head.",
            "At each area, breathe in and consciously release any tension as you exhale.",
            "Spend 10–20 minutes on the full scan.",
        ],
    },
    {
        "name": "Gratitude Practice",
        "emoji": "🙏",
        "description": "Shifting focus to positive aspects of your day to improve mood.",
        "steps": [
            "Take a quiet moment at the end of your day.",
            "Think of (or write down) **3 things** you are grateful for today.",
            "They can be small: a good meal, sunlight, a kind word.",
            "Reflect briefly on why each one matters to you.",
            "Repeat daily for best results — consistency builds the habit.",
        ],
    },
]


def _mood_checkin(user_id: int):
    st.markdown("### 😊 Daily Mood Check-In")

    checkin_date = st.date_input(
        "Date",
        value=datetime.date.today(),
        max_value=datetime.date.today(),
        min_value=datetime.date.today() - datetime.timedelta(days=365),
        key="mood_date",
    )
    date_str = checkin_date.isoformat()

    with st.form("mood_form"):
        mood = st.select_slider(
            "How are you feeling today?",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: f"{MOOD_EMOJIS[x]} {MOOD_LABELS[x]}",
            value=3,
        )

        selected_emotions = st.multiselect(
            "Optional: Select emotions that describe your day",
            options=sorted(EMOTION_TAGS),
        )

        journal = st.text_area(
            "📓 Private journal entry (optional — stored locally only)",
            placeholder="How was your day? What's on your mind?",
            height=150,
            max_chars=2000,
        )

        save = st.form_submit_button("💾 Save Mood Entry", use_container_width=True)

    if save:
        db.add_mood_entry(
            user_id,
            date_str,
            mood,
            emotions=", ".join(selected_emotions),
            journal=journal,
        )
        st.success(f"✅ Mood logged for {date_str}: {MOOD_EMOJIS[mood]} {MOOD_LABELS[mood]}")
        st.rerun()

    st.markdown(
        "<p class='hm-muted'>⚠️ Journal entries are stored only on your device. "
        "This is not a clinical tool — it does not diagnose or treat mental health conditions.</p>",
        unsafe_allow_html=True,
    )


def _mood_trends(user_id: int):
    st.markdown("### 📊 Mood Trends")
    n_days = st.select_slider("View last", options=[7, 14, 30, 90], value=30, key="mood_trend_days")
    start = past_n_days(n_days)
    end = today_str()

    rows = db.get_mood_entries(user_id, start, end)
    df = rows_to_df(rows)

    if df.empty:
        st.info("No mood entries yet. Log your first mood check-in above.")
        return

    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["label"] = df["mood_score"].map(lambda s: f"{MOOD_EMOJIS.get(s, '')} {MOOD_LABELS.get(s, '')}")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(df, x="entry_date", y="mood_score",
                      title="Mood Score Over Time", markers=True,
                      color_discrete_sequence=["#2d9b68"])
        fig.update_yaxes(range=[0.5, 5.5],
                         tickvals=[1, 2, 3, 4, 5],
                         ticktext=[f"{MOOD_EMOJIS[i]} {MOOD_LABELS[i]}" for i in range(1, 6)])
        fig.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        mood_counts = df["mood_score"].value_counts().sort_index()
        labels = [f"{MOOD_EMOJIS.get(i, '')} {MOOD_LABELS.get(i, i)}" for i in mood_counts.index]
        fig2 = px.pie(values=mood_counts.values, names=labels,
                      title="Mood Distribution",
                      color_discrete_sequence=px.colors.sequential.Greens_r)
        fig2.update_layout(height=320, margin=dict(t=40, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    # Summary stats
    avg = df["mood_score"].mean()
    st.metric("Average Mood", f"{mood_emoji(round(avg))} {avg:.1f}/5")

    # Emotion tags cloud
    all_emotions = ", ".join(df["emotions"].dropna().tolist())
    if all_emotions.strip():
        tags = [t.strip() for t in all_emotions.split(",") if t.strip()]
        from collections import Counter
        counts = Counter(tags).most_common(10)
        st.markdown("**Most frequent emotions:**")
        tags_html = " ".join(
            f"<span class='hm-tag'>{e} <b>{c}</b></span>" for e, c in counts
        )
        st.markdown(tags_html, unsafe_allow_html=True)

    # CSV export
    export_df = df[["entry_date", "mood_score", "emotions"]].copy()
    export_df["entry_date"] = export_df["entry_date"].dt.date
    csv = export_df.to_csv(index=False)
    st.download_button("📥 Download Mood Data (CSV)", csv,
                       file_name="healthmate_mood.csv", mime="text/csv")


def _exercises():
    st.markdown("### 🧘 Breathing & Mindfulness Exercises")
    tab_b, tab_m = st.tabs(["🌬️ Breathing Exercises", "🌿 Mindfulness Activities"])

    with tab_b:
        for ex in BREATHING_EXERCISES:
            with st.expander(f"{ex['emoji']} {ex['name']}"):
                st.markdown(f"*{ex['description']}*")
                for i, step in enumerate(ex["steps"], 1):
                    st.markdown(f"{i}. {step}")

    with tab_m:
        for act in MINDFULNESS_ACTIVITIES:
            with st.expander(f"{act['emoji']} {act['name']}"):
                st.markdown(f"*{act['description']}*")
                for i, step in enumerate(act["steps"], 1):
                    st.markdown(f"{i}. {step}")

    st.info(
        "**Note:** These exercises are general wellness techniques. "
        "If you are experiencing persistent mental health difficulties, "
        "please speak with a qualified mental health professional."
    )


def render():
    st.markdown("# 🧠 Mood & Mental Wellness")
    st.markdown(
        "<p class='hm-muted'>Track your daily mood, write in your private journal, "
        "and explore evidence-based relaxation techniques.</p>",
        unsafe_allow_html=True,
    )

    if not st.session_state.get("user_id"):
        st.info("Please log in from the **My Profile** page to use mood tracking.")
        _exercises()
        return

    user_id = st.session_state.user_id

    tab1, tab2, tab3 = st.tabs(["😊 Check-In", "📊 My Mood Trends", "🧘 Exercises & Techniques"])
    with tab1:
        _mood_checkin(user_id)
    with tab2:
        _mood_trends(user_id)
    with tab3:
        _exercises()

    st.markdown("---")
    st.markdown(
        "<div class='hm-card'><div class='hm-card-title'>💚 Mental Health Resources</div>"
        "<p class='hm-muted'>"
        "If you or someone you know is in crisis, please reach out immediately:<br>"
        "• <b>Emergency services:</b> 911 (US), 999 (UK), 112 (EU)<br>"
        "• <b>Crisis Text Line:</b> Text HOME to 741741 (US/UK/CA/IE)<br>"
        "• <b>Samaritans (UK/IE):</b> 116 123<br>"
        "• <b>WHO Mental Health:</b> https://www.who.int/health-topics/mental-health<br>"
        "</p></div>",
        unsafe_allow_html=True,
    )
