"""Consent Impact page -- the portfolio centerpiece."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components.charts import CONSENT_COLORS, grouped_bar, kpi_card, stacked_area
from components.db import query, table_exists

st.set_page_config(page_title="Consent Impact", page_icon="\U0001f4ca", layout="wide")
st.title("Consent Impact")

if not table_exists("fct_consent_impact"):
    st.warning("The `fct_consent_impact` table is not available. Run the dbt pipeline first.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

totals = query("""
SELECT
    sum(gross_revenue_eur) AS total_gross,
    sum(CASE WHEN consent_level = 'full' THEN gross_revenue_eur ELSE 0 END) AS full_gross,
    sum(CASE WHEN consent_level = 'minimal' THEN gross_revenue_eur ELSE 0 END) AS minimal_gross,
    sum(total_sessions) AS total_sessions,
    sum(CASE WHEN consent_level = 'full' THEN total_sessions ELSE 0 END) AS full_sessions
FROM fct_consent_impact
""")

if not totals.empty and totals["total_gross"].iloc[0] and totals["total_gross"].iloc[0] > 0:
    total_gross = totals["total_gross"].iloc[0]
    full_pct = totals["full_gross"].iloc[0] / total_gross * 100
    minimal_pct = totals["minimal_gross"].iloc[0] / total_gross * 100
    total_sessions = totals["total_sessions"].iloc[0] or 1
    full_session_pct = totals["full_sessions"].iloc[0] / total_sessions * 100
    measurement_gap = 100 - full_pct

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Full Consent Revenue", f"{full_pct:.1f}%")
    with c2:
        kpi_card("Measurement Gap", f"{measurement_gap:.1f}%", delta_color="inverse")
    with c3:
        kpi_card("Funnel Visibility Loss", f"{100 - full_session_pct:.1f}%", delta_color="inverse")
else:
    st.info("No consent impact data available yet.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Stacked area: revenue by consent level over time
# ---------------------------------------------------------------------------

rev_by_consent = query("""
SELECT
    report_month AS month,
    consent_level,
    round(net_revenue_eur, 2) AS net_revenue
FROM fct_consent_impact
ORDER BY report_month, consent_level
""")

if not rev_by_consent.empty:
    st.plotly_chart(
        stacked_area(
            rev_by_consent,
            x="month",
            y="net_revenue",
            color="consent_level",
            title="Net Revenue by Consent Level",
            color_map=CONSENT_COLORS,
        ),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Grouped bar: funnel conversion rates by consent level
# ---------------------------------------------------------------------------

funnel = query("""
SELECT
    consent_level,
    round(avg(session_conversion_rate) * 100, 2)  AS conversion_rate_pct,
    round(avg(cart_to_purchase_rate) * 100, 2)     AS cart_to_purchase_pct
FROM fct_consent_impact
GROUP BY consent_level
ORDER BY consent_level
""")

if not funnel.empty:
    melted = funnel.melt(id_vars="consent_level", var_name="metric", value_name="rate")
    st.plotly_chart(
        grouped_bar(
            melted,
            x="consent_level",
            y="rate",
            color="metric",
            title="Avg Funnel Rates by Consent Level",
            color_map=CONSENT_COLORS,
        ),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Detail table
# ---------------------------------------------------------------------------

st.subheader("Monthly Consent Impact Detail")

detail = query("""
SELECT
    report_month,
    consent_level,
    n_orders,
    round(gross_revenue_eur, 2)    AS gross_revenue_eur,
    round(net_revenue_eur, 2)      AS net_revenue_eur,
    round(avg_order_value_eur, 2)  AS aov,
    unique_customers,
    total_sessions,
    round(session_conversion_rate * 100, 2) AS conversion_pct
FROM fct_consent_impact
ORDER BY report_month DESC, consent_level
""")

if not detail.empty:
    st.dataframe(detail, use_container_width=True, hide_index=True)
