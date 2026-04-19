"""Streamlit session helpers."""

from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "feature" not in st.session_state:
        st.session_state.feature = None


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.feature = None
