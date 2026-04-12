"""Metric Health page — Financial Architect design."""

from __future__ import annotations

import streamlit as st
from components.charts import line_chart
from components.db import snapshot_query, snapshot_store_available
from design_system import (
    ACCENTS,
    hero_banner,
    section_header,
    spacer,
    editorial_table,
    insight_card,
)

hero_banner(
    title="Metric Health",
    subtitle="Semantic-CI snapshot drift monitoring — track how your metric definitions change over time",
    badge_text="Quality Assurance",
    page="metric_health",
)

spacer(32)

if not snapshot_store_available():
    spacer(16)
    c1, c2 = st.columns(2)
    with c1:
        insight_card(
            "\U0001f50d",
            "Snapshot Store Not Found",
            "The semantic-CI snapshot store was not found at `.semantic_ci/snapshots.duckdb`. Run the semantic-CI pipeline to generate snapshots, then refresh this page.",
            accent_color=ACCENTS["metric_health"]["accent"],
        )
    with c2:
        insight_card(
            "\U0001f4d6",
            "How to Generate Snapshots",
            "Run `python -m semantic_ci snapshot` from the project root. This will compute current metric values and store them for drift analysis.",
            accent_color=ACCENTS["metric_health"]["accent"],
        )
    st.stop()

# ---------------------------------------------------------------------------
# Latest metric values
# ---------------------------------------------------------------------------

section_header("Latest Metric Values", accent_color=ACCENTS["metric_health"]["accent"])

latest = snapshot_query("""
WITH ranked AS (
    SELECT s.metric_name, s.metric_value, s.period, s.grain,
           s.dimension_name, s.dimension_value, r.timestamp, r.git_branch,
           ROW_NUMBER() OVER (PARTITION BY s.metric_name, s.period, s.dimension_name, s.dimension_value
                              ORDER BY r.timestamp DESC) AS rn
    FROM metric_snapshots s
    JOIN snapshot_runs r ON s.run_id = r.run_id
)
SELECT metric_name, period, grain, dimension_name, dimension_value,
       round(metric_value, 4) AS metric_value, timestamp AS snapshot_time, git_branch
FROM ranked WHERE rn = 1 ORDER BY metric_name, period
""")

if latest is not None and not latest.empty:
    headers = ["Metric", "Period", "Grain", "Dimension", "Value", "Value", "Snapshot Time", "Branch"]
    rows = []
    for _, r in latest.iterrows():
        rows.append([
            f'<span style="font-weight:600;color:#5b21b6;">{r["metric_name"]}</span>',
            str(r["period"]), str(r["grain"] or ""),
            f"{r['dimension_name'] or ''}: {r['dimension_value'] or ''}",
            f"<span style='font-weight:700;'>{r['metric_value']}</span>",
            str(r["snapshot_time"]),
            f'<span style="font-family:monospace;font-size:11px;">{r["git_branch"]}</span>',
        ])
    editorial_table(
        ["Metric", "Period", "Grain", "Dimension", "Value", "Snapshot Time", "Branch"],
        rows,
        ["left", "left", "left", "left", "right", "left", "left"],
    )
else:
    st.info("No metric snapshots recorded yet.")

spacer(32)

# ---------------------------------------------------------------------------
# Drift history
# ---------------------------------------------------------------------------

section_header("Metric Drift Over Time", accent_color=ACCENTS["metric_health"]["accent"])

run_count = snapshot_query("SELECT count(DISTINCT run_id) AS n FROM snapshot_runs")
has_multiple = run_count is not None and not run_count.empty and run_count["n"].iloc[0] > 1

if has_multiple:
    metrics_list = snapshot_query("SELECT DISTINCT metric_name FROM metric_snapshots ORDER BY 1")
    if metrics_list is not None and not metrics_list.empty:
        selected_metric = st.selectbox("Metric", metrics_list["metric_name"].tolist())
        drift = snapshot_query(
            f"""
            SELECT r.timestamp, s.metric_value, s.period, s.dimension_value
            FROM metric_snapshots s
            JOIN snapshot_runs r ON s.run_id = r.run_id
            WHERE s.metric_name = '{selected_metric}'
            ORDER BY r.timestamp
        """  # nosec B608
        )
        if drift is not None and not drift.empty:
            fig = line_chart(drift, x="timestamp", y="metric_value", color="period", title=f"Drift: {selected_metric}")
            fig.update_layout(font=dict(family="Inter"), plot_bgcolor="white",
                              xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                              yaxis=dict(gridcolor="rgba(197,197,211,0.1)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No drift data for the selected metric.")
else:
    insight_card(
        "\U0001f4c8",
        "Single Snapshot Available",
        "Only one snapshot run exists. Drift analysis requires at least two runs. Run the semantic-CI pipeline again to compare metric values over time.",
        accent_color=ACCENTS["metric_health"]["accent"],
    )
