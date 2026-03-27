"""
Data processing helpers — aggregation, formatting, trend computation.

Keeps pandas logic out of the UI layer.
"""

import pandas as pd
import config


def kpi_achievement(row: pd.Series) -> float:
    """Calculate Key Result achievement as a percentage of target.

    For 'increase' KRs: achievement = (current - baseline) / (target - baseline).
    For 'decrease' KRs: achievement = (baseline - current) / (baseline - target).
    Both are expressed as 0-100+ percentages.
    """
    target = float(row.get("target_value", 0))
    current = float(row.get("current_value", 0))
    baseline = float(row.get("baseline_value", 0))
    direction = str(row.get("direction", "increase")).lower()

    if direction == "decrease":
        span = baseline - target  # e.g. 600 - 500 = 100
        if span == 0:
            return 0.0
        progress = baseline - current  # e.g. 600 - 550 = 50
        return round((progress / span) * 100, 1)
    else:
        span = target - baseline  # e.g. 100 - 0 = 100
        if span == 0:
            return 0.0
        progress = current - baseline
        return round((progress / span) * 100, 1)


def okr_progress_from_krs(okr_id: str, kpis_df: pd.DataFrame) -> float:
    """Compute an OKR's progress as the average achievement of its Key Results."""
    if kpis_df.empty:
        return 0.0
    krs = kpis_df[kpis_df["okr_id"] == str(okr_id)]
    if krs.empty:
        return 0.0
    achievements = krs.apply(kpi_achievement, axis=1)
    return round(achievements.mean(), 1)


def krs_for_okr(okr_id: str, kpis_df: pd.DataFrame) -> pd.DataFrame:
    """Return all Key Results belonging to an OKR."""
    if kpis_df.empty:
        return kpis_df
    return kpis_df[kpis_df["okr_id"] == str(okr_id)]


def okr_summary_stats(okrs_df: pd.DataFrame, kpis_df: pd.DataFrame) -> dict:
    """Return high-level stats with progress computed from Key Results."""
    if okrs_df.empty:
        return {"total": 0, "avg_progress": 0, "completed": 0, "at_risk": 0}
    progresses = okrs_df["id"].apply(lambda oid: okr_progress_from_krs(oid, kpis_df))
    return {
        "total": len(okrs_df),
        "avg_progress": round(progresses.mean(), 1),
        "completed": int((progresses >= 100).sum()),
        "at_risk": int((progresses < 25).sum()),
    }


def build_kpi_trend(history_df: pd.DataFrame, kpi_id: str) -> pd.DataFrame:
    """Filter history to a single KPI and sort by date for charting."""
    if history_df.empty:
        return history_df
    subset = history_df[history_df["kpi_id"] == str(kpi_id)].copy()
    if subset.empty:
        return subset
    subset["date"] = pd.to_datetime(subset["date"], errors="coerce")
    subset = subset.dropna(subset=["date"]).sort_values("date")
    return subset


def notes_for(notes_df: pd.DataFrame, parent_type: str, parent_id: str) -> pd.DataFrame:
    """Return notes filtered to a specific OKR or KPI, newest first."""
    if notes_df.empty:
        return notes_df
    mask = (notes_df["parent_type"] == parent_type) & (
        notes_df["parent_id"] == str(parent_id)
    )
    subset = notes_df[mask].copy()
    subset["timestamp"] = pd.to_datetime(subset["timestamp"], errors="coerce")
    return subset.sort_values("timestamp", ascending=False)


def progress_color(pct: float) -> str:
    """Return a CSS-friendly colour based on progress percentage."""
    if pct >= 75:
        return "#22c55e"  # green
    if pct >= 40:
        return "#f59e0b"  # amber
    return "#ef4444"      # red
