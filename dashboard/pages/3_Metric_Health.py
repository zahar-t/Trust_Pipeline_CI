"""Metric Health page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.charts import line_chart
from components.db import snapshot_query, snapshot_store_available
from design_system import apply_global_styles, ACCENTS, editorial_table, hero_banner, insight_card, section_header, sidebar_brand, spacer, top_nav

apply_global_styles()
sidebar_brand()
top_nav("Metric Health", "Search snapshots...")

hero_banner(
    title="Metric Health",
    subtitle="Semantic-CI snapshot drift monitoring for metric definition changes over time",
    badge_text="Quality Assurance",
    page="metric_health",
)

spacer(28)

def _normalize_uploaded_snapshot_csv(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame | None:
    """Normalize uploaded CSV into a snapshot-like frame used by the page."""
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Could not parse CSV: {exc}")
        return None

    if df.empty:
        st.warning("Uploaded CSV is empty.")
        return None

    # Normalize names so we can accept common variants.
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    rename_candidates = {
        "metric_name": ["metric", "name"],
        "metric_value": ["value"],
        "period": ["metric_period"],
        "grain": ["time_grain"],
        "dimension_name": ["dimension", "dim_name"],
        "dimension_value": ["dim_value"],
        "git_branch": ["branch"],
        "run_id": ["snapshot_run_id"],
        "snapshot_time": ["timestamp", "created_at", "run_created_at", "run_timestamp"],
    }
    for target, aliases in rename_candidates.items():
        if target in df.columns:
            continue
        for alias in aliases:
            if alias in df.columns:
                df = df.rename(columns={alias: target})
                break

    required = {"metric_name", "metric_value"}
    missing = sorted(required - set(df.columns))
    if missing:
        st.error(f"CSV is missing required columns: {', '.join(missing)}")
        return None

    df["metric_value"] = pd.to_numeric(df["metric_value"], errors="coerce")
    df = df.dropna(subset=["metric_name", "metric_value"])
    if df.empty:
        st.error("CSV rows do not contain valid metric values.")
        return None

    for col, default in [
        ("period", ""),
        ("grain", ""),
        ("dimension_name", ""),
        ("dimension_value", ""),
        ("git_branch", "uploaded_csv"),
    ]:
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default).astype(str)

    if "snapshot_time" in df.columns:
        ts = pd.to_datetime(df["snapshot_time"], errors="coerce", utc=True).dt.tz_convert(None)
        fallback_ts = pd.Timestamp("1970-01-01") + pd.to_timedelta(df.index, unit="s")
        df["_snapshot_sort"] = ts.fillna(fallback_ts)
        df["_snapshot_label"] = ts.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("uploaded_row")
    elif "run_id" in df.columns:
        run_order = {rid: idx for idx, rid in enumerate(df["run_id"].astype(str).drop_duplicates())}
        df["_snapshot_sort"] = df["run_id"].astype(str).map(run_order)
        df["_snapshot_label"] = df["run_id"].astype(str)
    else:
        df["_snapshot_sort"] = df.index
        df["_snapshot_label"] = (df.index + 1).map(lambda i: f"row_{i}")

    return df


uploaded_snapshots: pd.DataFrame | None = None
using_uploaded_csv = False

if not snapshot_store_available():
    c1, c2 = st.columns(2)
    with c1:
        insight_card(
            "🔍",
            "Snapshot Store Not Found",
            "The semantic-CI snapshot store was not found at `.semantic_ci/snapshots.duckdb`. Run the semantic-CI pipeline and refresh this page.",
        )
    with c2:
        insight_card(
            "📖",
            "How To Generate Snapshots",
            "Run `python -m semantic_ci snapshot` from the project root, or upload a CSV export below.",
        )

    st.caption("CSV required columns: `metric_name`, `metric_value`. Optional: `period`, `grain`, `dimension_name`, `dimension_value`, `timestamp`/`snapshot_time`, `git_branch`, `run_id`.")
    uploaded_file = st.file_uploader("Upload metric snapshots CSV", type=["csv"], accept_multiple_files=False)
    if uploaded_file is None:
        st.stop()
    uploaded_snapshots = _normalize_uploaded_snapshot_csv(uploaded_file)
    if uploaded_snapshots is None:
        st.stop()
    using_uploaded_csv = True
    st.success(f"Loaded {len(uploaded_snapshots)} snapshot rows from `{uploaded_file.name}`.")

section_header("Latest Metric Values", accent_color=ACCENTS["metric_health"]["accent"])

if using_uploaded_csv and uploaded_snapshots is not None:
    latest = (
        uploaded_snapshots.sort_values("_snapshot_sort")
        .groupby(["metric_name", "period", "dimension_name", "dimension_value"], dropna=False, as_index=False)
        .tail(1)
        .sort_values(["metric_name", "period"])
        .assign(metric_value=lambda d: d["metric_value"].round(4), snapshot_time=lambda d: d["_snapshot_label"])
    )
else:
    latest = snapshot_query(
        """
        WITH ranked AS (
            SELECT
                s.metric_name,
                s.metric_value,
                s.period,
                s.grain,
                s.dimension_name,
                s.dimension_value,
                r.timestamp,
                r.git_branch,
                ROW_NUMBER() OVER (
                    PARTITION BY s.metric_name, s.period, s.dimension_name, s.dimension_value
                    ORDER BY r.timestamp DESC
                ) AS rn
            FROM metric_snapshots s
            JOIN snapshot_runs r ON s.run_id = r.run_id
        )
        SELECT
            metric_name,
            period,
            grain,
            dimension_name,
            dimension_value,
            round(metric_value, 4) AS metric_value,
            timestamp AS snapshot_time,
            git_branch
        FROM ranked
        WHERE rn = 1
        ORDER BY metric_name, period
        """
    )

if latest is not None and not latest.empty:
    rows = [
        [
            f'<span style="font-weight:600;color:#5b21b6;">{r["metric_name"]}</span>',
            str(r["period"]),
            str(r["grain"] or ""),
            f"{r['dimension_name'] or ''}: {r['dimension_value'] or ''}",
            f"<span style='font-weight:700;'>{r['metric_value']}</span>",
            str(r["snapshot_time"]),
            f'<span style="font-family:monospace;font-size:11px;">{r["git_branch"]}</span>',
        ]
        for _, r in latest.iterrows()
    ]
    editorial_table(
        ["Metric", "Period", "Grain", "Dimension", "Value", "Snapshot Time", "Branch"],
        rows,
        ["left", "left", "left", "left", "right", "left", "left"],
    )
else:
    st.info("No metric snapshots recorded yet.")

spacer(28)
section_header("Metric Drift Over Time", accent_color=ACCENTS["metric_health"]["accent"])

if using_uploaded_csv and uploaded_snapshots is not None:
    has_multiple = uploaded_snapshots["_snapshot_label"].nunique() > 1
else:
    run_count = snapshot_query("SELECT count(DISTINCT run_id) AS n FROM snapshot_runs")
    has_multiple = run_count is not None and not run_count.empty and run_count["n"].iloc[0] > 1

if not has_multiple:
    insight_card(
        "📈",
        "Single Snapshot Available",
        "Drift analysis requires at least two snapshot runs/timestamps. Execute semantic-CI again or upload CSV data with multiple runs.",
    )
    st.stop()

if using_uploaded_csv and uploaded_snapshots is not None:
    metrics = sorted(uploaded_snapshots["metric_name"].dropna().astype(str).unique().tolist())
    metrics_list = pd.DataFrame({"metric_name": metrics})
else:
    metrics_list = snapshot_query("SELECT DISTINCT metric_name FROM metric_snapshots ORDER BY 1")

if metrics_list is None or metrics_list.empty:
    st.info("No metrics found in snapshot store.")
    st.stop()

selected_metric = st.selectbox("Metric", metrics_list["metric_name"].tolist())

if using_uploaded_csv and uploaded_snapshots is not None:
    drift = uploaded_snapshots[uploaded_snapshots["metric_name"].astype(str) == selected_metric].copy()
    drift = drift.sort_values("_snapshot_sort")
    drift["timestamp"] = drift["_snapshot_label"]
    drift = drift[["timestamp", "metric_value", "period"]]
else:
    drift = snapshot_query(
        f"""
        SELECT r.timestamp, s.metric_value, s.period
        FROM metric_snapshots s
        JOIN snapshot_runs r ON s.run_id = r.run_id
        WHERE s.metric_name = '{selected_metric}'
        ORDER BY r.timestamp
        """  # nosec B608
    )

if drift is not None and not drift.empty:
    fig = line_chart(drift, x="timestamp", y="metric_value", color="period", title=f"Drift: {selected_metric}")
    fig.update_layout(
        font=dict(family="Inter"),
        plot_bgcolor="white",
        xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
        yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No drift data for the selected metric.")
