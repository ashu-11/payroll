"""Login screen (demo credentials)."""

from __future__ import annotations

import streamlit as st

from payroll_app.config.settings import DUMMY_PASSWORD, DUMMY_USERNAME


def render_login_page() -> None:
    st.markdown("## Payroll Automation")
    st.caption("Sign in to open the dashboard.")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        username = st.text_input("Username", key="login_username", autocomplete="username")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            autocomplete="current-password",
        )
        if st.button("Sign in", type="primary", use_container_width=True):
            if username == DUMMY_USERNAME and password == DUMMY_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with st.expander("Demo credentials"):
        st.markdown(
            f"Username: `{DUMMY_USERNAME}`  \nPassword: `{DUMMY_PASSWORD}`"
        )
