# Payroll Automation

Streamlit application for payroll tooling: demo sign-in, a dashboard of feature cards, and modular tools (for example the Employee Transfer Analyzer).

## Prerequisites

- **Python** 3.10 or newer (3.11+ recommended)
- **pip**

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/ashu-11/payroll.git
cd payroll
python3 -m venv .venv
```

Activate the virtual environment:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

From the project root (with the virtual environment activated):

```bash
streamlit run app.py
```

Streamlit prints a local URL (typically `http://localhost:8501`). Open it in your browser.

## Authentication (demo)

Sign-in uses placeholder credentials for local development only. Values are defined in `payroll_app/config/settings.py` — update them there if needed. Do **not** commit production secrets into the repository.

## Project layout

- **`app.py`** — Entrypoint and routing (login → dashboard → feature screens).
- **`payroll_app/config/`** — Settings and feature registry for the dashboard.
- **`payroll_app/features/`** — Feature modules (`auth`, `dashboard`, `transfer`, etc.).
- **`requirements.txt`** — Python dependencies.

## License

See `LICENSE`.
