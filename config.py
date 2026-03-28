"""
Configuration for the OKR & KPI Tracker application.

Google Sheets credentials are loaded from Streamlit secrets (for cloud deployment)
or from a local service_account.json file (for local development).
"""

import streamlit as st
from datetime import date

# ---------- Google Sheets ----------
# The ID from your Google Sheet URL:
# https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
try:
    SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
except (KeyError, FileNotFoundError):
    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

# ---------- Quarter helpers ----------
def current_quarter() -> str:
    """Return the current quarter label, e.g. '2026-Q1'."""
    today = date.today()
    q = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{q}"


def quarter_list(start_year: int = 2024) -> list[str]:
    """Generate quarter labels from start_year through one quarter ahead."""
    today = date.today()
    current_y, current_q = today.year, (today.month - 1) // 3 + 1
    # Include one future quarter for planning ahead
    if current_q < 4:
        next_y, next_q = current_y, current_q + 1
    else:
        next_y, next_q = current_y + 1, 1
    quarters = []
    for y in range(start_year, next_y + 1):
        for q in range(1, 5):
            if y == next_y and q > next_q:
                break
            quarters.append(f"{y}-Q{q}")
    return quarters


# ---------- Sheet tab naming ----------
def okr_tab_name(quarter: str) -> str:
    return f"OKRs {quarter}"


def kpi_tab_name(quarter: str) -> str:
    return f"KPIs {quarter}"


def notes_tab_name() -> str:
    return "Notes"


# ---------- Column schemas ----------
OKR_COLUMNS = [
    "id", "title", "description", "owner",
    "target_date", "progress", "last_updated",
]

KPI_COLUMNS = [
    "id", "okr_id", "name", "owner", "current_value",
    "target_value", "baseline_value", "direction", "unit", "last_updated",
]

KPI_HISTORY_COLUMNS = [
    "kpi_id", "date", "value",
]

NOTES_COLUMNS = [
    "parent_type", "parent_id", "timestamp", "author", "text",
]

# ---------- UI ----------
PAGE_TITLE = "OKR Tracker"
PAGE_ICON = "assets/favicon.png"
CACHE_TTL_SECONDS = 120  # how long to cache sheet reads
