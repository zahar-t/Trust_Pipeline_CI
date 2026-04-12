"""Home / landing page — Financial Architect design."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from components.db import query, table_exists
from design_system import (
    ACCENTS,
    hero_banner,
    metric_card,
    nav_card,
    pipeline_health,
    section_header,
    spacer,
    editorial_table,
)

# ---------------------------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------------------------

hero_banner(
    title="Metric Trust Pipeline",
    subtitle="E-commerce analytics powered by dbt + DuckDB",
    badge_text="Live Pipeline",
    page="home",
    right_label="Last Data Sync",
    right_value=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
)

spacer(32)

# ---------------------------------------------------------------------------
# Quick Navigation Bento Grid
# ---------------------------------------------------------------------------

section_header("Quick Navigation", accent_color=ACCENTS["home"]["accent"])

cols = st.columns(5)
pages = [
    ("\U0001f3e0", "Home", "Central pipeline control."),
    ("\U0001f4ca", "Revenue", "Financial performance."),
    ("\U0001f6e1\ufe0f", "Consent", "Compliance & tracking."),
    ("\U0001f4b1", "FX Impact", "Volatility analysis."),
    ("\U0001f52e", "Forecast", "Revenue projections."),
]
for col, (icon, title, desc) in zip(cols, pages):
    with col:
        nav_card(icon, title, desc)

spacer(32)

# ---------------------------------------------------------------------------
# Key Statistics
# ---------------------------------------------------------------------------

section_header("Key Statistics", accent_color=ACCENTS["home"]["accent"])

try:
    stats = query(
        """
        SELECT
            count(DISTINCT order_id)       AS total_orders,
            count(DISTINCT customer_id)    AS total_customers,
            round(sum(net_revenue_eur), 2) AS total_net_revenue,
            round(avg(net_revenue_eur), 2) AS avg_order_value
        FROM fct_orders
        """
    )

    if not stats.empty:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(
                "Total Orders",
                f"{int(stats['total_orders'].iloc[0]):,}",
                accent_color="#3b82f6",
            )
        with c2:
            metric_card(
                "Unique Customers",
                f"{int(stats['total_customers'].iloc[0]):,}",
                accent_color="#60a5fa",
            )
        with c3:
            metric_card(
                "Net Revenue (EUR)",
                f"\u20ac{stats['total_net_revenue'].iloc[0]:,.2f}",
                accent_color="#1e3a8a",
            )
        with c4:
            metric_card(
                "Avg Order Value",
                f"\u20ac{stats['avg_order_value'].iloc[0]:,.2f}",
                accent_color="#94a3b8",
            )
    else:
        st.info("No order data found. Have you run `dbt run` yet?")
except Exception as exc:
    st.warning(f"Could not load summary stats: {exc}")

spacer(32)

# ---------------------------------------------------------------------------
# Data Pipeline Health
# ---------------------------------------------------------------------------

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

table_status = [(tbl, table_exists(tbl)) for tbl in expected_tables]
pipeline_health(table_status)

spacer(32)

# ---------------------------------------------------------------------------
# Recent Processed Orders
# ---------------------------------------------------------------------------

section_header("Recent Processed Orders", accent_color=ACCENTS["home"]["accent"])

try:
    recent = query("""
        SELECT order_id, order_date, country_code, currency,
               round(total_amount_eur, 2) AS amount_eur,
               consent_level_at_order AS consent
        FROM fct_orders
        ORDER BY order_date DESC
        LIMIT 8
    """)
    if not recent.empty:
        from design_system import status_badge

        headers = ["Order ID", "Date", "Region", "Amount (EUR)", "Consent", "Status"]
        aligns = ["left", "left", "center", "right", "center", "center"]
        rows = []
        for _, r in recent.iterrows():
            consent_variant = {"full": "success", "analytics_only": "warning", "minimal": "error"}.get(r["consent"], "neutral")
            consent_label = {"full": "Full Consent", "analytics_only": "Analytics Only", "minimal": "Minimal"}.get(r["consent"], r["consent"])
            rows.append([
                f'<span style="font-family:monospace;font-weight:600;color:#1e3a8a;font-size:12px;">{r["order_id"]}</span>',
                f'<span style="color:#444651;font-size:12px;">{r["order_date"]}</span>',
                f'<span style="background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{r["country_code"]} / EU</span>',
                f'<span style="font-weight:600;font-size:13px;">\u20ac {r["amount_eur"]:,.2f}</span>',
                status_badge(consent_label, consent_variant),
                '<span style="color:#10b981;font-size:16px;">&#x2713;</span>',
            ])
        editorial_table(headers, rows, aligns)
except Exception:
    st.info("Could not load recent orders.")
