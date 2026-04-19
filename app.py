"""
Payroll Automation — Streamlit entrypoint.

Run from project root: ``streamlit run app.py``

Dependencies: ``pip install streamlit pandas openpyxl numpy``
"""

from __future__ import annotations

import streamlit as st

from payroll_app.core.session import init_session_state
from payroll_app.features.auth.ui import render_login_page
from payroll_app.features.dashboard.ui import render_dashboard
from payroll_app.routing import render_active_feature


def main() -> None:
    st.set_page_config(
        page_title="Payroll Automation",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_session_state()

    if not st.session_state.authenticated:
        render_login_page()
        return

    if st.session_state.feature is None:
        render_dashboard()
    else:
        render_active_feature()


if __name__ == "__main__":
    main()
