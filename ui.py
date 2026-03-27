"""
Streamlit UI components — renders OKR cards with nested Key Results,
notes, trend charts, and update/add forms.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import uuid

import config
import sheets
import data

# Consistent border radius used everywhere
BR = "10px"

# ──────────────────────────────────────────────
#  Custom CSS — responsive, uniform radii, no purple bar
# ──────────────────────────────────────────────

def inject_css():
    st.markdown(f"""
    <style>
    /* ── Global ── */
    .stApp {{
        background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #fff1f2 100%) !important;
    }}

    /* ── Uniform border-radius for all interactive elements ── */
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

    /* ── Progress bars — clean, NO gradient bar above ── */
    [data-testid="stProgress"] > div > div {{
        border-radius: {BR};
        height: 8px !important;
    }}
    [data-testid="stProgress"] > div {{
        background-color: #e8e0f0 !important;
        border-radius: {BR};
    }}

    /* ── Tabs — responsive wrapping ── */
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
        color: #64748b !important;
        background: #f1f0fb !important;
    }}
    [data-testid="stTabs"] button[aria-selected="false"]:hover {{
        background: #e8e5f5 !important;
        color: #4338ca !important;
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

    /* ── Dialog ── */
    [data-testid="stDialog"] {{
        border-radius: {BR} !important;
    }}
    [data-testid="stDialog"] [data-testid="stVerticalBlock"] {{
        background: #ffffff !important;
    }}

    /* ── All buttons — consistent ── */
    button {{
        font-weight: 600 !important;
    }}
    button[kind="primary"] {{
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
        transition: all 0.2s ease;
    }}
    button[kind="primary"]:hover {{
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
        transform: translateY(-1px);
    }}
    button[kind="secondary"] {{
        border: 1px solid #d4d0e8 !important;
        color: #475569 !important;
    }}

    /* ── FORCE all buttons to have full 10px rounded corners ── */
    button,
    [data-testid="stBaseButton-secondary"] button,
    [data-testid="stBaseButton-primary"] button,
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-primary"],
    .stButton > button {{
        border-radius: {BR} !important;
    }}

    /* ── Pencil edit button — icon + text only, no border/bg ── */
    .pencil-edit button {{
        background: transparent !important;
        border: none !important;
        color: #64748b !important;
        box-shadow: none !important;
        padding: 2px 4px !important;
        min-height: 0 !important;
        font-size: 0.8rem !important;
        transition: color 0.15s ease;
    }}
    .pencil-edit button:hover {{
        background: transparent !important;
        border: none !important;
        color: #6366f1 !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* ── Update button — black outline, transparent bg ── */
    .kr-update-btn button {{
        background: transparent !important;
        border: 1.5px solid #1e293b !important;
        color: #1e293b !important;
        border-radius: {BR} !important;
        box-shadow: none !important;
        font-weight: 600 !important;
        transition: all 0.15s ease;
    }}
    .kr-update-btn button:hover {{
        background: #f1f5f9 !important;
        border-color: #000000 !important;
        color: #000000 !important;
        transform: none !important;
        box-shadow: none !important;
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
        .okr-pct {{
            font-size: 2rem !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  Color helper for inline progress bars
# ──────────────────────────────────────────────

def _pencil_svg(size: int = 16) -> str:
    """Return an inline SVG pencil icon matching the reference image style."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;">'
        f'<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>'
        f'<path d="M15 5l4 4"/>'
        f'</svg>'
    )


def _progress_bar_color(pct: float) -> str:
    """Return a CSS color based on progress percentage."""
    if pct >= 100:
        return "#22c55e"
    if pct >= 75:
        return "#22c55e"
    if pct >= 40:
        return "#eab308"
    return "#ef4444"


# ──────────────────────────────────────────────
#  Add OKR dialog (modal popup)
# ──────────────────────────────────────────────

@st.dialog("Create New Objective", width="large")
def add_okr_dialog(quarter: str):
    st.markdown(
        "<p style='color:#64748b; margin-bottom:16px;'>Add a new objective to track for this quarter.</p>",
        unsafe_allow_html=True,
    )
    title = st.text_input("Objective title")
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Owner")
    with col2:
        target_date = st.date_input("Target date")
    description = st.text_area("Description", height=100)

    st.markdown("")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with c3:
        if st.button("Create", type="primary", use_container_width=True):
            if title.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_id = str(uuid.uuid4())[:8]
                sheets.add_okr(quarter, [
                    new_id, title.strip(), description.strip(),
                    owner.strip(), str(target_date), 0, now,
                ])
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter an objective title.")


# ──────────────────────────────────────────────
#  Edit OKR dialog
# ──────────────────────────────────────────────

@st.dialog("Edit Objective", width="large")
def edit_okr_dialog(row: pd.Series, quarter: str):
    st.markdown(
        "<p style='color:#64748b; margin-bottom:16px;'>Update the objective details.</p>",
        unsafe_allow_html=True,
    )
    title = st.text_input("Objective title", value=str(row.get("title", "")))
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Owner", value=str(row.get("owner", "")))
    with col2:
        target_date = st.text_input("Target date", value=str(row.get("target_date", "")))
    description = st.text_area("Description", value=str(row.get("description", "")), height=100)

    st.markdown("")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c2:
        if st.button("Cancel", use_container_width=True, key="edit_okr_cancel"):
            st.rerun()
    with c3:
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

    # ── Danger zone: delete ──
    st.divider()
    st.markdown(
        "<p style='color:#ef4444; font-weight:600; font-size:0.85rem;'>Danger Zone</p>",
        unsafe_allow_html=True,
    )
    confirm = st.checkbox(
        f"I understand this will permanently delete **\"{row.get('title', '')}\"** and all its Key Results.",
        key="confirm_delete_okr",
    )
    if st.button(
        "Delete Objective",
        use_container_width=True,
        key="delete_okr_btn",
        disabled=not confirm,
    ):
        sheets.delete_okr(quarter, str(row["id"]))
        st.cache_data.clear()
        st.rerun()


# ──────────────────────────────────────────────
#  Edit Key Result dialog
# ──────────────────────────────────────────────

@st.dialog("Edit Key Result", width="large")
def edit_kr_dialog(row: pd.Series, quarter: str):
    st.markdown(
        "<p style='color:#64748b; margin-bottom:16px;'>Update the key result details.</p>",
        unsafe_allow_html=True,
    )
    name = st.text_input("Key Result name", value=str(row.get("name", "")))
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Owner", value=str(row.get("owner", "")))
    with col2:
        unit = st.text_input("Unit (e.g. %, $, users)", value=str(row.get("unit", "")))

    current_dir = str(row.get("direction", "increase")).lower()
    dir_options = ["increase", "decrease"]
    dir_index = dir_options.index(current_dir) if current_dir in dir_options else 0
    direction = st.radio(
        "Direction",
        options=dir_options,
        index=dir_index,
        horizontal=True,
        help="Choose 'decrease' for metrics you want to reduce",
    )

    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        baseline_value = st.number_input(
            "Baseline (start)",
            value=float(row.get("baseline_value", 0)),
        )
    with c2:
        target_value = st.number_input(
            "Target" + (" (lower)" if direction == "decrease" else ""),
            value=float(row.get("target_value", 0)),
        )
    with c3:
        current_value = st.number_input(
            "Current value",
            value=float(row.get("current_value", 0)),
        )

    st.markdown("")
    btn_c1, btn_c2, btn_c3 = st.columns([2, 1, 1])
    with btn_c2:
        if st.button("Cancel", use_container_width=True, key="edit_kr_cancel"):
            st.rerun()
    with btn_c3:
        if st.button("Save", type="primary", use_container_width=True, key="edit_kr_save"):
            if name.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheets.update_kpi_fields(quarter, str(row["id"]), {
                    "name": name.strip(),
                    "owner": owner.strip(),
                    "unit": unit.strip(),
                    "direction": direction,
                    "baseline_value": baseline_value,
                    "target_value": target_value,
                    "current_value": current_value,
                    "last_updated": now,
                })
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter a Key Result name.")

    # ── Danger zone: delete ──
    st.divider()
    st.markdown(
        "<p style='color:#ef4444; font-weight:600; font-size:0.85rem;'>Danger Zone</p>",
        unsafe_allow_html=True,
    )
    confirm = st.checkbox(
        f"I understand this will permanently delete **\"{row.get('name', '')}\"**.",
        key="confirm_delete_kr",
    )
    if st.button(
        "Delete Key Result",
        use_container_width=True,
        key="delete_kr_btn",
        disabled=not confirm,
    ):
        okr_id = str(row.get("okr_id", ""))
        sheets.delete_kpi(quarter, str(row["id"]), okr_id)
        st.cache_data.clear()
        st.rerun()


# ──────────────────────────────────────────────
#  Add Key Result dialog (modal popup)
# ──────────────────────────────────────────────

@st.dialog("Add Key Result", width="large")
def add_kr_dialog(okr_id: str, quarter: str):
    st.markdown(
        "<p style='color:#64748b; margin-bottom:16px;'>Define a measurable key result for this objective.</p>",
        unsafe_allow_html=True,
    )

    name = st.text_input("Key Result name")
    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input("Owner")
    with col2:
        unit = st.text_input("Unit (e.g. %, $, users)")

    direction = st.radio(
        "Direction",
        options=["increase", "decrease"],
        horizontal=True,
        help="Choose 'decrease' for metrics you want to reduce (e.g. cost, churn)",
    )

    st.divider()

    if direction == "decrease":
        st.caption("Lower is better — tracks reduction from baseline to target.")
        c1, c2, c3 = st.columns(3)
        with c1:
            baseline_value = st.number_input(
                "Baseline (start)", value=0.0,
                help="The value you're starting from (e.g. $600)",
            )
        with c2:
            current_value = st.number_input("Current value", value=baseline_value)
        with c3:
            target_value = st.number_input(
                "Target (lower)", value=0.0,
                help="The value you want to reach (e.g. $500)",
            )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            baseline_value = st.number_input("Baseline (start)", value=0.0)
        with c2:
            current_value = st.number_input("Current value", value=0.0)
        with c3:
            target_value = st.number_input("Target", value=100.0)

    st.markdown("")
    btn_c1, btn_c2, btn_c3 = st.columns([2, 1, 1])
    with btn_c2:
        if st.button("Cancel", use_container_width=True, key="kr_cancel"):
            st.rerun()
    with btn_c3:
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


# ──────────────────────────────────────────────
#  Update Key Result dialog (modal popup)
# ──────────────────────────────────────────────

@st.dialog("Update Key Result")
def update_kr_dialog(row: pd.Series, okr_id: str, quarter: str):
    direction = str(row.get("direction", "increase")).lower()
    is_decrease = direction == "decrease"
    unit = row.get("unit", "")

    st.markdown(
        f"<h4 style='margin-bottom:4px;'>{row['name']}</h4>"
        f"<p style='color:#64748b; font-size:0.85rem;'>"
        f"{'Lower is better' if is_decrease else 'Higher is better'} · "
        f"Target: {data.format_value(row['target_value'], unit)}</p>",
        unsafe_allow_html=True,
    )

    new_value = st.number_input(
        f"New value ({unit})",
        value=float(row["current_value"]),
    )
    note_author = st.text_input("Your name")
    note_text = st.text_area("Add a note (optional)", height=80)

    st.markdown("")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c2:
        if st.button("Cancel", use_container_width=True, key="upd_cancel"):
            st.rerun()
    with c3:
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

def render_sidebar(quarter_ref: list):
    with st.sidebar:
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

        quarters = config.quarter_list()
        current_q = config.current_quarter()
        default_idx = quarters.index(current_q) if current_q in quarters else len(quarters) - 1

        selected = st.selectbox("Quarter", options=quarters, index=default_idx)
        quarter_ref.append(selected)

        st.divider()

        if st.button("Create New Objective", use_container_width=True, type="primary"):
            add_okr_dialog(selected)

        st.divider()
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption("Auto-syncs from Google Sheets every 2 min.")


# ──────────────────────────────────────────────
#  Summary metrics
# ──────────────────────────────────────────────

def render_okr_metrics(stats: dict):
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.metric("Objectives", stats["total"])
    r1c2.metric("Avg Progress", f"{stats['avg_progress']}%")
    r1c3.metric("Completed", stats["completed"])
    r1c4.metric("At Risk", stats["at_risk"])


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
            "<div style='text-align:center; padding:60px 20px; background:#ffffff; "
            "border-radius:10px; border:1px dashed #c7c4e0;'>"
            "<p style='font-size:3rem; margin-bottom:8px;'>🎯</p>"
            "<h3 style='color:#475569;'>No objectives yet</h3>"
            "<p style='color:#8b8fa3;'>Click <strong>Create New Objective</strong> "
            "in the sidebar to get started.</p></div>",
            unsafe_allow_html=True,
        )
        return

    tab_labels = []
    for _, row in okrs_df.iterrows():
        okr_id = str(row["id"])
        pct = data.okr_progress_from_krs(okr_id, kpis_df)
        emoji = _progress_emoji(pct)
        tab_labels.append(f"{emoji} {row['title']}")

    tabs = st.tabs(tab_labels)
    for i, (_, row) in enumerate(okrs_df.iterrows()):
        with tabs[i]:
            _render_okr_content(row, kpis_df, history_df, notes_df, quarter)


def _progress_emoji(pct: float) -> str:
    if pct >= 100:
        return "✅"
    if pct >= 75:
        return "🟢"
    if pct >= 40:
        return "🟡"
    return "🔴"


# ──────────────────────────────────────────────
#  OKR content (inside a tab)
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

    # ── Header: title + pencil on same row, then % ──
    title_col, pencil_col, pct_col = st.columns([4, 0.6, 1])
    with title_col:
        st.markdown(f"### {row['title']}")
    with pencil_col:
        # Pencil icon button — inline SVG as label
        pencil = _pencil_svg(18)
        st.markdown('<div class="pencil-edit">', unsafe_allow_html=True)
        if st.button(f"✎ Edit", key=f"edit_okr_{okr_id}", help="Edit this objective"):
            edit_okr_dialog(row, quarter)
        st.markdown('</div>', unsafe_allow_html=True)
    with pct_col:
        st.markdown(
            f"<div style='text-align:right; padding:4px 0;'>"
            f"<span class='okr-pct' style='font-size:2.5rem; font-weight:800; color:{color};'>"
            f"{pct:.0f}%</span>"
            f"<br><span style='font-size:0.75rem; color:#94a3b8;'>overall</span></div>",
            unsafe_allow_html=True,
        )
    if row.get("description"):
        st.markdown(
            f"<p style='color:#64748b; margin-top:-8px;'>{row['description']}</p>",
            unsafe_allow_html=True,
        )

    # ── OKR progress bar (HTML-based, color matches status) ──
    clamped_pct = max(0.0, min(pct, 100.0))
    st.markdown(
        f"<div style='background:#e8e0f0; border-radius:10px; height:10px; width:100%; overflow:hidden;'>"
        f"<div style='background:{bar_color}; width:{clamped_pct}%; height:100%; border-radius:10px; "
        f"transition: width 0.4s ease;'></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Detail pills ──
    st.markdown(
        f"<div style='display:flex; gap:8px; flex-wrap:wrap; margin:4px 0 16px 0;'>"
        f"<span style='background:#ede9fe; color:#6d28d9; padding:4px 12px; "
        f"border-radius:10px; font-size:0.8rem; border:1px solid #ddd6fe;'>"
        f"👤 {row.get('owner', '—')}</span>"
        f"<span style='background:#e0f2fe; color:#0369a1; padding:4px 12px; "
        f"border-radius:10px; font-size:0.8rem; border:1px solid #bae6fd;'>"
        f"📅 {row.get('target_date', '—')}</span>"
        f"<span style='background:#fce7f3; color:#be185d; padding:4px 12px; "
        f"border-radius:10px; font-size:0.8rem; border:1px solid #fbcfe8;'>"
        f"🔄 {row.get('last_updated', '—')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Key Results header + add button ──
    kr_header_col, kr_add_col = st.columns([4, 1])
    with kr_header_col:
        st.markdown(f"#### Key Results ({len(krs)})")
    with kr_add_col:
        if st.button("Create Key Result", key=f"add_kr_btn_{okr_id}", type="primary", use_container_width=True):
            add_kr_dialog(okr_id, quarter)

    if krs.empty:
        st.markdown(
            "<div style='text-align:center; padding:40px; background:#faf9ff; "
            "border-radius:10px; border:2px dashed #c7c4e0;'>"
            "<p style='color:#8b8fa3; margin:0;'>No Key Results yet — "
            "click <strong>Create Key Result</strong> to get started.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        for _, kr in krs.iterrows():
            _render_kr_card(kr, history_df, notes_df, quarter)

    # ── OKR notes ──
    okr_notes = data.notes_for(notes_df, "OKR", okr_id)
    with st.expander(f"📝 Objective Notes ({len(okr_notes)})"):
        if okr_notes.empty:
            st.caption("No notes yet.")
        else:
            for _, n in okr_notes.iterrows():
                st.markdown(
                    f"<div style='background:#faf9ff; border:1px solid #e2e0f0; border-radius:10px; "
                    f"padding:10px 14px; margin-bottom:8px;'>"
                    f"<strong>{n['author']}</strong> <span style='color:#94a3b8;'>— {n['timestamp']}</span>"
                    f"<br>{n['text']}</div>",
                    unsafe_allow_html=True,
                )
        _render_note_form("OKR", okr_id)


# ──────────────────────────────────────────────
#  Key Result card
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

    with st.container(border=True):
        # ── Row 1: name + pencil edit + update button ──
        name_col, pencil_col, btn_col = st.columns([4, 0.6, 1])
        with name_col:
            arrow = "↓" if is_decrease else "↑"
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:8px;'>"
                f"<span style='display:inline-flex; align-items:center; justify-content:center; "
                f"background:{color}18; color:{color}; "
                f"width:24px; height:24px; border-radius:10px; "
                f"font-size:0.85rem; flex-shrink:0;'>{arrow}</span>"
                f"<strong style='font-size:1rem;'>{row['name']}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with pencil_col:
            st.markdown('<div class="pencil-edit">', unsafe_allow_html=True)
            if st.button("✎ Edit", key=f"edit_kr_{kr_id}", help="Edit this key result"):
                edit_kr_dialog(row, quarter)
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col:
            st.markdown('<div class="kr-update-btn">', unsafe_allow_html=True)
            if st.button("Update", key=f"upd_btn_{kr_id}", use_container_width=True):
                update_kr_dialog(row, okr_id, quarter)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Row 2: metrics in a 3-col layout ──
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Current", data.format_value(row["current_value"], unit))
        with m2:
            label = "Target ↓" if is_decrease else "Target"
            st.metric(label, data.format_value(row["target_value"], unit))
        with m3:
            st.metric("Achievement", f"{achievement:.0f}%")

        # ── Single progress bar (HTML, color matches status) ──
        clamped_pct = max(0.0, min(achievement, 100.0))
        st.markdown(
            f"<div style='background:#e8e0f0; border-radius:10px; height:8px; width:100%; overflow:hidden;'>"
            f"<div style='background:{bar_color}; width:{clamped_pct}%; height:100%; border-radius:10px; "
            f"transition: width 0.4s ease;'></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

        # ── Subtitle info ──
        parts = [f"👤 {row.get('owner', '—')}"]
        if is_decrease:
            parts.append(
                f"Baseline: {data.format_value(row.get('baseline_value', '—'), unit)} (lower is better)"
            )
        parts.append(f"🔄 {row.get('last_updated', '—')}")
        st.caption("  ·  ".join(parts))

        # ── Trend chart + notes ──
        trend = data.build_kpi_trend(history_df, kr_id)
        kr_notes = data.notes_for(notes_df, "KR", kr_id)

        if not trend.empty:
            _render_modern_chart(trend, row, is_decrease)

        with st.expander(f"📝 Notes ({len(kr_notes)})", expanded=False):
            _render_notes_list(kr_notes)
            _render_note_form("KR", kr_id)


# ──────────────────────────────────────────────
#  Modern chart
# ──────────────────────────────────────────────

def _render_modern_chart(trend: pd.DataFrame, row: pd.Series, is_decrease: bool):
    line_color = "#8b5cf6"
    fill_color = "rgba(139, 92, 246, 0.10)"
    target_color = "#22c55e" if is_decrease else "#ef4444"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend["date"], y=trend["value"],
        fill="tozeroy",
        fillcolor=fill_color,
        line=dict(color=line_color, width=2.5, shape="spline"),
        mode="lines+markers",
        marker=dict(
            size=7, color="#ffffff",
            line=dict(width=2, color=line_color),
        ),
        name="Value",
        hovertemplate="%{x|%b %d, %Y}<br><b>%{y:.1f}</b><extra></extra>",
    ))

    fig.add_hline(
        y=float(row["target_value"]),
        line_dash="dot",
        line_color=target_color,
        line_width=1.5,
        annotation_text="Target",
        annotation_font_color=target_color,
        annotation_font_size=11,
    )

    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#94a3b8", size=10),
            linecolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(226,232,240,0.6)",
            tickfont=dict(color="#94a3b8", size=10),
            linecolor="rgba(0,0,0,0)",
            title=dict(text=row.get("unit", ""), font=dict(color="#94a3b8", size=10)),
        ),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#ffffff",
            font_size=12,
            font_color="#1e293b",
            bordercolor="#e2e8f0",
        ),
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
                f"<strong>{n['author']}</strong> <span style='color:#94a3b8;'>— {n['timestamp']}</span>"
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
