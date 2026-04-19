"""Merge, clean, and analyze employee masters for transfers and flat export."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from payroll_app.features.transfer.constants import (
    BAND_EXCLUDE,
    COLUMN_HEADER_MAP,
    EXPECTED_EXCEL_HEADERS_TEXT,
    OPTIONAL_INTERNAL_COLUMNS,
    REQUIRED_INTERNAL_COLUMNS,
)


def _trim_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2a: Trim whitespace from column names."""
    out = df.copy()
    out.columns = out.columns.astype(str).str.strip()
    return out


_UNNAMED_COL = re.compile(r"^Unnamed:\s*\d+$", re.I)


def _fix_leading_unnamed_employee_id(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel often leaves cell **A1** blank (merged title above); pandas then names column A
    ``Unnamed: 0``. When the next header is **Full Name**, the first column is **Employee Id**.
    """
    out = df.copy()
    cols = [str(c).strip() for c in out.columns]
    if len(cols) < 2 or not _UNNAMED_COL.match(cols[0]):
        return out
    second_key = cols[1].strip().lower()
    if COLUMN_HEADER_MAP.get(second_key) == "Full Name":
        cols[0] = "Employee Id"
        out.columns = cols
    return out


def _fix_missing_company_header(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel often leaves the Company header blank (merged cells) so pandas uses
    ``Unnamed: N``. When that column sits between **Grade** and **Band**, treat it as Company.
    """
    out = df.copy()
    cols = [str(c).strip() for c in out.columns]
    changed = False
    for i in range(1, len(cols) - 1):
        c = cols[i]
        if not _UNNAMED_COL.match(c):
            continue
        if cols[i - 1].lower() == "grade" and cols[i + 1].lower() == "band":
            cols[i] = "Company"
            changed = True
            break
    if changed:
        out.columns = cols
    return out


def _add_optional_internal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Fill optional internal columns when the export omits them (e.g. Employment Status)."""
    out = df.copy()
    for name in OPTIONAL_INTERNAL_COLUMNS:
        if name not in out.columns:
            out[name] = pd.NA
    return out


def _map_excel_headers_to_internal(df: pd.DataFrame) -> pd.DataFrame:
    """Map workbook headers (any casing) to internal pipeline column names."""
    out = _trim_columns(df)
    new_cols: list[str] = []
    for col in out.columns:
        key = str(col).strip().lower()
        if key not in COLUMN_HEADER_MAP:
            hint = ""
            if _UNNAMED_COL.match(str(col).strip()):
                hint = (
                    " Excel left a header cell blank. Typical fixes: type **Employee Id** in **A1** "
                    "(first column); or type **Company** between **Grade** and **Band** if that header is missing."
                )
            raise ValueError(
                f'Unexpected column "{col}".{hint} Expected: {EXPECTED_EXCEL_HEADERS_TEXT}'
            )
        new_cols.append(COLUMN_HEADER_MAP[key])
    out.columns = new_cols
    dup_mask = out.columns.duplicated()
    if dup_mask.any():
        dupes = out.columns[dup_mask].unique().tolist()
        raise ValueError(
            "Duplicate columns after mapping (each logical column must appear once): "
            + ", ".join(str(x) for x in dupes)
        )
    return out


def _validate_required_columns(df: pd.DataFrame) -> None:
    """Raise ValueError if any required internal column is missing."""
    missing = [c for c in REQUIRED_INTERNAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing column(s) after mapping: "
            + ", ".join(missing)
            + ". Ensure the sheet includes all expected headers (see below).\n"
            + EXPECTED_EXCEL_HEADERS_TEXT
        )


def read_uploaded_excel(uploaded_file: Any, entity_label: str) -> pd.DataFrame:
    """Read one Excel file from Streamlit upload; map headers; Entity comes from Company."""
    try:
        raw = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Could not read Excel file '{entity_label}': {e}") from e
    df = _trim_columns(raw)
    df = _fix_leading_unnamed_employee_id(df)
    df = _fix_missing_company_header(df)
    df = _map_excel_headers_to_internal(df)
    df = _add_optional_internal_columns(df)
    _validate_required_columns(df)
    return df


def merge_files(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """Step 1: Concatenate two dataframes (already have Entity)."""
    merged = pd.concat([df_a, df_b], axis=0, ignore_index=True)
    return merged


def _strip_if_str(val: Any) -> Any:
    return val.strip() if isinstance(val, str) else val


def _coerce_id_scalar(val: Any) -> Any:
    """Normalize Excel numeric/string IDs (Employee Id, Aadhaar) to trimmed strings."""
    if pd.isna(val):
        return val
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    if isinstance(val, float):
        if np.isnan(val):
            return val
        rounded = round(val)
        if abs(val - rounded) < 1e-9:
            return str(int(rounded))
        return str(val)
    return str(val).strip()


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2: Data cleaning — datetime DOJ/DOL, normalize to calendar dates,
    consistent nullable handling for text fields used in IDs.
    """
    out = df.copy()

    for col in ["Date of Joining (DOJ)", "Date of Leaving (DOL)"]:
        out[col] = pd.to_datetime(out[col], errors="coerce")
        out[col] = out[col].dt.normalize()

    if "Employee Code" in out.columns:
        out["Employee Code"] = out["Employee Code"].map(_coerce_id_scalar)
    if "Aadhaar Number" in out.columns:
        out["Aadhaar Number"] = out["Aadhaar Number"].map(_coerce_id_scalar)

    str_cols = [
        "Full Name",
        "PAN Number",
        "Personal Email ID",
        "Band",
        "Grade",
        "Employment Status",
        "Entity",
    ]
    for c in str_cols:
        if c in out.columns:
            out[c] = out[c].map(_strip_if_str)

    if "Personal Email ID" in out.columns:
        pe = out["Personal Email ID"]

        def _lower_if_str(v: Any) -> Any:
            return v.lower() if isinstance(v, str) else v

        out["Personal Email ID"] = pe.map(_lower_if_str)

    if "PAN Number" in out.columns:

        def _upper_if_str(v: Any) -> Any:
            return v.upper() if isinstance(v, str) else v

        out["PAN Number"] = out["PAN Number"].map(_upper_if_str)

    for id_col in ("PAN Number", "Aadhaar Number", "Personal Email ID"):
        if id_col in out.columns:
            out[id_col] = out[id_col].replace("", np.nan)

    return out


def filter_bands(df: pd.DataFrame) -> pd.DataFrame:
    """Step 3: Remove excluded band values."""
    out = df.copy()
    mask = ~out["Band"].isin(BAND_EXCLUDE)
    return out.loc[mask].reset_index(drop=True)


def duplicate_identifier_sets(df: pd.DataFrame) -> tuple[set[Any], set[Any]]:
    """
    Identify PAN / Aadhaar values associated with more than one Employee Code.
    Null identifiers are ignored for duplicate detection.
    """
    dup_pan: set[Any] = set()
    dup_aadhaar: set[Any] = set()

    sub = df.dropna(subset=["PAN Number"])
    if len(sub) > 0:
        g = sub.groupby("PAN Number", dropna=False)["Employee Code"].nunique()
        dup_pan = set(g[g > 1].index.tolist())

    sub_a = df.dropna(subset=["Aadhaar Number"])
    if len(sub_a) > 0:
        g2 = sub_a.groupby("Aadhaar Number", dropna=False)["Employee Code"].nunique()
        dup_aadhaar = set(g2[g2 > 1].index.tolist())

    return dup_pan, dup_aadhaar


def assign_discrepancies(
    df: pd.DataFrame, dup_pan: set[Any], dup_aadhaar: set[Any]
) -> pd.DataFrame:
    """Step 4: Discrepancy_Flag and Discrepancy_Type."""
    out = df.copy()

    pan_series = out["PAN Number"]
    aadhaar_series = out["Aadhaar Number"]

    is_pan_dup = pan_series.notna() & pan_series.isin(dup_pan)
    is_aadhaar_dup = aadhaar_series.notna() & aadhaar_series.isin(dup_aadhaar)

    both = is_pan_dup & is_aadhaar_dup
    only_pan = is_pan_dup & ~is_aadhaar_dup
    only_aadhaar = ~is_pan_dup & is_aadhaar_dup

    out["Discrepancy_Flag"] = np.where(
        is_pan_dup | is_aadhaar_dup, "YES", "NO"
    )

    disc_type = np.full(len(out), "", dtype=object)
    disc_type[both] = "PAN & Aadhaar Duplicate"
    disc_type[only_pan] = "PAN Duplicate"
    disc_type[only_aadhaar] = "Aadhaar Duplicate"
    out["Discrepancy_Type"] = disc_type

    return out


def assign_unique_id(
    df: pd.DataFrame, dup_pan: set[Any], dup_aadhaar: set[Any]
) -> pd.DataFrame:
    """
    Step 5: Unique_ID — PAN (if usable), else Aadhaar (if usable),
    else Personal Email, else Employee Code.
    """
    out = df.copy()

    pan = out["PAN Number"]
    aadhaar = out["Aadhaar Number"]
    email = out["Personal Email ID"]
    emp_code = out["Employee Code"]

    pan_usable = pan.notna() & ~pan.isin(dup_pan)
    aadhaar_usable = aadhaar.notna() & ~aadhaar.isin(dup_aadhaar)
    email_usable = email.notna()

    uid = np.where(
        pan_usable,
        pan.astype(str),
        np.where(
            aadhaar_usable,
            aadhaar.astype(str),
            np.where(
                email_usable,
                email.astype(str),
                emp_code.astype(str),
            ),
        ),
    )
    out["Unique_ID"] = uid
    return out


def reconcile_unique_identity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge split ``Unique_ID`` values that refer to the same person.

    Initial assignment can emit different IDs for the same employee when, for
    example, PAN is duplicated across codes (fallback to different Aadhaars), or
    one row carries a typo PAN while **Personal Email** matches.

    Rule: rows sharing the same **Personal Email ID** use one canonical ID —
    the **most frequent non-null PAN** in that email group (fixes typos where
    one row has a wrong PAN); if no PAN in the group, the normalized email string.

    We **do not** merge only by PAN: the same PAN can incorrectly appear on two
    different people (duplicate data entry); email keeps them apart.
    """
    out = df.copy()
    if out.empty:
        return out

    def _canon_from_email_group(grp: pd.DataFrame) -> str:
        pans = grp["PAN Number"].dropna()
        pans = pans[pans.astype(str).str.strip() != ""]
        if not pans.empty:
            # Prefer idxmax frequency — multiple modes can occur with `.mode().iloc[0]` picking wrongly.
            vc = pans.astype(str).str.upper().str.strip().value_counts()
            if not vc.empty:
                return str(vc.index[0])
        e = grp["Personal Email ID"].dropna()
        if not e.empty:
            return str(e.iloc[0]).strip().lower()
        return str(grp["Unique_ID"].iloc[0])

    if "Personal Email ID" in out.columns:
        for _email, grp in out.groupby("Personal Email ID", sort=False, dropna=True):
            if grp["Unique_ID"].nunique() <= 1:
                continue
            out.loc[grp.index, "Unique_ID"] = _canon_from_email_group(grp)

    return out


def _gap_days_and_type(
    current_doj: pd.Timestamp | float | None,
    previous_dol: pd.Timestamp | float | None,
) -> tuple[float | np.floating, str]:
    """Compute day difference and bonus Gap_Type label."""
    if pd.isna(current_doj) or pd.isna(previous_dol):
        return np.nan, ""
    delta = (current_doj - previous_dol).days
    if delta < 0:
        gap_type = "Data Error"
    elif delta == 0:
        gap_type = "Same Day"
    elif delta == 1:
        gap_type = "Transfer"
    else:
        gap_type = "Break"
    return float(delta), gap_type


def add_transfer_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 6: Within each Unique_ID group (sorted DOJ ascending), mark Is_Transfer_Row
    on the current row when Entity changes and DOJ equals previous DOL + 1 day.
    """
    out = df.copy()
    out["Is_Transfer_Row"] = False

    sort_cols = ["Unique_ID", "Date of Joining (DOJ)"]
    out = out.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)

    is_transfer = np.zeros(len(out), dtype=bool)
    prev_entity = out["Entity"].shift(1)
    prev_dol = out["Date of Leaving (DOL)"].shift(1)
    curr_doj = out["Date of Joining (DOJ)"]
    curr_entity = out["Entity"]
    same_group = out["Unique_ID"].eq(out["Unique_ID"].shift(1))

    expected = prev_dol + pd.Timedelta(days=1)
    cond = (
        same_group
        & curr_entity.ne(prev_entity)
        & prev_dol.notna()
        & curr_doj.notna()
        & curr_doj.eq(expected)
    )
    is_transfer[cond.to_numpy()] = True
    out["Is_Transfer_Row"] = is_transfer

    return out


