"""FX Impact page -- rate trends and revenue comparison."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components.charts import REVENUE_PRIMARY, REVENUE_SECONDARY, line_chart
from components.db import query, table_exists

st.set_page_config(page_title="FX Impact", page_icon="\U0001f4ca", layout="wide")
st.title("FX Impact")

# ---------------------------------------------------------------------------
# FX rate trend lines
# ---------------------------------------------------------------------------

st.subheader("FX Rate Trends (to EUR)")

if table_exists("stg_fx_rates"):
    fx = query("""
        SELECT rate_date, base_currency || '/' || target_currency AS pair, rate
        FROM stg_fx_rates
        WHERE target_currency = 'EUR'
        ORDER BY rate_date
    """)

    if not fx.empty:
        st.plotly_chart(
            line_chart(fx, x="rate_date", y="rate", color="pair", title="Exchange Rates to EUR"),
            use_container_width=True,
        )
    else:
        # Try inverse (EUR as base)
        fx_inv = query("""
            SELECT rate_date, base_currency || '/' || target_currency AS pair, rate
            FROM stg_fx_rates
            ORDER BY rate_date
        """)
        if not fx_inv.empty:
            st.plotly_chart(
                line_chart(fx_inv, x="rate_date", y="rate", color="pair", title="Exchange Rates"),
                use_container_width=True,
            )
        else:
            st.info("No FX rate data found.")
else:
    st.warning("The `stg_fx_rates` table is not available.")

st.divider()

# ---------------------------------------------------------------------------
# Revenue comparison: static vs live FX
# ---------------------------------------------------------------------------

st.subheader("Revenue: Live FX vs Static FX")

if table_exists("int_orders_enriched"):
    comparison = query("""
        SELECT
            order_month AS month,
            round(sum(total_amount_eur), 2)         AS live_fx_revenue,
            round(sum(total_amount_eur_static), 2)  AS static_fx_revenue
        FROM int_orders_enriched
        GROUP BY order_month
        ORDER BY order_month
    """)

    if not comparison.empty:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["live_fx_revenue"],
                name="Live FX",
                marker_color=REVENUE_PRIMARY,
            )
        )
        fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["static_fx_revenue"],
                name="Static FX",
                marker_color=REVENUE_SECONDARY,
            )
        )
        fig.update_layout(
            barmode="group",
            title="Monthly Revenue: Live vs Static FX",
            template="plotly_white",
            margin=dict(l=40, r=20, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        # -- FX impact summary ------------------------------------------------
        st.subheader("FX Impact on Total Revenue")

        totals = query("""
            SELECT
                round(sum(total_amount_eur), 2)        AS live_total,
                round(sum(total_amount_eur_static), 2) AS static_total
            FROM int_orders_enriched
        """)

        if not totals.empty:
            live = totals["live_total"].iloc[0]
            static = totals["static_total"].iloc[0]
            diff = live - static
            pct = (diff / static * 100) if static else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Live FX Total", f"\u20ac{live:,.2f}")
            c2.metric("Static FX Total", f"\u20ac{static:,.2f}")
            c3.metric("FX Impact", f"\u20ac{diff:+,.2f}", delta=f"{pct:+.2f}%")

        # -- breakdown by currency -------------------------------------------
        by_currency = query("""
            SELECT
                currency,
                round(sum(total_amount_eur), 2)        AS live_eur,
                round(sum(total_amount_eur_static), 2) AS static_eur,
                round(sum(total_amount_eur) - sum(total_amount_eur_static), 2) AS fx_diff
            FROM int_orders_enriched
            GROUP BY currency
            ORDER BY abs(sum(total_amount_eur) - sum(total_amount_eur_static)) DESC
        """)

        if not by_currency.empty:
            st.subheader("FX Impact by Currency")
            st.dataframe(by_currency, use_container_width=True, hide_index=True)
    else:
        st.info("No enriched order data available.")
else:
    st.warning("The `int_orders_enriched` table is not available. Run the dbt pipeline first.")
