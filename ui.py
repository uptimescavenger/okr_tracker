"""
Streamlit UI components — renders OKR cards with nested Key Results,
notes, trend charts, and update/add forms.
"""

import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
import uuid

import config
import sheets
import data


# ──────────────────────────────────────────────
#  Sidebar
# ──────────────────────────────────────────────

def render_sidebar() -> str:
    """Render sidebar with quarter selector. Returns the selected quarter string."""
    with st.sidebar:
        st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")
        st.divider()

        quarters = config.quarter_list()
        current_q = config.current_quarter()
        default_idx = quarters.index(current_q) if current_q in quarters else len(quarters) - 1

        selected = st.selectbox(
            "Select quarter",
            options=quarters,
            index=default_idx,
        )

        st.divider()
        st.caption("Data syncs from Google Sheets every 2 minutes.")
        if st.button("Refresh now"):
            st.cache_data.clear()
            st.rerun()

    return selected


# ──────────────────────────────────────────────
#  Summary metrics
# ──────────────────────────────────────────────

def render_okr_metrics(stats: dict):
    cols = st.columns(4)
    cols[0].metric("Total OKRs", stats["total"])
    cols[1].metric("Avg Progress", f"{stats['avg_progress']}%")
    cols[2].metric("Completed", stats["completed"])
    cols[3].metric("At Risk (<25%)", stats["at_risk"])


# ──────────────────────────────────────────────
#  OKR card with nested Key Results
# ──────────────────────────────────────────────

def render_okr_card(
    row: pd.Series,
    kpis_df: pd.DataFrame,
    history_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str,
):
    """Render a single OKR with its Key Results nested inside."""
    okr_id = str(row["id"])
    pct = data.okr_progress_from_krs(okr_id, kpis_df)
    color = data.progress_color(pct)
    krs = data.krs_for_okr(okr_id, kpis_df)

    with st.container(border=True):
        # ── OKR header ──
        col_title, col_progress = st.columns([3, 1])
        with col_title:
            st.subheader(row["title"])
        with col_progress:
            st.markdown(
                f"<h2 style='color:{color}; text-align:right'>{pct:.0f}%</h2>",
                unsafe_allow_html=True,
            )

        st.progress(min(pct / 100, 1.0))

        detail_cols = st.columns(3)
        detail_cols[0].markdown(f"**Owner:** {row.get('owner', '—')}")
        detail_cols[1].markdown(f"**Target date:** {row.get('target_date', '—')}")
        detail_cols[2].markdown(f"**Updated:** {row.get('last_updated', '—')}")

        if row.get("description"):
            st.markdown(f"_{row['description']}_")

        # ── OKR-level notes ──
        okr_notes = data.notes_for(notes_df, "OKR", okr_id)
        with st.expander(f"OKR Notes ({len(okr_notes)})"):
            if okr_notes.empty:
                st.info("No notes yet.")
            else:
                for _, n in okr_notes.iterrows():
                    st.markdown(f"**{n['author']}** — {n['timestamp']}  \n{n['text']}")
            # Add note inline
            _render_note_form("OKR", okr_id)

        # ── Key Results ──
        st.markdown("**Key Results**")
        if krs.empty:
            st.caption("No Key Results yet — add one below.")
        else:
            for _, kr in krs.iterrows():
                _render_kr_card(kr, history_df, notes_df, quarter)

        # ── Add Key Result ──
        _render_add_kr_form(okr_id, quarter)


