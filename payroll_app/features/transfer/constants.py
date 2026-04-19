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
#   Company → Entity (legal entity per row — not derived from filename)
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

# All columns above must appear after mapping (exactly once each).
REQUIRED_INTERNAL_COLUMNS = list(dict.fromkeys(COLUMN_HEADER_MAP.values()))

BAND_EXCLUDE = {"B0", "Third Party"}

# Copy for errors / UI (human-readable original header names).
EXPECTED_EXCEL_HEADERS_TEXT = (
    "Employee Id, Full Name, Date Of Joining, Grade, Band, Personal Email Id, "
    "Pan Number, Aadhaar Number, Employment Status, Date Of Exit, Company"
)
