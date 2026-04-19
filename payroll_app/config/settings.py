"""App-wide configuration: demo auth and dashboard feature registry."""

from __future__ import annotations

from typing import Any

# Demo auth only — replace with real authentication for production.
DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "payroll2026"

# Register features for the dashboard (append as you add new tools under features/).
FEATURE_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "transfer",
        "title": "Employee Transfer Analyzer",
        "description": "Merge two employee masters, detect transfers between entities, and download a flattened Excel summary.",
        "enabled": True,
    },
    {
        "id": "payroll_reports",
        "title": "Payroll Reports",
        "description": "Placeholder for upcoming summary and variance reports.",
        "enabled": False,
    },
]
