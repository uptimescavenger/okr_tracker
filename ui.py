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
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* Progress bars */
    [data-testid="stProgress"] > div > div {
        border-radius: 10px;
        height: 8px !important;
    }
    [data-testid="stProgress"] > div {
        background-color: #334155 !important;
        border-radius: 10px;
    }

    /* Tabs styling */
    [data-testid="stTabs"] button {
        border-radius: 8px 8px 0 0 !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
    }

    /* Containers */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border-color: #334155 !important;
        background: #1e293b !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1a1f3d 100%) !important;
    }
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
    }

    /* Popover buttons */
    [data-testid="stPopoverButton"] button {
        border-radius: 8px !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        border-color: #334155 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  Sidebar
# ──────────────────────────────────────────────

def render_sidebar(quarter_ref: list):
    """Render sidebar with quarter selector and Add OKR form."""
    with st.sidebar:
        st.markdown(
            "<h1 style='text-align:center; "
            "background: linear-gradient(135deg, #6366f1, #a78bfa, #ec4899); "
            "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
            "font-size: 1.6rem;'>"
            "OKR Tracker</h1>",
            unsafe_allow_html=True,
        )
        st.caption("Track objectives & key results")
        st.divider()

        quarters = config.quarter_list()
        current_q = config.current_quarter()
        default_idx = quarters.index(current_q) if current_q in quarters else len(quarters) - 1

        selected = st.selectbox(
            "Quarter",
            options=quarters,
            index=default_idx,
        )
        quarter_ref.append(selected)

        st.divider()

        # ── Add OKR in sidebar ──
        st.markdown("**Create New Objective**")
        _render_sidebar_add_okr(selected)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            st.caption("Auto-syncs every 2 min")


def _render_sidebar_add_okr(quarter: str):
    with st.form("sidebar_add_okr", clear_on_submit=True):
        title = st.text_input("Objective title")
        description = st.text_area("Description", height=80)
        owner = st.text_input("Owner")
        target_date = st.date_input("Target date")
        submitted = st.form_submit_button("Create OKR", use_container_width=True)
        if submitted and title.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_id = str(uuid.uuid4())[:8]
            sheets.add_okr(quarter, [
                new_id, title.strip(), description.strip(),
                owner.strip(), str(target_date), 0, now,
            ])
            st.success(f"Created!")
            st.rerun()


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
#  OKR tabs (one tab per OKR to reduce scrolling)
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
            "<div style='text-align:center; padding:60px 20px; color:#64748b;'>"
            "<h3>No objectives yet</h3>"
            "<p>Create your first OKR using the sidebar.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # Create tabs — one per OKR
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

    # ── OKR header ──
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {row['title']}")
        if row.get("description"):
            st.markdown(f"*{row['description']}*")
    with col2:
        st.markdown(
            f"<div style='text-align:right; padding:8px;'>"
            f"<span style='font-size:2.5rem; font-weight:800; "
            f"background: linear-gradient(135deg, {color}, {color}aa); "
            f"-webkit-background-clip: text; -webkit-text-fill-color: transparent;'>"
            f"{pct:.0f}%</span></div>",
            unsafe_allow_html=True,
        )

    st.progress(max(0.0, min(pct / 100, 1.0)))

    # Detail chips
    st.markdown(
        f"<div style='display:flex; gap:16px; flex-wrap:wrap; margin:4px 0 16px 0;'>"
        f"<span style='background:#334155; padding:4px 12px; border-radius:20px; font-size:0.85rem;'>"
        f"👤 {row.get('owner', '—')}</span>"
        f"<span style='background:#334155; padding:4px 12px; border-radius:20px; font-size:0.85rem;'>"
        f"📅 {row.get('target_date', '—')}</span>"
        f"<span style='background:#334155; padding:4px 12px; border-radius:20px; font-size:0.85rem;'>"
        f"🔄 {row.get('last_updated', '—')}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Key Results ──
    kr_header_col, kr_add_col = st.columns([4, 1])
    with kr_header_col:
        st.markdown(f"**Key Results** ({len(krs)})")
    with kr_add_col:
        _render_add_kr_form(okr_id, quarter)

    if krs.empty:
        st.info("No Key Results yet — click **+ Add Key Result** to get started.")
    else:
        for _, kr in krs.iterrows():
            _render_kr_card(kr, history_df, notes_df, quarter)

    # ── OKR-level notes ──
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
        # Row 1: name, values, achievement, update button
        c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 0.8, 0.8])
        with c1:
            arrow = "↓" if is_decrease else "↑"
            st.markdown(
                f"<span style='color:{color}; font-size:1.1rem; margin-right:6px;'>{arrow}</span>"
                f"<strong>{row['name']}</strong>",
                unsafe_allow_html=True,
            )
            owner_text = row.get('owner', '—')
            updated_text = row.get('last_updated', '—')
            st.caption(f"👤 {owner_text}  |  🔄 {updated_text}")
        with c2:
            st.metric("Current", data.format_value(row['current_value'], row.get('unit', '')))
        with c3:
            target_label = "Target ↓" if is_decrease else "Target"
            st.metric(target_label, data.format_value(row['target_value'], row.get('unit', '')))
        with c4:
            st.markdown(
                f"<div style='text-align:center; padding-top:8px;'>"
                f"<span style='color:{color}; font-weight:800; font-size:1.4rem;'>"
                f"{achievement:.0f}%</span></div>",
                unsafe_allow_html=True,
            )
        with c5:
            _render_kr_update_form(row, okr_id, quarter)

        # Progress bar
        clamped = max(0.0, min(achievement / 100, 1.0))
        st.progress(clamped)

        if is_decrease:
            unit = row.get('unit', '')
            st.caption(
                f"Baseline: {data.format_value(row.get('baseline_value', '—'), unit)} → "
                f"Target: {data.format_value(row['target_value'], unit)} (lower is better)"
            )

        # Trend chart + notes side by side
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


