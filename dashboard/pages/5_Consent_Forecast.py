"""Consent Forecast page -- scenario modelling for consent distribution changes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components.charts import CONSENT_COLORS
from components.db import query, table_exists

st.set_page_config(page_title="Consent Forecast", page_icon="\U0001f4ca", layout="wide")
st.title("Consent Forecast")

# ---------------------------------------------------------------------------
# Predefined scenarios (from metric_definitions_forecast)
# ---------------------------------------------------------------------------

has_forecast = table_exists("metric_definitions_forecast")

if has_forecast:
    scenarios_df = query("""
        SELECT DISTINCT dimension_value AS scenario
        FROM metric_definitions_forecast
        WHERE dimension_name = 'scenario'
        ORDER BY 1
    """)
    scenario_list: list[str] = scenarios_df["scenario"].tolist() if not scenarios_df.empty else []
else:
    scenario_list = []

st.subheader("Predefined Scenarios")

if scenario_list:
    selected_scenario = st.selectbox("Select a scenario", scenario_list)

    forecast = query(
        f"""
        SELECT period, metric_name, round(metric_value, 4) AS metric_value
        FROM metric_definitions_forecast
        WHERE dimension_value = '{selected_scenario}'
        ORDER BY metric_name, period
    """  # nosec B608
    )

    baseline = query("""
        SELECT period, metric_name, round(metric_value, 4) AS metric_value
        FROM metric_definitions
        WHERE dimension_name = 'overall' OR dimension_name IS NULL
        ORDER BY metric_name, period
    """)

    if not forecast.empty:
        st.markdown(f"**Scenario:** {selected_scenario}")

        # Merge baseline and scenario
        if not baseline.empty:
            merged = forecast.rename(columns={"metric_value": "scenario_value"}).merge(
                baseline.rename(columns={"metric_value": "baseline_value"}),
                on=["period", "metric_name"],
                how="left",
            )
            merged["delta"] = merged["scenario_value"] - merged["baseline_value"]
            st.dataframe(merged, use_container_width=True, hide_index=True)
        else:
            st.dataframe(forecast, use_container_width=True, hide_index=True)
    else:
        st.info("No forecast data for the selected scenario.")
else:
    st.info("No predefined forecast scenarios found in `metric_definitions_forecast`.")

st.divider()

# ---------------------------------------------------------------------------
# Custom consent distribution sliders
# ---------------------------------------------------------------------------

st.subheader("Custom Consent Distribution")
st.markdown("Adjust the sliders to model a hypothetical consent distribution. The three values must sum to 100%.")

col1, col2, col3 = st.columns(3)
with col1:
    full_pct = st.slider("Full consent %", 0, 100, 60, key="full_slider")
with col2:
    analytics_pct = st.slider("Analytics-only %", 0, 100, 25, key="analytics_slider")
with col3:
    minimal_pct = st.slider("Minimal %", 0, 100, 15, key="minimal_slider")

total_pct = full_pct + analytics_pct + minimal_pct

if total_pct != 100:
    st.warning(f"Sliders sum to {total_pct}% -- please adjust so they total 100%.")
else:
    # Compute predicted metrics using consent-level averages from fct_consent_impact
    if table_exists("fct_consent_impact"):
        avgs = query("""
            SELECT
                consent_level,
                avg(avg_order_value_eur)     AS avg_aov,
                avg(session_conversion_rate) AS avg_conv,
                avg(cart_to_purchase_rate)   AS avg_cart_rate,
                sum(n_orders)                AS total_orders
            FROM fct_consent_impact
            GROUP BY consent_level
        """)

        if not avgs.empty:
            weights = {"full": full_pct / 100, "analytics_only": analytics_pct / 100, "minimal": minimal_pct / 100}
            weighted_aov = 0.0
            weighted_conv = 0.0
            weighted_cart = 0.0

            for _, row in avgs.iterrows():
                level = row["consent_level"]
                w = weights.get(level, 0)
                weighted_aov += row["avg_aov"] * w if row["avg_aov"] else 0
                weighted_conv += row["avg_conv"] * w if row["avg_conv"] else 0
                weighted_cart += row["avg_cart_rate"] * w if row["avg_cart_rate"] else 0

            st.divider()
            st.markdown("**Predicted Metrics (weighted by custom distribution)**")

            m1, m2, m3 = st.columns(3)
            m1.metric("Predicted AOV", f"\u20ac{weighted_aov:,.2f}")
            m2.metric("Predicted Conversion Rate", f"{weighted_conv * 100:.2f}%")
            m3.metric("Predicted Cart-to-Purchase", f"{weighted_cart * 100:.2f}%")

            # Measurement gap visualisation
            st.divider()
            st.subheader("Measurement Gap")
            st.markdown(
                f"With **{full_pct}%** full consent, the measurement gap is **{100 - full_pct}%** "
                f"-- meaning {100 - full_pct}% of user activity is only partially observed or invisible."
            )

            import plotly.graph_objects as go

            fig = go.Figure(
                go.Bar(
                    x=["Full", "Analytics Only", "Minimal"],
                    y=[full_pct, analytics_pct, minimal_pct],
                    marker_color=[CONSENT_COLORS["full"], CONSENT_COLORS["analytics_only"], CONSENT_COLORS["minimal"]],
                )
            )
            fig.update_layout(
                title="Custom Consent Distribution",
                yaxis_title="Percentage",
                template="plotly_white",
                margin=dict(l=40, r=20, t=40, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No consent impact averages available to compute predictions.")
    else:
        st.info("The `fct_consent_impact` table is required for custom scenario modelling.")
