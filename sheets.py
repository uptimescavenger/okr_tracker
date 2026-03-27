"""
Google Sheets integration layer using gspread.

All reads/writes go through this module so the rest of the app
never touches the Sheets API directly.
"""

import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

import config

# ---------- Auth ----------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def _get_client() -> gspread.Client:
    """Authenticate and return a gspread client (cached for the session)."""
    # Streamlit Cloud stores secrets as a dict under [gcp_service_account]
    if "gcp_service_account" in st.secrets:
        creds_info = dict(st.secrets["gcp_service_account"])
        # Fix private_key newlines — Streamlit Cloud TOML can mangle \n
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        # Local dev: read from file
        creds = Credentials.from_service_account_file(
            "service_account.json", scopes=SCOPES
        )
    return gspread.authorize(creds)


def _get_spreadsheet() -> gspread.Spreadsheet:
    client = _get_client()
    return client.open_by_key(config.SPREADSHEET_ID)


# ---------- Worksheet helpers ----------

def _get_or_create_worksheet(
    tab_name: str, headers: list[str], rows: int = 200, cols: int = 20
) -> gspread.Worksheet:
    """Return existing worksheet or create it with headers."""
    ss = _get_spreadsheet()
    try:
        ws = ss.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=tab_name, rows=rows, cols=cols)
        ws.append_row(headers, value_input_option="RAW")
    return ws


# ---------- Read ----------

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner="Loading data…")
def read_okrs(quarter: str) -> pd.DataFrame:
    """Read all OKRs for a quarter into a DataFrame."""
    ws = _get_or_create_worksheet(
        config.okr_tab_name(quarter), config.OKR_COLUMNS
    )
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=config.OKR_COLUMNS)
    df = pd.DataFrame(records)
    df["progress"] = pd.to_numeric(df["progress"], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner="Loading data…")
def read_kpis(quarter: str) -> pd.DataFrame:
    """Read all KPIs for a quarter."""
    ws = _get_or_create_worksheet(
        config.kpi_tab_name(quarter), config.KPI_COLUMNS
    )
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=config.KPI_COLUMNS)
    df = pd.DataFrame(records)
    for col in ("current_value", "target_value", "baseline_value"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "direction" not in df.columns:
        df["direction"] = "increase"
    df["direction"] = df["direction"].replace("", "increase").fillna("increase")
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner="Loading data…")
def read_kpi_history(quarter: str) -> pd.DataFrame:
    """Read KPI historical data points for a quarter."""
    tab = f"KPI History {quarter}"
    ws = _get_or_create_worksheet(tab, config.KPI_HISTORY_COLUMNS)
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=config.KPI_HISTORY_COLUMNS)
    df = pd.DataFrame(records)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner="Loading data…")
def read_notes() -> pd.DataFrame:
    """Read the global notes sheet."""
    ws = _get_or_create_worksheet(config.notes_tab_name(), config.NOTES_COLUMNS)
    records = ws.get_all_records()
    if not records:
        return pd.DataFrame(columns=config.NOTES_COLUMNS)
    return pd.DataFrame(records)


# ---------- Write ----------

def _clear_cache():
    """Clear Streamlit data caches so the next read fetches fresh data."""
    read_okrs.clear()
    read_kpis.clear()
    read_kpi_history.clear()
    read_notes.clear()


def _sync_okr_progress(quarter: str, okr_id: str, kpis_df, updated_at: str):
    """Recalculate and write OKR progress from its Key Results."""
    from data import okr_progress_from_krs
    progress = okr_progress_from_krs(okr_id, kpis_df)
    ws = _get_or_create_worksheet(
        config.okr_tab_name(quarter), config.OKR_COLUMNS
    )
    cell = ws.find(str(okr_id), in_column=1)
    if cell is None:
        return
    progress_col = config.OKR_COLUMNS.index("progress") + 1
    updated_col = config.OKR_COLUMNS.index("last_updated") + 1
    ws.update_cell(cell.row, progress_col, progress)
    ws.update_cell(cell.row, updated_col, updated_at)


def update_kpi_value(
    quarter: str, kpi_id: str, okr_id: str, value: float, updated_at: str
):
    """Update a Key Result's current value, append to history, and sync parent OKR progress."""
    ws = _get_or_create_worksheet(
        config.kpi_tab_name(quarter), config.KPI_COLUMNS
    )
    cell = ws.find(str(kpi_id), in_column=1)
    if cell is None:
        raise ValueError(f"Key Result id '{kpi_id}' not found")
    value_col = config.KPI_COLUMNS.index("current_value") + 1
    updated_col = config.KPI_COLUMNS.index("last_updated") + 1
    ws.update_cell(cell.row, value_col, value)
    ws.update_cell(cell.row, updated_col, updated_at)

    # Append to history
    history_tab = f"KPI History {quarter}"
    hws = _get_or_create_worksheet(history_tab, config.KPI_HISTORY_COLUMNS)
    hws.append_row(
        [kpi_id, updated_at, value], value_input_option="USER_ENTERED"
    )

    # Re-read KPIs (uncached) so rollup includes the new value
    _clear_cache()
    fresh_kpis = read_kpis(quarter)
    _sync_okr_progress(quarter, okr_id, fresh_kpis, updated_at)
    _clear_cache()


def add_note(parent_type: str, parent_id: str, author: str, text: str, timestamp: str):
    """Append a timestamped note to the Notes sheet."""
    ws = _get_or_create_worksheet(config.notes_tab_name(), config.NOTES_COLUMNS)
    ws.append_row(
        [parent_type, parent_id, timestamp, author, text],
        value_input_option="USER_ENTERED",
    )
    _clear_cache()


def add_okr(quarter: str, row: list):
    """Append a new OKR row."""
    ws = _get_or_create_worksheet(
        config.okr_tab_name(quarter), config.OKR_COLUMNS
    )
    ws.append_row(row, value_input_option="USER_ENTERED")
    _clear_cache()


def add_kpi(quarter: str, row: list):
    """Append a new KPI row."""
    ws = _get_or_create_worksheet(
        config.kpi_tab_name(quarter), config.KPI_COLUMNS
    )
    ws.append_row(row, value_input_option="USER_ENTERED")
    _clear_cache()
