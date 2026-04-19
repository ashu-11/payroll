"""Dispatch authenticated users to the selected feature UI."""

from __future__ import annotations

import streamlit as st

from payroll_app.features.transfer.ui import render_transfer_analyzer


def render_active_feature() -> None:
    fid = st.session_state.feature
    if fid == "transfer":
        render_transfer_analyzer()
    else:
        st.error("Unknown feature. Return to the dashboard.")
        if st.button("Back to dashboard"):
            st.session_state.feature = None
            st.rerun()
