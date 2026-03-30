-- fct_orders.sql
-- Core order fact table for downstream metric computation
-- Consent-filterable via project variable

{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('int_orders_enriched') }}
),

-- Apply consent filter if set (var defaults to 'all')
consent_filtered as (
    select *
    from orders
    {% if var('consent_filter') != 'all' %}
    where consent_level_at_order = '{{ var("consent_filter") }}'
    {% endif %}
)

select
    order_id,
    customer_id,
    order_date,
    date_trunc('month', order_date) as order_month,
    date_trunc('week', order_date) as order_week,
    status,
    currency,
    country_code,
    consent_level_at_order,

    -- Revenue (EUR-normalized)
    case when status = 'completed' then total_amount_eur else 0 end as gross_revenue_eur,
    case when status = 'refunded' then total_amount_eur else 0 end as refund_amount_eur,
    case
        when status = 'completed' then total_amount_eur
        when status = 'refunded' then -total_amount_eur
        else 0
    end as net_revenue_eur,

    -- Order attributes
    n_items,
    total_units,
    is_first_order,
    is_marketable,
    customer_order_sequence,
    days_since_signup

from consent_filtered
