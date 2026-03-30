"""Revenue Overview page -- KPIs, trends, and breakdowns."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components.charts import REVENUE_PRIMARY, REVENUE_SECONDARY, bar_chart, kpi_card
from components.db import query
from components.filters import build_where_clause, render_sidebar_filters

st.set_page_config(page_title="Revenue Overview", page_icon="\U0001f4ca", layout="wide")
st.title("Revenue Overview")

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

filters = render_sidebar_filters()
where = build_where_clause(filters)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

kpi_sql = f"""
SELECT
    round(sum(net_revenue_eur), 2)           AS net_revenue,
    round(sum(gross_revenue_eur), 2)         AS gross_revenue,
    round(avg(net_revenue_eur), 2)           AS aov,
    count(DISTINCT order_id)                 AS total_orders
FROM fct_orders
{where}
"""  # nosec B608
kpi = query(kpi_sql)

# MoM change
mom_sql = f"""
WITH monthly AS (
    SELECT order_month, sum(net_revenue_eur) AS rev
    FROM fct_orders {where}
    GROUP BY order_month
    ORDER BY order_month
)
SELECT
    rev AS last_month_rev,
    lag(rev) OVER (ORDER BY order_month) AS prev_month_rev
FROM monthly
ORDER BY order_month DESC
LIMIT 1
"""  # nosec B608
mom = query(mom_sql)

if not kpi.empty:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Net Revenue (EUR)", f"\u20ac{kpi['net_revenue'].iloc[0]:,.2f}")
    with c2:
        if not mom.empty and mom["prev_month_rev"].iloc[0] is not None and mom["prev_month_rev"].iloc[0] != 0:
            pct = (mom["last_month_rev"].iloc[0] / mom["prev_month_rev"].iloc[0] - 1) * 100
            kpi_card("MoM Change", f"{pct:+.1f}%", delta=f"{pct:+.1f}%")
        else:
            kpi_card("MoM Change", "N/A")
    with c3:
        kpi_card("Avg Order Value", f"\u20ac{kpi['aov'].iloc[0]:,.2f}")
    with c4:
        kpi_card("Total Orders", f"{int(kpi['total_orders'].iloc[0]):,}")
else:
    st.info("No data available for the selected filters.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Monthly net revenue trend (line) with gross as area
# ---------------------------------------------------------------------------

monthly_sql = f"""
SELECT
    order_month                         AS month,
    round(sum(net_revenue_eur), 2)      AS net_revenue,
    round(sum(gross_revenue_eur), 2)    AS gross_revenue
FROM fct_orders
{where}
GROUP BY order_month
ORDER BY order_month
"""  # nosec B608
monthly = query(monthly_sql)

if not monthly.empty:
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["gross_revenue"],
            fill="tozeroy",
            name="Gross Revenue",
            line=dict(color=REVENUE_SECONDARY),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["month"],
            y=monthly["net_revenue"],
            name="Net Revenue",
            line=dict(color=REVENUE_PRIMARY, width=3),
        )
    )
    fig.update_layout(
        title="Monthly Revenue",
        template="plotly_white",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Revenue by country (stacked bar)
# ---------------------------------------------------------------------------

country_sql = f"""
SELECT
    order_month       AS month,
    country_code,
    round(sum(net_revenue_eur), 2) AS net_revenue
FROM fct_orders
{where}
GROUP BY order_month, country_code
ORDER BY order_month, country_code
"""  # nosec B608
country_df = query(country_sql)

if not country_df.empty:
    st.plotly_chart(
        bar_chart(country_df, x="month", y="net_revenue", color="country_code", title="Revenue by Country"),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Revenue by currency
# ---------------------------------------------------------------------------

currency_sql = f"""
SELECT
    currency,
    round(sum(total_amount), 2)     AS total_original,
    round(sum(total_amount_eur), 2) AS total_eur
FROM fct_orders
{where}
GROUP BY currency
ORDER BY total_eur DESC
"""  # nosec B608
currency_df = query(currency_sql)

if not currency_df.empty:
    st.subheader("Revenue by Currency")
    st.dataframe(currency_df, use_container_width=True, hide_index=True)
