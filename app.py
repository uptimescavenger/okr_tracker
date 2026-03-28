"""
OKR Tracker — main Streamlit entry point.

Run locally:
    streamlit run app.py
"""

import streamlit as st
import config
import sheets
import data
import ui

# ── Page config ──
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
)

# ── Inject custom styling ──
ui.inject_css()

# ── Check secrets are configured ──
if config.SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
    st.error(
        "**SPREADSHEET_ID not found in secrets.** "
        "Go to Manage app → Settings → Secrets and add your secrets. "
        f"Available secret keys: {list(st.secrets) if hasattr(st.secrets, '__iter__') else 'none'}"
    )
    st.stop()

if "gcp_service_account" not in st.secrets:
    st.error(
        "**gcp_service_account not found in secrets.** "
        "Make sure your secrets.toml includes the [gcp_service_account] section."
    )
    st.stop()

# ── Sidebar ──
quarter_ref = []
ui.render_sidebar(quarter_ref)
quarter = quarter_ref[0]

# ── Load data ──
okrs_df = sheets.read_okrs(quarter)
kpis_df = sheets.read_kpis(quarter)
history_df = sheets.read_kpi_history(quarter)
notes_df = sheets.read_notes()

# ── Header ──
st.markdown(
    f"<h2 style='margin-bottom:2px; color:#1e293b;'>{quarter}</h2>"
    f"<p style='color:#94a3b8; margin-top:0;'>Click an objective tab to view key results and progress.</p>",
    unsafe_allow_html=True,
)

# ── Summary metrics ──
stats = data.okr_summary_stats(okrs_df, kpis_df)
ui.render_okr_metrics(stats)

st.markdown("")

# ── OKR tabs ──
ui.render_okr_tabs(okrs_df, kpis_df, history_df, notes_df, quarter)
