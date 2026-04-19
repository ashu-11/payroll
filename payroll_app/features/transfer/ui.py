"""Streamlit UI for Employee Transfer Analyzer."""

from __future__ import annotations

import streamlit as st

from payroll_app.features.transfer.constants import (
    CANONICAL_EXCEL_HEADERS_DISPLAY,
    OPTIONAL_EXCEL_HEADERS_DISPLAY,
)
from payroll_app.features.transfer.report_output import build_transfer_report, report_to_excel_bytes
from payroll_app.features.transfer.pipeline import process_files, read_uploaded_excel


def render_transfer_analyzer() -> None:
    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.title("Employee Transfer Analyzer")
        st.markdown(
            "Upload two `.xlsx` employee master exports. Each file must use the standard "
            "headers (first row); header text is matched case-insensitively."
        )
        with st.expander("Required Excel columns"):
            st.markdown("**Required** (header row, case-insensitive):")
            for h in CANONICAL_EXCEL_HEADERS_DISPLAY:
                st.markdown(f"- `{h}`")
            st.markdown("**Optional:**")
            for h in OPTIONAL_EXCEL_HEADERS_DISPLAY:
                st.markdown(f"- `{h}`")
            st.caption(
                "Legal entity for transfer matching comes from **Company**. "
                "If **A1** (Employee Id) or the Company header cell is empty, either type the header "
                "or keep the same column order as your HR extract — missing titles are detected when possible."
            )
    with top_r:
        st.markdown("")
        if st.button("← Back to dashboard", use_container_width=True):
            st.session_state.feature = None
            st.rerun()

    f1 = st.file_uploader(
        "Employee master file 1 (.xlsx)",
        type=["xlsx"],
        key="file1",
    )
    f2 = st.file_uploader(
        "Employee master file 2 (.xlsx)",
        type=["xlsx"],
        key="file2",
    )

    process = st.button("Process Data", type="primary")

    if process:
        if f1 is None or f2 is None:
            st.error("Please upload both Excel files before processing.")
            return

        try:
            with st.spinner("Processing…"):
                df_a = read_uploaded_excel(f1, "File1")
                df_b = read_uploaded_excel(f2, "File2")
                detail_df, flat_df = process_files(df_a, df_b)

            if flat_df.empty:
                st.warning(
                    "No rows remain after filtering (Band = B0 or Third Party excluded), "
                    "or input files produced no records."
                )
                return

            report_df = build_transfer_report(detail_df, flat_df)

            st.success(
                f"Processing complete. **{len(report_df)}** employee row(s) in transfer report."
            )

            st.subheader("Preview (transfer report)")
            st.dataframe(report_df.head(20), use_container_width=True)

            excel_buf = report_to_excel_bytes(report_df)
            st.download_button(
                label="Download Excel report",
                data=excel_buf,
                file_name="employee_transfer_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            with st.expander("Technical detail (pipeline flat row, optional)"):
                st.dataframe(flat_df.head(20), use_container_width=True)

            with st.expander("Row-level employment history (optional)"):
                st.dataframe(detail_df.head(50), use_container_width=True)

        except ValueError as ve:
            st.error(str(ve))
        except Exception as e:
            st.error(f"Unexpected error: {e}")
