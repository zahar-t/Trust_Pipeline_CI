"""Metric Trust Pipeline dashboard entry point (Home)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# Ensure local modules are importable from dashboard/pages too.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from components.db import query, table_exists
from design_system import (
    ACCENTS,
    apply_global_styles,
    editorial_table,
    hero_banner,
    metric_card,
    pipeline_health,
    section_header,
    sidebar_brand,
    spacer,
    status_badge,
    top_nav,
)

st.set_page_config(
    page_title="Metric Trust Pipeline",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
sidebar_brand()
top_nav("Main Dashboard", "Search metrics...")

hero_banner(
    title="Metric Trust Pipeline",
    subtitle="E-commerce analytics powered by dbt + DuckDB",
    badge_text="Live Pipeline",
    page="home",
    right_label="Last Data Sync",
    right_value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
)

spacer(30)
section_header("Quick Navigation", accent_color=ACCENTS["home"]["accent"])

nav_cols = st.columns(5)
for col, (icon, title, desc, page) in zip(
    nav_cols,
    [
        ("🏠", "Home", "Central pipeline control.", "app.py"),
        ("💰", "Revenue", "Financial performance.", "pages/1_Revenue_Overview.py"),
        ("🛡️", "Consent", "Compliance and tracking.", "pages/2_Consent_Impact.py"),
        ("💱", "FX Impact", "Volatility analysis.", "pages/4_FX_Impact.py"),
        ("🔮", "Forecast", "Revenue projections.", "pages/5_Consent_Forecast.py"),
    ],
    strict=True,
):
    with col:
        st.page_link(page, label=title, icon=icon, use_container_width=True)
        st.caption(desc)

spacer(30)
section_header("Key Statistics", accent_color=ACCENTS["home"]["accent"])

stats = query(
    """
    SELECT
        count(DISTINCT order_id) AS total_orders,
        count(DISTINCT customer_id) AS total_customers,
        round(sum(net_revenue_eur), 2) AS total_net_revenue,
        round(avg(net_revenue_eur), 2) AS avg_order_value
    FROM fct_orders
    """
)

if stats.empty:
    st.info("No order data found. Run `dbt run` first.")
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Orders", f"{int(stats['total_orders'].iloc[0]):,}", accent_color="#3b82f6")
    with c2:
        metric_card("Unique Customers", f"{int(stats['total_customers'].iloc[0]):,}", accent_color="#60a5fa")
    with c3:
        metric_card("Net Revenue (EUR)", f"€{stats['total_net_revenue'].iloc[0]:,.2f}", accent_color="#1e3a8a")
    with c4:
        metric_card("Avg Order Value", f"€{stats['avg_order_value'].iloc[0]:,.2f}", accent_color="#94a3b8")

spacer(30)
section_header("Data Pipeline Health", accent_color="#10b981")

expected_tables = [
    "fct_orders",
    "dim_customers",
    "fct_consent_impact",
    "metric_definitions",
    "metric_definitions_forecast",
    "stg_fx_rates",
    "int_orders_enriched",
]
pipeline_health([(tbl, table_exists(tbl)) for tbl in expected_tables])

spacer(30)
section_header("Recent Processed Orders", accent_color=ACCENTS["home"]["accent"])

recent = query(
    """
    SELECT
        order_id,
        order_date,
        country_code,
        net_revenue_eur,
        consent_level_at_order
    FROM fct_orders
    ORDER BY order_date DESC
    LIMIT 8
    """
)

if recent.empty:
    st.info("No recent orders available.")
else:
    headers = ["Order ID", "Processed At", "Region", "Amount (EUR)", "Consent", "Status"]
    aligns = ["left", "left", "center", "right", "center", "center"]
    rows: list[list[str]] = []
    consent_variant = {"full": "success", "analytics_only": "warning", "minimal": "error"}

    for _, row in recent.iterrows():
        consent = str(row["consent_level_at_order"])
        rows.append(
            [
                f'<span style="font-family:monospace;font-weight:700;color:#1e3a8a;">{row["order_id"]}</span>',
                str(row["order_date"]),
                f'<span style="background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{row["country_code"]} / EU</span>',
                f'<span style="font-weight:700;">€ {row["net_revenue_eur"]:,.2f}</span>',
                status_badge(consent.replace("_", " ").title(), consent_variant.get(consent, "neutral")),
                '<span style="color:#10b981;font-size:16px;">&#x2713;</span>',
            ]
        )

    editorial_table(headers, rows, aligns)
