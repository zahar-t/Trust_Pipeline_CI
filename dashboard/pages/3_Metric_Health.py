"""Metric Health page -- semantic-CI snapshot drift."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components.charts import line_chart
from components.db import snapshot_query, snapshot_store_available

st.set_page_config(page_title="Metric Health", page_icon="\U0001f4ca", layout="wide")
st.title("Metric Health")

if not snapshot_store_available():
    st.info(
        "The semantic-CI snapshot store was not found at the expected path "
        "(`.semantic_ci/snapshots.duckdb`).  \n"
        "Run the semantic-CI pipeline to generate snapshots, then refresh this page."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Latest metric values
# ---------------------------------------------------------------------------

st.subheader("Latest Metric Values")

latest = snapshot_query("""
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
        ROW_NUMBER() OVER (PARTITION BY s.metric_name, s.period, s.dimension_name, s.dimension_value
                           ORDER BY r.timestamp DESC) AS rn
    FROM metric_snapshots s
    JOIN snapshot_runs r ON s.run_id = r.run_id
)
SELECT metric_name, period, grain, dimension_name, dimension_value,
       round(metric_value, 4) AS metric_value, timestamp AS snapshot_time, git_branch
FROM ranked
WHERE rn = 1
ORDER BY metric_name, period
""")

if latest is not None and not latest.empty:
    st.dataframe(latest, use_container_width=True, hide_index=True)
else:
    st.info("No metric snapshots recorded yet.")

# ---------------------------------------------------------------------------
# Drift history (when multiple snapshots exist)
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Metric Drift Over Time")

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
            st.plotly_chart(
                line_chart(drift, x="timestamp", y="metric_value", color="period", title=f"Drift: {selected_metric}"),
                use_container_width=True,
            )
        else:
            st.info("No drift data for the selected metric.")
else:
    st.info("Only one snapshot run exists. Drift analysis requires at least two runs.")
