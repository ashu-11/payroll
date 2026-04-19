"""Column and business rules for the Employee Transfer Analyzer."""

from __future__ import annotations

# Incoming Excel headers are matched case-insensitively after strip().
# Expected production headers → internal pipeline column names:
#   Employee Id → Employee Code
#   Full Name → Full Name
#   Date Of Joining → Date of Joining (DOJ)
#   Date Of Exit → Date of Leaving (DOL)
#   Personal Email Id → Personal Email ID
#   Pan Number → PAN Number
#   company / Company → Entity
# Employment Status is optional (many exports omit it).
COLUMN_HEADER_MAP: dict[str, str] = {
    "employee id": "Employee Code",
    "full name": "Full Name",
    "date of joining": "Date of Joining (DOJ)",
    "grade": "Grade",
    "band": "Band",
    "personal email id": "Personal Email ID",
    "pan number": "PAN Number",
    "aadhaar number": "Aadhaar Number",
    "employment status": "Employment Status",
    "date of exit": "Date of Leaving (DOL)",
    "company": "Entity",
}

# Present in COLUMN_HEADER_MAP but not required on the sheet (added as empty if missing).
OPTIONAL_INTERNAL_COLUMNS = frozenset({"Employment Status"})

REQUIRED_INTERNAL_COLUMNS = [
    v for v in dict.fromkeys(COLUMN_HEADER_MAP.values()) if v not in OPTIONAL_INTERNAL_COLUMNS
]

BAND_EXCLUDE = {"B0", "Third Party"}

# Shown in validation errors (single line).
EXPECTED_EXCEL_HEADERS_TEXT = (
    "Employee Id; Full Name; Date Of Joining; Grade; Company; Band; "
    "Personal Email Id; Pan Number; Aadhaar Number; Date Of Exit "
    "(optional: Employment Status). "
    "Blank Company header between Grade and Band is supported."
)

# Dashboard copy — order matches typical HR extracts (see sample `extracted1.xlsx` / `extracted2.xlsx`).
CANONICAL_EXCEL_HEADERS_DISPLAY: tuple[str, ...] = (
    "Employee Id",
    "Full Name",
    "Date Of Joining",
    "Grade",
    "Company",
    "Band",
    "Personal Email Id",
    "Pan Number",
    "Aadhaar Number",
    "Date Of Exit",
)
OPTIONAL_EXCEL_HEADERS_DISPLAY: tuple[str, ...] = ("Employment Status",)
