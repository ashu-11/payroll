"""Feature-card dashboard."""

from __future__ import annotations

import streamlit as st

from payroll_app.config.settings import FEATURE_REGISTRY
from payroll_app.core.session import logout


def render_dashboard() -> None:
    head_l, head_r = st.columns([4, 1])
    with head_l:
        st.title("Dashboard")
        st.markdown("Choose a tool below.")
    with head_r:
        st.markdown("")
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()

    enabled = [f for f in FEATURE_REGISTRY if f.get("enabled")]
    disabled = [f for f in FEATURE_REGISTRY if not f.get("enabled")]

    if enabled:
        cols = st.columns(min(3, len(enabled)))
        for i, feat in enumerate(enabled):
            with cols[i % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"### {feat['title']}")
                    st.caption(feat["description"])
                    if st.button(
                        "Open",
                        key=f"card_open_{feat['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.feature = feat["id"]
                        st.rerun()

    if disabled:
        st.subheader("Coming soon")
        dcols = st.columns(min(3, len(disabled)))
        for i, feat in enumerate(disabled):
            with dcols[i % len(dcols)]:
                with st.container(border=True):
                    st.markdown(f"### {feat['title']}")
                    st.caption(feat["description"])
                    st.button(
                        "Coming soon",
                        key=f"card_disabled_{feat['id']}",
                        use_container_width=True,
                        disabled=True,
                    )
