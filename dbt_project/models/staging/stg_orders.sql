-- stg_orders.sql
-- Clean raw orders, flag data quality issues, deduplicate

with source as (
    select * from {{ source('raw_ecommerce', 'raw_orders') }}
),

-- Flag and handle known data quality issues
with_quality_flags as (
    select
        order_id,
        customer_id,
        cast(order_date as timestamp) as order_date,
        lower(trim(status)) as status,
        upper(trim(currency)) as currency,
        cast(total_amount as numeric) as total_amount,
        cast(total_amount_eur as numeric) as total_amount_eur,
        lower(trim(consent_level_at_order)) as consent_level_at_order,
        upper(trim(country_code)) as country_code,

        -- Data quality flags (don't filter yet — flag for observability)
        case when cast(total_amount as numeric) < 0 then true else false end as dq_negative_amount,
        case when cast(order_date as timestamp) > current_timestamp then true else false end as dq_future_date,

        -- Dedup: rank by order_id to catch intentional duplicates
        row_number() over (
            partition by order_id
            order by order_date
        ) as _row_num

    from source
),

deduplicated as (
    select * from with_quality_flags
    where _row_num = 1
)

select
    order_id,
    customer_id,
    order_date,
    status,
    currency,
    total_amount,
    total_amount_eur,
    consent_level_at_order,
    country_code,
    dq_negative_amount,
    dq_future_date
from deduplicated
