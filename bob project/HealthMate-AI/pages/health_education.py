"""
HealthMate AI — Health Education Library Page
"""
import json
from pathlib import Path

import streamlit as st

_ARTICLES_PATH = Path(__file__).parent.parent / "data" / "articles.json"


def _load_articles():
    with open(_ARTICLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def render():
    st.markdown("# 📚 Health Education Library")
    st.markdown(
        "<p class='hm-muted'>Evidence-based wellness articles covering nutrition, sleep, "
        "physical activity, mental well-being, hygiene, and more.</p>",
        unsafe_allow_html=True,
    )

    st.info(
        "**Disclaimer:** All articles provide general health education only. "
        "They do not constitute medical advice and are not a substitute for professional consultation. "
        "Links to reputable organisations such as the WHO and NHS are provided where relevant."
    )

    articles = _load_articles()
    all_categories = sorted(set(a["category"] for a in articles))

    # ── Filters ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    search_term = col1.text_input("🔍 Search articles", placeholder="e.g. sleep, stress, nutrition")
    selected_cat = col2.selectbox("📂 Category", ["All"] + all_categories)

    # Apply filters
    filtered = articles
    if selected_cat != "All":
        filtered = [a for a in filtered if a["category"] == selected_cat]
    if search_term.strip():
        q = search_term.strip().lower()
        filtered = [
            a for a in filtered
            if q in a["title"].lower()
            or q in a["summary"].lower()
            or any(q in tag for tag in a["tags"])
            or q in a["category"].lower()
        ]

    st.markdown(f"**{len(filtered)} article(s) found**")
    st.markdown("---")

    if not filtered:
        st.info("No articles matched your search. Try different keywords or clear the filter.")
        return

    # ── Article cards ─────────────────────────────────────────────────────────
    if "open_article" not in st.session_state:
        st.session_state.open_article = None

    for article in filtered:
        with st.container():
            col_text, col_btn = st.columns([5, 1])
            with col_text:
                tags_html = " ".join(
                    f"<span class='hm-tag'>{t.title()}</span>" for t in article["tags"][:3]
                )
                st.markdown(
                    f"<div class='hm-card'>"
                    f"<div class='hm-card-title'>📄 {article['title']}</div>"
                    f"<p class='hm-muted'>{article['summary']}</p>"
                    f"<p>{tags_html} "
                    f"<span class='hm-tag' style='background:#e8f4f8;color:#1d4ed8;'>{article['category']}</span>"
                    f"&nbsp;⏱️ {article.get('reading_time_min', 3)} min read</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_btn:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("Read →", key=f"open_{article['id']}"):
                    if st.session_state.open_article == article["id"]:
                        st.session_state.open_article = None
                    else:
                        st.session_state.open_article = article["id"]
                    st.rerun()

        # Article detail (inline expansion)
        if st.session_state.open_article == article["id"]:
            with st.expander(f"📄 {article['title']}", expanded=True):
                st.markdown(article["content"])
                if article.get("source"):
                    st.markdown(
                        f"<p class='hm-muted'>📎 <b>Source guidance:</b> {article['source']}</p>",
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    "<p class='hm-muted'>⚠️ This article provides general wellness education only. "
                    "It is not medical advice. Always consult a qualified healthcare professional "
                    "for personal health concerns.</p>",
                    unsafe_allow_html=True,
                )
                if st.button("Close", key=f"close_{article['id']}"):
                    st.session_state.open_article = None
                    st.rerun()

    st.markdown("---")
    st.markdown(
        "<div class='hm-card'><div class='hm-card-title'>🌐 Reputable Health Resources</div>"
        "<ul>"
        "<li><a href='https://www.who.int/health-topics' target='_blank'>WHO Health Topics</a></li>"
        "<li><a href='https://www.nhs.uk/live-well/' target='_blank'>NHS Live Well</a></li>"
        "<li><a href='https://www.cdc.gov/healthyweight/index.html' target='_blank'>CDC Healthy Living</a></li>"
        "<li><a href='https://www.mind.org.uk/' target='_blank'>Mind — Mental Health Charity</a></li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )
