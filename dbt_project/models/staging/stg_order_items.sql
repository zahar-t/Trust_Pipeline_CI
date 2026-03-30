-- stg_order_items.sql

with source as (
    select * from {{ source('raw_ecommerce', 'raw_order_items') }}
),

cleaned as (
    select
        order_item_id,
        order_id,
        product_id,
        cast(quantity as integer) as quantity,
        cast(unit_price as numeric) as unit_price,
        cast(unit_price_eur as numeric) as unit_price_eur,

        -- Line total
        cast(quantity as integer) * cast(unit_price as numeric) as line_total,
        cast(quantity as integer) * cast(unit_price_eur as numeric) as line_total_eur,

        -- Dedup: rank by order_item_id to catch intentional duplicates
        row_number() over (
            partition by order_item_id
            order by order_id
        ) as _row_num

    from source
),

deduplicated as (
    select * from cleaned
    where _row_num = 1
)

select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    unit_price_eur,
    line_total,
    line_total_eur
from deduplicated