def _render_kr_card(
    row: pd.Series,
    history_df: pd.DataFrame,
    notes_df: pd.DataFrame,
    quarter: str,
):
    """Render a single Key Result inside its parent OKR."""
    achievement = data.kpi_achievement(row)
    color = data.progress_color(achievement)
    kr_id = str(row["id"])
    okr_id = str(row["okr_id"])
    direction = str(row.get("direction", "increase")).lower()
    is_decrease = direction == "decrease"

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            label = "▼ " if is_decrease else ""
            st.markdown(f"**{label}{row['name']}**")
        with c2:
            st.metric("Current", f"{row['current_value']} {row.get('unit', '')}")
        with c3:
            target_label = "Target (↓)" if is_decrease else "Target"
            st.metric(target_label, f"{row['target_value']} {row.get('unit', '')}")
        with c4:
            st.markdown(
                f"<span style='color:{color}; font-weight:bold; font-size:1.2em'>"
                f"{achievement}%</span>",
                unsafe_allow_html=True,
            )

        clamped = max(0.0, min(achievement / 100, 1.0))
        st.progress(clamped)
        if is_decrease:
            st.caption(
                f"Baseline: {row.get('baseline_value', '—')} {row.get('unit', '')} → "
                f"Target: {row['target_value']} {row.get('unit', '')} (lower is better)"
            )
        st.caption(
            f"Owner: {row.get('owner', '—')} | Updated: {row.get('last_updated', '—')}"
        )

        # Trend chart
        trend = data.build_kpi_trend(history_df, kr_id)
        if not trend.empty:
            fig = px.line(
                trend, x="date", y="value",
                title=f"{row['name']} trend",
                markers=True,
            )
            fig.update_layout(
                height=220,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="",
                yaxis_title=row.get("unit", ""),
            )
            fig.add_hline(
                y=float(row["target_value"]),
                line_dash="dash",
                line_color="green" if is_decrease else "red",
                annotation_text="Target (get below)" if is_decrease else "Target",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Notes
        kr_notes = data.notes_for(notes_df, "KR", kr_id)
        with st.expander(f"Notes ({len(kr_notes)})"):
            if kr_notes.empty:
                st.info("No notes yet.")
            else:
                for _, n in kr_notes.iterrows():
                    st.markdown(f"**{n['author']}** — {n['timestamp']}  \n{n['text']}")
            _render_note_form("KR", kr_id)

        # Update value
        _render_kr_update_form(row, okr_id, quarter)


def _render_kr_update_form(row: pd.Series, okr_id: str, quarter: str):
    key_prefix = f"kr_update_{row['id']}"
    with st.popover("Update value"):
        new_value = st.number_input(
            f"New value ({row.get('unit', '')})",
            value=float(row["current_value"]),
            key=f"{key_prefix}_val",
        )
        if st.button("Save", key=f"{key_prefix}_save"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                sheets.update_kpi_value(
                    quarter, str(row["id"]), okr_id, new_value, now
                )
                st.success("Saved! OKR progress updated.")
                st.rerun()
            except Exception as exc:
                st.error(f"Error saving: {exc}")


def _render_note_form(parent_type: str, parent_id: str):
    """Inline form to add a note inside an expander."""
    key_prefix = f"note_{parent_type}_{parent_id}"
    author = st.text_input("Your name", key=f"{key_prefix}_author")
    text = st.text_area("Note", key=f"{key_prefix}_text")
    if st.button("Add note", key=f"{key_prefix}_btn"):
        if author.strip() and text.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheets.add_note(parent_type, parent_id, author.strip(), text.strip(), now)
            st.success("Note added.")
            st.rerun()
        else:
            st.warning("Please enter both your name and a note.")


def _render_add_kr_form(okr_id: str, quarter: str):
    """Popover form to add a new Key Result to an OKR."""
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

        if st.button("Create", key=f"{key_prefix}_btn"):
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


# ──────────────────────────────────────────────
#  Add new OKR form
# ──────────────────────────────────────────────

def render_add_okr_form(quarter: str):
    st.divider()
    with st.form("add_okr_form"):
        st.subheader("New OKR")
        title = st.text_input("Objective title")
        description = st.text_area("Description")
        owner = st.text_input("Owner")
        target_date = st.date_input("Target date")
        submitted = st.form_submit_button("Create OKR")
        if submitted and title.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_id = str(uuid.uuid4())[:8]
            sheets.add_okr(quarter, [
                new_id, title.strip(), description.strip(),
                owner.strip(), str(target_date), 0, now,
            ])
            st.success(f"OKR '{title}' created. Now add Key Results to it above.")
            st.rerun()
