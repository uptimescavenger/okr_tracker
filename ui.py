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
    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    [data-testid="stMetric"] label {
        color: #64748b !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    /* ── Progress bars ── */
    [data-testid="stProgress"] > div > div {
        border-radius: 10px;
        height: 6px !important;
    }
    [data-testid="stProgress"] > div {
        background-color: #e2e8f0 !important;
        border-radius: 10px;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] button {
        border-radius: 8px 8px 0 0 !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #818cf8) !important;
        color: white !important;
        border-bottom: none !important;
    }
    [data-testid="stTabs"] button[aria-selected="false"] {
        color: #64748b !important;
    }

    /* ── Containers / cards ── */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border-color: #e2e8f0 !important;
        background: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border-right: 1px solid #e2e8f0;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        border-color: #e2e8f0 !important;
        border-radius: 10px !important;
        background: #fafbfc;
    }

    /* ── Popover buttons ── */
    [data-testid="stPopoverButton"] button {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* ── Dialog ── */
    [data-testid="stDialog"] {
        border-radius: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  Add OKR dialog (modal popup)
# ──────────────────────────────────────────────

@st.dialog("Create New Objective", width="large")
def add_okr_dialog(quarter: str):
    st.markdown("Add a new objective to track for this quarter.")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Objective title")
        owner = st.text_input("Owner")
    with col2:
        target_date = st.date_input("Target date")
    description = st.text_area("Description", height=100)

    st.markdown("")  # spacer
    c1, c2, c3 = st.columns([2, 1, 1])
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with c3:
        if st.button("Create OKR", type="primary", use_container_width=True):
            if title.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_id = str(uuid.uuid4())[:8]
                sheets.add_okr(quarter, [
                    new_id, title.strip(), description.strip(),
                    owner.strip(), str(target_date), 0, now,
                ])
                st.rerun()
            else:
                st.warning("Please enter an objective title.")


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
            "<p style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:2px;'>"
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

        # New OKR button launches the dialog
        if st.button("➕  New Objective", use_container_width=True, type="primary"):
            add_okr_dialog(selected)

        st.divider()
        if st.button("🔄  Refresh Data", use_container_width=True):
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
            "<div style='text-align:center; padding:80px 20px;'>"
            "<p style='font-size:3rem; margin-bottom:8px;'>🎯</p>"
            "<h3 style='color:#475569;'>No objectives yet</h3>"
            "<p style='color:#94a3b8;'>Click <strong>New Objective</strong> "
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
        f"<span style='background:#f1f5f9; color:#475569; padding:5px 14px; "
        f"border-radius:20px; font-size:0.82rem; border:1px solid #e2e8f0;'>"
        f"👤 {row.get('owner', '—')}</span>"
        f"<span style='background:#f1f5f9; color:#475569; padding:5px 14px; "
        f"border-radius:20px; font-size:0.82rem; border:1px solid #e2e8f0;'>"
        f"📅 {row.get('target_date', '—')}</span>"
        f"<span style='background:#f1f5f9; color:#475569; padding:5px 14px; "
        f"border-radius:20px; font-size:0.82rem; border:1px solid #e2e8f0;'>"
        f"🔄 {row.get('last_updated', '—')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Key Results header + add button ──
    kr_header_col, kr_add_col = st.columns([5, 1])
    with kr_header_col:
        st.markdown(f"#### Key Results ({len(krs)})")
    with kr_add_col:
        _render_add_kr_form(okr_id, quarter)

    if krs.empty:
        st.markdown(
            "<div style='text-align:center; padding:40px; background:#f8fafc; "
            "border-radius:12px; border:1px dashed #cbd5e1;'>"
            "<p style='color:#94a3b8; margin:0;'>No Key Results yet — "
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
                st.markdown(f"**{n['author']}** — {n['timestamp']}  \n{n['text']}")
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
                f"width:24px; height:24px; border-radius:6px; text-align:center; "
                f"line-height:24px; font-size:0.85rem; margin-right:8px;'>{arrow}</span>"
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
            _render_kr_update_form(row, okr_id, quarter)

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
    line_color = "#6366f1"
    fill_color = "rgba(99, 102, 241, 0.08)"
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
#  Forms: update KR, add note, add KR
# ──────────────────────────────────────────────

def _render_kr_update_form(row: pd.Series, okr_id: str, quarter: str):
    key_prefix = f"kr_update_{row['id']}"
    with st.popover("✏️ Update"):
        new_value = st.number_input(
            f"New value ({row.get('unit', '')})",
            value=float(row["current_value"]),
            key=f"{key_prefix}_val",
        )
        note_author = st.text_input("Your name", key=f"{key_prefix}_author")
        note_text = st.text_area("Add a note (optional)", key=f"{key_prefix}_note", height=80)
        if st.button("Save", key=f"{key_prefix}_save", type="primary", use_container_width=True):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                sheets.update_kpi_value(quarter, str(row["id"]), okr_id, new_value, now)
                if note_text.strip() and note_author.strip():
                    sheets.add_note("KR", str(row["id"]), note_author.strip(), note_text.strip(), now)
                st.success("Saved!")
                st.rerun()
            except Exception as exc:
                st.error(f"Error: {exc}")


def _render_notes_list(notes_df: pd.DataFrame):
    if notes_df.empty:
        st.caption("No notes yet.")
    else:
        for _, n in notes_df.iterrows():
            st.markdown(f"**{n['author']}** — {n['timestamp']}  \n{n['text']}")


def _render_note_form(parent_type: str, parent_id: str):
    key_prefix = f"note_{parent_type}_{parent_id}"
    author = st.text_input("Your name", key=f"{key_prefix}_author")
    text = st.text_area("Note", key=f"{key_prefix}_text", height=60)
    if st.button("Add note", key=f"{key_prefix}_btn"):
        if author.strip() and text.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheets.add_note(parent_type, parent_id, author.strip(), text.strip(), now)
            st.success("Note added.")
            st.rerun()
        else:
            st.warning("Enter both name and note.")


def _render_add_kr_form(okr_id: str, quarter: str):
    key_prefix = f"add_kr_{okr_id}"
    with st.popover("+ Add Key Result"):
        name = st.text_input("Key Result name", key=f"{key_prefix}_name")
        owner = st.text_input("Owner", key=f"{key_prefix}_owner")

        direction = st.radio(
            "Direction",
            options=["increase", "decrease"],
            horizontal=True,
            key=f"{key_prefix}_dir",
            help="Choose 'decrease' for metrics you want to reduce (e.g. cost, churn)",
        )

        if direction == "decrease":
            baseline_value = st.number_input(
                "Starting value (baseline)", value=0.0, key=f"{key_prefix}_base",
                help="The value you're starting from (e.g. $600)",
            )
            current_value = st.number_input(
                "Current value", value=baseline_value, key=f"{key_prefix}_cur",
            )
            target_value = st.number_input(
                "Target value (lower)", value=0.0, key=f"{key_prefix}_tgt",
                help="The value you want to reach (e.g. $500)",
            )
        else:
            baseline_value = st.number_input(
                "Starting value (baseline)", value=0.0, key=f"{key_prefix}_base",
            )
            current_value = st.number_input(
                "Current value", value=0.0, key=f"{key_prefix}_cur",
            )
            target_value = st.number_input(
                "Target value", value=100.0, key=f"{key_prefix}_tgt",
            )

        unit = st.text_input("Unit (e.g. %, $, users)", key=f"{key_prefix}_unit")

        if st.button("Create", key=f"{key_prefix}_btn", type="primary", use_container_width=True):
            if name.strip():
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_id = str(uuid.uuid4())[:8]
                sheets.add_kpi(quarter, [
                    new_id, okr_id, name.strip(), owner.strip(),
                    current_value, target_value, baseline_value,
                    direction, unit.strip(), now,
                ])
                st.success(f"Key Result '{name}' added.")
                st.rerun()
            else:
                st.warning("Please enter a name.")