def enrich_gaps_and_flatten(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Steps 7–8: Per-row gap columns for sequential rows within Unique_ID,
    transfer counts, then flatten to one row per Unique_ID with Prev1..N and Gap1..N.
    """
    detailed_parts: list[pd.DataFrame] = []

    rows_flat: list[dict[str, Any]] = []

    grouped = df.groupby("Unique_ID", sort=False)

    for unique_id, g in grouped:
        g_sorted = g.sort_values(
            "Date of Joining (DOJ)", kind="mergesort"
        ).reset_index(drop=True)
        n = len(g_sorted)

        gap_days_list: list[float | np.floating] = []
        gap_type_list: list[str] = []
        for i in range(n):
            if i == 0:
                gap_days_list.append(np.nan)
                gap_type_list.append("")
            else:
                d, gt = _gap_days_and_type(
                    g_sorted.at[i, "Date of Joining (DOJ)"],
                    g_sorted.at[i - 1, "Date of Leaving (DOL)"],
                )
                gap_days_list.append(d)
                gap_type_list.append(gt)

        g_det = g_sorted.copy()
        g_det["Gap_Days"] = gap_days_list
        g_det["Gap_Type"] = gap_type_list
        detailed_parts.append(g_det)

        transfer_count = int(g_det["Is_Transfer_Row"].sum())

        latest = g_det.iloc[-1]
        row_out: dict[str, Any] = {
            "Unique_ID": unique_id,
            "Latest_Emp_Code": latest["Employee Code"],
            "Latest_Entity": latest["Entity"],
            "Latest_DOJ": latest["Date of Joining (DOJ)"],
            "Latest_DOL": latest["Date of Leaving (DOL)"],
            "Total_Transfer_Count": transfer_count,
            "Latest Band": latest["Band"],
            "Latest Grade": latest["Grade"],
            "Discrepancy_Flag": latest["Discrepancy_Flag"],
            "Discrepancy_Type": latest["Discrepancy_Type"],
        }

        num_prev = n - 1
        for k in range(1, num_prev + 1):
            prev_row = g_det.iloc[n - 1 - k]
            idx_label = k
            row_out[f"Prev{idx_label}_Emp_Code"] = prev_row["Employee Code"]
            row_out[f"Prev{idx_label}_Entity"] = prev_row["Entity"]
            row_out[f"Prev{idx_label}_DOJ"] = prev_row["Date of Joining (DOJ)"]
            row_out[f"Prev{idx_label}_DOL"] = prev_row["Date of Leaving (DOL)"]

            curr_doj = g_det.at[n - k, "Date of Joining (DOJ)"]
            prev_dol = prev_row["Date of Leaving (DOL)"]
            gd, gt = _gap_days_and_type(curr_doj, prev_dol)
            row_out[f"Gap{idx_label}_Days"] = gd
            row_out[f"Gap{idx_label}_Type"] = gt

        rows_flat.append(row_out)

    detailed = (
        pd.concat(detailed_parts, axis=0, ignore_index=True)
        if detailed_parts
        else pd.DataFrame()
    )

    flat_df = pd.DataFrame(rows_flat)
    return detailed, flat_df


def align_flat_columns(flat_df: pd.DataFrame) -> pd.DataFrame:
    """Order columns: base Latest fields, then Prev/Gap pairs sorted by index."""
    if flat_df.empty:
        return flat_df

    base = [
        "Unique_ID",
        "Latest_Emp_Code",
        "Latest_Entity",
        "Latest_DOJ",
        "Latest_DOL",
        "Total_Transfer_Count",
        "Latest Band",
        "Latest Grade",
        "Discrepancy_Flag",
        "Discrepancy_Type",
    ]

    prev_gap_cols: list[str] = []
    prev_nums = sorted(
        {
            int(m.group(1))
            for col in flat_df.columns
            for m in [re.match(r"^Prev(\d+)_Emp_Code$", col)]
            if m
        }
    )
    for num in prev_nums:
        prev_gap_cols.extend(
            [
                f"Prev{num}_Emp_Code",
                f"Prev{num}_Entity",
                f"Prev{num}_DOJ",
                f"Prev{num}_DOL",
                f"Gap{num}_Days",
                f"Gap{num}_Type",
            ]
        )

    ordered = [c for c in base + prev_gap_cols if c in flat_df.columns]
    extras = [c for c in flat_df.columns if c not in ordered]
    return flat_df[ordered + extras]


def process_files(df_a: pd.DataFrame, df_b: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full pipeline: merge → clean → filter → discrepancy → unique ID → transfers → flatten.

    Returns:
        detailed_df: row-level data with Gap_Days, Gap_Type, Is_Transfer_Row
        flat_df: one row per Unique_ID with Latest/Prev*/Gap* columns
    """
    merged = merge_files(df_a, df_b)
    cleaned = clean_data(merged)
    filtered = filter_bands(cleaned)

    if filtered.empty:
        return pd.DataFrame(), pd.DataFrame()

    dup_pan, dup_aadhaar = duplicate_identifier_sets(filtered)
    with_disc = assign_discrepancies(filtered, dup_pan, dup_aadhaar)
    with_uid = assign_unique_id(with_disc, dup_pan, dup_aadhaar)
    with_uid = reconcile_unique_identity(with_uid)
    with_xfer = add_transfer_flags(with_uid)

    detailed, flat_df = enrich_gaps_and_flatten(with_xfer)
    flat_df = align_flat_columns(flat_df)

    return detailed, flat_df
