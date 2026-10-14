"""
HealthMate AI — User Profile Page
"""
import streamlit as st

import auth
import database as db
from utils import bmi, bmi_category


def _require_logout():
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.page = "Home"
    st.rerun()


def _registration_form():
    st.markdown("#### 📝 Create an Account")
    with st.form("register_form"):
        username = st.text_input("Username (3–30 characters, letters/digits/_)")
        email = st.text_input("Email address")
        pw = st.text_input("Password (min 8 characters)", type="password")
        pw2 = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Register", use_container_width=True)

    if submitted:
        ok, msg = auth.register_user(username, email, pw, pw2)
        if ok:
            st.success(msg + " You can now log in.")
        else:
            st.error(msg)


def _login_form():
    st.markdown("#### 🔐 Log In")
    with st.form("login_form"):
        username = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        ok, msg, uid = auth.login_user(username, pw)
        if ok:
            st.session_state.user_id = uid
            st.session_state.username = username
            st.session_state.page = "Home"
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


def _profile_editor(user_id: int):
    profile = db.get_profile(user_id)
    user = db.get_user_by_id(user_id)

    st.markdown("#### ✏️ Edit Profile")
    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=profile["full_name"] or "")
        age = st.number_input("Age", min_value=1, max_value=120,
                              value=int(profile["age"]) if profile["age"] else 25)
        gender = st.selectbox("Gender", ["Prefer not to say", "Female", "Male", "Non-binary", "Other"],
                              index=["Prefer not to say", "Female", "Male", "Non-binary", "Other"].index(
                                  profile["gender"]) if profile["gender"] in
                                  ["Prefer not to say", "Female", "Male", "Non-binary", "Other"] else 0)
        col1, col2 = st.columns(2)
        height = col1.number_input("Height (cm)", min_value=50.0, max_value=250.0,
                                   value=float(profile["height_cm"]) if profile["height_cm"] else 170.0,
                                   step=0.5)
        weight = col2.number_input("Weight (kg)", min_value=10.0, max_value=300.0,
                                   value=float(profile["weight_kg"]) if profile["weight_kg"] else 70.0,
                                   step=0.5)
        activity_level = st.selectbox(
            "Activity level",
            ["sedentary", "light", "moderate", "active", "very active"],
            index=["sedentary", "light", "moderate", "active", "very active"].index(
                profile["activity_level"]) if profile["activity_level"] in
                ["sedentary", "light", "moderate", "active", "very active"] else 2,
        )
        health_notes = st.text_area("General health notes (optional, stored locally only)",
                                    value=profile["health_notes"] or "", max_chars=500)
        save = st.form_submit_button("Save Profile", use_container_width=True)

    if save:
        db.update_profile(
            user_id,
            full_name=full_name,
            age=age,
            gender=gender,
            height_cm=height,
            weight_kg=weight,
            activity_level=activity_level,
            health_notes=health_notes,
        )
        st.success("Profile updated successfully!")
        st.rerun()

    # BMI display
    b = bmi(weight, height)
    if b:
        cat = bmi_category(b)
        st.info(f"**Estimated BMI:** {b} — {cat}\n\n"
                "_BMI is a general screening tool only. It does not account for muscle mass, "
                "age, or individual variation. Consult your healthcare provider for a complete assessment._")


def render():
    st.markdown("# 👤 My Profile")

    if not st.session_state.get("user_id"):
        tab1, tab2 = st.tabs(["🔐 Log In", "📝 Register"])
        with tab1:
            _login_form()
        with tab2:
            _registration_form()

        st.markdown("---")
        st.info(
            "**Single-user local mode:** HealthMate AI stores all data in a local SQLite database "
            "on your device. Your data never leaves your computer unless you explicitly export it."
        )
        return

    user_id = st.session_state.user_id
    user = db.get_user_by_id(user_id)
    profile = db.get_profile(user_id)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 👋 {user['username']}")
        st.markdown(f"<p class='hm-muted'>Member since {user['created_at'][:10]}</p>",
                    unsafe_allow_html=True)
        if profile and profile["full_name"]:
            st.markdown(f"**Full name:** {profile['full_name']}")
        st.markdown(f"**Email:** {user['email']}")
    with col2:
        st.markdown("<div style='font-size:4rem;text-align:center;'>👤</div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    _profile_editor(user_id)

    # ── Danger zone ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚠️ Account Actions")
    with st.expander("Clear or delete my data"):
        st.warning(
            "**Clear wellness data** removes all your tracked records, mood entries, "
            "and chat history but keeps your account.\n\n"
            "**Delete account** permanently removes your account and all associated data."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Clear My Wellness Data", use_container_width=True):
                st.session_state["confirm_clear"] = True
            if st.session_state.get("confirm_clear"):
                st.error("Are you sure? This cannot be undone.")
                if st.button("✅ Yes, clear all my data", use_container_width=True):
                    db.delete_user_data(user_id)
                    st.session_state.pop("confirm_clear", None)
                    st.success("All wellness data cleared.")
                    st.rerun()
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.pop("confirm_clear", None)
                    st.rerun()
        with col_b:
            if st.button("❌ Delete My Account", use_container_width=True):
                st.session_state["confirm_delete"] = True
            if st.session_state.get("confirm_delete"):
                st.error("This will permanently delete your account and all data.")
                if st.button("✅ Yes, delete my account", use_container_width=True):
                    db.delete_user_account(user_id)
                    _require_logout()
                if st.button("❌ Cancel deletion", use_container_width=True):
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
