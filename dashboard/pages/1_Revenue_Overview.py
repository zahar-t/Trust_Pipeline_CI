"""Revenue Overview page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.charts import REVENUE_PRIMARY, REVENUE_SECONDARY, bar_chart
from components.db import query, table_exists
from components.filters import build_where_clause, render_sidebar_filters
from design_system import apply_global_styles, ACCENTS, editorial_table, hero_banner, metric_card, section_header, sidebar_brand, spacer, top_nav

apply_global_styles()
sidebar_brand()
top_nav("Revenue Overview", "Search metrics...")

hero_banner(
    title="Revenue Overview",
    subtitle="KPIs, monthly trends, and breakdowns by country and currency",
    badge_text="Financial Performance",
    page="revenue",
)

spacer(28)
filters = render_sidebar_filters()
where = build_where_clause(filters)

section_header("Key Metrics", accent_color=ACCENTS["revenue"]["accent"])

kpi_sql = f"""
SELECT
    round(sum(net_revenue_eur), 2) AS net_revenue,
    round(sum(gross_revenue_eur), 2) AS gross_revenue,
    round(avg(net_revenue_eur), 2) AS aov,
    count(DISTINCT order_id) AS total_orders
FROM fct_orders
{where}
"""  # nosec B608
kpi = query(kpi_sql)

mom_sql = f"""
WITH monthly AS (
    SELECT date_trunc('month', order_date) AS month, sum(net_revenue_eur) AS rev
    FROM fct_orders {where}
    GROUP BY 1
)
SELECT
    rev AS last_month_rev,
    lag(rev) OVER (ORDER BY month) AS prev_month_rev
FROM monthly
ORDER BY month DESC
LIMIT 1
"""  # nosec B608
mom = query(mom_sql)

if kpi.empty:
    st.info("No data available for the selected filters.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Net Revenue (EUR)", f"€{kpi['net_revenue'].iloc[0]:,.2f}", accent_color="#B5722F")
with c2:
    if not mom.empty and mom["prev_month_rev"].iloc[0] not in (None, 0):
        pct = (mom["last_month_rev"].iloc[0] / mom["prev_month_rev"].iloc[0] - 1) * 100
        metric_card("MoM Change", f"{pct:+.1f}%", delta=f"{pct:+.1f}%", delta_positive=pct >= 0, accent_color="#D49A5C")
    else:
        metric_card("MoM Change", "N/A", accent_color="#D49A5C")
with c3:
    metric_card("Avg Order Value", f"€{kpi['aov'].iloc[0]:,.2f}", accent_color="#D49A5C")
with c4:
    metric_card("Total Orders", f"{int(kpi['total_orders'].iloc[0]):,}", accent_color="#8A7F6D")

spacer(20)
tab1, tab2, tab3 = st.tabs(["Revenue Trend", "By Country", "By Currency"])

with tab1:
    monthly_sql = f"""
    SELECT
        date_trunc('month', order_date) AS month,
        round(sum(net_revenue_eur), 2) AS net_revenue,
        round(sum(gross_revenue_eur), 2) AS gross_revenue
    FROM fct_orders {where}
    GROUP BY 1
    ORDER BY 1
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
                fillcolor="rgba(212,154,92,0.08)",
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
    SELECT
        date_trunc('month', order_date) AS month,
        country_code,
        round(sum(net_revenue_eur), 2) AS net_revenue
    FROM fct_orders {where}
    GROUP BY 1, 2
    ORDER BY 1, 2
    """  # nosec B608
    country_df = query(country_sql)
    if not country_df.empty:
        st.plotly_chart(
            bar_chart(country_df, x="month", y="net_revenue", color="country_code", title=""),
            use_container_width=True,
        )

with tab3:
    if not table_exists("int_orders_enriched"):
        st.info("`int_orders_enriched` is required for currency breakdown.")
    else:
        currency_sql = f"""
        SELECT
            currency,
            round(sum(total_amount), 2) AS total_original,
            round(sum(total_amount_eur), 2) AS total_eur
        FROM int_orders_enriched
        {where}
        GROUP BY currency
        ORDER BY total_eur DESC
        """  # nosec B608
        currency_df = query(currency_sql)

        if not currency_df.empty:
            headers = ["Currency", "Original Total", "EUR Total"]
            rows = [
                [
                    str(r["currency"]),
                    f"{r['total_original']:,.2f}",
                    f"€{r['total_eur']:,.2f}",
                ]
                for _, r in currency_df.iterrows()
            ]
            editorial_table(headers, rows, ["left", "right", "right"])
