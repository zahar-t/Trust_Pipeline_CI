"""Metric Health page."""

from __future__ import annotations

import sys
from pathlib import Path

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
            "Run `python -m semantic_ci snapshot` from the project root to persist baseline values for drift analysis.",
        )
    st.stop()

section_header("Latest Metric Values", accent_color=ACCENTS["metric_health"]["accent"])

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

run_count = snapshot_query("SELECT count(DISTINCT run_id) AS n FROM snapshot_runs")
has_multiple = run_count is not None and not run_count.empty and run_count["n"].iloc[0] > 1

if not has_multiple:
    insight_card(
        "📈",
        "Single Snapshot Available",
        "Drift analysis requires at least two snapshot runs. Execute semantic-CI again to compare metric history.",
    )
    st.stop()

metrics_list = snapshot_query("SELECT DISTINCT metric_name FROM metric_snapshots ORDER BY 1")
if metrics_list is None or metrics_list.empty:
    st.info("No metrics found in snapshot store.")
    st.stop()

selected_metric = st.selectbox("Metric", metrics_list["metric_name"].tolist())

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
