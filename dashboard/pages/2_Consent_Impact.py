"""Consent Impact page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.charts import CONSENT_COLORS, grouped_bar, stacked_area
from components.db import query, table_exists
from design_system import (
    ACCENTS,
    apply_global_styles,
    editorial_table,
    hero_banner,
    metric_card,
    section_header,
    sidebar_brand,
    spacer,
    status_badge,
    top_nav,
)

apply_global_styles()
sidebar_brand()
top_nav("Consent Impact", "Search metrics...")

hero_banner(
    title="Consent Impact",
    subtitle="How consent levels affect measurement and revenue visibility across the EU portfolio",
    badge_text="Compliance and Tracking",
    page="consent",
)

spacer(28)

if not table_exists("fct_consent_impact"):
    st.warning("The `fct_consent_impact` table is not available. Run the dbt pipeline first.")
    st.stop()

section_header("Consent Metrics", accent_color=ACCENTS["consent"]["accent"])

totals = query(
    """
    SELECT
        sum(gross_revenue_eur) AS total_gross,
        sum(CASE WHEN consent_level = 'full' THEN gross_revenue_eur ELSE 0 END) AS full_gross,
        sum(total_sessions) AS total_sessions,
        sum(CASE WHEN consent_level = 'full' THEN total_sessions ELSE 0 END) AS full_sessions
    FROM fct_consent_impact
    """
)

if totals.empty or totals["total_gross"].iloc[0] in (None, 0):
    st.info("No consent impact data available yet.")
    st.stop()

total_gross = totals["total_gross"].iloc[0]
full_pct = totals["full_gross"].iloc[0] / total_gross * 100
total_sessions = totals["total_sessions"].iloc[0] or 1
full_session_pct = totals["full_sessions"].iloc[0] / total_sessions * 100
measurement_gap = 100 - full_pct

c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Full Consent Revenue", f"{full_pct:.1f}%", accent_color="#f97316", description="Share of total gross revenue")
with c2:
    metric_card("Measurement Gap", f"{measurement_gap:.1f}%", accent_color="#ea580c", description="Revenue not fully attributed")
with c3:
    metric_card(
        "Funnel Visibility Loss",
        f"{100 - full_session_pct:.1f}%",
        accent_color="#c2410c",
        description="Sessions with limited tracking",
    )

spacer(20)

tab1, tab2, tab3 = st.tabs(["Revenue by Consent", "Funnel Rates", "Detail Table"])

with tab1:
    rev_by_consent = query(
        """
        SELECT
            report_month AS month,
            consent_level,
            round(net_revenue_eur, 2) AS net_revenue
        FROM fct_consent_impact
        ORDER BY report_month, consent_level
        """
    )
    if not rev_by_consent.empty:
        fig = stacked_area(
            rev_by_consent,
            x="month",
            y="net_revenue",
            color="consent_level",
            title="",
            color_map=CONSENT_COLORS,
        )
        fig.update_layout(
            font=dict(family="Inter"),
            plot_bgcolor="white",
            xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
            yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    funnel = query(
        """
        SELECT
            consent_level,
            round(avg(session_conversion_rate) * 100, 2) AS conversion_rate_pct,
            round(avg(cart_to_purchase_rate) * 100, 2) AS cart_to_purchase_pct
        FROM fct_consent_impact
        GROUP BY consent_level
        ORDER BY consent_level
        """
    )
    if not funnel.empty:
        melted = funnel.melt(id_vars="consent_level", var_name="metric", value_name="rate")
        fig = grouped_bar(
            melted,
            x="consent_level",
            y="rate",
            color="metric",
            title="",
            color_map={"conversion_rate_pct": "#fb923c", "cart_to_purchase_pct": "#ea580c"},
        )
        fig.update_layout(font=dict(family="Inter"), plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    detail = query(
        """
        SELECT
            report_month,
            consent_level,
            n_orders,
            round(gross_revenue_eur, 2) AS gross_revenue_eur,
            round(net_revenue_eur, 2) AS net_revenue_eur,
            round(avg_order_value_eur, 2) AS aov,
            unique_customers,
            total_sessions,
            round(session_conversion_rate * 100, 2) AS conversion_pct
        FROM fct_consent_impact
        ORDER BY report_month DESC, consent_level
        """
    )
    if not detail.empty:
        def _safe_int(val: object) -> int:
            if pd.isna(val):
                return 0
            return int(float(val))

        consent_badge_map = {"full": "success", "analytics_only": "warning", "minimal": "error"}
        headers = ["Month", "Consent", "Orders", "Gross (EUR)", "Net (EUR)", "AOV", "Customers", "Sessions", "Conv %"]
        aligns = ["left", "center", "right", "right", "right", "right", "right", "right", "right"]
        rows = []
        for _, r in detail.iterrows():
            rows.append(
                [
                    str(r["report_month"]),
                    status_badge(r["consent_level"].replace("_", " ").title(), consent_badge_map.get(r["consent_level"], "neutral")),
                    f"{_safe_int(r['n_orders']):,}",
                    f"€{r['gross_revenue_eur']:,.2f}",
                    f"€{r['net_revenue_eur']:,.2f}",
                    f"€{r['aov']:,.2f}",
                    f"{_safe_int(r['unique_customers']):,}",
                    f"{_safe_int(r['total_sessions']):,}",
                    f"{r['conversion_pct']}%",
                ]
            )
        editorial_table(headers, rows, aligns)
