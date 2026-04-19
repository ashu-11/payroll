"""
Wide "transfer report" layout matching business sample exports.

Newest employment first (left), then older stints (.1, .2, …). Each block:
Employee Id, Full Name, Date Of Joining, company, Date Of Exit, and
a Gap column **except** the chronologically oldest block (rightmost).

**Remarks** include the transfer count and, when applicable, a **data discrepancy** note:
the same PAN and/or Aadhaar number appears on more than one Employee Code in the
uploaded data (see ``Discrepancy_Flag`` / ``Discrepancy_Type`` in the pipeline).
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd


def _scalar_employee_id(val: Any) -> Any:
    if pd.isna(val):
        return val
    if isinstance(val, float) and not np.isnan(val) and val == int(val):
        return int(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    s = str(val).strip()
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        try:
            return int(float(s))
        except ValueError:
            return s
    return s


def _build_remarks(
    transfer_count: Any,
    employment_rows: pd.DataFrame,
) -> str:
    """
    Transfer line + optional data-quality line from identifier rules (PAN / Aadhaar
    shared across more than one employee code in the input).
    """
    try:
        tc = int(transfer_count)
    except (TypeError, ValueError):
        tc = -1
    if tc <= 0:
        transfer_part = "No Transfer"
    else:
        transfer_part = f"{tc} time transfer"

    disc_part = ""
    if not employment_rows.empty and "Discrepancy_Flag" in employment_rows.columns:
        flag = employment_rows["Discrepancy_Flag"].astype(str).str.strip().str.upper()
        if (flag == "YES").any() and "Discrepancy_Type" in employment_rows.columns:
            types = (
                employment_rows.loc[flag == "YES", "Discrepancy_Type"]
                .dropna()
                .astype(str)
                .str.strip()
            )
            types = types[types != ""].unique()
            if len(types):
                disc_part = "Data discrepancy: " + "; ".join(sorted(types))
            else:
                disc_part = "Data discrepancy: identifier conflict (PAN/Aadhaar)"

    if disc_part:
        return f"{transfer_part} | {disc_part}"
    return transfer_part


def build_transfer_report(detailed_df: pd.DataFrame, flat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build one row per ``Unique_ID`` in the sample wide format.

    Parameters
    ----------
    detailed_df
        Row-level data from the pipeline (includes ``Gap_Days``, ``Full Name``, ``Entity``, etc.).
    flat_df
        One row per employee with ``Total_Transfer_Count`` and ``Unique_ID``.
    """
    if flat_df.empty or detailed_df.empty:
        return pd.DataFrame()

    max_slots = int(detailed_df.groupby("Unique_ID", sort=False).size().max())

    rows: list[dict[str, Any]] = []

    for _, flat_row in flat_df.sort_values("Unique_ID").iterrows():
        uid = flat_row["Unique_ID"]
        g = detailed_df.loc[detailed_df["Unique_ID"] == uid].sort_values(
            "Date of Joining (DOJ)", kind="mergesort"
        )
        n = len(g)
        out: dict[str, Any] = {}

        for d in range(max_slots):
            suffix = "" if d == 0 else f".{d}"
            if d < n:
                i = n - 1 - d
                r = g.iloc[i]
                out[f"Employee Id{suffix}"] = _scalar_employee_id(r["Employee Code"])
                out[f"Full Name{suffix}"] = r["Full Name"]
                out[f"Date Of Joining{suffix}"] = _as_date(r["Date of Joining (DOJ)"])
                out[f"company{suffix}"] = r["Entity"]
                out[f"Date Of Exit{suffix}"] = _as_date(r["Date of Leaving (DOL)"])
            else:
                out[f"Employee Id{suffix}"] = np.nan
                out[f"Full Name{suffix}"] = np.nan
                out[f"Date Of Joining{suffix}"] = pd.NaT
                out[f"company{suffix}"] = np.nan
                out[f"Date Of Exit{suffix}"] = pd.NaT

            if d < max_slots - 1:
                gap_key = "Gap" if d == 0 else f"Gap.{d}"
                if d < n:
                    i = n - 1 - d
                    gv = g.iloc[i]["Gap_Days"]
                    out[gap_key] = float(gv) if pd.notna(gv) else np.nan
                else:
                    out[gap_key] = np.nan

        out["Remarks"] = _build_remarks(flat_row.get("Total_Transfer_Count", 0), g)
        rows.append(out)

    out_df = pd.DataFrame(rows)
    # Stable ordering: Latest Employee Id (numbers before text when possible).
    def _latest_key(series: pd.Series) -> pd.Series:
        def one(v: Any) -> tuple[int, Any]:
            if pd.isna(v):
                return (2, "")
            s = str(v).strip()
            try:
                return (0, int(float(s)))
            except ValueError:
                return (1, s)

        return series.map(one)

    return out_df.sort_values(by="Employee Id", key=_latest_key).reset_index(drop=True)


def _as_date(val: Any) -> Any:
    if pd.isna(val):
        return pd.NaT
    ts = pd.Timestamp(val)
    if pd.isna(ts):
        return pd.NaT
    return ts.normalize()


def report_to_excel_bytes(df: pd.DataFrame) -> BytesIO:
    """Serialize report to xlsx bytes (single sheet ``Transfer Report``)."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transfer Report")
    buffer.seek(0)
    return buffer
