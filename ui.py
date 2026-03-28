"""
Streamlit UI components — renders OKR cards with nested Key Results,
notes, trend charts, and update/add forms.
All icons are inline SVGs (Lucide-style) — no emojis anywhere.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import uuid

import re
import base64
from pathlib import Path
import config
import sheets
import data

# Consistent border radius used everywhere
BR = "10px"


def _strip_seconds(ts: str) -> str:
    """Remove trailing :SS from a timestamp like '2026-03-28 00:01:00'."""
    return re.sub(r"(\d{2}:\d{2}):\d{2}$", r"\1", str(ts))


# ──────────────────────────────────────────────
#  Inline SVG icons (Lucide-style, outline only)
# ──────────────────────────────────────────────

def _icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    """Return an inline SVG icon. Outline-only, modern look."""
    common = (
        f'xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:middle; flex-shrink:0;"'
    )
    paths = {
        "pencil": '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/><path d="M15 5l4 4"/>',
        "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
        "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
        "refresh": '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
        "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
        "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
        "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
        "bar-chart": '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
        "trending-up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
        "trending-down": '<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>',
        "arrow-up": '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
        "arrow-down": '<line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>',
        "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
        "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
        "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    }
    return f'<svg {common}>{paths.get(name, "")}</svg>'


def _progress_bar_color(pct: float) -> str:
    if pct >= 75:
        return "#22c55e"
    if pct >= 40:
        return "#eab308"
    return "#ef4444"


def _progress_dot(pct: float) -> str:
    """Small colored dot SVG for tab labels."""
    c = _progress_bar_color(pct)
    return f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};margin-right:6px;"></span>'


# ──────────────────────────────────────────────
#  Custom CSS
# ──────────────────────────────────────────────

def inject_css():
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #fff1f2 100%) !important;
    }}

    /* ── Uniform border-radius ── */
    button,
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stDateInput"] > div > div {{
        border-radius: {BR} !important;
    }}

    /* ── Input borders ── */
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {{
        border: 2px solid #d4d0e8 !important;
        background: #ffffff !important;
    }}
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {{
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
    }}
    [data-testid="stSelectbox"] > div > div {{
        border: 2px solid #d4d0e8 !important;
    }}

    /* ── Metric cards ── */
    [data-testid="stMetric"] {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: {BR};
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
    }}
    [data-testid="stMetric"] label {{
        color: #6366f1 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700 !important;
    }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: #1e293b !important;
    }}

    /* ── Progress bars ── */
    [data-testid="stProgress"] > div > div {{
        border-radius: {BR};
        height: 8px !important;
    }}
    [data-testid="stProgress"] > div {{
        background-color: #e8e0f0 !important;
        border-radius: {BR};
    }}

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tablist"] {{
        flex-wrap: wrap;
        gap: 4px;
    }}
    [data-testid="stTabs"] button {{
        border-radius: {BR} {BR} 0 0 !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease;
        white-space: nowrap;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border-bottom: none !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
    }}
    [data-testid="stTabs"] button[aria-selected="false"] {{
        color: #1e293b !important;
        background: #f1f0fb !important;
        font-weight: 600 !important;
    }}
    [data-testid="stTabs"] button[aria-selected="false"]:hover {{
        background: #e8e5f5 !important;
        color: #000000 !important;
    }}

    /* ── Containers / cards ── */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: {BR} !important;
        border-color: #e2e8f0 !important;
        background: #ffffff !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.05);
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #f8f7ff 0%, #f3f0ff 50%, #faf5ff 100%) !important;
        border-right: 1px solid #e2e0f0;
    }}

    /* ── Expanders ── */
    [data-testid="stExpander"] {{
        border: 1px solid #e2e0f0 !important;
        border-radius: {BR} !important;
        background: #faf9ff !important;
    }}

    /* ── Dialog — compact ── */
    [data-testid="stDialog"] {{
        border-radius: {BR} !important;
    }}
    [data-testid="stDialog"] [data-testid="stVerticalBlock"] {{
        background: #ffffff !important;
        gap: 0.5rem !important;
    }}

    /*
     * ── ALL BUTTONS — 10px rounded, pill-like ──
     * This targets every button in the app via multiple selectors
     * to override Streamlit's defaults with maximum specificity.
     */
    button,
    .stButton > button,
    [data-testid="stBaseButton-primary"] > button,
    [data-testid="stBaseButton-secondary"] > button,
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-secondary"] {{
        font-weight: 600 !important;
        border-radius: {BR} !important;
    }}

    /* Primary style (purple gradient) */
    button[kind="primary"],
    .stButton > button[kind="primary"],
    [data-testid="stBaseButton-primary"] > button {{
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
        transition: all 0.2s ease;
        padding: 6px 20px !important;
        font-size: 0.82rem !important;
        border-radius: {BR} !important;
    }}
    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"] > button:hover {{
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
        transform: translateY(-1px);
    }}

    /* Secondary style — transparent with black text (Edit & Refresh buttons) */
    button[kind="secondary"],
    .stButton > button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] > button {{
        background: transparent !important;
        color: #000000 !important;
        border: 1px solid #d1d5db !important;
        border-radius: {BR} !important;
        box-shadow: none;
        padding: 3px 11px !important;
        font-size: 0.55rem !important;
        transition: all 0.2s ease;
        min-height: 0 !important;
        line-height: 1.2 !important;
        letter-spacing: 0.02em;
    }}
    button[kind="secondary"]:hover,
    .stButton > button[kind="secondary"]:hover,
    [data-testid="stBaseButton-secondary"] > button:hover {{
        background: rgba(0, 0, 0, 0.05) !important;
        color: #000000 !important;
        box-shadow: none;
        transform: translateY(-1px);
    }}

    /* ── Refresh button — black text on light purple bg ── */
    [data-testid="stSidebar"] [data-testid="stBaseButton-minimal"] > button,
    button[data-testid="stBaseButton-minimal"] {{
        color: #000000 !important;
        font-weight: 600 !important;
        background: rgba(99, 102, 241, 0.08) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
    }}

    /* ── Tabs — flat bottom, NOT pill-shaped ── */
    [data-testid="stTabs"] button,
    [data-testid="stTabs"] [role="tab"] {{
        border-radius: {BR} {BR} 0 0 !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
    }}

    /* ── Responsive: stack columns on narrow screens ── */
    @media (max-width: 768px) {{
        [data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
        }}
        [data-testid="stHorizontalBlock"] > div {{
            width: 100% !important;
            flex: 1 1 100% !important;
        }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{
            font-size: 1.3rem !important;
        }}
    }}

    /* ── Fun loading animation — bouncing target rings ── */
    @keyframes bounce {{
        0%, 80%, 100% {{ transform: scale(0); opacity: 0.3; }}
        40% {{ transform: scale(1); opacity: 1; }}
    }}
    @keyframes pulse-ring {{
        0% {{ transform: scale(0.8); opacity: 1; }}
        50% {{ transform: scale(1.2); opacity: 0.5; }}
        100% {{ transform: scale(0.8); opacity: 1; }}
    }}
    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}

    /* Override Streamlit's default spinner */
    [data-testid="stSpinner"] {{
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    [data-testid="stSpinner"] > div {{
        display: none !important;
    }}
    [data-testid="stSpinner"]::after {{
        content: "";
        display: flex;
        gap: 8px;
    }}

    /* Skeleton shimmer for loading cards */
    .skeleton-shimmer {{
        background: linear-gradient(90deg, #f0eeff 25%, #e0dcf5 50%, #f0eeff 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: {BR};
    }}
    </style>
    """, unsafe_allow_html=True)


