"""
HealthMate AI — Privacy & Settings Page
"""
import streamlit as st
from config import DB_PATH, AI_AVAILABLE, OPENAI_MODEL, APP_VERSION


def render():
    st.markdown("# ⚙️ Privacy & Settings")

    # ── Privacy notice ─────────────────────────────────────────────────────────
    st.markdown("## 🔒 Privacy Notice")
    st.markdown(f"""
<div class="hm-card">
<div class="hm-card-title">What information HealthMate AI stores</div>
<p>HealthMate AI is a <strong>locally hosted application</strong>. All data is stored in a SQLite
database file on your own device at:</p>
<code>{DB_PATH}</code>
<p>The following information may be stored:</p>
<ul>
  <li><strong>Account information:</strong> username, email address, and a securely hashed password
      (plain-text passwords are never stored).</li>
  <li><strong>Wellness records:</strong> daily water intake, activity, steps, sleep, and mood scores.</li>
  <li><strong>Mood journal entries:</strong> private text entries you write during mood check-ins.</li>
  <li><strong>Wellness goals:</strong> your personal goal settings.</li>
  <li><strong>Chat history:</strong> messages exchanged with the AI Wellness Assistant (optional).</li>
  <li><strong>Profile information:</strong> optional details such as age, height, weight, and activity level.</li>
</ul>
<p><strong>No data is transmitted to external servers</strong> unless you enable an AI provider
by configuring an API key in the <code>.env</code> file. In that case, only your chat messages
are sent to the configured AI API endpoint — wellness records, journal entries, and personal
profile data are never transmitted.</p>
<p>You can delete all your data or your entire account at any time from the <strong>My Profile</strong> page.
You can export your wellness and mood data as CSV from the <strong>Reports & Analytics</strong> page.</p>
</div>
""", unsafe_allow_html=True)

    # ── Configuration ──────────────────────────────────────────────────────────
    st.markdown("## 🛠️ Configuration")
    col1, col2 = st.columns(2)
    col1.metric("App Version", APP_VERSION)
    col2.metric("Database", str(DB_PATH.name))
    col1.metric("AI Mode", "API-powered" if AI_AVAILABLE else "Rule-based")
    if AI_AVAILABLE:
        col2.metric("AI Model", OPENAI_MODEL)

    st.markdown("### 🤖 AI Assistant Configuration")
    if AI_AVAILABLE:
        st.success(
            f"✅ AI provider is configured using the `OPENAI_API_KEY` environment variable. "
            f"Model: `{OPENAI_MODEL}`."
        )
    else:
        st.info(
            "The AI assistant is running in **rule-based mode**. "
            "To enable AI-powered responses:\n\n"
            "1. Copy `.env.example` to `.env` in the project directory.\n"
            "2. Set `OPENAI_API_KEY` to your API key.\n"
            "3. Optionally configure `OPENAI_BASE_URL` and `OPENAI_MODEL` "
            "(e.g. for a local LLM server).\n"
            "4. Restart the application.\n\n"
            "The API key is loaded from the environment variable — "
            "**never hardcode secrets in source files**."
        )

    # ── Limitations and scope ──────────────────────────────────────────────────
    st.markdown("## ⚠️ Application Scope and Limitations")
    st.warning(
        "**HealthMate AI is an educational wellness tool, not a medical application.**\n\n"
        "- It does **not** diagnose illnesses or medical conditions.\n"
        "- It does **not** prescribe or recommend medications.\n"
        "- It does **not** replace professional medical, nutritional, or psychological advice.\n"
        "- All wellness suggestions are general guidance, not personalised clinical recommendations.\n"
        "- For any health concern, please consult a qualified healthcare professional.\n"
        "- For emergencies, contact your local emergency services immediately."
    )

    st.markdown("## 📋 Technical Limitations")
    st.info(
        "- **Background notifications** are not available in the standard Streamlit local "
        "deployment. In-app reminders are shown on the Home Dashboard.\n"
        "- **Multi-device sync** is not supported — data is stored locally on one device.\n"
        "- **Production deployment** of this application would require additional security "
        "hardening, HTTPS, and a production-grade database.\n"
        "- **AI responses** may occasionally be inaccurate. Always verify health information "
        "with reputable sources."
    )