def _render_modern_chart(trend: pd.DataFrame, row: pd.Series, is_decrease: bool):
    """Render a modern area chart with gradient fill."""
    color_main = "#8b5cf6"
    color_fill = "rgba(139, 92, 246, 0.15)"
    target_color = "#22c55e" if is_decrease else "#f43f5e"

    fig = go.Figure()

    # Area fill
    fig.add_trace(go.Scatter(
        x=trend["date"], y=trend["value"],
        fill="tozeroy",
        fillcolor=color_fill,
        line=dict(color=color_main, width=3, shape="spline"),
        mode="lines+markers",
        marker=dict(size=8, color=color_main, line=dict(width=2, color="#0f172a")),
        name="Value",
        hovertemplate="%{x|%b %d}<br>%{y:.1f}<extra></extra>",
    ))

    # Target line
    fig.add_hline(
        y=float(row["target_value"]),
        line_dash="dot",
        line_color=target_color,
        line_width=2,
        annotation_text="Target",
        annotation_font_color=target_color,
        annotation_font_size=11,
    )

    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="#64748b", size=10),
            linecolor="rgba(0,0,0,0)",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(71,85,105,0.3)",
            tickfont=dict(color="#64748b", size=10),
            linecolor="rgba(0,0,0,0)",
            title=dict(text=row.get("unit", ""), font=dict(color="#64748b", size=10)),
        ),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=12,
            font_color="#e2e8f0",
            bordercolor="#6366f1",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ──────────────────────────────────────────────
#  Update / Note / Add KR forms
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
        if st.button("Save", key=f"{key_prefix}_save", use_container_width=True):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                sheets.update_kpi_value(
                    quarter, str(row["id"]), okr_id, new_value, now
                )
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

        if st.button("Create", key=f"{key_prefix}_btn", use_container_width=True):
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