def render_loading_animation():
    """Show a fun animated loading screen while data is being fetched."""
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                padding:60px 20px; min-height:300px;">
        <div style="display:flex; gap:12px; margin-bottom:24px;">
            <div style="width:18px; height:18px; border-radius:50%; background:#6366f1;
                        animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.32s;"></div>
            <div style="width:18px; height:18px; border-radius:50%; background:#8b5cf6;
                        animation: bounce 1.4s infinite ease-in-out both; animation-delay: -0.16s;"></div>
            <div style="width:18px; height:18px; border-radius:50%; background:#a855f7;
                        animation: bounce 1.4s infinite ease-in-out both;"></div>
            <div style="width:18px; height:18px; border-radius:50%; background:#c084fc;
                        animation: bounce 1.4s infinite ease-in-out both; animation-delay: 0.16s;"></div>
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


# ──────────────────────────────────────────────
#  Dialogs — all compact (width="small"), no dead space
# ──────────────────────────────────────────────

@st.dialog("Create New Objective", width="small")
def add_okr_dialog(default_quarter: str):
    quarters = config.quarter_list()
    default_idx = quarters.index(default_quarter) if default_quarter in quarters else len(quarters) - 1
    selected_quarter = st.selectbox("Quarter", options=quarters, index=default_idx)
    title = st.text_input("Objective title")
    owner = st.text_input("Owner")
    target_date = st.date_input("Target date")
    description = st.text_area("Description", height=68)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("Create", type="primary", use_container_width=True):
            if title.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_id = str(uuid.uuid4())[:8]
                sheets.add_okr(selected_quarter, [
                    new_id, title.strip(), description.strip(),
                    owner.strip(), str(target_date), 0, now,
                ])
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter an objective title.")


