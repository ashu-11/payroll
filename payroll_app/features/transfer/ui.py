"""Streamlit UI for Employee Transfer Analyzer."""

from __future__ import annotations

import streamlit as st

from payroll_app.features.transfer.constants import EXPECTED_EXCEL_HEADERS_TEXT
from payroll_app.features.transfer.export import dataframe_to_excel_bytes
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
            st.markdown(
                "Each workbook must contain these columns:\n\n"
                + "\n".join(f"- `{h.strip()}`" for h in EXPECTED_EXCEL_HEADERS_TEXT.split(", "))
            )
            st.caption(
                "**Entity** for matching is taken from the **Company** column (not the file name)."
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

            st.success(
                f"Processing complete. **{len(flat_df)}** employee row(s) in flattened output."
            )

            st.subheader("Preview (first 20 rows)")
            st.dataframe(flat_df.head(20), use_container_width=True)

            excel_buf = dataframe_to_excel_bytes(flat_df)
            st.download_button(
                label="Download Excel output",
                data=excel_buf,
                file_name="employee_transfer_flattened.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            with st.expander("Row-level detail preview (optional)"):
                st.dataframe(detail_df.head(50), use_container_width=True)

        except ValueError as ve:
            st.error(str(ve))
        except Exception as e:
            st.error(f"Unexpected error: {e}")
