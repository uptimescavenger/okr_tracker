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

# ──────────────────────────────────────────────
#  Custom CSS
# ──────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    /* ── Global ── */
    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #fff1f2 100%) !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 22px;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
    }
    [data-testid="stMetric"] label {
        color: #6366f1 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #1e293b !important;
    }

    /* ── Progress bars ── */
    [data-testid="stProgress"] > div > div {
        border-radius: 10px;
        height: 8px !important;
        background: linear-gradient(90deg, #6366f1, #a855f7) !important;
    }
    [data-testid="stProgress"] > div {
        background-color: #e8e0f0 !important;
        border-radius: 10px;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] button {
        border-radius: 10px 10px 0 0 !important;
        font-weight: 600 !important;
        padding: 10px 22px !important;
        font-size: 0.88rem !important;
        transition: all 0.2s ease;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border-bottom: none !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
    }
    [data-testid="stTabs"] button[aria-selected="false"] {
        color: #64748b !important;
        background: #f1f0fb !important;
    }
    [data-testid="stTabs"] button[aria-selected="false"]:hover {
        background: #e8e5f5 !important;
        color: #4338ca !important;
    }

    /* ── Containers / cards ── */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        border-color: #e2e8f0 !important;
        background: #ffffff !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.05);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f7ff 0%, #f3f0ff 50%, #faf5ff 100%) !important;
        border-right: 1px solid #e2e0f0;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        border: 1px solid #e2e0f0 !important;
        border-radius: 12px !important;
        background: #faf9ff !important;
    }

    /* ── Dialog ── */
    [data-testid="stDialog"] {
        border-radius: 18px !important;
    }
    [data-testid="stDialog"] [data-testid="stVerticalBlock"] {
        background: #ffffff !important;
    }

    /* ── Note input borders ── */
    [data-testid="stTextArea"] textarea,
    [data-testid="stTextInput"] input {
        border: 2px solid #d4d0e8 !important;
        border-radius: 10px !important;
        background: #ffffff !important;
    }
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stTextInput"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
    }

    /* ── Number inputs ── */
    [data-testid="stNumberInput"] input {
        border: 2px solid #d4d0e8 !important;
        border-radius: 10px !important;
    }
    [data-testid="stNumberInput"] input:focus {
        border-color: #6366f1 !important;
    }

    /* ── New Objective button in sidebar ── */
    [data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 12px 20px !important;
        box-shadow: 0 3px 12px rgba(99, 102, 241, 0.3);
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        box-shadow: 0 5px 20px rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
    }

    /* ── General primary buttons ── */
    button[kind="primary"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] > div > div {
        border: 2px solid #d4d0e8 !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  Add OKR dialog (modal popup)
# ──────────────────────────────────────────────

@st.dialog("Create New Objective", width="large")
def add_okr_dialog(quarter: str):
    st.markdown(
        "<p style='color:#64748b; margin-bottom:16px;'>Add a new objective to track for this quarter.</p>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Objective title")
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
        if st.button("Create Objective", type="primary", use_container_width=True):
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
#  Add Key Result dialog (modal popup)
# ──────────────────────────────────────────────

@st.dialog("Add Key Result", width="large")
def add_kr_dialog(okr_id: str, quarter: str):
    st.markdown(
        "<p style='color:#64748b; margin-bottom:16px;'>Define a measurable key result for this objective.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Key Result name")
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
        st.markdown(
            "<p style='color:#8b5cf6; font-size:0.85rem; font-weight:600;'>"
            "Lower is better — tracks how much you've reduced from baseline.</p>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            baseline_value = st.number_input(
                "Starting value (baseline)", value=0.0,
                help="The value you're starting from (e.g. $600)",
            )
        with c2:
            current_value = st.number_input(
                "Current value", value=baseline_value,
            )
        with c3:
            target_value = st.number_input(
                "Target value (lower)", value=0.0,
                help="The value you want to reach (e.g. $500)",
            )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            baseline_value = st.number_input(
                "Starting value (baseline)", value=0.0,
            )
        with c2:
            current_value = st.number_input(
                "Current value", value=0.0,
            )
        with c3:
            target_value = st.number_input(
                "Target value", value=100.0,
            )

    st.markdown("")
    btn_c1, btn_c2, btn_c3 = st.columns([2, 1, 1])
    with btn_c2:
        if st.button("Cancel", use_container_width=True, key="kr_cancel"):
            st.rerun()
    with btn_c3:
        if st.button("Create Key Result", type="primary", use_container_width=True, key="kr_create"):
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
        if st.button("Save Update", type="primary", use_container_width=True, key="upd_save"):
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
    """Render sidebar with quarter selector and new OKR button."""
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

        # New OKR button — white "+" via HTML
        if st.button(
            "\u2795  New Objective",
            use_container_width=True,
            type="primary",
        ):
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
    cols = st.columns(4)
    cols[0].metric("Objectives", stats["total"])
    cols[1].metric("Avg Progress", f"{stats['avg_progress']}%")
    cols[2].metric("Completed", stats["completed"])
    cols[3].metric("At Risk", stats["at_risk"])


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
            "<div style='text-align:center; padding:80px 20px; background:#ffffff; "
            "border-radius:16px; border:1px dashed #c7c4e0;'>"
            "<p style='font-size:3rem; margin-bottom:8px;'>🎯</p>"
            "<h3 style='color:#475569;'>No objectives yet</h3>"
            "<p style='color:#8b8fa3;'>Click <strong>New Objective</strong> "
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
    krs = data.krs_for_okr(okr_id, kpis_df)

    # ── Header row ──
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {row['title']}")
        if row.get("description"):
            st.markdown(
                f"<p style='color:#64748b; margin-top:-8px;'>{row['description']}</p>",
                unsafe_allow_html=True,
            )
    with col2:
        st.markdown(
            f"<div style='text-align:right; padding:4px 0;'>"
            f"<span style='font-size:2.8rem; font-weight:800; color:{color};'>"
            f"{pct:.0f}%</span></div>",
            unsafe_allow_html=True,
        )

    st.progress(max(0.0, min(pct / 100, 1.0)))

    # ── Detail pills ──
    st.markdown(
        f"<div style='display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 20px 0;'>"
        f"<span style='background:#ede9fe; color:#6d28d9; padding:5px 14px; "
        f"border-radius:20px; font-size:0.82rem; border:1px solid #ddd6fe;'>"
        f"👤 {row.get('owner', '—')}</span>"
        f"<span style='background:#e0f2fe; color:#0369a1; padding:5px 14px; "
        f"border-radius:20px; font-size:0.82rem; border:1px solid #bae6fd;'>"
        f"📅 {row.get('target_date', '—')}</span>"
        f"<span style='background:#fce7f3; color:#be185d; padding:5px 14px; "
        f"border-radius:20px; font-size:0.82rem; border:1px solid #fbcfe8;'>"
        f"🔄 {row.get('last_updated', '—')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Key Results header + add button ──
    kr_header_col, kr_add_col = st.columns([5, 1])
    with kr_header_col:
        st.markdown(f"#### Key Results ({len(krs)})")
    with kr_add_col:
        if st.button("+ Add Key Result", key=f"add_kr_btn_{okr_id}", type="primary", use_container_width=True):
            # Store the okr_id in session state so the dialog knows which OKR
            st.session_state["_add_kr_okr_id"] = okr_id
            st.session_state["_add_kr_quarter"] = quarter
            add_kr_dialog(okr_id, quarter)

    if krs.empty:
        st.markdown(
            "<div style='text-align:center; padding:40px; background:#faf9ff; "
            "border-radius:14px; border:2px dashed #c7c4e0;'>"
            "<p style='color:#8b8fa3; margin:0;'>No Key Results yet — "
            "click <strong>+ Add Key Result</strong> to get started.</p></div>",
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
    kr_id = str(row["id"])
    okr_id = str(row["okr_id"])
    direction = str(row.get("direction", "increase")).lower()
    is_decrease = direction == "decrease"

    with st.container(border=True):
        # ── Top row: name, metrics, achievement, update ──
        c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 0.8, 0.8])
        with c1:
            arrow = "↓" if is_decrease else "↑"
            st.markdown(
                f"<span style='display:inline-block; background:{color}18; color:{color}; "
                f"width:26px; height:26px; border-radius:8px; text-align:center; "
                f"line-height:26px; font-size:0.85rem; margin-right:8px;'>{arrow}</span>"
                f"<strong style='font-size:1rem;'>{row['name']}</strong>",
                unsafe_allow_html=True,
            )
            st.caption(f"👤 {row.get('owner', '—')}  ·  🔄 {row.get('last_updated', '—')}")
        with c2:
            st.metric("Current", data.format_value(row['current_value'], row.get('unit', '')))
        with c3:
            label = "Target ↓" if is_decrease else "Target"
            st.metric(label, data.format_value(row['target_value'], row.get('unit', '')))
        with c4:
            st.markdown(
                f"<div style='text-align:center; padding-top:6px;'>"
                f"<span style='font-size:1.5rem; font-weight:800; color:{color};'>"
                f"{achievement:.0f}%</span></div>",
                unsafe_allow_html=True,
            )
        with c5:
            if st.button("✏️ Update", key=f"upd_btn_{kr_id}", use_container_width=True):
                update_kr_dialog(row, okr_id, quarter)

        # ── Progress bar ──
        clamped = max(0.0, min(achievement / 100, 1.0))
        st.progress(clamped)

        if is_decrease:
            unit = row.get('unit', '')
            st.caption(
                f"Baseline: {data.format_value(row.get('baseline_value', '—'), unit)} → "
                f"Target: {data.format_value(row['target_value'], unit)} (lower is better)"
            )

        # ── Trend chart + notes ──
        trend = data.build_kpi_trend(history_df, kr_id)
        kr_notes = data.notes_for(notes_df, "KR", kr_id)

        if not trend.empty:
            chart_col, notes_col = st.columns([3, 2])
            with chart_col:
                _render_modern_chart(trend, row, is_decrease)
            with notes_col:
                with st.expander(f"📝 Notes ({len(kr_notes)})", expanded=False):
                    _render_notes_list(kr_notes)
                    _render_note_form("KR", kr_id)
        else:
            with st.expander(f"📝 Notes ({len(kr_notes)})", expanded=False):
                _render_notes_list(kr_notes)
                _render_note_form("KR", kr_id)


# ──────────────────────────────────────────────
#  Modern chart
# ──────────────────────────────────────────────

def _render_modern_chart(trend: pd.DataFrame, row: pd.Series, is_decrease: bool):
    """Area chart with gradient fill, modern styling."""
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
            size=8, color="#ffffff",
            line=dict(width=2.5, color=line_color),
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
        "<div style='border:2px solid #d4d0e8; border-radius:12px; padding:14px; margin-top:8px; background:#ffffff;'>",
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
