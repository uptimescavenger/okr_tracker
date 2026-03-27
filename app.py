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

# ── Sidebar → quarter selection ──
quarter = ui.render_sidebar()

# ── Load data ──
okrs_df = sheets.read_okrs(quarter)
kpis_df = sheets.read_kpis(quarter)
history_df = sheets.read_kpi_history(quarter)
notes_df = sheets.read_notes()

# ── OKR section ──
st.header(f"Objectives — {quarter}")
stats = data.okr_summary_stats(okrs_df, kpis_df)
ui.render_okr_metrics(stats)

if okrs_df.empty:
    st.info("No OKRs for this quarter yet. Add one below.")
else:
    for _, row in okrs_df.iterrows():
        ui.render_okr_card(row, kpis_df, history_df, notes_df, quarter)

# ── Add new OKR ──
ui.render_add_okr_form(quarter)
