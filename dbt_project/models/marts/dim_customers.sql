-- dim_customers.sql
-- Customer dimension with lifetime value and behavioral segments

{{ config(materialized='table') }}

with customers as (
    select * from {{ ref('stg_customers') }}
),

order_metrics as (
    select
        customer_id,
        count(*) as lifetime_orders,
        sum(net_revenue_eur) as lifetime_revenue_eur,
        avg(net_revenue_eur) as avg_order_value_eur,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        count(case when is_first_order then 1 end) as _first_order_check
    from {{ ref('fct_orders') }}
    where status != 'cancelled'
    group by 1
),

funnel_metrics as (
    select
        customer_id,
        count(*) as lifetime_sessions,
        avg(n_events) as avg_events_per_session,
        sum(has_purchase) as purchase_sessions,
        sum(has_add_to_cart) as cart_sessions
    from {{ ref('int_sessions_funnel') }}
    group by 1
)

select
    c.customer_id,
    c.email,
    c.country_code,
    c.currency,
    c.consent_level,
    c.created_at,
    c.is_active,
    c.is_marketable,

    -- Lifetime order metrics
    coalesce(om.lifetime_orders, 0) as lifetime_orders,
    coalesce(om.lifetime_revenue_eur, 0) as lifetime_revenue_eur,
    coalesce(om.avg_order_value_eur, 0) as avg_order_value_eur,
    om.first_order_date,
    om.last_order_date,

    -- Funnel metrics
    coalesce(fm.lifetime_sessions, 0) as lifetime_sessions,
    coalesce(fm.avg_events_per_session, 0) as avg_events_per_session,

    -- Segmentation
    case
        when om.lifetime_orders is null then 'never_purchased'
        when om.lifetime_orders = 1 then 'one_time'
        when om.lifetime_orders between 2 and 4 then 'repeat'
        when om.lifetime_orders >= 5 then 'loyal'
    end as customer_segment,

    -- Consent impact flag
    case
        when c.consent_level = 'minimal' then 'limited_visibility'
        when c.consent_level = 'analytics_only' then 'partial_visibility'
        when c.consent_level = 'full' then 'full_visibility'
    end as tracking_visibility

from customers c
left join order_metrics om on c.customer_id = om.customer_id
left join funnel_metrics fm on c.customer_id = fm.customer_id