@st.dialog("Edit Objective", width="small")
def edit_okr_dialog(row: pd.Series, quarter: str):
    title = st.text_input("Objective title", value=str(row.get("title", "")))
    owner = st.text_input("Owner", value=str(row.get("owner", "")))
    target_date = st.text_input("Target date", value=str(row.get("target_date", "")))
    description = st.text_area("Description", value=str(row.get("description", "")), height=68)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", use_container_width=True, key="edit_okr_cancel"):
            st.rerun()
    with c2:
        if st.button("Save", type="primary", use_container_width=True, key="edit_okr_save"):
            if title.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheets.update_okr_fields(quarter, str(row["id"]), {
                    "title": title.strip(),
                    "description": description.strip(),
                    "owner": owner.strip(),
                    "target_date": target_date.strip(),
                    "last_updated": now,
                })
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter an objective title.")
    # Danger zone
    st.divider()
    confirm = st.checkbox(
        f"I want to permanently delete **\"{row.get('title', '')}\"** and all its Key Results.",
        key="confirm_delete_okr",
    )
    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
    if st.button("Delete Objective", use_container_width=True, key="delete_okr_btn", disabled=not confirm):
        sheets.delete_okr(quarter, str(row["id"]))
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


@st.dialog("Edit Key Result", width="small")
def edit_kr_dialog(row: pd.Series, quarter: str):
    name = st.text_input("Key Result name", value=str(row.get("name", "")))
    c1, c2 = st.columns(2)
    with c1:
        owner = st.text_input("Owner", value=str(row.get("owner", "")))
    with c2:
        unit = st.text_input("Unit", value=str(row.get("unit", "")))
    current_dir = str(row.get("direction", "increase")).lower()
    dir_options = ["increase", "decrease"]
    dir_index = dir_options.index(current_dir) if current_dir in dir_options else 0
    direction = st.radio("Direction", options=dir_options, index=dir_index, horizontal=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        baseline_value = st.number_input("Baseline", value=float(row.get("baseline_value", 0)))
    with c2:
        target_value = st.number_input("Target", value=float(row.get("target_value", 0)))
    with c3:
        current_value = st.number_input("Current", value=float(row.get("current_value", 0)))
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("Cancel", use_container_width=True, key="edit_kr_cancel"):
            st.rerun()
    with bc2:
        if st.button("Save", type="primary", use_container_width=True, key="edit_kr_save"):
            if name.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheets.update_kpi_fields(quarter, str(row["id"]), {
                    "name": name.strip(), "owner": owner.strip(),
                    "unit": unit.strip(), "direction": direction,
                    "baseline_value": baseline_value, "target_value": target_value,
                    "current_value": current_value, "last_updated": now,
                })
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter a Key Result name.")
    # Danger zone
    st.divider()
    confirm = st.checkbox(
        f"I want to permanently delete **\"{row.get('name', '')}\"**.",
        key="confirm_delete_kr",
    )
    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
    if st.button("Delete Key Result", use_container_width=True, key="delete_kr_btn", disabled=not confirm):
        okr_id = str(row.get("okr_id", ""))
        sheets.delete_kpi(quarter, str(row["id"]), okr_id)
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


@st.dialog("Add Key Result", width="small")
def add_kr_dialog(okr_id: str, quarter: str):
    name = st.text_input("Key Result name")
    c1, c2 = st.columns(2)
    with c1:
        owner = st.text_input("Owner")
    with c2:
        unit = st.text_input("Unit (e.g. %, $, users)")
    direction = st.radio("Direction", options=["increase", "decrease"], horizontal=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        baseline_value = st.number_input("Baseline", value=0.0)
    with c2:
        current_value = st.number_input("Current", value=0.0)
    with c3:
        target_value = st.number_input("Target", value=100.0)
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("Cancel", use_container_width=True, key="kr_cancel"):
            st.rerun()
    with bc2:
        if st.button("Create", type="primary", use_container_width=True, key="kr_create"):
            if name.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_id = str(uuid.uuid4())[:8]
                sheets.add_kpi(quarter, [
                    new_id, okr_id, name.strip(), owner.strip(),
                    current_value, target_value, baseline_value,
                    direction, unit.strip(), now,
                ])
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter a Key Result name.")


@st.dialog("Update Key Result", width="small")
def update_kr_dialog(row: pd.Series, okr_id: str, quarter: str):
    direction = str(row.get("direction", "increase")).lower()
    is_decrease = direction == "decrease"
    unit = row.get("unit", "")
    st.markdown(
        f"**{row['name']}** &nbsp;·&nbsp; "
        f"{'Lower is better' if is_decrease else 'Higher is better'} &nbsp;·&nbsp; "
        f"Target: {data.format_value(row['target_value'], unit)}"
    )
    new_value = st.number_input(f"New value ({unit})", value=float(row["current_value"]))
    note_author = st.text_input("Your name")
    note_text = st.text_area("Note (optional)", height=60)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancel", use_container_width=True, key="upd_cancel"):
            st.rerun()
    with c2:
        if st.button("Save", type="primary", use_container_width=True, key="upd_save"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                sheets.update_kpi_value(quarter, str(row["id"]), okr_id, new_value, now)
                if note_text.strip() and note_author.strip():
                    sheets.add_note("KR", str(row["id"]), note_author.strip(), note_text.strip(), now)
                st.cache_data.clear()
                st.rerun()
            except Exception as exc:
                st.error(f"Error: {exc}")


# ──────────────────────────────────────────────
#  Sidebar
# ──────────────────────────────────────────────

def _logo_b64() -> str:
    """Return the logo as a base64-encoded data URI (cached in session)."""
    if "_logo_b64" not in st.session_state:
        raw = Path(__file__).parent.joinpath("assets", "logo.png").read_bytes()
        st.session_state["_logo_b64"] = base64.b64encode(raw).decode()
    return st.session_state["_logo_b64"]


def render_sidebar(quarter: str):
    with st.sidebar:
        st.markdown(
            f"<div style='text-align:center; margin-bottom:8px;'>"
            f"<img src='data:image/png;base64,{_logo_b64()}' style='width:100%; max-width:240px;' />"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h1 style='text-align:center; margin-bottom:0;'>"
            "<span style='background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7); "
            "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
            "font-size: 1.5rem;'>OKR Tracker</span></h1>"
            "<p style='text-align:center; color:#8b8fa3; font-size:0.8rem; margin-top:2px;'>"
            "Track objectives & key results</p>",
            unsafe_allow_html=True,
        )
        st.divider()
        if st.button("Create New Objective", use_container_width=True, type="primary"):
            add_okr_dialog(quarter)

        st.divider()
        if st.button("Refresh Data", use_container_width=True, key="refresh_btn", type="secondary"):
            st.cache_data.clear()
            st.rerun()
        st.caption("Auto-syncs from Google Sheets every 2 min.")


# ──────────────────────────────────────────────
#  Summary metrics
# ──────────────────────────────────────────────

def render_okr_metrics(stats: dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Objectives", stats["total"])
    c2.metric("Avg Progress", f"{stats['avg_progress']}%")
    c3.metric("Completed", stats["completed"])
    c4.metric("At Risk", stats["at_risk"])


# ──────────────────────────────────────────────
#  OKR tabs
# ──────────────────────────────────────────────

def render_okr_tabs(
    okrs_df: pd.DataFrame,
    kpis_df: pd.DataFrame,
    history_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str,
):
    if okrs_df.empty:
        st.markdown(
            f"<div style='text-align:center; padding:60px 20px; background:#ffffff; "
            f"border-radius:10px; border:1px dashed #c7c4e0;'>"
            f"<div style='margin-bottom:12px;'>{_icon('target', 48, '#c7c4e0')}</div>"
            f"<h3 style='color:#475569;'>No objectives yet</h3>"
            f"<p style='color:#8b8fa3;'>Click <strong>Create New Objective</strong> "
            f"in the sidebar to get started.</p></div>",
            unsafe_allow_html=True,
        )
        return

    tab_labels = []
    for _, row in okrs_df.iterrows():
        okr_id = str(row["id"])
        pct = data.okr_progress_from_krs(okr_id, kpis_df)
        dot = "●" if pct >= 75 else ("◐" if pct >= 40 else "○")
        tab_labels.append(f"{dot} {row['title']}")

    tabs = st.tabs(tab_labels)
    for i, (_, row) in enumerate(okrs_df.iterrows()):
        with tabs[i]:
            _render_okr_content(row, kpis_df, history_df, notes_df, quarter)


# ──────────────────────────────────────────────
#  OKR content
# ──────────────────────────────────────────────

def _render_okr_content(
    row: pd.Series,
    kpis_df: pd.DataFrame,
    history_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str,
):
    okr_id = str(row["id"])
    pct = data.okr_progress_from_krs(okr_id, kpis_df)
    color = data.progress_color(pct)
    bar_color = _progress_bar_color(pct)
    krs = data.krs_for_okr(okr_id, kpis_df)

    # Header: title + edit inline, then %
    title_col, pct_col = st.columns([5, 1])
    with title_col:
        # Title with inline edit link
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:8px;'>"
            f"<h3 style='margin:0;'>{row['title']}</h3>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with pct_col:
        st.markdown(
            f"<div style='text-align:right;'>"
            f"<span style='font-size:2.2rem; font-weight:800; color:{color}; line-height:1;'>"
            f"{pct:.0f}%</span>"
            f"<br><span style='font-size:0.7rem; color:#94a3b8;'>overall</span></div>",
            unsafe_allow_html=True,
        )

    # Edit button right below title
    if st.button("✎ Edit Objective", key=f"edit_okr_{okr_id}", type="secondary"):
        edit_okr_dialog(row, quarter)

    if row.get("description"):
        st.markdown(
            f"<p style='color:#64748b; margin-top:0; margin-bottom:8px; font-size:0.9rem;'>"
            f"{row['description']}</p>",
            unsafe_allow_html=True,
        )

    # OKR progress bar
    clamped_pct = max(0.0, min(pct, 100.0))
    st.markdown(
        f"<div style='background:#e8e0f0; border-radius:10px; height:10px; width:100%; overflow:hidden;'>"
        f"<div style='background:{bar_color}; width:{clamped_pct}%; height:100%; border-radius:10px; "
        f"transition: width 0.4s ease;'></div></div>",
        unsafe_allow_html=True,
    )

    # Detail pills — SVG icons instead of emojis
    user_icon = _icon("user", 13, "#6d28d9")
    cal_icon = _icon("calendar", 13, "#0369a1")
    clock_icon = _icon("clock", 13, "#be185d")
    st.markdown(
        f"<div style='display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 16px 0;'>"
        f"<span style='background:#ede9fe; color:#6d28d9; padding:4px 12px; "
        f"border-radius:10px; font-size:0.8rem; border:1px solid #ddd6fe; display:inline-flex; align-items:center; gap:4px;'>"
        f"{user_icon} {row.get('owner', '—')}</span>"
        f"<span style='background:#e0f2fe; color:#0369a1; padding:4px 12px; "
        f"border-radius:10px; font-size:0.8rem; border:1px solid #bae6fd; display:inline-flex; align-items:center; gap:4px;'>"
        f"{cal_icon} {row.get('target_date', '—')}</span>"
        f"<span style='background:#fce7f3; color:#be185d; padding:4px 12px; "
        f"border-radius:10px; font-size:0.8rem; border:1px solid #fbcfe8; display:inline-flex; align-items:center; gap:4px;'>"
        f"{clock_icon} {_strip_seconds(row.get('last_updated', '—'))}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Key Results header + add button
    kr_header_col, kr_add_col = st.columns([4, 1])
    with kr_header_col:
        st.markdown(f"#### Key Results ({len(krs)})")
    with kr_add_col:
        if st.button("Create Key Result", key=f"add_kr_btn_{okr_id}", type="primary", use_container_width=True):
            add_kr_dialog(okr_id, quarter)

    if krs.empty:
        st.markdown(
            f"<div style='text-align:center; padding:40px; background:#faf9ff; "
            f"border-radius:10px; border:2px dashed #c7c4e0;'>"
            f"<p style='color:#8b8fa3; margin:0;'>No Key Results yet — "
            f"click <strong>Create Key Result</strong> to get started.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        # 2-column tile grid for KR cards
        kr_list = list(krs.iterrows())
        for row_start in range(0, len(kr_list), 2):
            pair = kr_list[row_start:row_start + 2]
            cols = st.columns(2)
            for col_idx, (_, kr) in enumerate(pair):
                with cols[col_idx]:
                    _render_kr_card(kr, history_df, notes_df, quarter)

    # OKR notes
    okr_notes = data.notes_for(notes_df, "OKR", okr_id)
    notes_icon = _icon("file-text", 14, "#64748b")
    with st.expander(f"Objective Notes ({len(okr_notes)})"):
        _render_note_form("OKR", okr_id)
        if okr_notes.empty:
            st.caption("No notes yet.")
        else:
            for _, n in okr_notes.iterrows():
                st.markdown(
                    f"<div style='background:#faf9ff; border:1px solid #e2e0f0; border-radius:10px; "
                    f"padding:10px 14px; margin-bottom:8px;'>"
                    f"<strong>{n['author']}</strong> <span style='color:#94a3b8;'> {_strip_seconds(n['timestamp'])}</span>"
                    f"<br>{n['text']}</div>",
                    unsafe_allow_html=True,
                )


# ──────────────────────────────────────────────
#  Key Result card — compact tile
# ──────────────────────────────────────────────

def _render_kr_card(
    row: pd.Series,
    history_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str,
):
    achievement = data.kpi_achievement(row)
    color = data.progress_color(achievement)
    bar_color = _progress_bar_color(achievement)
    kr_id = str(row["id"])
    okr_id = str(row["okr_id"])
    direction = str(row.get("direction", "increase")).lower()
    is_decrease = direction == "decrease"
    unit = row.get("unit", "")

    dir_icon = _icon("arrow-down" if is_decrease else "arrow-up", 14, color)

    with st.container(border=True):
        # Name row with edit + update
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:6px; margin-bottom:2px;'>"
            f"<span style='display:inline-flex; align-items:center; justify-content:center; "
            f"background:{color}15; color:{color}; "
            f"width:22px; height:22px; border-radius:6px;'>{dir_icon}</span>"
            f"<strong style='font-size:0.95rem; flex:1;'>{row['name']}</strong>"
            f"<span style='font-size:1.3rem; font-weight:800; color:{color};'>{achievement:.0f}%</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Edit left-justified, Update right-justified
        bc1, bc2, bc3 = st.columns([1, 3, 1.5])
        with bc1:
            if st.button("✎ Edit", key=f"edit_kr_{kr_id}", type="secondary"):
                edit_kr_dialog(row, quarter)
        with bc3:
            if st.button("Update", key=f"upd_btn_{kr_id}", type="primary"):
                update_kr_dialog(row, okr_id, quarter)

        # Metrics row
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Current", data.format_value(row["current_value"], unit))
        with m2:
            label = "Target" + (" (lower)" if is_decrease else "")
            st.metric(label, data.format_value(row["target_value"], unit))

        # Progress bar
        clamped_pct = max(0.0, min(achievement, 100.0))
        st.markdown(
            f"<div style='background:#e8e0f0; border-radius:10px; height:6px; width:100%; overflow:hidden;'>"
            f"<div style='background:{bar_color}; width:{clamped_pct}%; height:100%; border-radius:10px; "
            f"transition: width 0.4s ease;'></div></div>",
            unsafe_allow_html=True,
        )

        # Subtitle
        user_icon = _icon("user", 11, "#94a3b8")
        clock_icon = _icon("clock", 11, "#94a3b8")
        parts = f"{user_icon} {row.get('owner', '—')}"
        if is_decrease:
            parts += f" &middot; Baseline: {data.format_value(row.get('baseline_value', '—'), unit)}"
        parts += f" &middot; {clock_icon} {_strip_seconds(row.get('last_updated', '—'))}"
        st.markdown(
            f"<p style='color:#94a3b8; font-size:0.75rem; margin:4px 0 0 0; display:flex; align-items:center; gap:4px; flex-wrap:wrap;'>"
            f"{parts}</p>",
            unsafe_allow_html=True,
        )

        # Trend chart
        trend = data.build_kpi_trend(history_df, kr_id)
        if not trend.empty:
            _render_modern_chart(trend, row, is_decrease)

        # Notes
        kr_notes = data.notes_for(notes_df, "KR", kr_id)
        with st.expander(f"Notes ({len(kr_notes)})", expanded=False):
            _render_note_form("KR", kr_id)
            _render_notes_list(kr_notes)


# ──────────────────────────────────────────────
#  Modern chart — zoomed Y-axis
# ──────────────────────────────────────────────

def _render_modern_chart(trend: pd.DataFrame, row: pd.Series, is_decrease: bool):
    line_color = "#8b5cf6"
    target_color = "#22c55e" if is_decrease else "#ef4444"
    target_val = float(row["target_value"])

    all_values = list(trend["value"].dropna()) + [target_val]
    y_min = min(all_values)
    y_max = max(all_values)
    padding = (y_max - y_min) * 0.15 if y_max != y_min else max(abs(y_max) * 0.15, 1)
    range_lo = y_min - padding
    range_hi = y_max + padding
    if y_min >= 0 and range_lo < 0:
        range_lo = 0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["date"], y=[range_lo] * len(trend),
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=trend["date"], y=trend["value"],
        fill="tonexty",
        fillcolor="rgba(139, 92, 246, 0.10)",
        line=dict(color=line_color, width=2.5, shape="spline"),
        mode="lines+markers",
        marker=dict(size=6, color="#ffffff", line=dict(width=2, color=line_color)),
        name="Value",
        hovertemplate="%{x|%b %d, %Y}<br><b>%{y:.1f}</b><extra></extra>",
    ))
    fig.add_hline(
        y=target_val, line_dash="dot", line_color=target_color, line_width=1.5,
        annotation_text="Target", annotation_font_color=target_color, annotation_font_size=10,
    )
    fig.update_layout(
        height=160,
        margin=dict(l=0, r=0, t=4, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickfont=dict(color="#94a3b8", size=9), linecolor="rgba(0,0,0,0)"),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(226,232,240,0.6)",
            tickfont=dict(color="#94a3b8", size=9), linecolor="rgba(0,0,0,0)",
            range=[range_lo, range_hi],
        ),
        showlegend=False,
        hoverlabel=dict(bgcolor="#ffffff", font_size=11, font_color="#1e293b", bordercolor="#e2e8f0"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ──────────────────────────────────────────────
#  Notes helpers
# ──────────────────────────────────────────────

def _render_notes_list(notes_df: pd.DataFrame):
    if notes_df.empty:
        st.caption("No notes yet.")
    else:
        for _, n in notes_df.iterrows():
            st.markdown(
                f"<div style='background:#faf9ff; border:1px solid #e2e0f0; border-radius:10px; "
                f"padding:10px 14px; margin-bottom:8px;'>"
                f"<strong>{n['author']}</strong> <span style='color:#94a3b8;'> {_strip_seconds(n['timestamp'])}</span>"
                f"<br>{n['text']}</div>",
                unsafe_allow_html=True,
            )


def _render_note_form(parent_type: str, parent_id: str):
    key_prefix = f"note_{parent_type}_{parent_id}"
    st.markdown(
        "<div style='border:2px solid #d4d0e8; border-radius:10px; padding:14px; "
        "margin-top:8px; background:#ffffff;'>",
        unsafe_allow_html=True,
    )
    author = st.text_input("Your name", key=f"{key_prefix}_author")
    text = st.text_area("Note", key=f"{key_prefix}_text", height=60)
    if st.button("Add note", key=f"{key_prefix}_btn", type="primary"):
        if author.strip() and text.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheets.add_note(parent_type, parent_id, author.strip(), text.strip(), now)
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("Enter both name and note.")
    st.markdown("</div>", unsafe_allow_html=True)
