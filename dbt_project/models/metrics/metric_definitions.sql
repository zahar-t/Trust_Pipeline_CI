-- metric_definitions.sql
-- Centralized metric definitions — the "source of truth" layer
-- These are the metrics that Semantic CI snapshots and monitors

{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('fct_orders') }}
),

customers as (
    select * from {{ ref('dim_customers') }}
),

-- =========================================================================
-- REVENUE METRICS (monthly grain)
-- =========================================================================
monthly_revenue as (
    select
        order_month as period,
        'monthly' as grain,
        sum(gross_revenue_eur) as gross_revenue_eur,
        sum(net_revenue_eur) as net_revenue_eur,
        sum(refund_amount_eur) as total_refunds_eur,
        count(distinct order_id) as total_orders,
        count(distinct customer_id) as unique_buyers,
        count(distinct case when is_first_order then customer_id end) as new_customers,

        -- Computed metrics
        case when count(distinct order_id) > 0
            then sum(net_revenue_eur) / count(distinct order_id)
            else 0
        end as avg_order_value_eur,

        case when sum(gross_revenue_eur) > 0
            then sum(refund_amount_eur) / sum(gross_revenue_eur)
            else 0
        end as refund_rate

    from orders
    group by 1
),

-- =========================================================================
-- CONSENT-SEGMENTED REVENUE (the EU differentiator metric)
-- =========================================================================
consent_revenue as (
    select
        order_month as period,
        consent_level_at_order as consent_level,
        sum(net_revenue_eur) as net_revenue_eur,
        count(distinct order_id) as total_orders,
        count(distinct customer_id) as unique_buyers
    from orders
    group by 1, 2
),

-- =========================================================================
-- CUSTOMER HEALTH METRICS (monthly snapshot)
-- =========================================================================
customer_health as (
    select
        date_trunc('month', created_at) as period,
        count(*) as new_signups,
        count(case when consent_level = 'full' then 1 end) as full_consent_signups,
        count(case when consent_level = 'minimal' then 1 end) as minimal_consent_signups,
        round(
            cast(count(case when consent_level = 'full' then 1 end) as double)
            / nullif(count(*), 0),
            4
        ) as full_consent_rate
    from customers
    group by 1
),

-- =========================================================================
-- COUNTRY MIX (monthly)
-- =========================================================================
country_mix as (
    select
        order_month as period,
        country_code,
        sum(net_revenue_eur) as net_revenue_eur,
        count(distinct order_id) as total_orders
    from orders
    group by 1, 2
)

-- =========================================================================
-- FINAL: Unpivoted metric store
-- Each row = one metric value at one point in time
-- This structure is what Semantic CI snapshots
-- =========================================================================
select
    period,
    'gross_revenue_eur' as metric_name,
    cast(gross_revenue_eur as double) as metric_value,
    'monthly' as grain,
    cast(null as varchar) as dimension_name,
    cast(null as varchar) as dimension_value
from monthly_revenue

union all

select period, 'net_revenue_eur', cast(net_revenue_eur as double), 'monthly', cast(null as varchar), cast(null as varchar)
from monthly_revenue

union all

select period, 'total_orders', cast(total_orders as double), 'monthly', cast(null as varchar), cast(null as varchar)
from monthly_revenue

union all

select period, 'avg_order_value_eur', round(cast(avg_order_value_eur as double), 2), 'monthly', cast(null as varchar), cast(null as varchar)
from monthly_revenue

union all

select period, 'refund_rate', round(cast(refund_rate as double), 4), 'monthly', cast(null as varchar), cast(null as varchar)
from monthly_revenue

union all

select period, 'new_customers', cast(new_customers as double), 'monthly', cast(null as varchar), cast(null as varchar)
from monthly_revenue

union all

select period, 'unique_buyers', cast(unique_buyers as double), 'monthly', cast(null as varchar), cast(null as varchar)
from monthly_revenue

union all

-- Consent-segmented metrics
select
    period,
    'net_revenue_eur' as metric_name,
    cast(net_revenue_eur as double),
    'monthly',
    'consent_level' as dimension_name,
    consent_level as dimension_value
from consent_revenue

union all

-- Customer health
select period, 'full_consent_rate', cast(full_consent_rate as double), 'monthly', cast(null as varchar), cast(null as varchar)
from customer_health

union all

-- Country mix
select
    period,
    'net_revenue_eur',
    cast(net_revenue_eur as double),
    'monthly',
    'country_code' as dimension_name,
    country_code as dimension_value
from country_mix
