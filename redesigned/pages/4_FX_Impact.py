"""FX Impact page — Financial Architect design (matches Stitch mockup)."""

from __future__ import annotations

import streamlit as st
from components.charts import REVENUE_PRIMARY, REVENUE_SECONDARY, line_chart
from components.db import query, table_exists
from design_system import (
    ACCENTS,
    hero_banner,
    metric_card,
    section_header,
    spacer,
    editorial_table,
    signal_badges,
    insight_card,
    status_badge,
)

hero_banner(
    title="FX Impact",
    subtitle="Real-time analysis of currency fluctuations and their cumulative effect on your multi-market revenue streams.",
    badge_text="Global Currency Monitor",
    page="fx",
    right_label="Last Revaluation",
    right_value="Daily Auto-Sync",
)

spacer(32)

# ---------------------------------------------------------------------------
# Tab system
# ---------------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["FX Rate Trends", "Live vs Static Revenue", "Currency Breakdown"])

with tab1:
    if table_exists("stg_fx_rates"):
        fx = query("""
            SELECT rate_date, base_currency || '/' || target_currency AS pair, rate
            FROM stg_fx_rates
            WHERE target_currency = 'EUR'
            ORDER BY rate_date
        """)

        if not fx.empty:
            # Legend badges
            pairs = fx["pair"].unique().tolist()
            pair_colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
            legend_html = ""
            for i, p in enumerate(pairs[:5]):
                c = pair_colors[i % len(pair_colors)]
                legend_html += f"""
                <span style="
                    display:inline-flex;align-items:center;gap:6px;
                    padding:4px 12px;border-radius:999px;
                    background:rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.08);
                    font-size:11px;font-weight:700;color:{c};
                ">
                    <span style="width:6px;height:6px;border-radius:50%;background:{c};display:inline-block;"></span>
                    {p}
                </span>
                """
            st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                    <div>
                        <h3 style="font-size:16px;font-weight:700;margin:0;">Daily Exchange Rates to EUR</h3>
                        <p style="font-size:12px;color:#444651;margin:4px 0 0 0;">Comparative trend analysis across primary trading pairs</p>
                    </div>
                    <div style="display:flex;gap:8px;">{legend_html}</div>
                </div>
            """, unsafe_allow_html=True)

            fig = line_chart(fx, x="rate_date", y="rate", color="pair", title="")
            fig.update_layout(
                font=dict(family="Inter"), plot_bgcolor="white", showlegend=False,
                xaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                yaxis=dict(gridcolor="rgba(197,197,211,0.1)"),
                margin=dict(l=40, r=20, t=10, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            fx_inv = query("""
                SELECT rate_date, base_currency || '/' || target_currency AS pair, rate
                FROM stg_fx_rates ORDER BY rate_date
            """)
            if not fx_inv.empty:
                fig = line_chart(fx_inv, x="rate_date", y="rate", color="pair", title="")
                fig.update_layout(font=dict(family="Inter"), plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No FX rate data found.")
    else:
        st.warning("The `stg_fx_rates` table is not available.")

with tab2:
    if table_exists("int_orders_enriched"):
        # Bento layout: chart left, metrics right
        chart_col, metrics_col = st.columns([2, 1])

        comparison = query("""
            SELECT order_month AS month,
                   round(sum(total_amount_eur), 2) AS live_fx_revenue,
                   round(sum(total_amount_eur_static), 2) AS static_fx_revenue
            FROM int_orders_enriched
            GROUP BY order_month ORDER BY order_month
        """)

        with chart_col:
            if not comparison.empty:
                import plotly.graph_objects as go

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=comparison["month"], y=comparison["static_fx_revenue"],
                    name="Static Revenue", marker_color="#e0e8ff",
                ))
                fig.add_trace(go.Bar(
                    x=comparison["month"], y=comparison["live_fx_revenue"],
                    name="Live Revenue", marker_color="#1e3a8a",
                ))
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
            totals = query("""
                SELECT round(sum(total_amount_eur), 2) AS live_total,
                       round(sum(total_amount_eur_static), 2) AS static_total
                FROM int_orders_enriched
            """)
            if not totals.empty:
                live = totals["live_total"].iloc[0]
                static = totals["static_total"].iloc[0]
                diff = live - static
                pct = (diff / static * 100) if static else 0

                metric_card("Live FX Total", f"\u20ac{live:,.2f}",
                            accent_color="#10b981", description="Market Value (Real-time)")
                spacer(16)
                metric_card("Static FX Total", f"\u20ac{static:,.2f}",
                            accent_color="#86efac", description="Budgetary Rate (Locked)")
                spacer(16)
                metric_card("FX Impact", f"\u20ac{diff:+,.2f}",
                            delta=f"{pct:+.2f}%", delta_positive=diff >= 0,
                            accent_color="#065f46",
                            description="Net gain/loss from exchange movements")
    else:
        st.warning("The `int_orders_enriched` table is not available. Run the dbt pipeline first.")

with tab3:
    if table_exists("int_orders_enriched"):
        by_currency = query("""
            SELECT currency,
                   round(sum(total_amount_eur), 2) AS live_eur,
                   round(sum(total_amount_eur_static), 2) AS static_eur,
                   round(sum(total_amount_eur) - sum(total_amount_eur_static), 2) AS fx_diff
            FROM int_orders_enriched
            GROUP BY currency
            ORDER BY abs(sum(total_amount_eur) - sum(total_amount_eur_static)) DESC
        """)

        if not by_currency.empty:
            headers = ["Currency Pair", "Live EUR Value", "Static EUR Value", "FX Diff", "Status"]
            aligns = ["left", "right", "right", "right", "center"]
            rows = []
            badge_items = []
            for _, r in by_currency.iterrows():
                variant = "favorable" if r["fx_diff"] >= 0 else "adverse"
                diff_color = "#10b981" if r["fx_diff"] >= 0 else "#ba1a1a"
                sign = "+" if r["fx_diff"] >= 0 else ""
                pct = (r["fx_diff"] / r["static_eur"] * 100) if r["static_eur"] else 0
                rows.append([
                    f"""<div style="display:flex;align-items:center;gap:10px;">
                        <div style="width:32px;height:32px;border-radius:50%;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:10px;">{r['currency'][:2]}</div>
                        <span style="font-weight:600;font-size:13px;">{r['currency']} / EUR</span>
                    </div>""",
                    f"\u20ac {r['live_eur']:,.2f}",
                    f"\u20ac {r['static_eur']:,.2f}",
                    f'<span style="font-weight:700;color:{diff_color};">{sign}\u20ac {abs(r["fx_diff"]):,.2f}</span>',
                    status_badge("FAVORABLE" if r["fx_diff"] >= 0 else "ADVERSE", variant),
                ])
                badge_items.append((f"{r['currency']} {sign}{pct:.1f}%", "positive" if r["fx_diff"] >= 0 else "negative"))

            editorial_table(headers, rows, aligns)
            spacer(4)
            signal_badges(badge_items)
        else:
            st.info("No currency breakdown data available.")
    else:
        st.warning("The `int_orders_enriched` table is not available.")

# ---------------------------------------------------------------------------
# Insight Cards (bottom of page, matching Stitch mockup)
# ---------------------------------------------------------------------------

spacer(32)
section_header("Contextual Insights", accent_color=ACCENTS["fx"]["accent"])

c1, c2 = st.columns(2)
with c1:
    insight_card(
        "\U0001f4a1",
        "Hedging Opportunity",
        "Current FX trends may present opportunities for forward contracts. Review the currency breakdown above to identify pairs with significant positive drift that could be locked in.",
        accent_color="#10b981",
    )
with c2:
    insight_card(
        "\U0001f4cb",
        "Revaluation Policy",
        "Static rates are updated based on the seed data in the dbt project. Live rates are computed from the `stg_fx_rates` table using daily ECB fixings.",
        accent_color="#3b82f6",
    )
