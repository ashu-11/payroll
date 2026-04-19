"""Excel export helpers."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def dataframe_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    """Serialize a single-sheet Excel workbook to memory."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Flattened")
    buffer.seek(0)
    return buffer
