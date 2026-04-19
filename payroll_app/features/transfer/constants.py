"""Column and business rules for the Employee Transfer Analyzer."""

REQUIRED_COLUMNS = [
    "Employee Code",
    "PAN Number",
    "Aadhaar Number",
    "Personal Email ID",
    "Date of Joining (DOJ)",
    "Date of Leaving (DOL)",
    "Band",
    "Grade",
]

BAND_EXCLUDE = {"B0", "Third Party"}
