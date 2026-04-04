"""Consent Forecast page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.charts import CONSENT_COLORS
from components.db import query, table_exists
from design_system import (
    ACCENTS,
    apply_global_styles,
    editorial_table,
    hero_banner,
    metric_card,
    section_header,
    sidebar_brand,
    signal_badges,
    spacer,
    top_nav,
)

apply_global_styles()
sidebar_brand()
top_nav("Consent Forecast", "Search scenarios...")

hero_banner(
    title="Consent Forecast",
    subtitle="Scenario modeling for consent distribution changes and their impact on business metrics",
    badge_text="Revenue Projections",
    page="forecast",
)

spacer(28)

has_forecast = table_exists("metric_definitions_forecast")
if has_forecast:
    scenarios_df = query(
        """
        SELECT DISTINCT dimension_value AS scenario
        FROM metric_definitions_forecast
        WHERE dimension_name = 'scenario'
        ORDER BY 1
        """
    )
    scenario_list = scenarios_df["scenario"].tolist() if not scenarios_df.empty else []
else:
    scenario_list = []

tab1, tab2 = st.tabs(["Predefined Scenarios", "Custom Scenario"])

with tab1:
    if scenario_list:
        section_header("Select Scenario", accent_color=ACCENTS["forecast"]["accent"])
        selected_scenario = st.selectbox("Scenario", scenario_list, label_visibility="collapsed")

        forecast = query(
            f"""
            SELECT period, metric_name, round(metric_value, 4) AS metric_value
            FROM metric_definitions_forecast
            WHERE dimension_value = '{selected_scenario}'
            ORDER BY metric_name, period
            """  # nosec B608
        )

        baseline = query(
            """
            SELECT period, metric_name, round(metric_value, 4) AS metric_value
            FROM metric_definitions
            WHERE dimension_name = 'overall' OR dimension_name IS NULL
            ORDER BY metric_name, period
            """
        )

        if not forecast.empty:
            spacer(16)
            if not baseline.empty:
                merged = forecast.rename(columns={"metric_value": "scenario_value"}).merge(
                    baseline.rename(columns={"metric_value": "baseline_value"}),
                    on=["period", "metric_name"],
                    how="left",
                )
                merged["delta"] = merged["scenario_value"] - merged["baseline_value"]

                headers = ["Period", "Metric", "Scenario", "Baseline", "Delta"]
                aligns = ["left", "left", "right", "right", "right"]
                rows = []
                for _, r in merged.iterrows():
                    delta_val = r["delta"]
                    delta_color = "#10b981" if delta_val and delta_val >= 0 else "#ba1a1a"
                    sign = "+" if delta_val and delta_val >= 0 else ""
                    delta_str = f"{sign}{delta_val:.4f}" if delta_val is not None else "N/A"
                    rows.append(
                        [
                            str(r["period"]),
                            f'<span style="font-weight:600;">{r["metric_name"]}</span>',
                            f"{r['scenario_value']:.4f}",
                            f"{r['baseline_value']:.4f}" if r["baseline_value"] is not None else "N/A",
                            f'<span style="font-weight:700;color:{delta_color};">{delta_str}</span>',
                        ]
                    )
                editorial_table(headers, rows, aligns)
            else:
                st.dataframe(forecast, use_container_width=True, hide_index=True)
        else:
            st.info("No forecast data for the selected scenario.")
    else:
        st.info("No predefined forecast scenarios found in `metric_definitions_forecast`.")

with tab2:
    section_header("Custom Consent Distribution", accent_color=ACCENTS["forecast"]["accent"])
    st.markdown(
        "<p style='font-size:13px;color:#444651;margin-bottom:16px;'>"
        "Adjust sliders to model a hypothetical consent distribution. Values must sum to <strong>100%</strong>."
        "</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        full_pct = st.slider("Full consent %", 0, 100, 60, key="full_slider")
    with col2:
        analytics_pct = st.slider("Analytics-only %", 0, 100, 25, key="analytics_slider")
    with col3:
        minimal_pct = st.slider("Minimal %", 0, 100, 15, key="minimal_slider")

    total_pct = full_pct + analytics_pct + minimal_pct
    if total_pct == 100:
        signal_badges([(f"Distribution: {total_pct}% ✓", "positive")])
    else:
        signal_badges([(f"Distribution: {total_pct}% (must equal 100%)", "negative")])

    if total_pct == 100 and table_exists("fct_consent_impact"):
        avgs = query(
            """
            SELECT
                consent_level,
                avg(avg_order_value_eur) AS avg_aov,
                avg(session_conversion_rate) AS avg_conv,
                avg(cart_to_purchase_rate) AS avg_cart_rate
            FROM fct_consent_impact
            GROUP BY consent_level
            """
        )

        if not avgs.empty:
            weights = {"full": full_pct / 100, "analytics_only": analytics_pct / 100, "minimal": minimal_pct / 100}
            weighted_aov = sum(row["avg_aov"] * weights.get(row["consent_level"], 0) for _, row in avgs.iterrows() if row["avg_aov"])
            weighted_conv = sum(row["avg_conv"] * weights.get(row["consent_level"], 0) for _, row in avgs.iterrows() if row["avg_conv"])
            weighted_cart = sum(row["avg_cart_rate"] * weights.get(row["consent_level"], 0) for _, row in avgs.iterrows() if row["avg_cart_rate"])

            spacer(22)
            section_header("Predicted Metrics", accent_color=ACCENTS["forecast"]["accent"])
            m1, m2, m3 = st.columns(3)
            with m1:
                metric_card("Predicted AOV", f"€{weighted_aov:,.2f}", accent_color="#ef4444", description="Weighted average order value")
            with m2:
                metric_card(
                    "Predicted Conversion",
                    f"{weighted_conv * 100:.2f}%",
                    accent_color="#dc2626",
                    description="Weighted conversion rate",
                )
            with m3:
                metric_card(
                    "Predicted Cart-To-Purchase",
                    f"{weighted_cart * 100:.2f}%",
                    accent_color="#b91c1c",
                    description="Weighted cart completion",
                )

            spacer(20)
            section_header("Measurement Gap Visualization", accent_color=ACCENTS["forecast"]["accent"])
            signal_badges(
                [
                    (f"Full: {full_pct}%", "positive"),
                    (f"Analytics: {analytics_pct}%", "positive" if analytics_pct < 30 else "negative"),
                    (f"Minimal: {minimal_pct}%", "positive" if minimal_pct < 20 else "negative"),
                ]
            )

            import plotly.graph_objects as go

            fig = go.Figure(
                go.Bar(
                    x=["Full", "Analytics Only", "Minimal"],
                    y=[full_pct, analytics_pct, minimal_pct],
                    marker_color=[CONSENT_COLORS["full"], CONSENT_COLORS["analytics_only"], CONSENT_COLORS["minimal"]],
                    text=[f"{full_pct}%", f"{analytics_pct}%", f"{minimal_pct}%"],
                    textposition="outside",
                    textfont=dict(family="Inter", size=14, color="#0d1b34"),
                )
            )
            fig.update_layout(
                yaxis_title="Percentage",
                template="plotly_white",
                margin=dict(l=40, r=20, t=20, b=40),
                font=dict(family="Inter"),
                plot_bgcolor="white",
                xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
            )
            st.plotly_chart(fig, use_container_width=True)
