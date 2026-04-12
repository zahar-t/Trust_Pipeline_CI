"""Revenue Overview page — Financial Architect design."""

from __future__ import annotations

import streamlit as st
import pygwalker as pyg
from components.charts import REVENUE_PRIMARY, REVENUE_SECONDARY, bar_chart
from components.db import query
from components.filters import build_where_clause, render_sidebar_filters
from design_system import (
    ACCENTS,
    hero_banner,
    metric_card,
    section_header,
    spacer,
    editorial_table,
)

hero_banner(
    title="Revenue Overview",
    subtitle="KPIs, monthly trends, and breakdowns by country & currency",
    badge_text="Financial Performance",
    badge_icon="query_stats",
    page="revenue",
)

spacer(32)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

filters = render_sidebar_filters()
where = build_where_clause(filters)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

section_header("Key Metrics", accent_color=ACCENTS["revenue"]["accent"])

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
        metric_card("Net Revenue (EUR)", f"\u20ac{kpi['net_revenue'].iloc[0]:,.2f}", accent_color="#1e3a8a")
    with c2:
        if not mom.empty and mom["prev_month_rev"].iloc[0] is not None and mom["prev_month_rev"].iloc[0] != 0:
            pct = (mom["last_month_rev"].iloc[0] / mom["prev_month_rev"].iloc[0] - 1) * 100
            metric_card("MoM Change", f"{pct:+.1f}%", delta=f"{pct:+.1f}%", delta_positive=pct >= 0, accent_color="#3b82f6")
        else:
            metric_card("MoM Change", "N/A", accent_color="#3b82f6")
    with c3:
        metric_card("Avg Order Value", f"\u20ac{kpi['aov'].iloc[0]:,.2f}", accent_color="#60a5fa")
    with c4:
        metric_card("Total Orders", f"{int(kpi['total_orders'].iloc[0]):,}", accent_color="#94a3b8")
else:
    st.info("No data available for the selected filters.")
    st.stop()

spacer(24)

# ---------------------------------------------------------------------------
# Charts — Streamlit native tabs styled via CSS
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(["Revenue Trend", "By Country", "By Currency", "Explore Data"])

with tab1:
    monthly_sql = f"""
    SELECT
        order_month AS month,
        round(sum(net_revenue_eur), 2) AS net_revenue,
        round(sum(gross_revenue_eur), 2) AS gross_revenue
    FROM fct_orders {where}
    GROUP BY order_month ORDER BY order_month
    """  # nosec B608
    monthly = query(monthly_sql)

    if not monthly.empty:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["gross_revenue"],
            fill="tozeroy", name="Gross Revenue",
            line=dict(color=REVENUE_SECONDARY),
            fillcolor="rgba(149,165,166,0.08)",
        ))
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["net_revenue"],
            name="Net Revenue", line=dict(color=REVENUE_PRIMARY, width=3),
        ))
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family="Inter, sans-serif", size=12),
            plot_bgcolor="white",
            xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
            yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    country_sql = f"""
    SELECT order_month AS month, country_code,
           round(sum(net_revenue_eur), 2) AS net_revenue
    FROM fct_orders {where}
    GROUP BY order_month, country_code ORDER BY order_month, country_code
    """  # nosec B608
    country_df = query(country_sql)
    if not country_df.empty:
        st.plotly_chart(bar_chart(country_df, x="month", y="net_revenue", color="country_code", title=""), use_container_width=True)

with tab3:
    currency_sql = f"""
    SELECT currency,
           round(sum(total_amount), 2) AS total_original,
           round(sum(total_amount_eur), 2) AS total_eur
    FROM fct_orders {where}
    GROUP BY currency ORDER BY total_eur DESC
    """  # nosec B608
    currency_df = query(currency_sql)
    if not currency_df.empty:
        headers = ["Currency", "Original Total", "EUR Total"]
        rows = [[r["currency"], f"{r['total_original']:,.2f}", f"\u20ac{r['total_eur']:,.2f}"] for _, r in currency_df.iterrows()]
        editorial_table(headers, rows, ["left", "right", "right"])

with tab4:
    explore_sql = f"""
    SELECT order_id, order_date, order_month, country_code, currency,
           round(total_amount, 2) AS total_amount,
           round(total_amount_eur, 2) AS total_amount_eur,
           round(net_revenue_eur, 2) AS net_revenue_eur,
           consent_level_at_order
    FROM fct_orders {where}
    ORDER BY order_date DESC LIMIT 5000
    """  # nosec B608
    explore_df = query(explore_sql)
    if not explore_df.empty:
        pyg.walk(explore_df, env="Streamlit")
    else:
        st.info("No data to explore.")
