"""FX Impact page."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.charts import line_chart
from components.db import query, table_exists
from design_system import (
    ACCENTS,
    apply_global_styles,
    editorial_table,
    hero_banner,
    insight_card,
    metric_card,
    section_header,
    sidebar_brand,
    signal_badges,
    spacer,
    status_badge,
    top_nav,
)

apply_global_styles()
sidebar_brand()
top_nav("FX Impact Analysis", "Search datasets...")

hero_banner(
    title="FX Impact",
    subtitle="Real-time analysis of currency fluctuations and their cumulative effect on multi-market revenue.",
    badge_text="Global Currency Monitor",
    page="fx",
    right_label="Last Revaluation",
    right_value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
)

spacer(28)

tab1, tab2, tab3 = st.tabs(["FX Rate Trends", "Live vs Static Revenue", "Currency Breakdown"])

with tab1:
    if not table_exists("stg_fx_rates"):
        st.warning("The `stg_fx_rates` table is not available.")
    else:
        fx = query(
            """
            WITH direct AS (
                SELECT
                    rate_date,
                    base_currency || '/EUR' AS pair,
                    rate AS rate_value
                FROM stg_fx_rates
                WHERE target_currency = 'EUR' AND base_currency != 'EUR'
            ),
            inverted AS (
                SELECT
                    rate_date,
                    target_currency || '/EUR' AS pair,
                    rate_inverse AS rate_value
                FROM stg_fx_rates
                WHERE base_currency = 'EUR' AND target_currency != 'EUR'
            )
            SELECT
                rate_date,
                pair,
                rate_value AS rate
            FROM (
                SELECT * FROM direct
                UNION ALL
                SELECT * FROM inverted
            )
            ORDER BY rate_date, pair
            """
        )
        if fx.empty:
            st.info("No FX rate data found.")
        else:
            st.markdown(
                """
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                    <div>
                        <h3 style="font-size:16px;font-weight:700;margin:0;">Daily Exchange Rates to EUR</h3>
                        <p style="font-size:12px;color:#444651;margin:4px 0 0 0;">Comparative trend analysis across primary trading pairs</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fig = line_chart(
                fx,
                x="rate_date",
                y="rate",
                color="pair",
                title="",
                color_map={"USD/EUR": "#10b981", "GBP/EUR": "#3b82f6", "JPY/EUR": "#f59e0b"},
            )
            fig.update_layout(
                font=dict(family="Inter"),
                plot_bgcolor="white",
                xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                margin=dict(l=40, r=20, t=10, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    if not table_exists("int_orders_enriched"):
        st.warning("The `int_orders_enriched` table is not available. Run the dbt pipeline first.")
    else:
        chart_col, metrics_col = st.columns([2, 1])

        comparison = query(
            """
            SELECT
                date_trunc('month', order_date) AS month,
                round(sum(total_amount_eur), 2) AS live_fx_revenue,
                round(sum(total_amount_eur_static), 2) AS static_fx_revenue
            FROM int_orders_enriched
            GROUP BY 1
            ORDER BY 1
            """
        )

        with chart_col:
            if not comparison.empty:
                import plotly.graph_objects as go

                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=comparison["month"],
                        y=comparison["static_fx_revenue"],
                        name="Static Revenue",
                        marker_color="#e0e8ff",
                    )
                )
                fig.add_trace(
                    go.Bar(
                        x=comparison["month"],
                        y=comparison["live_fx_revenue"],
                        name="Live Revenue",
                        marker_color="#1e3a8a",
                    )
                )
                fig.update_layout(
                    barmode="group",
                    template="plotly_white",
                    margin=dict(l=40, r=20, t=20, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    font=dict(family="Inter"),
                    plot_bgcolor="white",
                    xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                    yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                )
                st.plotly_chart(fig, use_container_width=True)

        with metrics_col:
            totals = query(
                """
                SELECT
                    round(sum(total_amount_eur), 2) AS live_total,
                    round(sum(total_amount_eur_static), 2) AS static_total
                FROM int_orders_enriched
                """
            )
            if not totals.empty:
                live = float(totals["live_total"].iloc[0] or 0)
                static = float(totals["static_total"].iloc[0] or 0)
                diff = live - static
                pct = (diff / static * 100) if static else 0

                metric_card("Live FX Total", f"€{live:,.2f}", accent_color="#10b981", description="Market value (real-time)")
                spacer(12)
                metric_card("Static FX Total", f"€{static:,.2f}", accent_color="#86efac", description="Budgetary rate (locked)")
                spacer(12)
                metric_card(
                    "FX Impact",
                    f"€{diff:+,.2f}",
                    delta=f"{pct:+.2f}%",
                    delta_positive=diff >= 0,
                    accent_color="#065f46",
                    description="Net gain or loss from FX movement",
                )

with tab3:
    if not table_exists("int_orders_enriched"):
        st.warning("The `int_orders_enriched` table is not available.")
    else:
        by_currency = query(
            """
            SELECT
                currency,
                round(sum(total_amount_eur), 2) AS live_eur,
                round(sum(total_amount_eur_static), 2) AS static_eur,
                round(sum(total_amount_eur) - sum(total_amount_eur_static), 2) AS fx_diff
            FROM int_orders_enriched
            GROUP BY currency
            ORDER BY abs(sum(total_amount_eur) - sum(total_amount_eur_static)) DESC
            """
        )

        if by_currency.empty:
            st.info("No currency breakdown data available.")
        else:
            headers = ["Currency Pair", "Live EUR Value", "Static EUR Value", "FX Diff", "Status"]
            aligns = ["left", "right", "right", "right", "center"]
            rows = []
            badge_items = []
            for _, r in by_currency.iterrows():
                variant = "favorable" if r["fx_diff"] >= 0 else "adverse"
                sign = "+" if r["fx_diff"] >= 0 else ""
                diff_color = "#10b981" if r["fx_diff"] >= 0 else "#ba1a1a"
                pct = (r["fx_diff"] / r["static_eur"] * 100) if r["static_eur"] else 0
                rows.append(
                    [
                        f"<span style='font-weight:600;'>{r['currency']} / EUR</span>",
                        f"€ {r['live_eur']:,.2f}",
                        f"€ {r['static_eur']:,.2f}",
                        f"<span style='font-weight:700;color:{diff_color};'>{sign}€ {abs(r['fx_diff']):,.2f}</span>",
                        status_badge("FAVORABLE" if r["fx_diff"] >= 0 else "ADVERSE", variant),
                    ]
                )
                badge_items.append((f"{r['currency']} {sign}{pct:.1f}%", "positive" if r["fx_diff"] >= 0 else "negative"))

            editorial_table(headers, rows, aligns)
            spacer(4)
            signal_badges(badge_items)

spacer(28)
section_header("Contextual Insights", accent_color=ACCENTS["fx"]["accent"])

c1, c2 = st.columns(2)
with c1:
    insight_card(
        "💡",
        "Hedging Opportunity",
        "Current FX trends may present opportunities for forward contracts on pairs showing consistent positive drift.",
    )
with c2:
    insight_card(
        "📋",
        "Revaluation Policy",
        "Static rates come from seeded budget assumptions while live rates track `stg_fx_rates` daily values.",
    )
