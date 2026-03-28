"""
OKR Tracker — main Streamlit entry point.

Run locally:
    streamlit run app.py
"""

import streamlit as st
from PIL import Image
import config
import sheets
import data
import ui

# ── Page config ──
from pathlib import Path
_favicon = Image.open(Path(__file__).parent / "assets" / "favicon.png")
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=_favicon,
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

# ── Quarter selector on main page (1/4 width, left-justified) ──
_q_col, _ = st.columns([1, 3])
with _q_col:
    quarters = config.quarter_list()
    current_q = config.current_quarter()
    default_idx = quarters.index(current_q) if current_q in quarters else len(quarters) - 1
    quarter = st.selectbox("Quarter", options=quarters, index=default_idx, label_visibility="collapsed")

# ── Sidebar ──
ui.render_sidebar(quarter)

# ── Load data with fun animation ──
_loading = st.empty()
with _loading.container():
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                padding:60px 20px; min-height:300px;">
        <div style="display:flex; gap:12px; margin-bottom:24px;">
            <div style="width:18px; height:18px; border-radius:50%; background:#6366f1;
                        animation: bounce 1.4s infinite ease-in-out both; animation-delay:-0.32s;"></div>
            <div style="width:18px; height:18px; border-radius:50%; background:#8b5cf6;
                        animation: bounce 1.4s infinite ease-in-out both; animation-delay:-0.16s;"></div>
            <div style="width:18px; height:18px; border-radius:50%; background:#a855f7;
                        animation: bounce 1.4s infinite ease-in-out both;"></div>
            <div style="width:18px; height:18px; border-radius:50%; background:#c084fc;
                        animation: bounce 1.4s infinite ease-in-out both; animation-delay:0.16s;"></div>
        </div>
        <div style="position:relative; width:60px; height:60px; margin-bottom:20px;">
            <div style="position:absolute; inset:0; border:3px solid #6366f1; border-radius:50%;
                        animation: pulse-ring 1.5s infinite ease-in-out;"></div>
            <div style="position:absolute; inset:12px; border:3px solid #8b5cf6; border-radius:50%;
                        animation: pulse-ring 1.5s infinite ease-in-out 0.3s;"></div>
            <div style="position:absolute; inset:24px; background:#6366f1; border-radius:50%;
                        animation: pulse-ring 1.5s infinite ease-in-out 0.6s;"></div>
        </div>
        <p style="color:#6366f1; font-weight:600; font-size:1rem; margin:0;">Loading your OKRs...</p>
        <p style="color:#94a3b8; font-size:0.8rem; margin-top:4px;">Syncing with Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)

okrs_df = sheets.read_okrs(quarter)
kpis_df = sheets.read_kpis(quarter)
history_df = sheets.read_kpi_history(quarter)
notes_df = sheets.read_notes()

_loading.empty()

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
