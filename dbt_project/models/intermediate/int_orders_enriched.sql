-- int_orders_enriched.sql
-- Join orders with customer context and aggregate line items
-- This is the canonical "order fact" before mart-level aggregation

with orders as (
    select * from {{ ref('stg_orders') }}
    where not dq_negative_amount  -- exclude known bad data
      and not dq_future_date
),

customers as (
    select * from {{ ref('stg_customers') }}
),

order_items_agg as (
    select
        order_id,
        count(*) as n_items,
        sum(quantity) as total_units,
        sum(line_total_eur) as computed_total_eur
    from {{ ref('stg_order_items') }}
    group by 1
),

enriched as (
    select
        o.order_id,
        o.customer_id,
        o.order_date,
        o.status,
        o.currency,
        o.total_amount,
        o.total_amount_eur,
        o.consent_level_at_order,
        o.country_code,

        -- Customer context
        c.email,
        c.consent_level as current_consent_level,
        c.created_at as customer_created_at,
        c.is_marketable,

        -- Order items aggregation
        coalesce(oi.n_items, 0) as n_items,
        coalesce(oi.total_units, 0) as total_units,
        coalesce(oi.computed_total_eur, 0) as computed_total_eur,

        -- Derived: is this a first order?
        row_number() over (
            partition by o.customer_id
            order by o.order_date
        ) as customer_order_sequence,

        -- Derived: days since customer signup
        {{ datediff('c.created_at', 'o.order_date', 'day') }} as days_since_signup

    from orders o
    left join customers c on o.customer_id = c.customer_id
    left join order_items_agg oi on o.order_id = oi.order_id
)

select
    *,
    case when customer_order_sequence = 1 then true else false end as is_first_order
from enriched
