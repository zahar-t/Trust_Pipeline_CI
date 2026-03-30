"""Metric Trust Pipeline -- Streamlit dashboard entry point."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the dashboard package root is importable so ``components.*`` works.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from components.db import query, table_exists

st.set_page_config(page_title="Metric Trust Pipeline", page_icon="\U0001f4ca", layout="wide")

# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

st.title("Metric Trust Pipeline")
st.markdown(
    """
    This dashboard surfaces the key outputs of the **Metric Trust Pipeline** --
    a dbt project that models e-commerce orders, customer behaviour, consent
    impact, and FX effects, all backed by DuckDB.

    Use the sidebar to navigate between pages:

    | Page | What it shows |
    |---|---|
    | **Revenue Overview** | KPIs, monthly trends, breakdowns by country and currency |
    | **Consent Impact** | How consent levels affect measurement and revenue visibility |
    | **Metric Health** | Semantic-CI snapshot drift (when available) |
    | **FX Impact** | Live vs static FX rates and their effect on reported revenue |
    | **Consent Forecast** | Scenario modelling for consent-level distribution changes |
    """
)

st.divider()

# ---------------------------------------------------------------------------
# Key stats
# ---------------------------------------------------------------------------

st.subheader("Key stats at a glance")

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
        c1.metric("Total Orders", f"{int(stats['total_orders'].iloc[0]):,}")
        c2.metric("Unique Customers", f"{int(stats['total_customers'].iloc[0]):,}")
        c3.metric("Net Revenue (EUR)", f"\u20ac{stats['total_net_revenue'].iloc[0]:,.2f}")
        c4.metric("Avg Order Value", f"\u20ac{stats['avg_order_value'].iloc[0]:,.2f}")
    else:
        st.info("No order data found. Have you run `dbt run` yet?")
except Exception as exc:
    st.warning(f"Could not load summary stats: {exc}")

# ---------------------------------------------------------------------------
# Data availability
# ---------------------------------------------------------------------------

st.subheader("Data availability")

expected_tables = [
    "fct_orders",
    "dim_customers",
    "fct_consent_impact",
    "metric_definitions",
    "metric_definitions_forecast",
    "stg_fx_rates",
    "int_orders_enriched",
]

cols = st.columns(len(expected_tables))
for col, tbl in zip(cols, expected_tables, strict=True):
    exists = table_exists(tbl)
    col.markdown(f"**{tbl}**  \n{'Available' if exists else 'Missing'}")
