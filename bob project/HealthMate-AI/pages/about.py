"""
HealthMate AI — About the Project Page
"""
import streamlit as st


def render():
    st.markdown("# ℹ️ About HealthMate AI")

    st.markdown("""
<div class="hm-card" style="text-align:center;padding:32px;">
  <div style="font-size:3rem;">🩺</div>
  <h2 style="color:#1a6b4a;margin:8px 0;">HealthMate AI</h2>
  <p style="color:#555;font-size:1.05rem;">An Intelligent Health and Well-Being Platform</p>
  <p><span class="hm-tag">Version 1.0.0</span>
     <span class="hm-tag">Python + Streamlit</span>
     <span class="hm-tag">UN SDG 3 Aligned</span></p>
</div>
""", unsafe_allow_html=True)

    st.markdown("## 🌍 UN Sustainable Development Goal 3")
    st.markdown("""
**SDG 3: Good Health and Well-Being** aims to *"ensure healthy lives and promote well-being
for all at all ages."*

HealthMate AI directly supports several SDG 3 targets:

| Target | Description | How HealthMate AI Helps |
|--------|-------------|------------------------|
| **3.4** | Reduce premature mortality from non-communicable diseases and promote mental health | Daily wellness tracking, mental mood check-ins, stress management tools |
| **3.8** | Achieve universal health coverage and access to essential health services | Free, locally hosted health education accessible to anyone |
| **3.d** | Strengthen capacity for health risk reduction | Preventive health education, wellness goal-setting, AI assistant |

> *"The greatest wealth is health."* — Virgil
""")

    st.markdown("## 🎯 Project Objectives")
    st.markdown("""
1. Provide an accessible, user-friendly platform for daily wellness self-monitoring.
2. Deliver evidence-based health education aligned with WHO and NHS guidelines.
3. Offer an AI-powered assistant that answers wellness questions safely and responsibly.
4. Enable users to visualise trends in their own wellness data.
5. Promote preventive health awareness and healthy lifestyle habits.
6. Demonstrate responsible AI use in health contexts — with appropriate safety guardrails.
7. Support SDG 3 through a free, open, privacy-first local application.
""")

    st.markdown("## 🛠️ Technology Stack")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Core Framework**
- Python 3.9+
- Streamlit (UI framework)

**Data & Analytics**
- Pandas (data processing)
- NumPy (numerical operations)
- Plotly (interactive charts)
- Scikit-learn (trend analysis ML)

**Database**
- SQLite (local, file-based)
""")
    with col2:
        st.markdown("""
**AI / Assistant**
- Rule-based knowledge base (default)
- OpenAI-compatible API (optional)

**Security**
- bcrypt (password hashing)
- python-dotenv (secrets management)
- Parameterised SQL queries

**Testing**
- Pytest + pytest-cov
""")

    st.markdown("## 🏗️ System Architecture")
    st.markdown("""
```
HealthMate-AI/
├── app.py                    # Streamlit entry point, navigation
├── config.py                 # Environment configuration
├── database.py               # SQLite layer (all parameterised queries)
├── auth.py                   # Registration, login, password hashing
├── utils.py                  # Shared utilities and validation
├── pages/                    # One module per navigation page
│   ├── dashboard.py
│   ├── profile.py
│   ├── wellness_tracker.py
│   ├── mental_wellness.py
│   ├── ai_assistant.py
│   ├── health_education.py
│   ├── goals.py
│   ├── analytics.py
│   ├── settings.py
│   └── about.py
├── services/                 # Business logic layer
│   ├── wellness_service.py   # Goal progress, summaries
│   ├── assistant_service.py  # Rule-based + LLM assistant
│   └── analytics_service.py # Stats, ML trend analysis
├── data/
│   └── articles.json         # Health education articles
├── tests/                    # Pytest test suite
└── docs/                     # Project documentation
```
""")

    st.markdown("## ⚠️ Important Disclaimers")
    st.warning("""
**HealthMate AI is an educational wellness tool — not a medical application.**

- It does **not** diagnose medical conditions.
- It does **not** prescribe or recommend medications or treatments.
- It does **not** replace professional medical, nutritional, or psychological advice.
- All wellness content is general education aligned with publicly available guidelines (WHO, NHS, CDC).
- For any personal health concern, consult a qualified healthcare professional.
- For emergencies, contact your local emergency services immediately.

The application was built for educational and demonstration purposes as a university-level project.
It should not be deployed as a production health service without additional clinical oversight,
regulatory compliance review, and security hardening.
""")

    st.markdown("## 📚 References")
    st.markdown("""
The wellness content in HealthMate AI is aligned with the following reputable public health sources.
No fabricated citations or invented studies are used.

- **World Health Organization (WHO):** https://www.who.int/health-topics
- **NHS Live Well:** https://www.nhs.uk/live-well/
- **CDC Healthy Living:** https://www.cdc.gov/
- **Mind (Mental Health):** https://www.mind.org.uk/
- **American Psychological Association:** https://www.apa.org/topics/stress
- **American Academy of Sleep Medicine:** https://aasm.org/
- **WHO Physical Activity Guidelines (2020):** https://www.who.int/publications/i/item/9789240015128
- **WHO Healthy Diet Fact Sheet:** https://www.who.int/news-room/fact-sheets/detail/healthy-diet
""")

    st.markdown("---")
    st.markdown(
        "<p class='hm-muted' style='text-align:center;'>"
        "Built with 🩺 HealthMate AI · Python + Streamlit · Supporting UN SDG 3</p>",
        unsafe_allow_html=True,
    )
