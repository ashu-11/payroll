"""Login screen (demo credentials)."""

from __future__ import annotations

import streamlit as st

from payroll_app.config.settings import DUMMY_PASSWORD, DUMMY_USERNAME


def _login_accepted(username: str, password: str) -> bool:
    """
    Compare demo credentials with forgiving normalization:
    strip accidental spaces/newlines from paste; username is case-insensitive.
    """
    u = username.strip().casefold()
    p = password.strip()
    ok_user = u == DUMMY_USERNAME.strip().casefold()
    ok_pass = p == DUMMY_PASSWORD
    return ok_user and ok_pass


def render_login_page() -> None:
    st.markdown("## Payroll Automation")
    st.caption("Sign in to open the dashboard.")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        # Form batches inputs on submit — avoids occasional empty/stale reads on button click.
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input(
                "Password",
                type="password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

        if submitted:
            if _login_accepted(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with st.expander("Demo credentials"):
        st.markdown(
            f"Username: `{DUMMY_USERNAME}`  \nPassword: `{DUMMY_PASSWORD}`"
        )
