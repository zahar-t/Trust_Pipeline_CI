-- fct_consent_impact.sql
-- Quantifies the measurement gap caused by different consent regimes
-- This is the EU differentiator: showing HOW MUCH you lose by consent level

{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('fct_orders') }}
),

events as (
    select * from {{ ref('stg_events') }}
),

-- Revenue by consent level per month
revenue_by_consent as (
    select
        order_month,
        consent_level_at_order as consent_level,
        count(*) as n_orders,
        sum(gross_revenue_eur) as gross_revenue_eur,
        sum(net_revenue_eur) as net_revenue_eur,
        avg(net_revenue_eur) as avg_order_value_eur,
        count(distinct customer_id) as unique_customers
    from orders
    group by 1, 2
),

-- Event visibility by consent level per month
event_visibility as (
    select
        date_trunc('month', event_timestamp) as event_month,
        consent_level,
        event_type,
        count(*) as n_events
    from events
    group by 1, 2, 3
),

-- Funnel conversion by consent level
funnel_by_consent as (
    select
        date_trunc('month', session_start) as session_month,
        consent_level,
        count(*) as total_sessions,
        sum(has_page_view) as sessions_with_pageview,
        sum(has_add_to_cart) as sessions_with_cart,
        sum(has_checkout_start) as sessions_with_checkout,
        sum(has_purchase) as sessions_with_purchase
    from {{ ref('int_sessions_funnel') }}
    group by 1, 2
)

select
    r.order_month as report_month,
    r.consent_level,

    -- Revenue metrics
    r.n_orders,
    r.gross_revenue_eur,
    r.net_revenue_eur,
    r.avg_order_value_eur,
    r.unique_customers,

    -- Funnel metrics (where available)
    f.total_sessions,
    f.sessions_with_pageview,
    f.sessions_with_cart,
    f.sessions_with_checkout,
    f.sessions_with_purchase,

    -- Conversion rates
    case when f.total_sessions > 0
        then round(cast(f.sessions_with_purchase as double) / f.total_sessions, 4)
        else null
    end as session_conversion_rate,

    -- Cart-to-purchase rate
    case when f.sessions_with_cart > 0
        then round(cast(f.sessions_with_purchase as double) / f.sessions_with_cart, 4)
        else null
    end as cart_to_purchase_rate

from revenue_by_consent r
left join funnel_by_consent f
    on r.order_month = f.session_month
    and r.consent_level = f.consent_level
